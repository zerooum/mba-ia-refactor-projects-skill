```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.0.52)
Files:   14 analyzed | 1158 lines of code
Routes:  22 endpoints
Date:    2026-09-13
================================
```

## Summary

| Severidade | Findings |
|---|---|
| CRITICAL | 4 |
| HIGH | 6 |
| MEDIUM | 4 |
| LOW | 3 |
| **Total** | **17** |

**Nível de organização:** Nível 2 — camadas nominais. Os diretórios `models/`, `routes/`,
`services/` e `utils/` existem, mas:

- `services/notification_service.py` nunca é importado (grep por `from services` / `NotificationService`: zero resultados fora da própria definição);
- as rotas acessam o banco direto: 75 usos de `.query.`/`db.session` em `routes/` (report 31, task 24, user 20);
- `Task.validate_status`, `Task.validate_priority`, `Task.is_overdue` e `User.is_admin` nunca são chamados — a lógica está copiada inline nas rotas;
- de `utils/helpers.py`, só `format_date` e `calculate_percentage` são importados (`routes/report_routes.py:7`), e nenhum dos dois é chamado.

## Findings

### [CRITICAL] Ausência total de autenticação e autorização (AP-05)

- **File:** `routes/user_routes.py:210`
- **Occurrences:** 22 endpoints sem guard; destaques:
  - `routes/user_routes.py:210` — `POST /login` devolve `'fake-jwt-token-' + str(user.id)`: token previsível e nunca verificado em lugar nenhum
  - `routes/user_routes.py:52` e `routes/user_routes.py:71` — `POST /users` aceita `role: "admin"` vindo do body (auto-cadastro como admin)
  - `routes/user_routes.py:119-122` — `PUT /users/<id>` troca `role` de qualquer usuário
  - `routes/user_routes.py:134` — `DELETE /users/<id>` apaga qualquer usuário e todas as tasks dele (IDOR)
  - `routes/report_routes.py:12`, `routes/report_routes.py:103` — relatórios com nome/email de todos os usuários
  - `routes/task_routes.py:225`, `routes/report_routes.py:211` — deletes de task e categoria abertos
- **Description:** O projeto não tem nenhum guard (`login_required`, `before_request`, verificação de token):
  o grep por `authenticate|authorize|login_required|jwt_required|before_request` só encontra
  `User.is_admin` (`models/user.py:34`), que nunca é chamado. O "token" do login é decorativo.
- **Impact:** **Verificado em execução.** `POST /users` com `{"role":"admin","email":"h@x",...}` retornou
  201 com `"role":"admin"`; `PUT /users/2 {"role":"admin"}` retornou 200; `DELETE /users/3` sem credencial
  retornou 200. Qualquer cliente anônimo vira admin, altera ou apaga dados de qualquer usuário.
- **Recommendation:** Criar a estrutura de guard (decorator na camada de rota) e a verificação do token;
  exigir autenticação nas rotas de escrita e de dado pessoal, e restringir atribuição de `role`.
  Isso muda o contrato (novas respostas 401/403) — ver Breaking change #2. (T-09)

### [CRITICAL] Hash de senha e traceback vazados na resposta HTTP (AP-06)

- **File:** `models/user.py:21`
- **Occurrences:** 5
  - `models/user.py:21` — `User.to_dict()` inclui `'password': self.password`
  - `routes/user_routes.py:33` — `GET /users/<id>` serializa via `to_dict()`
  - `routes/user_routes.py:85` — `POST /users`
  - `routes/user_routes.py:129` — `PUT /users/<id>`
  - `routes/user_routes.py:209` — `POST /login` devolve o hash dentro de `user`
- **Description:** O hash da senha sai em toda resposta que serializa `User` por `to_dict()`. Além disso,
  com `debug=True` (`app.py:34`), toda exceção não tratada devolve a página do Werkzeug Debugger com
  stack trace e trechos do código-fonte.
