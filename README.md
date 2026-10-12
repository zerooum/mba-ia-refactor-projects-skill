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

## Construção da Skill

### Decisões de design

Estrutura da skill:

```
refactor-arch/
├── SKILL.md                              # orquestra as fases e define as regras
├── references/
│   ├── 01-analise-de-projeto.md          # detectar stack, banco, rotas e nível de organização
│   ├── 02-catalogo-anti-patterns.md      # 21 anti-patterns + APIs deprecated + guardas anti-falso-positivo
│   ├── 03-template-relatorio.md          # formato do relatório da Fase 2
│   ├── 04-guidelines-mvc.md              # regras das camadas e estrutura alvo por stack
│   ├── 05-playbook-refatoracao.md        # 15 transformações com código antes/depois
│   └── 06-validacao.md                   # como subir a app, rodar o smoke e comparar
└── scripts/
    └── smoke.sh                          # chama todas as rotas e grava o status de cada uma
```

**SKILL.md como roteiro, referências como conhecimento.** O `SKILL.md` diz *o que* fazer e em que ordem. O *como* fica nos arquivos de referência. Cada referência é lida só no início da fase que a usa.

**Fluxo em fases com um GATE.** A skill roda `Fase 0 (preflight) → 1 (análise) → 2 (auditoria) → GATE → 3 (refatoração)`. Até o GATE ela só lê o código. No GATE ela usa `AskUserQuestion` com três opções: prosseguir, fazer um commit de checkpoint antes, ou abortar.

**Regras invioláveis e racionalizações proibidas.** O `SKILL.md` tem uma tabela de regras que valem em todas as fases: nada é escrito antes do GATE, finding sem `arquivo:linha` conferido não existe, o contrato HTTP não muda, refatorar é mover e não reescrever, segredo vai para variável de ambiente. Tem também uma tabela com os "atalhos" que o agente costuma tomar e por que eles estão errados, por exemplo: "o projeto já tem `services/`, então tem camada de serviço".

**IDs ligando catálogo, playbook e ondas.** Cada anti-pattern tem um ID (`AP-01`…`AP-21`) e aponta para a transformação que o resolve (`T-01`…`T-15`). Cada transformação pertence a uma onda da Fase 3. Assim, o plano de refatoração sai direto do relatório: `finding → transformação → arquivos → onda`.

**Refatoração em ondas com smoke test.** A Fase 3 roda em ondas de ordem fixa (layout `src/`, config, dados, negócio, rotas, erros/validação, higiene). Depois de cada onda, a app sobe e o `smoke.sh` compara o status de cada rota com o baseline gravado na Fase 1. Se a onda quebrar algo, ela é revertida.

**Saídas com formato fixo.** Os blocos `PHASE 1`, o relatório e o `PHASE 3` têm formato definido e todas as linhas são obrigatórias. Isso deixa os resultados dos 3 projetos comparáveis.

### Anti-patterns do catálogo

O catálogo nasceu da análise manual: cada padrão virou uma entrada. Alguns foram acrescentados para cobrir casos comuns em outras stacks. Cada entrada tem descrição, comandos `rg` de detecção, por que importa, falsos positivos conhecidos e a transformação que resolve.

| Severidade | Anti-patterns | Por que estão no catálogo |
|---|---|---|
| CRITICAL | AP-01 Credenciais hardcoded · AP-02 SQL Injection · AP-03 God Class · AP-04 Senha em texto puro ou hash fraco · AP-05 Endpoint sensível sem autenticação · AP-06 Dado sensível vazado na resposta | Apareceram nos 3 projetos e expõem dados ou impedem qualquer separação de camadas |
| HIGH | AP-07 Regra de negócio na rota · AP-08 Acoplamento sem injeção de dependência · AP-09 Estado global mutável · AP-10 Camada pulada · AP-11 Erro engolido / sem handler central · AP-12 Escrita múltipla sem transação · AP-13 Callback hell · AP-14 Camada fantasma | São as violações de MVC/SOLID que a Fase 3 precisa desfazer. AP-10 e AP-14 existem por causa do `task-manager-api`, que tem pastas de camada sem responsabilidade real |
| MEDIUM | AP-15 N+1 · AP-16 Validação ausente ou divergente · AP-17 Duplicação · AP-18 API deprecated · AP-19 Config ou middleware inseguro | Problemas de performance e padronização encontrados nos 3 projetos |
| LOW | AP-20 Magic numbers/strings · AP-21 Ruído de legibilidade | Imports não usados, `print` como log, nomes ruins e código verboso |

