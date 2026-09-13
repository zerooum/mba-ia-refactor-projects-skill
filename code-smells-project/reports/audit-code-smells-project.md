```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3 + Flask 3.1.1 (sqlite3 driver cru)
Files:   4 analyzed | 780 lines of code
Routes:  19 endpoints
Date:    2026-09-13
================================
```

## Summary

| Severidade | Findings |
|---|---|
| CRITICAL | 6 |
| HIGH | 7 |
| MEDIUM | 4 |
| LOW | 2 |
| **Total** | **19** |

Nível de organização: **Nível 1 — monolito flat.** Quatro módulos na raiz (`app.py`, `controllers.py`,
`models.py`, `database.py`), sem diretórios de camada. `models.py` mistura SQL, regra de negócio e
serialização; `controllers.py` e `app.py` executam SQL direto. O diretório `src/` existe mas está vazio e
não é versionado.

## Findings

### [CRITICAL] SQL Injection por concatenação (AP-02)

- **File:** `models.py:109-111`
- **Occurrences:** 22 (11 alimentadas por body/query string; 11 por path param `<int:>` ou valor já validado)
  - `models.py:109-111` — `login_usuario`: `email` e `senha` do body concatenados no `WHERE`
  - `models.py:47-50` — `criar_produto`: `nome`, `descricao`, `categoria` do body
  - `models.py:57-61` — `atualizar_produto`: `nome`, `descricao`, `categoria` do body (categoria nem é validada no update)
  - `models.py:126-129` — `criar_usuario`: `nome`, `email`, `senha` do body
  - `models.py:140` — `criar_pedido`: `item["produto_id"]` do body, sem checagem de tipo
  - `models.py:148-151` — `criar_pedido`: `usuario_id` do body, sem checagem de tipo
  - `models.py:155` — `criar_pedido`: `item["produto_id"]`
  - `models.py:157-161` — `criar_pedido`: `item["produto_id"]`, `item["quantidade"]`
  - `models.py:163-166` — `criar_pedido`: `item["quantidade"]`, `item["produto_id"]`
  - `models.py:291` — `buscar_produtos`: `termo` (query string `q`) em `LIKE`
  - `models.py:293` — `buscar_produtos`: `categoria` (query string)
  - `models.py:28`, `models.py:68`, `models.py:92`, `models.py:174`, `models.py:188`, `models.py:192`,
    `models.py:220`, `models.py:224`, `models.py:279-281`, `models.py:295`, `models.py:297` — mesmo padrão
    com valores hoje tipados (path `<int:>`, `float()` ou lista de status validada); explorável no primeiro
    refactor que mudar a origem do valor
- **Description:** Todas as queries de runtime são montadas por concatenação de string. Nenhuma usa
  placeholder — apenas o seed em `database.py:70-73` e `database.py:80-83` usa `?`.
- **Impact:** **Verificado em execução.** `POST /login` com
  `{"email": "admin@loja.com' OR '1'='1' --", "senha": "x"}` retornou HTTP 200 e autenticou como `Admin`
  sem a senha. Qualquer um dos 11 pontos alimentados por body/query permite dump ou destruição do banco.
- **Recommendation:** Trocar toda montagem por queries parametrizadas (`?`), dentro de repositórios na
  camada de dados. `buscar_produtos` monta o `WHERE` dinâmico acumulando cláusulas e parâmetros em listas
  separadas. (T-02)

### [CRITICAL] Dado sensível vazado na resposta (AP-06)

- **File:** `controllers.py:286-289`
- **Occurrences:** 20
  - `controllers.py:289` — `GET /health` devolve `secret_key` com o valor real da `SECRET_KEY`
  - `controllers.py:287-288` — `GET /health` devolve `db_path` e `debug`
  - `models.py:83` — `get_todos_usuarios` serializa `senha` → `GET /usuarios` lista a senha de todos
  - `models.py:99` — `get_usuario_por_id` serializa `senha` → `GET /usuarios/<id>`
  - `controllers.py:12`, `:22`, `:62`, `:96`, `:109`, `:126`, `:134`, `:144`, `:165`, `:186`, `:220`,
    `:227`, `:235`, `:255`, `:262`, `:292` e `app.py:78` — `jsonify({"erro": str(e)})` devolve a mensagem
    crua da exceção