- **Impact:** **Verificado em execução.** `POST /login` (baseline) retornou
  `"password": "81dc9bdb52d04dc20036dbd8313ed055"` — MD5 de `1234`, reversível em qualquer rainbow table.
  `POST /tasks {"title":"Tarefa","priority":"3"}` retornou 500 `text/html` com
  `TypeError ... // Werkzeug Debugger` e 3 referências a `task_routes.py` no corpo.
- **Recommendation:** Tirar `password` da serialização pública (Breaking change #1) e desligar o debug por
  env var com handler central de erro devolvendo JSON genérico. (T-10, T-07)

### [CRITICAL] Credenciais e segredos hardcoded + debugger exposto (AP-01)

- **File:** `app.py:13`
- **Occurrences:** 4
  - `app.py:13` — `SECRET_KEY` literal
  - `services/notification_service.py:7-10` — host, usuário e senha SMTP literais (`email_password` na linha 10)
  - `app.py:34` — `app.run(debug=True, host='0.0.0.0', port=5000)`: debugger interativo do Werkzeug escutando em todas as interfaces
  - `app.py:11` — URI do banco literal (não é segredo, mas impede trocar o banco por ambiente)
- **Description:** Toda configuração sensível está no código. `python-dotenv` está no
  `requirements.txt:6` mas nunca é carregado; não existe `.env` nem `.env.example`.
- **Impact:** Qualquer pessoa com acesso ao repositório tem a `SECRET_KEY` (forja de sessão/cookie assinado)
  e a senha da conta SMTP. O debugger em `0.0.0.0` expõe traceback a qualquer host da rede (verificado:
  resposta 500 em HTML do debugger). Os segredos já commitados precisam ser rotacionados.
- **Recommendation:** Mover tudo para variáveis de ambiente, `.env.example` com `CHANGE_ME`, `.env` no
  `.gitignore`, `debug`/host/porta vindos de config com default seguro. (T-01)

### [CRITICAL] Senha com MD5 sem salt e comparação não constante (AP-04)

- **File:** `models/user.py:29`
- **Occurrences:** 2
  - `models/user.py:29` — `set_password`: `hashlib.md5(pwd.encode()).hexdigest()`
  - `models/user.py:32` — `check_password`: compara digest com `==`
- **Description:** MD5 sem salt nem fator de custo; senhas iguais geram hashes iguais.
- **Impact:** Combinado com AP-06, qualquer cliente lê o hash e recupera a senha instantaneamente
  (`81dc9bdb…` = `1234`, visto no baseline). Comparação com `==` permite timing attack.
- **Recommendation:** `werkzeug.security.generate_password_hash`/`check_password_hash` (já instalado com
  Flask), aceitando o hash MD5 legado no login e regravando no formato novo, para não invalidar contas
  existentes. (T-10)

### [HIGH] Camada pulada — rotas consultam e gravam no banco direto (AP-10)

- **File:** `routes/task_routes.py:14`
- **Occurrences:** 75
  - `routes/report_routes.py:15-163` — 31 acessos (`Task.query`, `User.query`, `Category.query`, `db.session`), incluindo 12 `count()` seguidos em `:15-28`
  - `routes/task_routes.py:14-281` — 24 acessos, inclusive `db.session.add/commit/rollback` em `:147-152`, `:218-222`, `:232-237`
  - `routes/user_routes.py:12-197` — 20 acessos, inclusive delete em laço `:140-146`
  - `routes/task_routes.py:2`, `routes/user_routes.py:2`, `routes/report_routes.py:2` — handlers importam o `db` global
- **Description:** Não existe camada entre handler HTTP e ORM: cada handler monta query, controla a
  transação e serializa. Os models só declaram colunas e `to_dict()`.
- **Impact:** Nenhuma regra é testável sem subir HTTP e banco; a mesma query (`Task.query.filter_by(user_id=...)`)
  aparece em `routes/user_routes.py:35`, `:140`, `:159` e `routes/report_routes.py:56`, `:109`.
- **Recommendation:** Extrair repositórios/serviços por agregado (tasks, users, categories, reports);
  handler só traduz HTTP ↔ serviço. (T-04, T-05)

### [HIGH] Camada fantasma — service, helpers e métodos de model nunca usados (AP-14)

- **File:** `services/notification_service.py:4`
- **Occurrences:** 22
  - `services/notification_service.py:4` — `NotificationService` (5 métodos) nunca importado nem instanciado
  - `utils/helpers.py:9`, `:14` — `format_date`, `calculate_percentage`: importados em `routes/report_routes.py:7`, nunca chamados; `round((x / total) * 100, 2)` reescrito em `routes/task_routes.py:296`, `routes/report_routes.py:67`, `:151`
  - `utils/helpers.py:19`, `:25`, `:31`, `:36`, `:43`, `:52`, `:57` — `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `parse_date`, `is_valid_color`, `process_task_data`: nunca referenciados
  - `utils/helpers.py:110-116` — 7 constantes (`VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, …) nunca referenciadas; os valores estão literais nas rotas
  - `models/task.py:38`, `:45`, `:50` — `validate_status`, `validate_priority`, `is_overdue` nunca chamados; cópias inline em 6 lugares (ver AP-17)
  - `models/user.py:34` — `is_admin` nunca chamado
  - `requirements.txt:4` — `marshmallow` declarado e nunca importado