Além da lista, o catálogo traz:

- **Tabelas de APIs deprecated** para Python (`datetime.utcnow()`, `Model.query.get()`…) e Node (`new Buffer`, `url.parse`, driver em callback…), com o equivalente moderno, mais uma forma genérica de detectar: ler os warnings do boot.
- **Regra de agrupamento:** 20 ocorrências do mesmo problema viram 1 finding com 20 linhas, não 20 findings.
- **Regra de promoção:** um MEDIUM sobe para HIGH quando atinge login, pagamento ou dado pessoal.
- **Guardas anti-falso-positivo:** casos que parecem problema mas não são (ver Desafios).

### Como a skill é agnóstica de tecnologia

- **Detecção pelo manifesto, não pela extensão.** `requirements.txt`, `package.json`, `go.mod`, `pom.xml`, `Cargo.toml` etc. dizem a linguagem e as versões. O framework é confirmado pela dependência **e** pela assinatura de rota (`@app.route`, `app.get(`, `@GetMapping`…), com tabela para 10 frameworks.
- **Sinais de detecção cobrem várias sintaxes.** Os comandos `rg` do catálogo pegam concatenação com `+`, f-string do Python e template literal do JS no mesmo padrão.
- **Estrutura alvo por stack, com fallback genérico.** `04-guidelines-mvc.md` define a estrutura para Flask, Express e uma versão genérica (`config · models · controllers · views/routes · middlewares · infra`).
- **Receita por nível de organização, não por linguagem.** A Fase 1 classifica o projeto como monolito flat, camadas nominais ou camadas reais, e a Fase 3 aplica a receita do nível. Um projeto Flask flat e um Express flat recebem o mesmo tratamento.
- **Validação por HTTP.** O `smoke.sh` usa só `curl` e um `rotas.tsv` montado na Fase 1. Não depende de suíte de testes nem da linguagem do projeto.
- **Prova prática:** a pasta da skill foi copiada sem nenhuma alteração para os 3 projetos (`diff -r` entre as cópias é vazio) e rodou em Python/Flask com `sqlite3` puro, em Node/Express com callbacks e em Python/Flask com SQLAlchemy.

### Desafios encontrados

**1. Onde o código deveria terminar.** A primeira versão não dizia onde o código refatorado devia ficar. No `code-smells-project`, o `app.py` da raiz ficou como launcher chamando `src/app.py`. No `task-manager-api`, as camadas já existiam na raiz e a mudança para `src/` só aconteceu na última onda, depois de os arquivos já terem sido editados, então o git perde o histórico de rename.
**Solução:** criei a regra "código da aplicação termina em `src/`", a transformação T-15 e a **onda 0** (`git mv` puro, antes de qualquer edição). Também acrescentei uma tabela com o que quebra ao mover (comando de boot, `instance_path` do Flask, SQLite relativo, `main` do `package.json`) e uma checagem de que a app sobe a partir de outro diretório. A atualização foi aplicada nas 3 cópias da skill.

**2. Corrigir segurança sem quebrar os clientes.** Proteger `/admin/*` ou o `DELETE /api/users/:id` muda o status de 200 para 401, e o smoke test acusa divergência.
**Solução:** a regra "o contrato HTTP não muda" e uma seção **Breaking changes propostos** no relatório. Tudo que altera o contrato é listado ali e só é aplicado se aprovado no GATE. No fim, as divergências do smoke são justificadas uma a uma (ex.: no projeto 1, 30/33 idênticas, e as 3 diferentes são o 401 aprovado).

**3. Falsos positivos na auditoria.** O grep de SQL injection marca `` `Checkout curso ${cid}` `` em `AppManager.js:57`, mas a interpolação está no array de parâmetros, não no SQL. No `task-manager-api`, `Task.title.like(f'%{q}%')` parece injection, mas o ORM parametriza.
**Solução:** a tabela de **guardas anti-falso-positivo** e a regra "o grep localiza, a leitura confirma". O relatório do projeto 2 registra que não há SQL injection, e o do projeto 3 classifica o `like` como LOW (só falta escapar `%`/`_`).

**4. Projeto parcialmente organizado engana.** No `task-manager-api`, a existência de `services/` e `utils/` fazia parecer que as camadas estavam separadas, mas nenhuma rota importava esses módulos.
**Solução:** três testes objetivos para o nível "camadas nominais" (o service é importado? a rota faz query? o método do model é chamado?), os anti-patterns AP-10 (camada pulada) e AP-14 (camada fantasma), e a exigência de registrar no plano, para cada módulo morto, se ele será usado ou removido. No projeto 3, `is_overdue` e `validate_*` foram reaproveitados, e `NotificationService`, `marshmallow` e `requests` foram removidos.

