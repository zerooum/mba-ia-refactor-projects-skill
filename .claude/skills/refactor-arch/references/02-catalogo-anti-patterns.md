# 02 — Catálogo de Anti-Patterns

21 anti-patterns com sinais de detecção, severidade e transformação correspondente.

**Índice:** [Escala](#escala-de-severidade) · [CRITICAL](#critical) · [HIGH](#high) · [MEDIUM](#medium) · [LOW](#low) · [APIs deprecated](#apis-deprecated) · [Guardas anti-falso-positivo](#guardas-anti-falso-positivo)

---

## Escala de severidade

| Nível | Critério |
|---|---|
| **CRITICAL** | Falha grave de arquitetura ou segurança: impede o funcionamento correto, expõe dados sensíveis, ou viola completamente a separação de responsabilidades. |
| **HIGH** | Forte violação de MVC ou SOLID que dificulta muito manutenção e testes. |
| **MEDIUM** | Padronização, duplicação ou gargalo de performance moderado. |
| **LOW** | Legibilidade, nomenclatura, magic numbers. |

Regra de agrupamento: **N ocorrências do mesmo anti-pattern no mesmo escopo = 1 finding com N linhas listadas.** Não infle a contagem.

Regra de promoção: um anti-pattern MEDIUM sobe para HIGH quando atinge caminho de autenticação, pagamento ou dado pessoal. Justifique a promoção no finding.

---

## CRITICAL

### AP-01 — Credenciais e segredos hardcoded
Chave, senha, token ou string de conexão literal no código-fonte.

```bash
rg -n -i "(secret|password|passwd|pwd|api[_-]?key|token|private[_-]?key)\s*[:=]\s*['\"][^'\"]{4,}" --glob '!node_modules'
rg -n "(sk_live|pk_live|AKIA|ghp_|xox[baprs]-|-----BEGIN)" --glob '!node_modules'
rg -n -i "(postgres|mysql|mongodb|redis)://[^'\"\s]*:[^'\"\s]*@"
rg -n "debug\s*=\s*True|DEBUG\s*[:=]\s*true"
```

Inclui: `SECRET_KEY` literal, senha de SMTP, chave de gateway de pagamento, `debug=True` combinado com `host="0.0.0.0"` (expõe o debugger remoto).
**Por que importa:** qualquer pessoa com acesso ao repositório tem acesso ao sistema. Segredo commitado é segredo vazado — rotacionar é obrigatório, remover do código não basta.
**Falso positivo:** `settings.py` lendo `os.getenv("SECRET_KEY", "dev-only")` com valor default claramente de desenvolvimento — reporte como LOW.
→ **T-01**

### AP-02 — SQL Injection por concatenação
Query montada com `+`, f-string, `%` ou template literal contendo entrada do usuário.

```bash
rg -n "(execute|query|run|all|get)\s*\(\s*[\"'].*(SELECT|INSERT|UPDATE|DELETE)" -i
rg -n "f[\"'].*(SELECT|INSERT|UPDATE|DELETE).*\{" -i
rg -n "[\"'].*(SELECT|INSERT|UPDATE|DELETE).*[\"']\s*\+" -i
rg -n '`.*(SELECT|INSERT|UPDATE|DELETE).*\$\{' -i
```

**Por que importa:** em rota de login, permite bypass de autenticação com `' OR '1'='1`. Em qualquer rota, permite dump ou destruição do banco.
**Sempre confira a leitura:** só é injection se o valor concatenado vier de entrada externa (body, query param, path param, header).
→ **T-02**

### AP-03 — God Class / God File
Um arquivo ou classe concentrando responsabilidades de camadas diferentes.

```bash
find . -name '*.py' -o -name '*.js' -o -name '*.ts' | grep -v node_modules | xargs wc -l | sort -rn | head -20
```

Confirme por **leitura**, não por tamanho. É God File quando o mesmo arquivo faz duas ou mais destas: conexão/DDL do banco, registro de rotas, regra de negócio, serialização de resposta, autenticação. Ou quando cobre 3+ domínios de negócio distintos.
**Falso positivo:** arquivo longo com uma responsabilidade só (um mapa de constantes, um schema) não é God File. Reporte tamanho como LOW, se algo.
→ **T-03**

### AP-04 — Senha em texto puro ou hash fraco
Senha armazenada sem hash, com MD5/SHA1, sem salt, ou com criptografia caseira.

```bash
rg -n -i "md5|sha1\(|hashlib\.(md5|sha1)|createHash\(['\"](md5|sha1)"
rg -n -i "senha\s*==|password\s*==|pwd\s*==|\.password\s*===?"
rg -n -i "btoa|atob|base64.*password|encrypt.*function|badCrypto"
```

Sinais de criptografia caseira: loop de "rounds" manual, `substring()` no digest, base64 chamado de criptografia, comparação de hash com `==` (timing attack).
**Por que importa:** MD5 sem salt cai em rainbow table instantaneamente. Criptografia caseira é sempre pior que a biblioteca padrão.
→ **T-10**

### AP-05 — Endpoint sensível sem autenticação ou autorização
Rota que lê dado pessoal, movimenta dinheiro ou destrói estado, sem verificação de identidade.

```bash
rg -n "(admin|reset|delete|drop|truncate|query|exec|report|financial)" --glob '*rout*' --glob '*app*' --glob '*controller*' -i
rg -n "@(login_required|jwt_required|requires_auth)|authenticate|authorize|verifyToken|isAuthenticated" -i
```

Lógica: liste as rotas, liste os guards. Rota sensível sem guard é finding. **Zero guards no projeto inteiro é um único finding CRITICAL** ("ausência total de autenticação"), com as rotas afetadas listadas.
Casos agravantes: endpoint que executa SQL arbitrário; endpoint que apaga o banco; `DELETE /users/:id` sem checar identidade (IDOR).
→ **T-09** (estrutura de guard) + registro de risco

### AP-06 — Dado sensível vazado na resposta
Hash de senha, `SECRET_KEY`, caminho interno, stack trace ou número de cartão no corpo HTTP.

```bash
rg -n -i "['\"]?(password|senha|secret|token|hash)['\"]?\s*:\s*(self|row|user|obj)\." 
rg -n "str\(e\)|err\.message|e\.stack|traceback" 
rg -n -i "console\.log.*(card|cc|cvv|password|key)|print.*(senha|password|secret)"
```

Inclui: `to_dict()` que devolve o campo de senha; `/health` que devolve a `SECRET_KEY`; `jsonify({"erro": str(e)})` expondo schema e paths; PAN de cartão em log.
**Por que importa:** log com cartão completo é violação de PCI-DSS. `str(e)` no corpo entrega nome de tabela e caminho de arquivo para o atacante.
→ **T-07** (erro) + **T-10** (serialização)

---

## HIGH

### AP-07 — Regra de negócio na rota / Fat Controller
Validação, cálculo, decisão de domínio ou montagem de relatório dentro do handler HTTP.

```bash
rg -n -c "if |for |while " --glob '*rout*' --glob '*view*' --glob '*controller*'
rg -n "round\(|sum\(|\* 0\.|/ 100|timedelta|discount|desconto|total\s*=" --glob '*rout*' --glob '*controller*'
```

Sinais: handler com mais de ~20 linhas; lista de valores válidos literal dentro do handler; cálculo de desconto/imposto/score no handler; handler que abre o banco e formata a resposta no mesmo corpo.
**Por que importa:** regra presa ao handler só é testável subindo HTTP, e é reimplementada divergente em cada rota que precisa dela.
→ **T-04**

### AP-08 — Acoplamento forte sem injeção de dependência
Módulo instancia sua própria dependência ou importa conexão global, impossibilitando substituição em teste.

```bash
rg -n "^from database import|^import database|require\(['\"]\.\./(db|database)|new [A-Z][A-Za-z]*\(\)" 
rg -n "smtplib\.|requests\.(get|post)|fetch\(|axios\." --glob '*model*' --glob '*service*' --glob '*controller*'
```

**Por que importa:** sem ponto de injeção, testar o controller exige banco real e rede real.
→ **T-05**

### AP-09 — Estado global mutável
Variável de módulo reatribuída em runtime, singleton de conexão, cache global sem limite.

```bash
rg -n "^(let|var) [a-zA-Z_]+ = (\{\}|\[\]|0|null)|^[a-z_]+ = (None|\{\}|\[\])" 
rg -n "global \w+|globalThis\.|module\.exports\s*=\s*\{[^}]*cache"
rg -n "check_same_thread\s*=\s*False"
```

Inclui: conexão única compartilhada entre threads; `globalCache = {}` sem TTL (memory leak); contador global exportado por valor em CommonJS (mutação nunca se propaga — bug latente).
**Por que importa:** quebra sob concorrência e impede múltiplos workers. É a causa raiz mais comum de bug intermitente.
→ **T-06**, **T-13**

### AP-10 — Camada pulada
View/rota acessando o banco diretamente, ou model conhecendo HTTP.

```bash
rg -n "cursor\.execute|\.query\.|db\.session|db\.(all|get|run)\(" --glob '*rout*' --glob '*view*'
rg -n "request\.|jsonify|res\.(json|send)|abort\(" --glob '*model*'
```

**Por que importa:** a dependência flui nos dois sentidos e a camada do meio vira decoração.
→ **T-04**, **T-05**

### AP-11 — Erro engolido ou sem tratamento centralizado
`except:` pelado, `catch` vazio, callback que recebe `err` e nunca checa, `try/except` copiado em todo handler.

```bash
rg -n "except\s*:|except Exception\s*:|catch\s*\([^)]*\)\s*\{\s*\}|catch\s*\{\s*\}"
rg -n "function\s*\(err[,)]" -A2
rg -n "@app\.errorhandler|app\.use\(\(err|errorHandler|@ExceptionHandler"
```

Dois findings distintos, avalie os dois:
1. **Erro suprimido** — `except: pass`, `catch {}`, callback com `err` ignorado respondendo 200.
2. **Ausência de handler central** — mesmo bloco `try/except → 500` repetido em todos os handlers, sem `@app.errorhandler`/middleware de erro.

**Por que importa:** erro engolido transforma bug em comportamento silencioso e errado. Em callback assíncrono, um `undefined` não checado derruba o processo inteiro.
→ **T-07**

### AP-12 — Fluxo multi-escrita sem transação
Duas ou mais escritas relacionadas sem `BEGIN`/`COMMIT`/`ROLLBACK`.

```bash
rg -n -B3 -A10 "INSERT INTO|UPDATE .* SET" | rg -n "commit|rollback|BEGIN|transaction|atomic" 
rg -n "begin|transaction|atomic|session\.begin|db\.transaction" -i
```

Sinais: checkout que insere pedido, insere itens e decrementa estoque em statements soltos; `return` de erro no meio do fluxo sem rollback; leitura de estoque e decremento sem lock (race condition).
**Por que importa:** falha no meio deixa o banco inconsistente — matrícula sem pagamento, pedido sem item, estoque negativo.
→ **T-13**

### AP-13 — Callback hell / async mal gerenciado
Aninhamento profundo de callbacks, contagem manual de pendências, mistura de `function` e arrow por causa de `this`.

```bash
rg -n "function\s*\([^)]*\)\s*\{" -c
rg -n "const self = this|var that = this|_this = this"
rg -n "Pending|pending\s*--|counter\s*--"
```

Sinais: 3+ níveis de callback; `pending--` simulando `Promise.all` (se um erro ocorrer o contador nunca zera e a requisição pendura para sempre); `const self = this` contornando escopo.
**Por que importa:** erro não propaga, não há timeout, e `res.json` pode ser chamado duas vezes (`ERR_HTTP_HEADERS_SENT`).
→ **T-14**

### AP-14 — Camada fantasma
Diretório ou classe de camada que existe mas não é usada — e cuja lógica está duplicada onde deveria ser consumida.

```bash
# para cada módulo em services/, utils/, helpers/: ele é importado?
rg -n "from (services|utils|helpers)|require.*(services|utils|helpers)"
# para cada função pública definida lá: ela é chamada?
rg -n "^def |^class |^function |^export function" services/ utils/
```

Inclui: método de model (`validate_status`, `is_overdue`) definido e nunca chamado, com a lógica copiada inline nas rotas; constantes definidas em `helpers.py` e reescritas como literais nas rotas; biblioteca de validação declarada no manifesto e nunca importada.
**Por que importa:** dá a ilusão de arquitetura em camadas. Duas cópias da regra divergem na primeira manutenção.
→ **T-04** (ativar) ou remoção (documentar qual dos dois)

---

## MEDIUM

### AP-15 — N+1 queries
Query dentro de laço, ou acesso lazy a relacionamento dentro de laço.

```bash
rg -n -A6 "for |forEach|\.map\(" | rg -n "execute|\.query\.|\.get\(|\.all\(|\.count\(|findOne"
rg -n "len\(\w+\.\w+s\)|\.length" --glob '*rout*'
```

Sinais: loop sobre pedidos com query de itens por pedido (e outra por item); `User.query.get()` dentro do laço quando existe `relationship` disponível; `len(u.tasks)` dentro do laço (dispara lazy load); N counts de agregação onde um `GROUP BY` resolveria; delete em laço no lugar de cascade.
Quantifique no finding: `GET /tasks = 1 + 2N queries`.
→ **T-08**

### AP-16 — Validação ausente ou divergente
Entrada usada sem checagem de presença, tipo, formato ou faixa — ou regra de create diferente da de update.

```bash
rg -n "request\.(json|get_json|form|args)|req\.(body|params|query)" -A5
rg -n "int\(|float\(|parseInt|Number\(" --glob '*rout*' --glob '*controller*'
```

Sinais: `preco < 0` sem checar tipo (`TypeError` → 500 se vier string); `int(query_param)` sem `try`; email validado com regex frouxo ou não validado; ausência de `UNIQUE` no schema e ausência de checagem de duplicidade; política de senha de 4 caracteres; create valida tamanho do nome e update não.
**Compare create e update lado a lado** — divergência é o caso mais comum e o mais difícil de ver por grep.
→ **T-09**

### AP-17 — Duplicação de código
Bloco equivalente repetido em 2+ lugares.

Detecção é por leitura. Candidatos frequentes:
- Serialização do mesmo objeto reescrita em cada função
- Duas funções idênticas exceto pelo `WHERE`
- Bloco de validação copiado entre create e update
- Cálculo de "está atrasado"/"está ativo" copiado em cada rota que precisa
- `try/except → 500` idêntico em todos os handlers (conta como AP-11, não duplique o finding)

→ **T-04**, **T-07**, **T-12**

### AP-18 — API deprecated em uso
Ver [seção dedicada](#apis-deprecated).
→ **T-11**

### AP-19 — Configuração ou middleware inseguro
```bash
rg -n "CORS\(app\)|origin:\s*['\"]\*|Access-Control-Allow-Origin.*\*"
rg -n "helmet|rate.?limit|express\.json\(\{" -i
rg -n "debug\s*=\s*True|host\s*=\s*['\"]0\.0\.0\.0"
```

Inclui: CORS liberado para qualquer origem; ausência de `helmet`/headers de segurança; ausência de rate limiting em `/login`; ausência de limite de tamanho de body; `SELECT *` sem paginação em coleção que cresce; healthcheck que roda `COUNT(*)` em tabela inteira.
→ **T-01**, **T-09**

---

## LOW

### AP-20 — Magic numbers e magic strings
```bash
rg -n "[^a-zA-Z_](0\.[0-9]+|[1-9][0-9]{2,})[^a-zA-Z_0-9]" --glob '*rout*' --glob '*model*' --glob '*controller*'
rg -n "\[['\"][a-z_]+['\"],\s*['\"]"
```
Sinais: faixas de desconto (`10000`, `0.1`) sem constante nomeada; listas de status/role/categoria escritas literalmente em cada lugar que precisa; `#000000` repetido; `priority <= 2` significando "alta prioridade".
→ **T-12**

### AP-21 — Ruído de legibilidade
Agrupe tudo em **um finding** com as linhas listadas por categoria:

```bash
rg -n "^import |^from |^const .* = require" # cruze com uso real
rg -n "print\(|console\.log\(" --glob '!*test*'
rg -n "cursor2|cursor3|tmp[0-9]|data[0-9]|\b[a-z]{1,2}\s*=" 
rg -n "type\(.*\)\s*==|if .*:\s*$" -A2
```

Inclui: imports não usados; dependência declarada e nunca importada; `print`/`console.log` como logging; nomes de 1-2 letras em código de pagamento; `cursor2`, `cursor3`; `if x: return True else: return False`; `type(x) == list` em vez de `isinstance`; `x = x + 1` em vez de `+=`; idioma misturado (código em inglês, mensagem em português, chave de resposta nos dois); versão hardcoded em dois lugares; data serializada com `str()` em vez de ISO 8601; import dentro da função sem motivo.
→ **T-11**, **T-12**

---

## APIs deprecated

Detecção obrigatória na Fase 2. Reporte como **AP-18** com a tabela `obsoleto → moderno` preenchida para o que foi encontrado.

### Python

| Obsoleto | Moderno | Desde |
|---|---|---|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` | Python 3.12 |
| `datetime.utcfromtimestamp()` | `datetime.fromtimestamp(ts, timezone.utc)` | Python 3.12 |
| `Model.query.get(id)` | `db.session.get(Model, id)` | SQLAlchemy 2.0 |
| `Model.query.filter_by(...)` | `db.session.execute(select(Model).filter_by(...))` | SQLAlchemy 2.0 (legacy) |
| `@app.before_first_request` | `with app.app_context()` na factory | Flask 2.3 |
| `flask.Markup`, `flask.escape` | `markupsafe.Markup`, `markupsafe.escape` | Flask 2.3 |
| `werkzeug.urls.url_encode` | `urllib.parse.urlencode` | Werkzeug 2.3 |
| `imp` | `importlib` | Python 3.4 |
| `distutils` | `setuptools` / `packaging` | Python 3.12 (removido) |
| `dict.has_key(k)` | `k in dict` | Python 3 (removido) |
| `hashlib.md5` / `sha1` para senha | `bcrypt`, `argon2`, `werkzeug.security.generate_password_hash` | sempre |
| `"a" + str(b)` como estilo | f-string | Python 3.6 |
| `asyncio.get_event_loop()` | `asyncio.get_running_loop()` / `asyncio.run()` | Python 3.10 |

### Node.js

| Obsoleto | Moderno | Desde |
|---|---|---|
| `new Buffer(x)` | `Buffer.from(x)` / `Buffer.alloc(n)` | Node 6 |
| `url.parse()` | `new URL()` | Node 11 |
| `crypto.createCipher` | `crypto.createCipheriv` | Node 10 |
| `util.isArray` | `Array.isArray` | Node 4 |
| `domain` | `AsyncLocalStorage` | Node 4 |
| `fs.exists` | `fs.access` / `fs.promises.access` | Node 1 |
| `body-parser` standalone | `express.json()` / `express.urlencoded()` | Express 4.16 |
| `request` / `request-promise` | `fetch` nativo / `undici` / `axios` | pacote deprecado 2020 |
| driver em callback (`db.all(sql, cb)`) | `util.promisify` + `async/await`, ou `node:sqlite` | Node 8 |
| `var`, ou `let` para valor nunca reatribuído | `const` | ES6 |
| `process.on('uncaughtException')` como controle de fluxo | tratamento local + `unhandledRejection` | sempre |
| `new Promise` envolvendo função já async | `await` direto | ES2017 |

### Detecção genérica (qualquer stack)

```bash
pip list --outdated              # Python
npm outdated && npm audit        # Node
go list -u -m all                # Go
```

- Suba a aplicação e **leia o stderr do boot**: `DeprecationWarning`, `LegacyAPIWarning`, `[DEP0xxx]` aparecem ali.
- Python: `python -W error::DeprecationWarning app.py` transforma warning em erro e mostra a linha exata.
- Node: `node --pending-deprecation --throw-deprecation src/app.js`.
- Grepe as major versions: framework 2.x com código escrito para 1.x costuma usar API removida mas ainda tolerada por shim.

---

## Guardas anti-falso-positivo

Cheque **antes** de registrar o finding. Falso positivo destrói a credibilidade do relatório inteiro.

| Parece | Mas não é, quando | Como confirmar |
|---|---|---|
| SQL injection | A f-string/template literal está **dentro do array de parâmetros**, não dentro da string SQL — `db.run(sql, [\`${a}-${b}\`])` é seguro | Olhe qual argumento contém a interpolação: 1º (SQL) = injection, 2º (params) = seguro |
| SQL injection | O ORM parametriza: `Task.title.like(f'%{q}%')` passa o valor como bind param | Verifique se é construtor de query do ORM ou string crua. Aqui o problema real é `%`/`_` não escapados — finding LOW, não CRITICAL |
| Código seguro | Você viu `?` em um trecho e generalizou | Grepe **todas** as chamadas de query. É comum o seed usar placeholder e o runtime concatenar |
| Camada de serviço | O diretório `services/` existe | Grepe se é importado. Nunca importado = AP-14, não camada |
| Segredo hardcoded | É valor default explícito de desenvolvimento em `os.getenv(k, "dev")` | Rebaixe para LOW |
| Estado global | É constante de módulo (`MAX_SIZE = 100`) nunca reatribuída | Global **mutável** é o problema; constante é a solução do AP-20 |
| N+1 | O laço roda sobre lista já materializada em memória, sem I/O | Confirme que há chamada ao banco dentro do laço |
| Dead code | É ponto de extensão declarado (interface, ABC, hook documentado) | Só é fantasma se for implementação concreta nunca referenciada |
| API deprecated | A versão instalada no manifesto ainda não deprecou aquilo | Compare com a versão declarada no manifesto, não com a mais recente do mundo |