- **Description:** A estrutura dá a impressão de camadas de serviço, utilitários e regra no model, mas
  toda a lógica efetiva está duplicada inline nas rotas.
- **Impact:** As cópias já divergem: `process_task_data` (`utils/helpers.py:63`) faz `strip()` do título e
  aceita `DD/MM/YYYY` (`:48`); as rotas não fazem nenhum dos dois. Quem corrigir o helper acha que corrigiu o sistema.
- **Recommendation:** Ativar o que corresponde à regra atual (`Task.is_overdue`, constantes de domínio,
  `calculate_percentage`) movendo a regra das rotas para lá; remover o que não tem consumidor nem
  equivalente em runtime (`NotificationService`, `process_task_data`, `parse_date` etc.), documentando a remoção. (T-04)

### [HIGH] Validação ausente ou divergente entre create e update (AP-16)

- **File:** `routes/task_routes.py:113`
- **Occurrences:** 17
  - `routes/task_routes.py:113` e `:182` — `priority < 1` sem checar tipo: `"priority":"3"` → `TypeError` → 500
  - `routes/task_routes.py:96` — `len(title)` com título não-string: `"title":123` → 500
  - `routes/task_routes.py:167` — update com `"title":null` → 500 (create rejeita com 400 em `:93`)
  - `routes/task_routes.py:142`, `:211` — `','.join(tags)` com tag não-string → 500
  - `routes/task_routes.py:261`, `:264` — `int()` em query param sem `try`: `?priority=abc` → 500
  - `routes/report_routes.py:196-197` — `update_category` não checa body vazio (create checa em `:170`): body `null` → 500
  - `routes/user_routes.py:102-103` — update aceita `name` vazio (create exige em `:54-55`)
  - `routes/user_routes.py:61`, `:106` — regex de email aceita `h@x` (sem TLD)
  - `routes/user_routes.py:64`, `:115` — política de senha: 4 caracteres
  - `routes/report_routes.py:180`, `:202` — `color` gravado sem validação (existe `is_valid_color` não usado)
- **Description:** Validação é feita inline, sem checagem de tipo, e cada handler tem sua versão.
  **Promovido de MEDIUM para HIGH:** atinge cadastro e alteração de credenciais (senha de 4 caracteres,
  email frouxo) e é a origem dos 500 com traceback exposto (AP-06).
- **Impact:** **Verificado em execução:** `POST /tasks` com `priority` string, `title` numérico e tags
  numéricas, `PUT /tasks/1 {"title":null}`, `GET /tasks/search?priority=abc` e `PUT /categories/1` com
  body `null` retornaram 500 HTML do debugger. `PUT /users/2 {"name":""}` retornou 200.
