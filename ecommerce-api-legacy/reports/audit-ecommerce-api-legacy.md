```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js 22) + Express 4.22.1 + sqlite3 5.1.7 (driver cru)
Files:   3 analyzed | 180 lines of code
Routes:  3 endpoints
Date:    2026-09-13
================================
```

## Contexto

Apesar do nome, o domínio é um **LMS de cursos pagos**: `users`, `courses`, `enrollments`,
`payments`, `audit_logs`. O fluxo principal é o checkout (cadastro implícito + matrícula +
pagamento simulado). Nível de organização: **1 — monolito flat**. A classe `AppManager`
(`src/AppManager.js`) concentra conexão, DDL, seed, rotas, regra de negócio e SQL; `src/utils.js`
é um saco de gatos (config + cache + "criptografia").

Nenhuma SQL injection foi encontrada: todas as queries de runtime usam placeholder `?`. A
interpolação em `src/AppManager.js:57` está dentro do array de parâmetros, não da string SQL.

## Summary

| Severidade | Findings |
|---|---|
| CRITICAL | 6 |
| HIGH | 6 |
| MEDIUM | 4 |
| LOW | 2 |
| **Total** | **18** |

## Findings

### [CRITICAL] God Class / God File (AP-03)

- **File:** `src/AppManager.js:4-139`
- **Occurrences:** 8 responsabilidades na mesma classe
  - `src/AppManager.js:7` — cria a conexão com o banco
  - `src/AppManager.js:12-16` — DDL das 5 tabelas
  - `src/AppManager.js:18-21` — seed
  - `src/AppManager.js:28`, `:80`, `:131` — registro das 3 rotas HTTP
  - `src/AppManager.js:37-57`, `:83-106`, `:133` — SQL direto dentro dos handlers (camada pulada, AP-10)
  - `src/AppManager.js:46`, `:68`, `:108-110` — regra de negócio (aprovação de pagamento, senha default, cálculo de receita)
  - `src/AppManager.js:59` — escrita em cache
  - `src/utils.js:1-25` — segundo arquivo misturando config, cache global e hash de senha
- **Description:** `AppManager` é banco, schema, seed, roteador, controller e regra de negócio
  ao mesmo tempo. Não existe Model, Controller nem View separados; os handlers falam SQL.
- **Impact:** Nenhuma regra é testável sem subir HTTP + SQLite. Qualquer mudança em um dos três
  domínios (checkout, relatório, usuários) edita o mesmo arquivo e o mesmo closure.
- **Recommendation:** Quebrar em `config/`, `database/` (conexão + schema + seed),
  `models/` (repositórios), `services/` (checkout, relatório), `controllers/`, `routes/`. (T-03)

### [CRITICAL] Credenciais e segredos hardcoded (AP-01)

- **File:** `src/utils.js:1-7`
- **Occurrences:** 5
  - `src/utils.js:2` — `dbUser` literal
  - `src/utils.js:3` — `dbPass` literal (nome sugere senha de produção)
  - `src/utils.js:4` — `paymentGatewayKey` com prefixo `pk_live_`
  - `src/utils.js:5` — `smtpUser` literal
  - `src/utils.js:6` — `port` literal
- **Description:** Toda a configuração é um objeto literal. Não há leitura de `process.env`,
  `.env` nem `.env.example`.
- **Impact:** A chave do gateway e a senha do banco estão no histórico do git para qualquer um
  com acesso ao repositório. Remover do código não basta: os valores precisam ser rotacionados.
- **Recommendation:** Mover para variáveis de ambiente lidas em `src/config/`, com
  `.env.example` contendo `CHANGE_ME`. Remover os campos nunca lidos (`dbUser`, `dbPass`,
  `smtpUser` — ver AP-21). (T-01)

### [CRITICAL] Entrada não validada derruba o processo (AP-16, promovido)

- **File:** `src/AppManager.js:29-35`
- **Occurrences:** 5
  - `src/AppManager.js:35` — só checa presença; `pwd` nem isso
  - `src/AppManager.js:46` — `cc.startsWith("4")` sem garantir que `card` é string
  - `src/AppManager.js:32` — `c_id` sem checagem de tipo
  - `src/AppManager.js:30` — `eml` sem validação de formato
  - `src/AppManager.js:68` — `pwd` ausente vira a senha default `"123456"`
- **Description:** O body do checkout é usado cru. `card` enviado como número chega em
  `cc.startsWith` dentro de um callback do sqlite3, onde a exceção não é capturada por ninguém.