**5. Validar sem testes automatizados.** Nenhum dos 3 projetos tem suíte de testes.
**Solução:** capturar um baseline na Fase 1 (app rodando + `smoke.sh` em todas as rotas) e repetir o smoke depois de cada onda, comparando os arquivos `.status`. Uma onda que quebra algo é revertida antes da próxima.

**6. Segredos que continuam no histórico do git.** Mover a `SECRET_KEY` para variável de ambiente não apaga o valor dos commits antigos.
**Solução:** o `.env.example` recebe só placeholder (`CHANGE_ME`), o `.env` vai para o `.gitignore`, e o relatório final de cada projeto termina com a ação obrigatória de rotacionar os segredos expostos.

---

## Resultados

### Resumo das auditorias

Relatórios completos em `<projeto>/reports/audit-<projeto>.md`.

| Projeto | Stack detectada | Arquivos / LOC | Endpoints | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `code-smells-project` | Python 3 + Flask 3.1.1 + `sqlite3` cru | 4 / 780 | 19 | 6 | 7 | 4 | 2 | **19** |
| `ecommerce-api-legacy` | Node.js 22 + Express 4.22.1 + `sqlite3` 5.1.7 | 3 / 180 | 3 | 6 | 6 | 4 | 2 | **18** |
| `task-manager-api` | Python 3 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 | 14 / 1158 | 22 | 4 | 6 | 4 | 3 | **17** |

Comparado à análise manual (16 / 16 / 15), a skill encontrou mais findings em todos os projetos. A diferença vem principalmente de anti-patterns que a análise manual não separou: acoplamento sem injeção de dependência (AP-08), camada pulada (AP-10), configuração insegura (AP-19) e dependências com vulnerabilidade conhecida (AP-18).

Situação dos findings após a Fase 3:

| Projeto | Resolvidos | Parciais / residuais |
|---|:-:|---|
| `code-smells-project` | 16/19 | AP-05 (só `/admin/*` ganhou guard), AP-16 (formato de email e política de senha), AP-19 (rate limit e paginação) — todos mudariam o contrato e não foram aprovados |
| `ecommerce-api-legacy` | 17/18 | AP-18 — 7 vulnerabilidades na cadeia de build do `sqlite3@5` só saem com o major `sqlite3@6` |
| `task-manager-api` | 14/17 | AP-16 (senha de 4 caracteres, regex de email), AP-19 (paginação, rate limit), AP-02 LOW (escape de `%`/`_` no LIKE) |

### Estrutura antes e depois

**1. code-smells-project** — monolito flat → camadas em `src/`

```
ANTES                         DEPOIS
app.py          (88)          app.py                  # launcher: python app.py continua valendo
controllers.py  (292)         src/
database.py     (86)          ├── app.py              # create_app (composition root)
models.py       (314)         ├── config/settings.py
                              ├── infra/              # database, schema, notificador
                              ├── models/             # entidades + *_repository + errors
                              ├── controllers/        # pedido, produto, usuario, relatorio, sistema
                              ├── views/              # *_routes + serializers
                              └── middlewares/        # auth (X-Admin-Token), error_handler
```

**2. ecommerce-api-legacy** — God Class → camadas em `src/`

```
ANTES                         DEPOIS
src/app.js         (14)       src/
src/AppManager.js  (141)      ├── app.js              # entrypoint + composition root
src/utils.js       (25)       ├── config/index.js     # tudo via env
                              ├── infra/              # db (promises + transação), schema, seed,
                              │                       # password, paymentGateway, cache, logger
                              ├── models/             # user, course, enrollment, auditLog,
                              │                       # financialReport (1 JOIN), constants, errors
                              ├── controllers/        # checkout, financialReport, user
                              ├── routes/             # checkout, admin, user + serializers
                              └── middlewares/        # auth, validate, rateLimit, asyncHandler, errorHandler
```

**3. task-manager-api** — camadas nominais → camadas reais em `src/`