- **Description:** A resposta HTTP carrega segredo de aplicação, senha de usuário e mensagem interna de
  exceção.
- **Impact:** **Verificado em execução.** `GET /usuarios/1` devolveu `"senha": "<senha do seed em texto puro>"`; `GET /health`
  devolveu a chave `secret_key`; `POST /produtos` com `"preco": "10"` devolveu HTTP 500 com
  `"'<' not supported between instances of 'str' and 'int'"`. Sem autenticação (AP-05), qualquer cliente
  anônimo colhe credenciais de todos os usuários e a chave que assina sessões.
- **Recommendation:** Serializador de usuário sem `senha`; `/health` sem `secret_key`/`db_path`
  (ambos mudam chaves do JSON — ver Breaking changes BC-1 e BC-2); mensagem genérica no 500 com a
  exceção só no log, via handler central (a chave `erro` é preservada). (T-07, T-10)

### [CRITICAL] Endpoint sensível sem autenticação — ausência total de autenticação (AP-05)

- **File:** `app.py:59-78`
- **Occurrences:** 11 rotas sensíveis (zero guards no projeto; `/login` não emite token nem sessão — `controllers.py:176-180`)
  - `app.py:59-78` — `POST /admin/query` executa **SQL arbitrário** vindo do body
  - `app.py:47-57` — `POST /admin/reset-db` apaga as quatro tabelas
  - `app.py:18` — `GET /usuarios` (dados pessoais + senha)
  - `app.py:19` — `GET /usuarios/<id>` (dados pessoais + senha)
  - `app.py:14` — `POST /produtos`
  - `app.py:15` — `PUT /produtos/<id>`
  - `app.py:16` — `DELETE /produtos/<id>`
  - `app.py:24` — `GET /pedidos` (pedidos de todos os clientes)
  - `app.py:25` — `GET /pedidos/usuario/<id>` (IDOR: qualquer id)
  - `app.py:26` — `PUT /pedidos/<id>/status` (aprovar/cancelar pedido alheio)
  - `app.py:28` — `GET /relatorios/vendas` (faturamento)
- **Description:** Nenhuma rota verifica identidade ou papel. `tipo = 'admin'` existe no schema
  (`database.py:32`) mas nunca é consultado.
- **Impact:** **Verificado em execução.** `POST /admin/query` com
  `{"sql": "SELECT email, senha FROM usuarios LIMIT 1"}` devolveu HTTP 200 com
  `admin@loja.com` / `<senha em texto puro>`. Um `DROP TABLE` pelo mesmo endpoint destrói o banco.
- **Recommendation:** Estruturar um guard reutilizável e aplicá-lo às rotas `/admin/*`. Proteger as
  demais rotas exige emitir credencial no `/login` e muda o contrato de todos os clientes — registrado
  como BC-3, não é feito sem aval. (T-09)

### [CRITICAL] Credenciais e segredos hardcoded (AP-01)

- **File:** `app.py:7`
- **Occurrences:** 6
  - `app.py:7` — `SECRET_KEY` literal
  - `controllers.py:289` — o mesmo literal repetido (e devolvido no `/health`)
  - `app.py:8` — `DEBUG = True` literal
  - `app.py:88` — `app.run(host="0.0.0.0", port=5000, debug=True)`: debugger Werkzeug exposto na rede
    (boot log: `Debugger is active!`, `Running on all addresses (0.0.0.0)`)
  - `controllers.py:288` — `"debug": True` literal na resposta
  - `database.py:76-78` — senhas iniciais de admin e clientes literais no seed
- **Description:** Nenhuma configuração vem do ambiente; segredo, modo debug, host e senhas iniciais
  estão no código.
- **Impact:** Quem lê o repositório conhece a `SECRET_KEY` e a senha do admin. Debug + `0.0.0.0` expõe o
  console interativo do Werkzeug (execução de código, protegido só pelo PIN) para qualquer host da rede.
- **Recommendation:** Módulo de config lendo `SECRET_KEY`, `DEBUG`, `HOST`, `PORT`, `DB_PATH` de variáveis
  de ambiente; `.env.example` com `CHANGE_ME`; `.env` no `.gitignore`; debug desligado por padrão. A chave
  commitada deve ser considerada vazada e rotacionada. (T-01)

### [CRITICAL] Senha em texto puro (AP-04)

