## Análise Manual

### Resumo

| Projeto | Stack | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|:-:|:-:|:-:|:-:|
| `code-smells-project` | Python + Flask 3.1.1 + `sqlite3` puro | 4 | 4 | 5 | 3 | **16** |
| `ecommerce-api-legacy` | Node.js + Express 4.18 + `sqlite3` 5.1 |  4 | 5 | 4 | 3 | **16** |
| `task-manager-api` | Python + Flask 3.0 + Flask-SQLAlchemy 3.1 | 4 | 2 | 6 | 3 | **15** |

---

### 1. code-smells-project

#### P1-01 · [CRITICAL] SQL Injection
- **Local:** `models.py:28, 47-50, 109-111, 289-297` (e demais queries do arquivo)
- **Problema:** as queries são montadas concatenando dados do usuário, sem parâmetros.
- **Por que é relevante:** permite burlar o login e ler ou apagar qualquer dado do banco.

#### P1-02 · [CRITICAL] Endpoints administrativos sem autenticação
- **Local:** `app.py:47-57`, `app.py:59-78`
- **Problema:** `/admin/query` executa qualquer SQL e `/admin/reset-db` apaga o banco, e nenhum dos dois pede autenticação.
- **Por que é relevante:** qualquer pessoa pode vazar ou destruir todos os dados.

#### P1-03 · [CRITICAL] Secret key hardcoded e exposta
- **Local:** `app.py:7`, `controllers.py:289`
- **Problema:** a `SECRET_KEY` está fixa no código e é devolvida pelo `/health`.
- **Por que é relevante:** permite forjar sessões, e o segredo fica no histórico do git.

#### P1-04 · [CRITICAL] Senhas em texto puro
- **Local:** `database.py:31, 76-78`, `models.py:83, 99, 110`
- **Problema:** as senhas são salvas sem hash e retornadas em `GET /usuarios`.
- **Por que é relevante:** vaza a senha de todos os usuários.

#### P1-05 · [HIGH] Debug ligado em produção
- **Local:** `app.py:8, 88`
- **Problema:** `debug=True` com `host="0.0.0.0"`.
- **Por que é relevante:** o debugger do Werkzeug permite executar código remotamente.

#### P1-06 · [HIGH] Sem separação de camadas
- **Local:** `app.py:47-78`, `controllers.py`, `models.py:133-169, 235-273`
- **Problema:** há rotas com SQL, controllers com validação e notificação, e models com regra de negócio.
- **Por que é relevante:** o código fica difícil de testar e de manter, e qualquer mudança afeta tudo.

#### P1-07 · [HIGH] Pedido criado sem transação
- **Local:** `models.py:139-168`
- **Problema:** o estoque é verificado e baixado sem transação, e quantidade negativa não é bloqueada.
- **Por que é relevante:** permite vender além do estoque e aumentar o estoque com quantidade negativa.

#### P1-08 · [MEDIUM] Queries N+1
- **Local:** `models.py:171-201, 203-233`
- **Problema:** é feita uma query por pedido e outra por item.
- **Por que é relevante:** a performance piora conforme o número de pedidos cresce.

#### P1-09 · [MEDIUM] Código duplicado
- **Local:** `controllers.py:28-50` vs `72-90`; `models.py:171-201` vs `203-233`
- **Problema:** a validação de produto e a listagem de pedidos estão copiadas.
- **Por que é relevante:** as cópias já divergiram: a atualização não valida a categoria.

#### P1-10 · [MEDIUM] Validação de entrada ausente
- **Local:** `controllers.py:153-160, 170, 240`
- **Problema:** e-mail, senha e tipos não são validados, e corpo vazio gera erro 500.
- **Por que é relevante:** dados inválidos chegam ao banco e o cliente recebe 500 em vez de 400.

#### P1-11 · [MEDIUM] Tratamento de erro repetido e vazando detalhes
- **Local:** todos os handlers de `controllers.py` (ex.: `10-12`)
- **Problema:** cada função repete `except Exception` e devolve `str(e)` ao cliente.
- **Por que é relevante:** expõe detalhes internos, e não existe tratamento central de erros.

#### P1-12 · [LOW] `print` como log
- **Local:** `controllers.py:8, 57, 161, 179`
- **Problema:** não usa `logging` e imprime e-mails de usuários.
- **Por que é relevante:** o log fica sem nível e expõe dados pessoais.

---

### 2. ecommerce-api-legacy

#### P2-01 · [CRITICAL] God Class
- **Local:** `src/AppManager.js:4-139`
- **Problema:** uma única classe cuida de banco, rotas, validação, pagamento e relatório.
- **Por que é relevante:** é impossível testar ou alterar uma parte isolada.

#### P2-02 · [CRITICAL] Credenciais hardcoded
- **Local:** `src/utils.js:1-7`
- **Problema:** a senha do banco e a chave de pagamento (`pk_live_...`) estão no código.
- **Por que é relevante:** quem acessa o repositório acessa o gateway de pagamento.