- **Recommendation:** Centralizar validação por entidade na camada de serviço/schema, com a mesma regra no
  create e no update; entrada de tipo errado vira 400. Os casos que hoje dão 500 mudariam de status —
  ver Breaking change #3. (T-09)

### [HIGH] Erro engolido e ausência de tratamento central (AP-11)

- **File:** `routes/task_routes.py:62`
- **Occurrences:** 16
  - `routes/task_routes.py:62` — `GET /tasks` inteiro dentro de `try/except:` pelado → 500 genérico sem log
  - `routes/task_routes.py:137`, `:204` — `except:` em `strptime`
  - `routes/task_routes.py:151`, `:221`, `:236` — `try/except → rollback → 500` copiado
  - `routes/user_routes.py:87`, `:130`, `:149` — idem
  - `routes/report_routes.py:186`, `:207`, `:221` — idem
  - `utils/helpers.py:46`, `:49`, `:88` — `except:` pelado
  - `services/notification_service.py:23` — falha de SMTP vira `print` + `return False`
- **Description:** Dois problemas: `except:` pelado suprime qualquer exceção (inclusive bug de programação)
  e não existe `@app.errorhandler`/`register_error_handler` — o grep retorna zero. O mesmo bloco
  `try/except → 500` está copiado em 9 handlers, enquanto os demais não têm tratamento algum.
- **Impact:** Bug em `GET /tasks` vira "Erro interno" sem rastro; erro fora dos `try` vira página HTML do
  debugger (verificado: 5 entradas diferentes produziram 500 `text/html`, ver AP-16).
- **Recommendation:** Handler central que devolve JSON e loga a exceção; `except` só com tipo específico. (T-07)

### [HIGH] Fat controller — regra de negócio e montagem de relatório no handler (AP-07)

- **File:** `routes/report_routes.py:12-101`
- **Occurrences:** 9
  - `routes/report_routes.py:12-101` — `summary_report` (90 linhas): 12 contagens, cálculo de atraso, produtividade por usuário e montagem do JSON
  - `routes/report_routes.py:103-155` — `user_report`: classificação por status, "alta prioridade" (`priority <= 2`), taxa de conclusão
  - `routes/task_routes.py:85-154` — `create_task` (70 linhas): validação, lookup de FK, parse de data, normalização de tags, persistência
  - `routes/task_routes.py:156-223` — `update_task`: mesma regra reescrita
  - `routes/task_routes.py:11-63` — `get_tasks`: serialização manual + cálculo de atraso + lookup de nomes
  - `routes/task_routes.py:273-299` — `task_stats`
  - `routes/user_routes.py:42-90`, `:92-132` — `create_user`, `update_user`: validação de email/senha/role inline
  - `routes/report_routes.py:157-223` — CRUD de categorias hospedado no arquivo de relatórios (domínio errado)
- **Description:** Handlers concentram validação, decisão de domínio, acesso a dados e formatação.
  `report_routes.py` mistura dois domínios (relatórios e categorias).
- **Impact:** A regra "task atrasada" e a "taxa de conclusão" só são testáveis subindo HTTP, e já existem
  em 6 e 3 cópias, respectivamente.
- **Recommendation:** Mover regra para o model/serviço, relatório para um serviço de relatórios, categorias
  para controller próprio; handler fica com parse de request e resposta. (T-03, T-04)

### [HIGH] Acoplamento sem ponto de injeção — app sem factory (AP-08)

- **File:** `app.py:9-31`
- **Occurrences:** 4
  - `app.py:9-16` — `Flask(__name__)` criado no import do módulo com config literal
  - `app.py:30-31` — `db.create_all()` executado no import
  - `seed.py:2` — `from app import app, db`: rodar o seed importa a app e cria tabelas como efeito colateral
  - `services/notification_service.py:15` — `smtplib.SMTP(...)` instanciado dentro do método, sem injeção
- **Description:** Não há `create_app(config)`. Toda importação de `app` usa o mesmo banco e a mesma
  configuração fixa.