- **Impact:** **Verificado em execução.** `POST /api/checkout` com `"card": 4111222233334444`
  (número, não string) derrubou o processo Node com
  `TypeError: cc.startsWith is not a function` — a app para de responder para **todos** os
  clientes. O usuário já tinha sido inserido (`:69`) antes do crash. Promovido de MEDIUM para
  CRITICAL: atinge o caminho de pagamento e impede o funcionamento da aplicação.
- **Recommendation:** Validar tipo/formato no controller antes de chamar o service e responder
  `400 "Bad Request"` (mesmo contrato já usado em `:35`). Handler de erro central como rede de
  segurança. (T-09, T-07)

### [CRITICAL] Endpoints sensíveis sem autenticação (AP-05)

- **File:** `src/AppManager.js:80`
- **Occurrences:** 3 — zero guards no projeto inteiro
  - `src/AppManager.js:80` — `GET /api/admin/financial-report` expõe nome de todos os alunos e quanto pagaram
  - `src/AppManager.js:131-133` — `DELETE /api/users/:id` apaga qualquer usuário (IDOR)
  - `src/AppManager.js:73-75` — checkout com email existente matricula e cobra na conta do dono do email sem checar `pwd`
- **Description:** Não existe middleware de autenticação nem checagem de identidade em nenhuma rota.
- **Impact:** **Verificado em execução.** Checkout com `"eml": "leonan@fullcycle.com.br"` e
  `"pwd": "errada"` retornou `200` e criou matrícula na conta do Leonan. Qualquer anônimo lê o
  relatório financeiro e apaga usuários.
- **Recommendation:** Estrutura de guard (middleware) aplicada às rotas admin e destrutivas,
  e verificação de senha no checkout para email já cadastrado. **Toda correção muda status
  HTTP** — ver Breaking changes BC-1 e BC-2. (T-09)

### [CRITICAL] Hash de senha caseiro e senha em texto puro (AP-04)

- **File:** `src/utils.js:17-23`
- **Occurrences:** 3
  - `src/utils.js:17-23` — `badCrypto`: base64 da senha, pega 2 caracteres, repete, corta em 10
  - `src/AppManager.js:18` — seed grava a senha do Leonan em texto puro (`pass = '123'`)
  - `src/AppManager.js:68` — senha default `"123456"` quando `pwd` não é enviado
- **Description:** O "hash" depende só dos ~12 primeiros bits da senha. O laço de 10.000
  iterações (`:19`) é teatro: toda iteração concatena os mesmos 2 caracteres.
- **Impact:** **Verificado em execução.** `badCrypto("senhaforte") === badCrypto("senha123")
  === "c2c2c2c2c2"` e `badCrypto("123") === badCrypto("123456")`. Há no máximo 4.096 hashes
  possíveis; qualquer senha colide com milhares de outras.
- **Recommendation:** Trocar por `crypto.scrypt` com salt aleatório (stdlib, sem dependência
  nova) e comparação com `timingSafeEqual`. O seed passa a gravar hash. (T-10)

### [CRITICAL] Número de cartão e chave do gateway em log (AP-06)

- **File:** `src/AppManager.js:45`
- **Description:** ``console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)``
  imprime o PAN completo e a chave `pk_live_` a cada checkout.
- **Impact:** **Verificado em execução.** `boot.log` do baseline contém
  `Processando cartão 4111222233334444 na chave pk_live_…`. PAN completo em log é violação
  direta de PCI-DSS; qualquer um com acesso aos logs tem cartões e a chave do gateway.
- **Recommendation:** Logar só os 4 últimos dígitos mascarados, nunca a chave. (T-10)

### [HIGH] Callback hell e contagem manual de pendências (AP-13)

- **File:** `src/AppManager.js:37-77`
- **Occurrences:** 4
  - `src/AppManager.js:37`, `:40`, `:50`, `:54`, `:57` — 5 níveis de callback no checkout
  - `src/AppManager.js:26` — `const self = this` para contornar `function(err)` em `:50`, `:54`, `:69`
  - `src/AppManager.js:86`, `:93`, `:97`, `:117`, `:120` — contadores `coursesPending`/`enrPending` simulando `Promise.all`
  - `src/AppManager.js:98`, `:121` — `res.json(report)` duplicado em dois ramos
- **Description:** O relatório é montado por callbacks concorrentes que dão `push` em ordem de
  chegada e decrementam contadores manuais.