- **File:** `models.py:126-129`
- **Occurrences:** 3
  - `models.py:126-129` — `criar_usuario` grava `senha` como veio no body
  - `models.py:109-111` — `login_usuario` compara a senha em texto puro dentro do SQL
  - `database.py:76-78` — seed grava senhas em texto puro
- **Description:** Não há hash de senha em nenhum ponto do ciclo (cadastro, seed, login).
- **Impact:** Qualquer leitura do banco — via AP-02, AP-05 (`/admin/query`) ou AP-06 (`GET /usuarios`) —
  entrega todas as senhas utilizáveis diretamente, inclusive em outros sistemas onde o usuário as reusa.
- **Recommendation:** `werkzeug.security.generate_password_hash` no cadastro e no seed;
  `check_password_hash` no login (busca por email, compara fora do SQL). Bancos existentes precisam de
  migração — ver BC-5. (T-10)

### [CRITICAL] God File (AP-03)

- **File:** `models.py:1-314`
- **Occurrences:** 3
  - `models.py:1-314` — 4 domínios (produtos, usuários, pedidos, relatórios) + SQL + regra de negócio
    (`criar_pedido` calcula total e checa estoque em `:137-146`; `relatorio_vendas` aplica faixas de
    desconto em `:256-262`) + serialização manual para `dict`
  - `controllers.py:1-292` — 4 domínios + validação + notificações (`:208-210`, `:247-250`) + SQL direto
    (`health_check`, `:264-292`)
  - `app.py:1-88` — config + registro de todas as rotas + dois handlers com SQL (`:47-78`) + boot
- **Description:** Nenhum arquivo tem responsabilidade única; cada um cobre todos os domínios e mais de
  uma camada.
- **Impact:** Qualquer mudança em pedidos toca os três arquivos; nada é testável isoladamente sem subir
  banco e HTTP.
- **Recommendation:** Separar por camada e por domínio: `config`, `database`, repositórios, serviços,
  controllers por recurso (blueprints), `app.py` só como factory + entrypoint. (T-03)

### [HIGH] Erro sem tratamento centralizado (AP-11)

- **File:** `controllers.py:10-12`
- **Occurrences:** 17
  - `controllers.py:10`, `:21`, `:60`, `:95`, `:108`, `:125`, `:133`, `:143`, `:164`, `:185`, `:218`,
    `:226`, `:234`, `:254`, `:261`, `:291` — `except Exception as e: return jsonify({"erro": str(e)}), 500`
    copiado em todo handler
  - `app.py:77` — mesmo bloco em `executar_query`
- **Description:** Não existe `@app.errorhandler`; cada handler repete o mesmo `try/except` genérico,
  que também transforma erro de entrada do cliente em 500.
- **Impact:** **Verificado em execução.** `POST /login` sem body → `dados.get` em `None` → HTTP 500;
  `GET /produtos/busca?preco_min=abc` → HTTP 500. Erro do cliente vira erro do servidor e a mensagem
  interna vaza (AP-06).
- **Recommendation:** Handler central para `Exception` (500 genérico + log) e para exceções de domínio
  (`ValidationError` → 400, `NotFoundError` → 404); remover os `try/except` dos handlers. (T-07)

### [HIGH] Validação ausente ou divergente (AP-16) — promovido de MEDIUM

- **File:** `controllers.py:195-201`
- **Occurrences:** 7
  - `controllers.py:195-201` — `criar_pedido`: `quantidade` sem checagem de sinal/tipo; `usuario_id` e
    `produto_id` sem tipo nem existência do usuário
  - `controllers.py:153-158` — `criar_usuario`: sem formato de email, sem unicidade (schema também não tem
    `UNIQUE`, `database.py:27-34`), sem política de senha
  - `controllers.py:169-170` e `controllers.py:239-240` — `dados.get` sem checar `dados is None`
  - `controllers.py:43-46` — `criar_produto`: `preco < 0` sem checar tipo
  - `controllers.py:81-90` — `atualizar_produto` diverge de `criar_produto` (`:47-54`): não valida
    tamanho do nome nem categoria
  - `controllers.py:118-121` — `buscar_produtos`: `float()` sem tratamento
  - `controllers.py:245` — `atualizar_status_pedido` não verifica se o pedido existe