- **Impact:** Impossível subir a app de teste apontando para outro banco sem editar código; qualquer
  `import app` (teste, script, shell) cria/abre `instance/tasks.db` de produção.
- **Recommendation:** Application factory recebendo config; `create_all` dentro da factory; entrypoint
  fino. (T-05)

### [MEDIUM] APIs deprecated em uso (AP-18)

- **File:** `routes/task_routes.py:31`
- **Occurrences:** 33 (+5 em `seed.py`)
  - `datetime.utcnow()` — 17x: `models/task.py:15`, `:16`, `:52`; `models/user.py:14`; `models/category.py:11`; `routes/task_routes.py:31`, `:72`, `:215`, `:285`; `routes/user_routes.py:172`; `routes/report_routes.py:35`, `:42`, `:45`, `:71`, `:133`; `utils/helpers.py:38`; `services/notification_service.py:35`
  - `Model.query.get(id)` — 16x: `routes/task_routes.py:42`, `:51`, `:67`, `:117`, `:122`, `:158`, `:188`, `:195`, `:227`; `routes/user_routes.py:29`, `:94`, `:136`, `:155`; `routes/report_routes.py:105`, `:192`, `:213`
- **Description:** Detecção executada por grep e por boot com `-W default`.
- **Impact:** **Verificado em execução:** o log emite `DeprecationWarning: datetime.datetime.utcnow() is
  deprecated` (seed e `sqlalchemy/sql/schema.py` via defaults das colunas) e `LegacyAPIWarning: The Query.get()
  method is considered legacy` (`routes/user_routes.py:94`, `:136`, `routes/task_routes.py:158`,
  `routes/report_routes.py:192`). `utcnow` está agendado para remoção.
- **Recommendation:** Ver tabela "APIs Deprecated". (T-11)

### [MEDIUM] Duplicação de código (AP-17)

- **File:** `routes/task_routes.py:30-39`
- **Occurrences:** 17
  - Cálculo de "atrasada" copiado 6x: `routes/task_routes.py:30-39`, `:71-80`, `:284-287`; `routes/user_routes.py:171-180`; `routes/report_routes.py:34-37`, `:132-135` — idêntico a `Task.is_overdue` (`models/task.py:50-60`)
  - Serialização de task reescrita: `routes/task_routes.py:17-28` (igual a `Task.to_dict`, `models/task.py:23-36`); `routes/user_routes.py:162-169` (subconjunto)
  - Contagem por status: `routes/task_routes.py:276-279` e `routes/report_routes.py:19-22`
  - Taxa de conclusão: `routes/task_routes.py:296`, `routes/report_routes.py:67`, `:151`
  - Validação create × update: `routes/task_routes.py:92-144` × `:166-213`; `routes/user_routes.py:54-72` × `:102-122`
- **Description:** O mesmo bloco de regra está reescrito em cada handler que precisa dele.
- **Impact:** Mudar a definição de atraso (ex.: incluir o dia do vencimento) exige editar 6 lugares; a
  validação de create e update já divergiu (ver AP-16).
- **Recommendation:** Uma implementação por regra, no model/serviço, consumida por todos. (T-04, T-12)

### [MEDIUM] N+1 queries e agregação em laço (AP-15)

- **File:** `routes/task_routes.py:42`
- **Occurrences:** 7
  - `routes/task_routes.py:42`, `:51` — `GET /tasks`: `User.query.get` e `Category.query.get` por task = **1 + 2N queries** (21 com o seed), apesar de `Task.user`/`Task.category` existirem (`models/task.py:20-21`)
  - `routes/user_routes.py:22` — `GET /users`: `len(u.tasks)` dispara lazy load por usuário = 1 + N
  - `routes/report_routes.py:56` — `summary_report`: `Task.query.filter_by(user_id=u.id).all()` por usuário = 1 + N
  - `routes/report_routes.py:163` — `GET /categories`: `count()` por categoria = 1 + N
  - `routes/report_routes.py:15-30` — 12 `COUNT` separados + `Task.query.all()` onde um `GROUP BY` resolve
  - `routes/task_routes.py:275-281` — 5 `COUNT` + varredura completa
  - `routes/user_routes.py:140-142` — delete de tasks em laço, um `DELETE` por task
