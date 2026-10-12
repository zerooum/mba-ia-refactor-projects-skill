# 04 — Guidelines de Arquitetura MVC

Arquitetura alvo da Fase 3.

**Índice:** [Regra de dependência](#regra-de-dependência) · [Camadas](#responsabilidade-por-camada) · [View numa API](#o-que-é-view-numa-api) · [Composition root](#composition-root) · [Layout src/](#layout-todo-código-da-aplicação-em-src) · [Estruturas alvo](#estruturas-alvo) · [Adaptação por nível](#adaptação-por-nível-de-organização) · [Critérios de pronto](#critérios-de-pronto)

---

## Regra de dependência

```
View / Rota  →  Controller  →  Model  →  Banco
```

Setas apontam para baixo e **só** para baixo.

- Model **não** conhece HTTP: nada de `request`, `jsonify`, `res.json`, status code, `abort()`.
- View **não** conhece SQL: nada de `cursor.execute`, `.query.`, `db.session`.
- Controller não sabe de onde veio a requisição nem para onde vai a resposta — recebe dados já parseados, devolve dados ou levanta exceção de domínio.

Teste de verificação: se você não consegue chamar o Controller de um script de linha de comando, sem servidor HTTP, a separação não está feita.

---

## Responsabilidade por camada

| Camada | Responsabilidade | PODE conter | NÃO pode conter |
|---|---|---|---|
| **Config** | Carregar configuração do ambiente | Leitura de env var, defaults de desenvolvimento, validação de config obrigatória | Valor secreto literal |
| **Model / Repository** | Persistência e regras invariantes do dado | Queries parametrizadas, mapeamento de linha para objeto, transações, validação de invariante do domínio | `request`, `jsonify`, status code, regra de caso de uso |
| **Controller / Service** | Orquestrar o caso de uso | Chamadas a models, decisão de negócio, cálculo, coordenação de transação, levantar exceção de domínio | SQL cru, `request`, montagem de resposta HTTP |
| **View / Rota** | Traduzir HTTP ↔ domínio | Extrair body/params, validar formato de entrada, chamar o controller, serializar a saída, mapear exceção para status | Query, cálculo de negócio, lista de valores válidos do domínio |
| **Middleware** | Preocupação transversal | Error handler central, autenticação, CORS, logging, rate limit | Regra de negócio |
| **Entrypoint** | Composition root | Instanciar dependências, injetar, registrar rotas e middlewares, subir o servidor | Rota, query, regra |

Um handler de rota bem feito tem 3 a 8 linhas.

---

## O que é "View" numa API

Não existe template. A camada View é **rota + serialização**:

- **Rota** — path, método, extração de entrada, chamada do controller, status code de saída.
- **Serializer / Schema** — converte objeto de domínio para o JSON público. É aqui que campo sensível é **omitido** (senha, hash, token interno). A regra de "o que sai" mora na View, não no Model.

Em app não-HTTP, View é a camada de entrada que existir: comando de CLI, consumer de fila, handler de evento. As demais camadas não mudam.

---

## Composition root

O entrypoint monta o grafo de objetos e não faz mais nada:

```python
# src/app.py — composition root
def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or Settings())

    db = Database(app.config["DATABASE_URL"])
    produto_controller = ProdutoController(ProdutoRepository(db))

    register_error_handlers(app)
    app.register_blueprint(make_produto_routes(produto_controller))
    return app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
```

Consequências obrigatórias:
- Nada de DDL, seed ou `create_all()` rodando no import do módulo — só dentro da factory ou de um comando explícito.
- Nada de conexão criada em nível de módulo.
- A factory aceita config alternativa (é o que torna a app testável).

---

## Layout: todo código da aplicação em `src/`

Vale para os três níveis de organização. O projeto refatorado tem esta forma:

```
<projeto>/
├── src/                 # TODO código da aplicação: entrypoint, seed, camadas
├── reports/             # relatório da auditoria
├── <manifesto>          # requirements.txt / pyproject.toml / package.json + lockfile
├── .env.example  .gitignore  README.md
└── Dockerfile, CI, docs/   (se existirem)
```

A raiz guarda só arquivos **do projeto**; nenhum `.py`/`.js` da aplicação e nenhum diretório de camada fica fora de `src/`.

| Manifesto presente | Layout |
|---|---|
| `pom.xml` ou `build.gradle` | O da toolchain: `src/main/java/...` (já é `src/`) |
| `go.mod` | O da toolchain: `cmd/<app>/` + `internal/` |
| Qualquer outro | `src/` |

A mudança para `src/` é a **onda 0** da Fase 3 (T-15): `git mv` puro, antes de qualquer edição, para o git registrar os arquivos como rename com 100% de similaridade. Movidos depois de editados, eles aparecem como delete + add.

### O que quebra ao mover para `src/`

Confira cada item antes de rodar o smoke da onda 0:

| Item | Sintoma | Correção |
|---|---|---|
| Comando de boot | `python app.py` não acha o arquivo | `python src/app.py` / `node src/app.js`; atualize `scripts` do `package.json`, `Procfile`, `Dockerfile`, CI e README |
| Caminho relativo a `__file__` / `__dirname` | `.env`, templates ou arquivos estáticos não carregam | Resolva a partir da raiz do projeto (`Path(__file__).resolve().parents[N]`) |
| Flask `instance_path` | SQLite `sqlite:///x.db` passa a criar `src/instance/x.db` e o banco "some" | `Flask(__name__, instance_path=<raiz>/instance)` ou `DATABASE_URL` absoluto |
| SQLite relativo ao cwd (driver cru, Node) | Banco criado em outro diretório | Caminho do banco via config, resolvido a partir da raiz |
| Imports | `ModuleNotFoundError` / `Cannot find module` | Python: `python src/app.py` põe `src/` no `sys.path`, então imports absolutos entre módulos de `src/` continuam valendo. Node: `require` relativo entre arquivos movidos juntos continua valendo. Ajuste só o import que atravessa a fronteira `src/` ↔ raiz |
| Testes | pytest/jest não acham os módulos | `pythonpath = src` no `pytest.ini`/`pyproject.toml`; `roots`/`moduleDirectories` no jest |
| `main` do `package.json` | `npm start` quebra | `"main": "src/app.js"` |

**Validar:** app sobe a partir de outro diretório (`cd /tmp && python <projeto>/src/app.py`); banco e `.env` continuam na raiz; smoke idêntico ao baseline.

---

## Estruturas alvo

### Flask

```
src/
├── config/
│   └── settings.py          # lê env vars, sem valor secreto literal
├── models/
│   ├── produto_model.py     # queries + invariantes de Produto
│   └── usuario_model.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── views/
│   ├── produto_routes.py    # Blueprint fino
│   └── serializers.py
├── middlewares/
│   ├── error_handler.py
│   └── auth.py
├── infra/
│   └── database.py          # conexão, transação, teardown por request
└── app.py                   # composition root (create_app)
```

### Express

```
src/
├── config/index.js          # process.env, sem segredo literal
├── models/
│   ├── userModel.js
│   └── courseModel.js
├── controllers/
│   └── checkoutController.js
├── routes/
│   ├── checkoutRoutes.js
│   └── index.js
├── middlewares/
│   ├── errorHandler.js
│   └── validate.js
├── infra/
│   └── db.js                # conexão promisificada
└── app.js                   # composition root
```

### Genérico

`src/` → `config/ · models/ · controllers/ · views|routes/ · middlewares/ · infra/ · entrypoint`

O container é sempre o da tabela de [Layout](#layout-todo-código-da-aplicação-em-src). Dentro dele, o nome de cada camada pode seguir o que o projeto já usa (ver Nível 2).

---

## Adaptação por nível de organização

A Fase 3 **não aplica a mesma receita nos três níveis**. Use o nível detectado na Fase 1. O que os três têm em comum: a onda 0 leva o código para `src/` (T-15) antes de qualquer outra mudança.

### Nível 1 — Monolito flat
Extração completa, com todo arquivo novo nascendo em `src/`.
0. `git mv` do entrypoint e dos módulos soltos para `src/` (T-15)
1. Config e segredos para `src/config/` (T-01)
2. Cada domínio do God File vira um model (T-03, T-05)
3. Regra de negócio dos handlers vai para controllers (T-04)
4. Rotas viram blueprints/routers finos (T-03)
5. Entrypoint vira composition root (T-06)
6. Error handler central (T-07)

### Nível 2 — Camadas nominais
Os diretórios de camada já existem; a responsabilidade não. **Mova-os para `src/` e preencha-os** — não os recrie nem os renomeie.
0. `git mv` de cada diretório de camada, do entrypoint e do seed para `src/` (T-15). Mantenha os nomes: um `services/` existente assume o papel de controller; `routes/` assume o de view
1. Config e segredos (T-01)
2. Resolva a camada fantasma (AP-14): cada módulo não usado ou passa a ser consumido, ou é removido — **decida um e registre a decisão**
3. Mova regra de negócio das rotas para controllers/services (T-04)
4. Reaproveite método de model já existente e não chamado antes de escrever qualquer lógica nova
5. Elimine a lógica duplicada que existia porque o método não era usado
6. Mova sub-recurso hospedado no arquivo errado para o seu próprio módulo (ex: CRUD de categoria dentro de `report_routes`)
7. Error handler central substituindo o `try/except` repetido

**Cuidado específico:** mover rota entre blueprints pode mudar a ordem de registro. Rota estática (`/tasks/search`) e rota com parâmetro (`/tasks/<id>`) no mesmo prefixo colidem se o converter de tipo for removido. Preserve os converters (`<int:id>`) exatamente como estão, ou registre a estática antes.

### Nível 3 — Camadas reais
Sem reestruturação de responsabilidades. A única mudança estrutural é a onda 0: se o código está fora de `src/`, `git mv` para `src/` (T-15), mantendo nomes e divisão de arquivos. Depois, foco em segurança, performance (T-08), validação (T-09), API deprecated (T-11) e higiene (T-12).

---

## Critérios de pronto

A Fase 3 só termina com todos verificados:

- [ ] Todo código da aplicação dentro de `src/` (ou no layout da toolchain, pela tabela de Layout); raiz só com arquivos do projeto
- [ ] Estrutura de diretórios dentro de `src/` segue o padrão MVC da stack
- [ ] App sobe a partir de outro diretório de trabalho, com `.env` e banco resolvidos na raiz
- [ ] Configuração em módulo próprio, lendo env var, sem valor hardcoded
- [ ] Models abstraem os dados; nenhum SQL fora deles
- [ ] Views/Routes finas: sem query, sem cálculo de negócio
- [ ] Controllers concentram o fluxo do caso de uso
- [ ] Error handling centralizado; nenhum `try/except` repetido por handler
- [ ] Entry point é composition root, sem lógica
- [ ] Aplicação inicia sem erro
- [ ] Todos os endpoints do `rotas.tsv` respondem com o mesmo status do baseline