- **Description:** Entradas são usadas sem checagem de tipo/faixa/existência, e create/update de produto
  aplicam regras diferentes.
- **Impact:** **Verificado em execução.** Pedido com `"quantidade": -5` retornou 201 com
  `"total": -1499.5` e o estoque do produto 3 subiu de 30 para 35; pedido para `usuario_id` 9999
  retornou 201; dois `POST /usuarios` com o mesmo email retornaram 201; `PUT /pedidos/9999/status`
  retornou 200. **Promoção a HIGH:** atinge caminho de autenticação (cadastro duplicado de email, login
  500) e de pagamento (total negativo).
- **Recommendation:** Validadores por recurso na camada de serviço, compartilhados entre create e update;
  erros de validação como exceção de domínio → 400 via handler central. Mudanças de status para entradas
  hoje aceitas vão em BC-4. (T-09)

### [HIGH] Regra de negócio na rota / Fat Controller (AP-07)

- **File:** `controllers.py:24-62`
- **Occurrences:** 5
  - `controllers.py:24-62` — `criar_produto`: 38 linhas de validação e lista de categorias literal (`:52`)
  - `controllers.py:64-96` — `atualizar_produto`: validação reescrita
  - `controllers.py:208-210` — `criar_pedido`: disparo de notificações (email/SMS/push) no handler
  - `controllers.py:242-250` — `atualizar_status_pedido`: lista de status válidos e decisão de notificação no handler
  - `models.py:256-262` — `relatorio_vendas`: faixas de desconto na camada de dados (sem serviço, a regra
    se divide entre controller e model)
- **Description:** Não há camada de serviço; validação, decisões de domínio e efeitos colaterais ficam no
  handler HTTP ou dentro das funções de SQL.
- **Impact:** A regra só é testável subindo HTTP + banco, e já divergiu (create vs update de produto).
- **Recommendation:** Criar serviços por domínio (`produto_service`, `usuario_service`,
  `pedido_service`, `relatorio_service`) recebendo a regra transportada como está. (T-04)

### [HIGH] Camada pulada (AP-10)

- **File:** `controllers.py:264-274`
- **Occurrences:** 3
  - `controllers.py:264-274` — `health_check` executa `SELECT COUNT(*)` direto
  - `app.py:47-57` — `reset_database` executa `DELETE` direto na rota
  - `app.py:59-78` — `executar_query` executa SQL direto na rota
- **Description:** Rotas falam com o banco sem passar pela camada de dados.
- **Impact:** A camada `models` não é o único ponto de acesso ao banco; qualquer mudança de schema ou de
  conexão precisa caçar SQL em três arquivos.
- **Recommendation:** Mover as queries para repositórios e expor via serviço. (T-04, T-05)

### [HIGH] Acoplamento forte sem injeção de dependência (AP-08)

- **File:** `models.py:1`
- **Occurrences:** 3
  - `models.py:1` — `from database import get_db`, chamado dentro de cada uma das 16 funções
  - `controllers.py:3` — idem, usado em `health_check`
  - `app.py:4` — idem, usado nas rotas admin
- **Description:** Cada função busca a conexão global por import; não há ponto para injetar outra conexão.
- **Impact:** Testar qualquer função exige o arquivo `loja.db` real no cwd.
- **Recommendation:** Conexão obtida por request (`flask.g`) via um único provider em `database.py`;
  repositórios recebem a conexão desse provider. (T-05)

### [HIGH] Fluxo multi-escrita sem transação (AP-12)

- **File:** `models.py:133-169`
- **Occurrences:** 1
  - `models.py:133-169` — `criar_pedido`: insere pedido (`:148`), insere itens (`:157`) e decrementa estoque
    (`:163-166`) sem `BEGIN`/`ROLLBACK` explícito; a checagem de estoque (`:144`) e o decremento (`:163`)
    são separados (TOCTOU)
- **Description:** O fluxo de checkout depende da transação implícita do `sqlite3` numa conexão
  compartilhada entre threads (AP-09): se uma exceção ocorrer no meio, as escritas pendentes ficam na
  conexão e são persistidas pelo `commit()` do próximo request de qualquer usuário.
- **Impact:** Dois pedidos concorrentes para o último item passam ambos na checagem de `:144` e deixam o
  estoque negativo; falha no meio deixa pedido sem itens.