- **Impact:** **Verificado em execução.** Duas execuções idênticas do baseline devolveram os
  alunos do curso Docker em ordem diferente (`Guilherme, Leonan` vs `Leonan, Guilherme`). Se a
  query de `:92` falhar, `enrollments` é `undefined` e `enrollments.length` (`:93`) derruba o
  processo.
- **Recommendation:** Promisificar o driver e reescrever os fluxos com `async/await`, com
  ordem determinística. (T-14)

### [HIGH] Erro engolido e sem tratamento centralizado (AP-11)

- **File:** `src/AppManager.js:133-135`
- **Occurrences:** 6
  - `src/AppManager.js:133-135` — `DELETE` ignora `err` e responde 200 sempre
  - `src/AppManager.js:57` — falha ao gravar `audit_logs` é ignorada e o checkout responde 200
  - `src/AppManager.js:92`, `:104`, `:106` — `err` recebido e nunca checado no relatório
  - `src/AppManager.js:38` — erro de banco mascarado como `404 "Curso não encontrado"`
  - `src/app.js:1-14` — nenhum middleware de erro (`app.use((err, req, res, next) => …)`)
- **Description:** Erros de I/O são descartados ou convertidos em respostas enganosas; não há
  ponto único de tratamento.
- **Impact:** **Verificado no baseline:** `DELETE /api/users/999` (usuário inexistente) responde
  `200 "Usuário deletado…"`. Sem handler central, qualquer exceção em callback derruba o
  processo (ver AP-16).
- **Recommendation:** Erros tipados nos services + middleware de erro único em `app.js` que
  preserve os status e textos atuais. (T-07)

### [HIGH] Fluxo multi-escrita sem transação (AP-12)

- **File:** `src/AppManager.js:50-57`
- **Occurrences:** 4 escritas encadeadas sem `BEGIN`/`COMMIT`
  - `src/AppManager.js:69` — `INSERT users`
  - `src/AppManager.js:50` — `INSERT enrollments`
  - `src/AppManager.js:54` — `INSERT payments`
  - `src/AppManager.js:57` — `INSERT audit_logs`
- **Description:** Matrícula, pagamento e auditoria são statements independentes. Um `return`
  de erro no meio (`:55`) deixa o que já foi gravado.
- **Impact:** Falha em `:54` deixa matrícula sem pagamento — o aluno aparece no relatório com
  `paid: 0` e acesso ao curso sem ter pago. **Verificado:** o crash de AP-16 deixou um usuário
  gravado sem matrícula.
- **Recommendation:** Envolver matrícula + pagamento + auditoria em uma transação no service
  de checkout. A criação do usuário fica fora, preservando o comportamento atual (usuário
  continua existindo mesmo com pagamento recusado). (T-13)

### [HIGH] Regra de negócio no handler (Fat Controller) (AP-07)

- **File:** `src/AppManager.js:28-78`
- **Occurrences:** 2 handlers
  - `src/AppManager.js:28-78` — checkout (51 linhas): aprovação do pagamento (`:46`), cadastro implícito com hash (`:66-72`), auditoria (`:57`), cache (`:59`)
  - `src/AppManager.js:80-129` — relatório (50 linhas): cálculo de receita só com `PAID` (`:108-110`), `paid` e `'Unknown'` (`:112-115`)
- **Description:** A regra "cartão começando com 4 é aprovado" e "receita soma só pagamentos
  PAID" vivem dentro de closures de rota.
- **Impact:** Só é possível testar a aprovação de pagamento ou o cálculo de receita subindo
  HTTP e SQLite.
- **Recommendation:** Extrair `CheckoutService` e `FinancialReportService`; controllers só
  traduzem HTTP ↔ service. (T-04)

### [HIGH] Estado global mutável (AP-09)

- **File:** `src/utils.js:9-14`
- **Occurrences:** 3
  - `src/utils.js:9`, `:14` — `globalCache` sem limite nem TTL, escrito a cada checkout e **nunca lido**
  - `src/utils.js:10`, `:25` — `totalRevenue` exportado por valor (CommonJS): mutação nunca se propagaria
  - `src/AppManager.js:2` — `totalRevenue` importado e nunca usado
- **Description:** Cache de módulo write-only e contador exportado por valor.
- **Impact:** `globalCache` cresce uma chave por usuário que já comprou e nunca é liberado —
  vazamento de memória sem nenhum benefício, e impossível de compartilhar entre workers.
