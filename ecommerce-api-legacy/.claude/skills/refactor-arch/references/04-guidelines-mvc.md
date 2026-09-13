# 04 — Guidelines de Arquitetura MVC

Arquitetura alvo da Fase 3.

**Índice:** [Regra de dependência](#regra-de-dependência) · [Camadas](#responsabilidade-por-camada) · [View numa API](#o-que-é-view-numa-api) · [Composition root](#composition-root) · [Estruturas alvo](#estruturas-alvo) · [Adaptação por nível](#adaptação-por-nível-de-organização) · [Critérios de pronto](#critérios-de-pronto)

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
# app.py — composition root
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

`config/ · models/ · controllers/ · views|routes/ · middlewares/ · infra/ · entrypoint`

Adapte os nomes à convenção da linguagem (`internal/` em Go, `src/main/java/...` em Java). **Não force `src/` onde a convenção da stack não usa.** O que importa é a separação, não o nome do diretório.

---

## Adaptação por nível de organização

A Fase 3 **não aplica a mesma receita nos três níveis**. Use o nível detectado na Fase 1.

### Nível 1 — Monolito flat
Extração completa.
1. Config e segredos para `config/` (T-01)
2. Cada domínio do God File vira um model (T-03, T-05)
3. Regra de negócio dos handlers vai para controllers (T-04)
4. Rotas viram blueprints/routers finos (T-03)
5. Entrypoint vira composition root (T-06)
6. Error handler central (T-07)

### Nível 2 — Camadas nominais
Os diretórios já existem; a responsabilidade não. **Não recrie a estrutura, preencha-a.**
1. Config e segredos primeiro (T-01)
2. Resolva a camada fantasma (AP-14): cada módulo não usado ou passa a ser consumido, ou é removido — **decida um e registre a decisão**
3. Mova regra de negócio das rotas para controllers/services (T-04)
4. Reaproveite método de model já existente e não chamado antes de escrever qualquer lógica nova
5. Elimine a lógica duplicada que existia porque o método não era usado
6. Mova sub-recurso hospedado no arquivo errado para o seu próprio módulo (ex: CRUD de categoria dentro de `report_routes`)
7. Error handler central substituindo o `try/except` repetido

**Cuidado específico:** mover rota entre blueprints pode mudar a ordem de registro. Rota estática (`/tasks/search`) e rota com parâmetro (`/tasks/<id>`) no mesmo prefixo colidem se o converter de tipo for removido. Preserve os converters (`<int:id>`) exatamente como estão, ou registre a estática antes.

### Nível 3 — Camadas reais
Sem reestruturação. Foco em segurança, performance (T-08), validação (T-09), API deprecated (T-11) e higiene (T-12). Propor reorganização aqui é mudança não solicitada.

---

## Critérios de pronto

A Fase 3 só termina com todos verificados:

- [ ] Estrutura de diretórios segue o padrão MVC da stack
- [ ] Configuração em módulo próprio, lendo env var, sem valor hardcoded
- [ ] Models abstraem os dados; nenhum SQL fora deles
- [ ] Views/Routes finas: sem query, sem cálculo de negócio
- [ ] Controllers concentram o fluxo do caso de uso
- [ ] Error handling centralizado; nenhum `try/except` repetido por handler
- [ ] Entry point é composition root, sem lógica
- [ ] Aplicação inicia sem erro
- [ ] Todos os endpoints do `rotas.tsv` respondem com o mesmo status do baseline