- **Recommendation:** Transação explícita com rollback em erro e decremento condicional
  (`UPDATE ... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?`). (T-13)

### [HIGH] Estado global mutável (AP-09)

- **File:** `database.py:4-11`
- **Occurrences:** 1
  - `database.py:4-11` — `db_connection` global reatribuído via `global`, aberto com `check_same_thread=False`
- **Description:** Uma única conexão SQLite é compartilhada por todas as threads do servidor.
- **Impact:** Transações de requests concorrentes se misturam (causa raiz do risco em AP-12); a conexão
  nunca é fechada.
- **Recommendation:** Conexão por request em `flask.g`, fechada em `teardown_appcontext`; DDL e seed
  executados uma vez no boot. (T-06, T-13)

### [MEDIUM] API deprecated em uso (AP-18)

- **File:** `requirements.txt:1-2`
- **Occurrences:** 13
  - `requirements.txt:1` — `flask==3.1.1`: `PYSEC-2026-2151`, corrigido em 3.1.3
  - `requirements.txt:2` — `flask-cors==5.0.1`: `PYSEC-2026-1383`, `PYSEC-2026-1384`, `PYSEC-2026-1385`, corrigidos em 6.0.0 (major)
  - `controllers.py:8`, `:11`, `:54`, `:57`, `:61`, `:106`, `:208`, `:219`, `:248`, `:250`, `models.py:143` —
    `"texto" + str(x)` no lugar de f-string
- **Description:** Nenhuma API removida ou deprecada no código (grep do catálogo vazio; boot com
  `-W error::DeprecationWarning` sem warnings). As dependências fixadas têm vulnerabilidades conhecidas
  (`pip-audit`) e o estilo de concatenação é o obsoleto do catálogo.
- **Impact:** Vulnerabilidades publicadas nas duas únicas dependências da aplicação.
- **Recommendation:** Subir `flask` para 3.1.3 (patch). `flask-cors` 6.0.0 é major — só com smoke verde
  após a troca; se quebrar, fica registrado como pendência. Trocar concatenação por f-string. (T-11)

### [MEDIUM] Duplicação de código (AP-17)

- **File:** `models.py:171-233`
- **Occurrences:** 4 blocos
  - `models.py:171-201` e `models.py:203-233` — `get_pedidos_usuario` e `get_todos_pedidos` idênticas exceto pelo `WHERE`
  - `models.py:12-21`, `models.py:31-40`, `models.py:304-313` — serialização de produto repetida 3×
  - `models.py:79-86`, `models.py:95-102` — serialização de usuário repetida 2×
  - `controllers.py:28-46` e `controllers.py:72-90` — bloco de validação de produto copiado (e divergente, AP-16)
- **Description:** Mesmos blocos reescritos em várias funções.
- **Impact:** A divergência já aconteceu: o update de produto perdeu as validações de nome e categoria.
- **Recommendation:** Um serializador por entidade (`row_to_produto`, `row_to_usuario`), uma função de
  pedidos com filtro opcional, um validador de produto usado por create e update. (T-04, T-12)

### [MEDIUM] Configuração ou middleware inseguro (AP-19)

- **File:** `app.py:9`
- **Occurrences:** 5
  - `app.py:9` — `CORS(app)` libera qualquer origem
  - `app.py:21` — `/login` sem rate limiting (brute force livre)
  - `models.py:7`, `models.py:75`, `models.py:206` — `SELECT *` sem paginação em coleções que crescem
  - `controllers.py:269-274` — healthcheck roda `COUNT(*)` em três tabelas inteiras
  - `database.py:5` — `db_path = "loja.db"` relativo ao cwd: o banco muda de lugar conforme o diretório de onde a app é iniciada
- **Description:** Middleware e defaults sem restrição; caminho do banco dependente do cwd.
- **Impact:** Qualquer site pode chamar a API a partir do navegador do usuário; `/login` aceita tentativas
  ilimitadas.
- **Recommendation:** Origens de CORS e `DB_PATH` via config (default atual preservado para não mudar
  comportamento); paginação e rate limit mudam contrato — ficam como recomendação. (T-01, T-09)

### [MEDIUM] N+1 queries (AP-15)