#### P2-03 · [CRITICAL] Cartão e chave do gateway em log
- **Local:** `src/AppManager.js:45`
- **Problema:** o número do cartão e a chave do gateway são impressos no console.
- **Por que é relevante:** viola o PCI-DSS e vaza dados sensíveis.

#### P2-04 · [CRITICAL] Hash de senha inseguro
- **Local:** `src/utils.js:17-23`, `src/AppManager.js:68`
- **Problema:** `badCrypto` só usa os primeiros caracteres da senha (`"senhaforte"` e `"senha123"` geram o mesmo hash), e a senha padrão é `"123456"`.
- **Por que é relevante:** na prática, as senhas ficam sem proteção.

#### P2-05 · [HIGH] Rotas administrativas sem autenticação
- **Local:** `src/AppManager.js:80, 131`
- **Problema:** o relatório financeiro e a exclusão de usuário não pedem autenticação.
- **Por que é relevante:** qualquer um vê os dados financeiros ou apaga usuários.

#### P2-06 · [HIGH] Checkout sem transação
- **Local:** `src/AppManager.js:50-72`
- **Problema:** usuário, matrícula e pagamento são gravados em passos separados, sem transação, e o usuário é criado mesmo quando o pagamento é recusado.
- **Por que é relevante:** o fluxo principal do sistema deixa dados inconsistentes.

#### P2-07 · [HIGH] Regra de pagamento dentro da rota
- **Local:** `src/AppManager.js:43-64`
- **Problema:** o pagamento é simulado (`cc.startsWith("4")`) direto no handler, sem service.
- **Por que é relevante:** não dá para testar nem trocar o gateway.

#### P2-08 · [HIGH] Entrada inválida derruba o servidor
- **Local:** `src/AppManager.js:35, 46`
- **Problema:** se `card` vier como número, `cc.startsWith` lança um erro dentro do callback e ninguém trata.
- **Por que é relevante:** um único request malformado derruba a API.

#### P2-09 · [HIGH] Estado global mutável
- **Local:** `src/utils.js:9-15`
- **Problema:** `globalCache` cresce a cada checkout e nunca é limpo.
- **Por que é relevante:** causa vazamento de memória e mantém estado compartilhado entre requisições.

#### P2-10 · [MEDIUM] Queries N+1 no relatório
- **Local:** `src/AppManager.js:83-127`
- **Problema:** faz uma query por curso, por matrícula, por usuário e por pagamento.
- **Por que é relevante:** fica lento conforme a base cresce, quando um único JOIN resolveria.

#### P2-11 · [MEDIUM] Erros ignorados
- **Local:** `src/AppManager.js:57, 92, 104, 133`
- **Problema:** vários callbacks ignoram o `err`, e as respostas misturam texto e JSON.
- **Por que é relevante:** as falhas passam em silêncio.

#### P2-12 · [MEDIUM] Dados órfãos e banco em memória
- **Local:** `src/AppManager.js:7, 131-136`
- **Problema:** apagar um usuário deixa matrículas e pagamentos órfãos, e o banco é `:memory:`.
- **Por que é relevante:** os dados ficam inconsistentes e se perdem a cada restart.

#### P2-13 · [LOW] Strings hardcoded
- **Local:** `src/AppManager.js:46, 108`
- **Problema:** `'PAID'`, `'DENIED'` e `"4"` aparecem soltos no código.
- **Por que é relevante:** um erro de digitação quebra o fluxo sem aviso.

#### P2-14 · [LOW] Código morto
- **Local:** `src/AppManager.js:2`, `src/utils.js:2-5`
- **Problema:** `totalRevenue`, `dbUser`, `dbPass` e `smtpUser` não são usados.
- **Por que é relevante:** confunde quem lê.

---

### 3. task-manager-api

#### P3-01 · [CRITICAL] Senha com MD5
- **Local:** `models/user.py:29, 32`
- **Problema:** usa MD5 sem salt e aceita senha com apenas 4 caracteres.
- **Por que é relevante:** o hash é quebrado facilmente.

#### P3-02 · [CRITICAL] Hash da senha na resposta
- **Local:** `models/user.py:21`
- **Problema:** `to_dict()` inclui o campo `password` e é usado no login e nas rotas de usuário.
- **Por que é relevante:** expõe o hash da senha a qualquer cliente.

#### P3-03 · [CRITICAL] Autenticação falsa
- **Local:** `routes/user_routes.py:71, 210`
- **Problema:** o token é fixo (`fake-jwt-token-<id>`) e nunca validado, e qualquer um pode criar um usuário admin.
- **Por que é relevante:** não existe controle de acesso nenhum.

#### P3-04 · [CRITICAL] Credenciais hardcoded
- **Local:** `app.py:13`, `services/notification_service.py:7-10`
- **Problema:** a `SECRET_KEY` e a senha SMTP estão no código.
- **Por que é relevante:** os segredos ficam versionados no git.

#### P3-05 · [HIGH] Debug ligado
- **Local:** `app.py:34`
- **Problema:** `debug=True` com `host='0.0.0.0'`.
- **Por que é relevante:** permite execução remota de código pelo debugger.