```
ANTES                                   DEPOIS
app.py, database.py, seed.py            src/
models/      (task, user, category)     ├── app.py, seed.py
routes/      (task 299, user 211,       ├── config/settings.py
              report 223 linhas)        ├── infra/database.py
services/    (notification: nunca       ├── models/        # entidades + *_repository + constants + errors
              importado)                ├── services/      # task, user, category, report, auth
utils/helpers.py (quase nada usado)     ├── routes/        # task, user, category, report, health
                                        │                  # (finas: 17-53 linhas) + serializers + params
                                        ├── middlewares/   # auth (token assinado), error_handler
                                        └── utils/helpers.py
```

As rotas de categoria saíram do blueprint de relatórios, `NotificationService`, `marshmallow` e `requests` foram removidos, e `is_overdue`/`validate_*`/`is_admin` passaram a ser usados.

### Checklist de validação

Legenda: `[x]` verificado · `[!]` verificado com ressalva.

| Item | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|:-:|:-:|:-:|
| **Fase 1 — Análise** | | | |
| Linguagem detectada corretamente | [x] | [x] | [x] |
| Framework detectado corretamente | [x] | [x] | [x] |
| Domínio da aplicação descrito corretamente | [x] e-commerce | [x] LMS de cursos pagos | [x] gerenciador de tarefas |
| Número de arquivos analisados condiz com a realidade | [x] 4 | [x] 3 | [!] 14 (são 15 `.py`; LOC 1158 bate) |
| **Fase 2 — Auditoria** | | | |
| Relatório segue o template definido nos arquivos de referência | [x] | [x] | [x] |
| Cada finding tem arquivo e linhas exatos | [x] | [x] | [x] |
| Findings ordenados por severidade (CRITICAL → LOW) | [x] | [x] | [x] |
| Mínimo de 5 findings identificados | [x] 19 | [x] 18 | [x] 17 |
| Detecção de APIs deprecated incluída (se aplicável) | [x] nenhuma API; deps vulneráveis | [x] | [x] |
| Skill pausa e pede confirmação antes da Fase 3 | [x] | [x] | [x] |
| **Fase 3 — Refatoração** | | | |
| Estrutura de diretórios segue padrão MVC | [x] | [x] | [x] |
| Configuração extraída para módulo de config (sem hardcoded) | [x] | [x] | [x] |
| Models criados para abstrair dados | [x] | [x] | [x] |
| Views/Routes separadas para visualização ou roteamento | [x] `views/` | [x] `routes/` | [x] `routes/` |
| Controllers concentram o fluxo da aplicação | [x] | [x] | [x] papel exercido por `services/` |
| Error handling centralizado | [x] | [x] | [x] |
| Entry point claro | [!] `src/app.py` + launcher na raiz | [x] `npm start` → `src/app.js` | [x] `src/app.py` |
| Aplicação inicia sem erros | [x] | [x] | [x] |
| Endpoints originais respondem corretamente | [x] 30/33 + 3 intencionais | [x] 7/9 + 2 intencionais | [x] 65/65 |

Checagens finais do `06-validacao.md`, rodadas nos 3 `src/`: nenhum segredo literal, nenhuma query concatenada, nenhum `except:`/`catch {}` vazio, nenhuma rota/controller acessando o banco e nenhum model usando objetos HTTP. O único resultado do grep de API deprecated é uma docstring em `task-manager-api/src/utils/helpers.py:8` que menciona `datetime.utcnow()`.

### Logs das aplicações após a refatoração

Execução de 2026-10-12, com banco limpo, comparando o `.status` de cada requisição com o baseline gravado na Fase 1 (antes de qualquer alteração).

**code-smells-project** — `bash .refactor-arch/run-smoke.sh .refactor-arch/readme-final app.py`

```
INFO __main__: Servidor iniciado em http://0.0.0.0:5000
 * Serving Flask app 'src.app'
 * Debug mode: off
...
ok     200  /relatorios/vendas                            GET
ok     401  /admin/query                                  POST
ok     200  /produtos/11                                  DELETE
ok     404  /produtos/9999                                DELETE
ok     401  /admin/reset-db                               POST
---
rotas: 33 | respondeu: 33 | falhou (5xx/conexao): 0

diff contra baseline:
DIVERGE 029-POST-admin-query.status: 200 -> 401      # BC-3 aprovado no GATE
DIVERGE 030-POST-admin-query.status: 400 -> 401      # BC-3
DIVERGE 033-POST-admin-reset-db.status: 200 -> 401   # BC-3
```

**ecommerce-api-legacy** — mesmo smoke, com `Authorization: Bearer $ADMIN_TOKEN`