- **Description:** Relacionamentos ORM declarados e ignorados; agregações feitas em Python.
- **Impact:** Custo cresce linearmente com o volume de dados em rotas sem paginação (ver AP-19).
- **Recommendation:** Usar os relacionamentos com eager loading (`joinedload`/`selectinload`) e agregar com
  `func.count` + `group_by`, sem mudar o JSON. (T-08)

### [MEDIUM] Configuração e middleware inseguros (AP-19)

- **File:** `app.py:15`
- **Occurrences:** 4
  - `app.py:15` — `CORS(app)` sem restrição de origem
  - `routes/user_routes.py:185` — `POST /login` sem rate limiting
  - `routes/task_routes.py:14`, `routes/user_routes.py:12` — `GET /tasks` e `GET /users` devolvem a tabela inteira, sem paginação
  - `app.py:9-16` — sem `MAX_CONTENT_LENGTH`
- **Description:** Nenhum controle de origem, volume ou taxa.
- **Impact:** **Verificado em execução:** request com `Origin: https://evil.example` recebeu
  `Access-Control-Allow-Origin: https://evil.example`. `/login` aceita força bruta ilimitada contra senhas de 4 caracteres.
- **Recommendation:** Origens de CORS por config (default atual preservado via env para não quebrar
  clientes), limite de body por config. Paginação e rate limit alteram o contrato — ficam registrados como
  risco, fora da Fase 3. (T-01, T-09)

### [LOW] Ruído de legibilidade (AP-21)

- **File:** `routes/task_routes.py:7`
- **Occurrences:** 44
  - Imports não usados: `app.py:7` (`os`, `sys`, `json`); `routes/task_routes.py:7` (`json`, `os`, `sys`, `time`); `routes/user_routes.py:6` (`hashlib`, `json`); `routes/report_routes.py:7` (`format_date`, `calculate_percentage`), `:8` (`json`); `models/task.py:3` (`json`); `utils/helpers.py:3-7` (`os`, `json`, `sys`, `math`, `hashlib`)
  - Dependências declaradas e nunca importadas: `requirements.txt:5` (`requests`), `requirements.txt:6` (`python-dotenv`)
  - `print` como logging: `routes/task_routes.py:149`, `:153`, `:219`, `:234`; `routes/user_routes.py:83`, `:89`, `:147`; `services/notification_service.py:21`, `:24`; `utils/helpers.py:39`, `:41`
  - `type(x) == list`: `routes/task_routes.py:141`, `:210`; `utils/helpers.py:103`
  - `x = x + 1`: `routes/report_routes.py:37`, `:61`, `:121`, `:123`, `:125`, `:127`, `:130`, `:135`; `routes/task_routes.py:287`
  - `if cond: return True else: return False`: `models/task.py:40-43`, `:46-48`, `:51-60`; `models/user.py:35-38`; `utils/helpers.py:21-23`, `:53-55`
  - Import dentro de função sem motivo: `utils/helpers.py:33` (`uuid`)
  - `updated_at` atribuído à mão (`routes/task_routes.py:215`) apesar de `onupdate` (`models/task.py:16`)
- **Description:** Código morto de import, logging por `print` e idiomas não-pythônicos.
- **Impact:** Ruído esconde o que importa; `print` não tem nível nem destino configurável.
- **Recommendation:** Remover imports/deps mortos, `logging` no lugar de `print`, `isinstance`, `+=`,
  retorno direto de booleano. (T-11, T-12)

### [LOW] Magic numbers e magic strings (AP-20)