#### P3-06 · [HIGH] Lógica de negócio nas rotas
- **Local:** `routes/task_routes.py:85-223`, `routes/report_routes.py:12-101`
- **Problema:** as rotas fazem validação, regra de negócio e persistência, enquanto `services/` e `utils/helpers.py` existem mas não são usados.
- **Por que é relevante:** as camadas existem só no nome, e a lógica não é reutilizável nem testável.

#### P3-07 · [MEDIUM] Queries N+1 e sem paginação
- **Local:** `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:55-57`
- **Problema:** há queries dentro de loops, e `Task.query.all()` não tem paginação.
- **Por que é relevante:** a performance cai com o volume de dados.

#### P3-08 · [MEDIUM] APIs deprecated
- **Local:** `Model.query.get()` em `routes/*.py` (ex.: `task_routes.py:67`); `datetime.utcnow()` em `models/*.py` e `routes/*.py`
- **Problema:** usa APIs obsoletas no lugar de `db.session.get()` e `datetime.now(timezone.utc)`.
- **Por que é relevante:** gera warnings e dificulta upgrades.

#### P3-09 · [MEDIUM] Lógica duplicada
- **Local:** `routes/task_routes.py:30-39, 71-80`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43`
- **Problema:** a regra de "tarefa atrasada" se repete em vários lugares, ignorando `Task.is_overdue()`.
- **Por que é relevante:** mudar a regra exige editar todos os pontos.

#### P3-10 · [MEDIUM] `except:` genérico
- **Local:** `routes/task_routes.py:62, 137`, `routes/user_routes.py:130`, `routes/report_routes.py:186`
- **Problema:** captura qualquer exceção sem registrar log, e não há tratamento central de erros.
- **Por que é relevante:** esconde bugs.

#### P3-11 · [MEDIUM] Validação de tipos ausente
- **Local:** `routes/task_routes.py:113, 261`, `routes/report_routes.py:196`
- **Problema:** `priority` enviado como string ou corpo vazio geram erro 500.
- **Por que é relevante:** o cliente recebe 500 em vez de 400.

#### P3-12 · [MEDIUM] CRUD de categorias no arquivo de relatórios
- **Local:** `routes/report_routes.py:157-223`
- **Problema:** as rotas de categoria estão no blueprint de relatórios, e apagar uma categoria deixa tasks órfãs.
- **Por que é relevante:** a responsabilidade fica no lugar errado e os dados ficam inconsistentes.

#### P3-13 · [LOW] Imports não usados
- **Local:** `app.py:7`, `routes/task_routes.py:7`, `utils/helpers.py:3-7`
- **Problema:** `os`, `sys`, `json`, `time` etc. são importados sem uso, e `marshmallow` e `requests` estão no `requirements.txt` sem uso.
- **Por que é relevante:** gera ruído no código.

#### P3-14 · [LOW] Magic numbers
- **Local:** `routes/task_routes.py:110, 113`, `routes/report_routes.py:129`
- **Problema:** status e faixas de prioridade são repetidos no código, mesmo com constantes definidas em `utils/helpers.py:110-116`.
- **Por que é relevante:** gera duplicação e risco de inconsistência.

#### P3-15 · [LOW] Código verboso e `print` como log
- **Local:** `models/task.py:38-60`, `routes/task_routes.py:149`
- **Problema:** usa `if/else` para retornar booleano, ifs aninhados e `print` no lugar de log.
- **Por que é relevante:** dificulta a leitura.

---

### Padrões recorrentes (insumo para a skill)

| Anti-pattern | P1 (Flask) | P2 (Express) | P3 (Flask + ORM) | Severidade típica |
|---|:-:|:-:|:-:|---|
| Credenciais / segredos hardcoded | ✓ | ✓ | ✓ | CRITICAL |
| Senha em texto puro ou hash fraco | ✓ | ✓ | ✓ | CRITICAL |
| Dados sensíveis expostos em resposta ou log | ✓ | ✓ | ✓ | CRITICAL |
| Ausência de autenticação/autorização em rotas sensíveis | ✓ | ✓ | ✓ | CRITICAL / HIGH |
| SQL Injection | ✓ | | | CRITICAL |
| God Class / camadas misturadas | ✓ | ✓ | ✓ (rotas gordas) | CRITICAL / HIGH |
| Debug ativo em produção | ✓ | | ✓ | HIGH |
| Estado global mutável | ✓ | ✓ | | HIGH |
| Operação multi-etapa sem transação | ✓ | ✓ | | HIGH |
| Queries N+1 | ✓ | ✓ | ✓ | MEDIUM |
| Tratamento de erro genérico/não centralizado | ✓ | ✓ | ✓ | MEDIUM |
| Validação de entrada ausente | ✓ | ✓ | ✓ | MEDIUM |
| Duplicação de regras | ✓ | | ✓ | MEDIUM |
| APIs deprecated | | (callbacks legados) | ✓ | MEDIUM |
| Magic numbers / strings | ✓ | ✓ | ✓ | LOW |
| Nomenclatura ruim / código morto / imports não usados | ✓ | ✓ | ✓ | LOW |
| `print`/`console.log` como logging | ✓ | ✓ | ✓ | LOW |