- **Recommendation:** Isolar o cache atrás de um módulo com interface explícita (mantendo o
  log `[LOG] Salvando no cache`), remover `totalRevenue`. (T-06, T-13)

### [HIGH] Acoplamento forte sem injeção de dependência (AP-08)

- **File:** `src/AppManager.js:7`
- **Occurrences:** 3
  - `src/AppManager.js:7` — `new sqlite3.Database(':memory:')` no construtor
  - `src/app.js:8` — `new AppManager()` sem parâmetros
  - `src/AppManager.js:2` — `config` importado direto do módulo global
- **Description:** A classe cria sua própria conexão e lê config global; não há ponto de
  injeção.
- **Impact:** Testar o checkout exige o SQLite real em memória e a config real; não dá para
  trocar o banco (ex.: arquivo, Postgres) sem editar a classe.
- **Recommendation:** Composição em `app.js`: cria a conexão, passa para repositórios, que
  são passados para services, que são passados para controllers. (T-05)

### [MEDIUM] Dependências e APIs obsoletas (AP-18)

- **File:** `package.json:8-11`
- **Occurrences:** 3
  - `src/AppManager.js:37-133` — driver `sqlite3` em estilo callback nas 11 chamadas de runtime (`:37`, `:40`, `:50`, `:54`, `:57`, `:69`, `:83`, `:92`, `:104`, `:106`, `:133`)
  - `src/AppManager.js:29-33`, `:43`, `:46`, `:52`, `:68`, `:81`, `:90`, `:132` — `let` para valor nunca reatribuído
  - `package.json:9-10` — `npm audit`: 12 vulnerabilidades (1 critical, 7 high); runtime: `path-to-regexp`, `qs`, `body-parser` corrigíveis via express 4.22.2; `tar`/`node-gyp`/`cacache` vêm da cadeia de build do `sqlite3` 5 e só saem com `sqlite3@6` (major)
- **Description:** Ver tabela em "APIs Deprecated".
- **Impact:** O estilo callback é a causa de AP-13. As vulnerabilidades de runtime do Express
  incluem ReDoS em `path-to-regexp`.
- **Recommendation:** `util.promisify` sobre o driver + `async/await`; `const`; `npm audit fix`
  (sem major). `sqlite3@6` fica fora do escopo (major, exige teste próprio). (T-11)

### [MEDIUM] N+1 queries no relatório financeiro (AP-15)

- **File:** `src/AppManager.js:83-106`
- **Occurrences:** 3 queries dentro de laço
  - `src/AppManager.js:92` — enrollments por curso
  - `src/AppManager.js:104` — usuário por matrícula
  - `src/AppManager.js:106` — pagamento por matrícula
- **Description:** `GET /api/admin/financial-report = 1 + C + 2E queries` (C cursos, E matrículas).
- **Impact:** No seed do baseline já são 9 queries por request; cresce linearmente com cada
  venda, em rota que não tem paginação.
- **Recommendation:** Uma query com `LEFT JOIN` ordenada por curso/matrícula, agregação em
  memória no service preservando exatamente a regra atual (`paid` = valor do pagamento
  independente do status; receita soma só `PAID`; aluno removido vira `'Unknown'`). (T-08)

### [MEDIUM] Schema sem restrições de integridade (AP-16)

- **File:** `src/AppManager.js:12-16`
- **Occurrences:** 4
  - `src/AppManager.js:12` — `users.email` sem `UNIQUE`, nenhuma coluna `NOT NULL`
  - `src/AppManager.js:14` — `enrollments.user_id`/`course_id` sem `REFERENCES`, sem `UNIQUE(user_id, course_id)`
  - `src/AppManager.js:15` — `payments.enrollment_id` sem `REFERENCES`
  - `src/AppManager.js:13` — `courses.price`/`active` anuláveis
- **Description:** A integridade depende só do código da rota.
- **Impact:** **Verificado em execução.** O mesmo usuário comprou o mesmo curso duas vezes e
  foi cobrado duas vezes (ambos `200`). Após `DELETE /api/users/1`, o relatório mostra
  `"student":"Unknown"` com o pagamento ainda somado na receita (a própria resposta admite:
  "as matrículas e pagamentos ficaram sujos"). Dois checkouts simultâneos com email novo criam
  usuários duplicados.
- **Recommendation:** `UNIQUE` em `users.email` e `NOT NULL` onde o código já garante presença
  (sem mudança de contrato). FK com política de exclusão e `UNIQUE(user_id, course_id)` mudam
  status HTTP — ver BC-4 e BC-5. (T-13)