- **File:** `models.py:187-199`
- **Occurrences:** 4
  - `models.py:187-199` — `get_pedidos_usuario`: `GET /pedidos/usuario/<id>` = 1 + N + ΣM queries
  - `models.py:219-231` — `get_todos_pedidos`: `GET /pedidos` = 1 + N + ΣM queries
  - `models.py:239-254` — `relatorio_vendas`: 5 queries sequenciais onde um `SELECT` com `SUM(CASE ...)` resolve
  - `models.py:140` e `models.py:155` — `criar_pedido` lê cada produto duas vezes
- **Description:** Queries dentro de laço, uma por pedido e outra por item.
- **Impact:** 100 pedidos com 3 itens = 401 queries por `GET /pedidos`.
- **Recommendation:** Um `JOIN itens_pedido/produtos` agrupado em memória por pedido; agregação única no
  relatório; reutilizar o produto lido na validação. (T-08)

### [LOW] Ruído de legibilidade (AP-21)

- **File:** `controllers.py:8`
- **Occurrences:** 5 categorias
  - `print` como logging (19): `controllers.py:8`, `:11`, `:57`, `:61`, `:106`, `:161`, `:179`, `:182`,
    `:208`, `:209`, `:210`, `:219`, `:248`, `:250`; `app.py:56`, `:83`, `:84`, `:85`, `:86` — os de
    `controllers.py:161`, `:179`, `:182` gravam email (dado pessoal) no stdout
  - imports não usados: `database.py:2` (`os`), `models.py:2` (`sqlite3`)
  - nomes: `cursor2`/`cursor3` em `models.py:187`, `:191`, `:219`, `:223`; `id` sombreando builtin em
    `controllers.py:14`, `:64`, `:98`, `:136` e `models.py:24`, `:54`, `:65`, `:89`
  - redundância: `if not itens or len(itens) == 0` em `controllers.py:200`; `total = total + ...` em `models.py:146`
  - inconsistência: `"ambiente": "producao"` literal em `controllers.py:286` com debug ligado
- **Description:** Ruído que não quebra comportamento mas dificulta leitura e operação.
- **Impact:** Sem níveis de log, sem como silenciar; PII no stdout.
- **Recommendation:** `logging` com logger por módulo, remover imports mortos, renomear. (T-11, T-12)

### [LOW] Magic numbers e magic strings (AP-20)

- **File:** `models.py:257-262`
- **Occurrences:** 5
  - `models.py:257-262` — faixas de desconto `10000`/`0.1`, `5000`/`0.05`, `1000`/`0.02`
  - `controllers.py:52` — lista de categorias literal
  - `controllers.py:242` — lista de status literal; `models.py:150`, `:247`, `:250`, `:253` — status como string solta
  - `controllers.py:47`, `controllers.py:49` — limites de tamanho do nome `2` e `200`
  - `app.py:35` e `controllers.py:285` — versão `"1.0.0"` em dois lugares
- **Description:** Regras de domínio expressas como literais espalhados.
- **Impact:** Adicionar um status exige editar 3 lugares; mudar faixa de desconto exige ler o código do SQL.
- **Recommendation:** Módulo de constantes de domínio (`CATEGORIAS_VALIDAS`, `STATUS_PEDIDO`,
  `FAIXAS_DESCONTO`, `API_VERSION`). (T-12)

## APIs Deprecated

Grep do catálogo (`datetime.utcnow`, `before_first_request`, `flask.Markup/escape`, `werkzeug.urls`,
`distutils`, `imp`, `.query.get(`, …): **nenhuma ocorrência.** Boot com
`python -W error::DeprecationWarning app.py`: **nenhum warning.**

| Obsoleto | Ocorrências | Equivalente moderno |
|---|---|---|
| `"texto" + str(x)` | `controllers.py:8`, `:11`, `:54`, `:57`, `:61`, `:106`, `:208`, `:219`, `:248`, `:250`, `models.py:143` (11x) — mais 22x em SQL, cobertos por AP-02 | f-string (placeholders `?` no SQL) |
| `flask==3.1.1` (PYSEC-2026-2151) | `requirements.txt:1` | `flask==3.1.3` |
| `flask-cors==5.0.1` (PYSEC-2026-1383/1384/1385) | `requirements.txt:2` | `flask-cors>=6.0.0` |

## Breaking changes propostos