```
> node src/app.js
Frankenstein LMS rodando na porta 3000...
Processando cartão ****4444                 # antes: número completo + chave do gateway
ok     200  /api/checkout                                 POST
ok     200  /api/checkout                                 POST
ok     400  /api/checkout                                 POST
ok     404  /api/checkout                                 POST
ok     400  /api/checkout                                 POST
ok     200  /api/admin/financial-report                   GET
ok     409  /api/users/1                                  DELETE
ok     200  /api/admin/financial-report                   GET
ok     404  /api/users/999                                DELETE
rotas: 9 | respondeu: 9 | falhou (5xx/conexao): 0

diff contra baseline:
DIVERGE 007-DELETE-api-users-1.status: 200 -> 409    # BC-5: usuário com pagamento
DIVERGE 009-DELETE-api-users-999.status: 200 -> 404  # BC-5: usuário inexistente
```

Sem token, as rotas admin e o `DELETE` respondem `401` (BC-1).

**task-manager-api** — smoke com token de admin + contrato novo

```
Seed concluído com sucesso!
 * Serving Flask app 'app'
 * Debug mode: off
...
ok     200  /tasks/stats                                  GET
ok     200  /reports/summary                              GET
ok     200  /tasks/12                                     DELETE
ok     404  /tasks/999                                    DELETE
ok     200  /categories/5                                 DELETE
ok     404  /users/999                                    DELETE
---
rotas: 65 | respondeu: 65 | falhou (5xx/conexao): 0
status idênticos ao baseline: 65/65

.refactor-arch/check-contract.sh
contrato novo: 48 ok | 0 falhas
```

O projeto 3 também sobe a partir de outro diretório (`cd /tmp && python <projeto>/src/app.py`), o que confirma que `.env` e banco são resolvidos a partir da raiz do projeto.

### Comportamento da skill em stacks diferentes

**Detecção.** A stack foi identificada corretamente nos 3 projetos, inclusive versões exatas de dependências. No projeto 2, a skill ignorou o nome do repositório (`ecommerce`) e descreveu o domínio real (LMS de cursos pagos) a partir das tabelas e rotas.

**Mesmo catálogo, achados diferentes.** O catálogo é o mesmo nas 3 cópias, mas o resultado mudou conforme o código:
- **Flask + `sqlite3` cru:** SQL injection (AP-02) foi o finding central, com 22 queries concatenadas.
- **Express + callbacks:** nenhuma SQL injection, e o relatório registra explicitamente o falso positivo do template literal em `AppManager.js:57`. Em compensação apareceram callback hell (AP-13) e o crash do processo por `card` numérico, promovido a CRITICAL por estar no caminho de pagamento.
- **Flask + SQLAlchemy:** o foco passou para camada fantasma (AP-14) e camada pulada (AP-10), com números objetivos (75 acessos ao banco direto nas rotas, `services/` nunca importado). O `like(f'%{q}%')` foi rebaixado a LOW porque o ORM parametriza.

**Receita por nível de organização.** Os projetos 1 e 2 (monolito flat) receberam a mesma sequência de ondas, apesar de serem de linguagens diferentes. O projeto 3 (camadas nominais) teve um plano diferente: decidir, para cada módulo morto, se seria ativado ou removido, em vez de criar camadas do zero.

**Particularidades por stack.**
- No Express, a transação do checkout exigiu converter o driver de callback para promises (`infra/db.js`) antes de mover a regra de negócio. Foi a maior reescrita entre os três projetos.
- No Flask com SQLAlchemy, `onupdate` não dispara quando nenhuma coluna muda, então o `updated_at` explícito em `update_task` foi mantido. O relatório registra essa correção da própria auditoria.
- Os 3 projetos rodaram antes da regra da onda 0 existir (ver Desafio 1): no projeto 1 o `app.py` da raiz ficou como launcher, e no projeto 3 a ida para `src/` ficou para a última onda (7).

**Limites observados.**
- O smoke compara só status HTTP, então mudanças de corpo (mensagens unificadas, 404 em JSON) foram verificadas por scripts auxiliares (`check-contract.sh`, `bc-checks.sh`) que a skill gerou durante a Fase 3. Esses scripts não fazem parte da skill.
- A contagem de arquivos no projeto 3 ficou com 1 a menos que o real (14 vs 15), enquanto a de linhas bateu.
- Todo item que mudaria o contrato e não foi aprovado no GATE ficou como residual documentado, em vez de ser aplicado silenciosamente. Por isso nenhum projeto fechou 100% dos findings.