- **File:** `routes/task_routes.py:110`
- **Occurrences:** 18
  - Lista de status literal: `routes/task_routes.py:110`, `:177`; `models/task.py:39`; `utils/helpers.py:75`
  - Lista de roles literal: `routes/user_routes.py:71`, `:120`
  - Faixa de prioridade `1..5`: `routes/task_routes.py:113`, `:182`; `models/task.py:46`
  - Tamanho de título `3`/`200`: `routes/task_routes.py:96`, `:99`, `:167`, `:169`
  - Senha mínima `4`: `routes/user_routes.py:64`, `:115`
  - `priority <= 2` como "alta prioridade": `routes/report_routes.py:129`
  - `'#000000'` repetido: `models/category.py:10`, `routes/report_routes.py:180`
- **Description:** As constantes existem em `utils/helpers.py:110-116`, mas ninguém as usa.
- **Impact:** Adicionar um status exige achar 4 listas; esquecer uma cria divergência silenciosa.
- **Recommendation:** Constantes de domínio num único módulo, consumidas por model e serviço. (T-12)

### [LOW] Curinga de LIKE não escapado na busca (AP-02, rebaixado)

- **File:** `routes/task_routes.py:252-253`
- **Occurrences:** 2
  - `routes/task_routes.py:252` — `Task.title.like(f'%{query}%')`
  - `routes/task_routes.py:253` — `Task.description.like(f'%{query}%')`
- **Description:** A f-string é passada ao construtor do ORM, que a envia como bind parameter — **não é
  SQL injection** (guarda anti-falso-positivo aplicada). O problema é `%` e `_` do usuário não serem escapados.
- **Impact:** **Verificado em execução:** `GET /tasks/search?q=%25` retorna todas as tasks; busca por texto
  literal com `_` casa qualquer caractere.
- **Recommendation:** Mover a busca para o repositório. O escape (`.like(..., escape='\\')`) muda o
  resultado de buscas com `%`/`_` — fica como melhoria opcional, fora da Fase 3. (T-02)

## APIs Deprecated

| Obsoleto | Ocorrências | Equivalente moderno |
|---|---|---|
| `datetime.utcnow()` | `routes/report_routes.py:35` e mais 16 locais (17x) + `seed.py:66-74` (5x) | `datetime.now(timezone.utc)` — mantendo datetime *naive* em UTC para não mudar o formato serializado (`str()` sem `+00:00`) |
| `Model.query.get(id)` | `routes/task_routes.py:42` e mais 15 locais (16x) | `db.session.get(Model, id)` |
| `Model.query.filter_by(...)` (legacy, sem warning na 2.0) | `routes/` (22x) | `db.session.execute(select(Model).filter_by(...))` |
| `hashlib.md5` para senha | `models/user.py:29`, `:32` (2x) | `werkzeug.security.generate_password_hash` / `check_password_hash` |

Checagem feita com grep e com boot `python -W default` + tráfego nas rotas (warnings capturados no log).

## Breaking changes propostos

Cada item exige aval explícito antes da Fase 3. Sem aval, a Fase 3 **preserva o comportamento atual** e o
finding correspondente fica registrado como risco residual.

1. **Remover `password` das respostas de `User`** (`GET /users/<id>`, `POST /users`, `PUT /users/<id>`,
   `POST /login`). Fecha a parte principal de AP-06. Remove uma chave do JSON.
2. **Autenticação real + guards** (token assinado emitido no `/login`, verificação nas rotas, bloqueio de
   atribuição de `role` por não-admin). Fecha AP-05. Rotas hoje abertas passam a responder 401/403, e o
   formato de `token` muda.
3. **Entrada de tipo inválido responde 400 em vez de 500** (casos listados em AP-16). Hoje nenhum desses
   casos está no `rotas.tsv`; o status muda de 500 para 400.

Fora de escopo (alteram resultado/contrato, só registrados): paginação de `GET /tasks`/`GET /users`, rate
limit em `/login`, escape de `%`/`_` na busca, endurecimento da política de senha/email.

## Baseline de comportamento