Cada item altera o contrato HTTP (chave de JSON ou status) ou dados persistidos e **só é aplicado com aval
explícito**. Sem aval, a Fase 3 preserva o comportamento atual e o finding correspondente fica registrado
como residual.

1. **BC-1 — Remover `senha` de `GET /usuarios` e `GET /usuarios/<id>`** (AP-06). Remove uma chave do JSON.
2. **BC-2 — Remover `secret_key` e `db_path` de `GET /health`** (AP-06, AP-01). Remove chaves do JSON;
   `debug` passa a refletir a config real.
3. **BC-3 — Exigir credencial de admin em `POST /admin/query` e `POST /admin/reset-db`** (AP-05): header
   com token vindo de variável de ambiente; sem ele → 401. Proteger as demais rotas sensíveis exige que
   `/login` emita token e que todos os clientes o enviem — proposto como trabalho separado.
4. **BC-4 — Validação mais estrita** (AP-16, AP-11): entrada malformada passa de 500 para 400
   (body ausente, tipo errado, `preco_min=abc`); `quantidade <= 0` e `usuario_id` inexistente passam de 201
   para 400; email duplicado passa de 201 para 400; `PUT /pedidos/<id>/status` em pedido inexistente passa
   de 200 para 404.
5. **BC-5 — Hash de senha** (AP-04): o contrato HTTP não muda (login continua respondendo 200/401 igual), mas
   um `loja.db` já existente com senhas em texto puro precisa de migração no boot (rehash das senhas que não
   são hash); sem ela os logins antigos param de funcionar.

Não são breaking change (mantêm chaves e status): queries parametrizadas, mensagem genérica no lugar de
`str(e)` (chave `erro` preservada), transação no checkout, conexão por request, reestruturação em camadas.

## Baseline de comportamento

33/33 requisições responderam (19 endpoints; 20 × 2xx, 13 × 4xx, 0 × 5xx). Rotas destrutivas
(`DELETE /produtos/11`, `POST /admin/reset-db`) executadas por último; nenhuma excluída.
Contrato em `.refactor-arch/rotas.tsv`; saídas em `.refactor-arch/baseline/`.

```
================================
Total: 19 findings
================================
```

## Resultado da refatoração (Fase 3)

Executada em 6 ondas, smoke após cada uma. Estrutura final: `src/{config,infra,models,controllers,views,middlewares}`
com `src/app.py` como composition root; `app.py` na raiz é só o launcher (`python app.py` continua valendo).

| Severidade | Resolvidos | Pendentes |
|---|---|---|
| CRITICAL | 5/6 | AP-05 — só `/admin/*` recebeu guard (BC-3); as demais rotas sensíveis continuam sem autenticação. Resolver exige emitir credencial no `/login` (novo contrato para todos os clientes). |
| HIGH | 6/7 | AP-16 parcial — tipos, body ausente, quantidade, usuário inexistente, email duplicado (checado na aplicação) e pedido inexistente resolvidos; formato de email, política de senha e `UNIQUE` no schema não foram aprovados. |
| MEDIUM | 3/4 | AP-19 parcial — `DB_PATH` e `CORS_ORIGINS` vêm do ambiente (default `*` mantido); rate limit no `/login`, paginação e healthcheck sem `COUNT(*)` mudam contrato. |
| LOW | 2/2 | — |

Breaking changes aplicados (aprovados no GATE): BC-1, BC-2, BC-3, BC-4, BC-5. Smoke final: 30/33 requisições com
status idêntico ao baseline; as 3 divergências são BC-3 (`/admin/*` sem `X-Admin-Token` → 401), verificadas com
token → 200.

Mudanças de comportamento além do contrato do smoke, todas intencionais:

- `PUT /produtos/<id>` passa a aplicar as mesmas validações do create (tamanho do nome, categoria).
- Pedido com o mesmo produto repetido acima do estoque → 400 com rollback (antes: estoque negativo).
- Rota inexistente devolve 404 em JSON (antes: HTML).
- Erro no SQL de `/admin/query` → 400 com a mensagem do SQLite (antes: 500).
- `debug` desligado por padrão; `/health.debug` reflete a config real.
- Logs sem email do usuário; `print` substituído por `logging`.

Ação obrigatória fora do código: a `SECRET_KEY` antiga e as senhas do seed estão no histórico do git — rotacionar.