### [MEDIUM] Configuração e middleware inseguros (AP-19)

- **File:** `src/app.js:5-6`
- **Occurrences:** 4
  - `src/app.js:5-6` — sem headers de segurança (`helmet` ou equivalente)
  - `src/app.js:6`, `src/AppManager.js:28` — sem rate limiting no checkout
  - `src/utils.js:6` — porta hardcoded (resolvido junto com AP-01)
  - `src/AppManager.js:1` — `sqlite3.verbose()` ligado incondicionalmente
- **Description:** App exposta sem nenhuma camada de proteção HTTP.
- **Impact:** Checkout sem rate limit permite *card testing* (testar milhares de cartões
  roubados). Não promovido a HIGH apesar de tocar pagamento: a mitigação (`429`) muda o
  contrato e depende de BC-6.
- **Recommendation:** Porta via env (T-01); `verbose()` só com flag de debug; headers e rate
  limit condicionados a BC-6. (T-01, T-09)

### [LOW] Ruído de legibilidade (AP-21)

- **File:** `src/AppManager.js:29-33`
- **Occurrences:** 6 categorias
  - `src/AppManager.js:29-33`, `:89`, `:102` — nomes de 1-3 letras em código de pagamento (`u`, `e`, `p`, `cid`, `cc`, `c`, `enr`)
  - `src/app.js:13`, `src/utils.js:13` — `console.log` como logger
  - `src/AppManager.js:2`, `src/utils.js:25` — import/export sem uso (`totalRevenue`, `globalCache`)
  - `src/utils.js:2`, `:3`, `:5` — config nunca lida (`dbUser`, `dbPass`, `smtpUser`)
  - `src/AppManager.js:104` — `SELECT name, email` mas `email` nunca é usado
  - `src/AppManager.js:38`, `:60`, `:135` — idioma misturado: código em inglês, mensagens em português, chave `msg`
- **Description:** Nomes opacos, código morto e logging ad-hoc.
- **Impact:** `cc` e `p` no fluxo de pagamento escondem o que é cartão e o que é senha — foi
  exatamente isso que levou o PAN para o log.
- **Recommendation:** Renomear, remover mortos, logger mínimo centralizado. Textos de resposta
  **não mudam** (contrato). (T-11, T-12)

### [LOW] Magic numbers e magic strings (AP-20)

- **File:** `src/AppManager.js:46`
- **Occurrences:** 5
  - `src/AppManager.js:21`, `:46`, `:108` — `'PAID'`
  - `src/AppManager.js:46`, `:48` — `'DENIED'`
  - `src/AppManager.js:46` — `"4"` (regra de aprovação do gateway simulado)
  - `src/AppManager.js:68` — `"123456"` (senha default)
  - `src/AppManager.js:113` — `'Unknown'`; `src/utils.js:19` — `10000`
- **Description:** Status de pagamento e regras de negócio espalhados como literais.
- **Impact:** Um typo em `'PAID'` zera a receita do relatório sem erro nenhum.
- **Recommendation:** Constantes nomeadas no model (`PaymentStatus.PAID/DENIED`). (T-12)

## APIs Deprecated

Detecção executada: grep do catálogo Node, `node --pending-deprecation --throw-deprecation src/app.js`
(nenhum `DEP0xxx` no boot), `npm outdated`, `npm audit`.

| Obsoleto | Ocorrências | Equivalente moderno |
|---|---|---|
| driver em callback (`db.run/get/all(sql, cb)`) | `src/AppManager.js:37-133` (11x) | `util.promisify` + `async/await` |
| `let` para valor nunca reatribuído | `src/AppManager.js:29-132` (12x) | `const` |
| `express@4.22.1` (deps `path-to-regexp`, `qs`, `body-parser` vulneráveis) | `package.json:9` | `express@4.22.2` via `npm audit fix` |
| `sqlite3@5.1.7` (cadeia de build `tar`/`node-gyp` vulnerável) | `package.json:10` | `sqlite3@6` — major, fora do escopo desta refatoração |

Nenhuma ocorrência de `new Buffer(`, `url.parse(`, `crypto.createCipher`, `body-parser` standalone.

## Breaking changes propostos

Cada item muda status HTTP ou texto de resposta. Só entra na Fase 3 com aval explícito.