65/65 requisições responderam (22/22 endpoints, 0 respostas 5xx), banco recém-semeado por `seed.py`.
Nenhuma rota excluída do smoke: os `DELETE` operam sobre recursos criados pelo próprio smoke e ficam no fim.
Contrato em `.refactor-arch/rotas.tsv`; saída em `.refactor-arch/baseline/`.

```
================================
Total: 17 findings
================================
```

## Resultado da Fase 3

Código da aplicação movido para `src/` (onda 7, `git mv`); os caminhos da tabela abaixo são relativos a `src/`.
Breaking changes #1, #2 e #3 aprovados no GATE e aplicados. Validação: smoke com token de admin — 65/65
status idênticos ao baseline; `.refactor-arch/check-contract.sh` — 48/48 casos do contrato novo.

| Finding | Situação | Onde |
|---|---|---|
| AP-05 | resolvido — token assinado (`itsdangerous`) + guards; role só por admin; editar/apagar usuário só dono ou admin | `middlewares/auth.py`, `services/auth_service.py`, `services/user_service.py` |
| AP-06 | resolvido — `password` fora do JSON (allowlist); debug off; 500 vira JSON genérico | `routes/serializers.py`, `middlewares/error_handler.py` |
| AP-01 | resolvido — config por env/`.env`; `SECRET_KEY` obrigatória; `NotificationService` (SMTP literal) removido | `config/settings.py`, `.env.example` |
| AP-04 | resolvido — `werkzeug.security`; hash MD5 legado só é verificado (tempo constante) e regravado no 1º login | `models/user.py` |
| AP-10, AP-07, AP-08 | resolvidos — repositórios, services, rotas finas, `create_app` como composition root | `models/*_repository.py`, `services/`, `routes/`, `app.py` |
| AP-14 | resolvido — decisões em `.refactor-arch/plano-refatoracao.md` (ativados: `is_overdue`, `validate_*`, `is_admin`, `format_date`, `calculate_percentage`, `validate_email`, `python-dotenv`; removidos: `NotificationService`, 6 helpers, `marshmallow`, `requests`) | — |
| AP-11 | resolvido — handler central; nenhum `try/except` em rota | `middlewares/error_handler.py` |
| AP-16 | **parcial** — tipo inválido → 400 e create/update unificados; **restam** senha mínima de 4 caracteres, regex de email frouxo e `color` sem validação (alteram contrato, não autorizados) | `models/*.py` |
| AP-18, AP-17, AP-15, AP-20 | resolvidos — `GET /tasks` de 21 para 2 queries (seed de 10 tasks) | `models/task_repository.py`, `models/constants.py` |
| AP-19 | **parcial** — CORS e limite de body por config; **restam** paginação e rate limit em `/login` | `config/settings.py` |
| AP-21 | resolvido — exceção: `print` mantido no `seed.py` (saída de CLI). Correção da auditoria: `updated_at` explícito em `update_task` foi **mantido** — `onupdate` não dispara quando nenhuma coluna muda | `services/task_service.py` |
| AP-02 (LOW) | **residual** — escape de `%`/`_` não aplicado (muda resultado da busca) | `models/task_repository.py` |

Mudanças de contrato intencionais, além de #1/#2/#3:

- Mensagens de erro unificadas entre create e update (T-04): `PUT /tasks` data inválida → `Formato de data inválido. Use YYYY-MM-DD`; `PUT /users` senha curta → `Senha deve ter no mínimo 4 caracteres`; `PUT` com `name`/`email`/`password` vazio passa a exigir o campo, como o create (400).
- 500 inesperado responde `{"error": "Erro interno"}` em JSON (antes: HTML do debugger ou mensagem por rota); rota inexistente, 405, 413 e 415 também respondem JSON.
- Corpo acima de `MAX_CONTENT_LENGTH` (padrão 1 MB) → 413.

**Ação obrigatória fora do código:** a `SECRET_KEY` e a senha SMTP que estavam em `app.py:13` e
`services/notification_service.py:10` continuam no histórico do git — rotacione as duas.