1. **BC-1 — Autenticação nas rotas admin e destrutivas.** `GET /api/admin/financial-report` e
   `DELETE /api/users/:id` passam a exigir credencial (ex.: header `Authorization: Bearer
   <ADMIN_TOKEN>` via env) → `401` sem ela. Sem BC-1, AP-05 permanece aberto.
2. **BC-2 — Senha conferida no checkout de email existente.** Senha errada → `401`. Hoje `200`
   e matricula na conta alheia.
3. **BC-3 — `pwd` obrigatório.** Sem `pwd` → `400 "Bad Request"`, eliminando a senha default
   `"123456"`. Hoje `200`.
4. **BC-4 — `UNIQUE(user_id, course_id)`.** Recompra do mesmo curso → `409`. Hoje `200` e
   cobra de novo.
5. **BC-5 — FK + política de exclusão de usuário.** `PRAGMA foreign_keys = ON`; `DELETE` de
   usuário inexistente → `404` (hoje `200`, linha 9 do baseline); usuário com pagamentos →
   `409` (preserva histórico financeiro) ou soft delete. Muda o texto atual da resposta.
6. **BC-6 — Rate limiting no checkout + headers de segurança.** Excesso de requisições → `429`.
   Exige dependência nova (`helmet`, `express-rate-limit`) ou middleware próprio.

**Não são breaking** (serão feitas na Fase 3 sem aval extra): `card`/`c_id` com tipo inválido
passam a responder `400 "Bad Request"` em vez de derrubar o processo (crash não é contrato;
`400` já é a resposta de entrada inválida em `:35`); ordem de cursos e alunos no relatório
passa a ser determinística (mesmas chaves; hoje a ordem já varia entre execuções).

## Baseline de comportamento

9/9 requisições responderam (3 endpoints, 0 × 5xx) — `.refactor-arch/baseline/`.
Destrutivas (`DELETE`) ficam no fim do `rotas.tsv`. Excluída do smoke: checkout com `card`
numérico, porque derruba o processo e invalidaria as linhas seguintes (verificada
manualmente, ver AP-16). O corpo de `GET /api/admin/financial-report` não é determinístico
na ordem dos alunos (AP-13); status é.

```
================================
Total: 18 findings
================================
```

## Resultado da Fase 3 (2026-09-13)

Refatoração in-place na `main`, sem commit de checkpoint (escolha no GATE). BC-1 … BC-6 aprovados e aplicados.
Plano: `.refactor-arch/plano-refatoracao.md`. 6 ondas, smoke após cada uma; ondas 1-4 com status **e** corpo
idênticos ao baseline.

| Finding | Situação |
|---|---|
| AP-03, AP-01, AP-16 (crash), AP-05, AP-04, AP-06 | Resolvidos |
| AP-11, AP-13, AP-12, AP-09, AP-08, AP-07 | Resolvidos |
| AP-16 (schema), AP-19, AP-15 | Resolvidos |
| AP-18 | **Parcial**: callback/`let` e vulnerabilidades de runtime resolvidos (`express@4.22.2`, override `qs@^6.16.0`); 7 vulnerabilidades da cadeia de build do `sqlite3@5` (`tar`, `node-gyp`) só saem com `sqlite3@6` (major, fora do escopo) |
| AP-21, AP-20 | Resolvidos; mensagens de resposta seguem em português por serem contrato |

Divergências de status contra o baseline, todas intencionais:

- Anônimo: `GET /api/admin/financial-report` e `DELETE /api/users/:id` → `401` (BC-1).
- Autenticado: `DELETE /api/users/1` → `409` (BC-5, usuário com pagamento); `DELETE /api/users/999` → `404` (BC-5).

Mudanças de comportamento em caminhos de erro (fora do smoke):

- Tipo inválido no checkout (`card`/`pwd` numéricos, `usr`/`eml` não-string) → `400`; antes derrubava o processo ou gravava tipo misto.
- JSON malformado → `400 "Bad Request"` em texto; antes HTML do Express com stack trace.
- Falha ao gravar `audit_logs` → rollback + `500`; antes era ignorada e o checkout respondia `200`.
- Erro de banco na busca do curso continua `404` (contrato), mas agora é logado.

Resíduos:

- Dois checkouts **simultâneos** com o mesmo email novo: o segundo responde `500 "Erro ao criar usuário"` (UNIQUE impede a duplicata que antes era gravada). Melhorar para `409` exige nova decisão de contrato.
- Os segredos que estavam em `src/utils.js` continuam no histórico do git e **precisam ser rotacionados**.
