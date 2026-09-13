# 05 — Playbook de Refatoração

14 transformações. Cada uma resolve anti-patterns específicos do catálogo.

| ID | Transformação | Resolve | Onda |
|---|---|---|---|
| [T-01](#t-01--extrair-configuração-para-env-vars) | Extrair configuração para env vars | AP-01, AP-19 | 1 |
| [T-02](#t-02--parametrizar-queries) | Parametrizar queries | AP-02 | 2 |
| [T-03](#t-03--quebrar-god-file-em-camadas) | Quebrar God File em camadas | AP-03 | 3-4 |
| [T-04](#t-04--extrair-regra-de-negócio-da-rota) | Extrair regra de negócio da rota | AP-07, AP-10, AP-14, AP-17 | 3 |
| [T-05](#t-05--repository-com-injeção-de-dependência) | Repository com injeção de dependência | AP-08, AP-10 | 2 |
| [T-06](#t-06--eliminar-estado-global) | Eliminar estado global | AP-09 | 4 |
| [T-07](#t-07--centralizar-error-handling) | Centralizar error handling | AP-06, AP-11, AP-17 | 5 |
| [T-08](#t-08--resolver-n1) | Resolver N+1 | AP-15 | 3 |
| [T-09](#t-09--camada-de-validação-de-entrada) | Camada de validação de entrada | AP-05, AP-16, AP-19 | 5 |
| [T-10](#t-10--hash-de-senha-e-serialização-segura) | Hash de senha e serialização segura | AP-04, AP-06 | 5 |
| [T-11](#t-11--substituir-api-deprecated) | Substituir API deprecated | AP-18, AP-21 | 6 |
| [T-12](#t-12--extrair-constantes-nomeadas) | Extrair constantes nomeadas | AP-20, AP-21 | 6 |
| [T-13](#t-13--conexão-e-transação) | Conexão e transação | AP-09, AP-12 | 2 |
| [T-14](#t-14--callback-hell--asyncawait) | Callback hell → async/await | AP-13 | 3 |

---

## T-01 — Extrair configuração para env vars

**Antes**
```python
# app.py
SECRET_KEY = "minha-chave-super-secreta-123"
DEBUG = True
app.run(host="0.0.0.0", port=5000, debug=True)
```

**Depois**
```python
# config/settings.py
import os

class Settings:
    SECRET_KEY = os.environ["SECRET_KEY"]          # obrigatório: falha no boot se faltar
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    PORT = int(os.getenv("PORT", "5000"))
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///loja.db")
```
```bash
# .env.example  (commitado)
SECRET_KEY=CHANGE_ME
DEBUG=false
PORT=5000
```

**Cuidados**
- Segredo obrigatório usa `os.environ[...]` e derruba o boot se faltar. Default silencioso reintroduz o problema.
- `.env.example` recebe `CHANGE_ME`, **nunca** o valor que estava no código.
- `.env` vai para o `.gitignore`.
- O segredo que estava commitado está comprometido: avise que precisa ser rotacionado. Removê-lo do código não o desvaza do histórico do git.

**Validar:** `rg -n -i "secret|password|api_key" --glob '!*.example'` não retorna valor literal; a app boota com `.env` presente e falha com mensagem clara sem ele.

---

## T-02 — Parametrizar queries

**Antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
cursor.execute("SELECT * FROM produtos WHERE nome LIKE '%" + termo + "%'")
```

**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
cursor.execute("SELECT * FROM produtos WHERE nome LIKE ?", (f"%{termo}%",))
```

**Cuidados**
- O placeholder substitui **valor**, nunca identificador. Nome de tabela/coluna dinâmico exige allowlist:
  ```python
  ORDENACOES = {"preco": "preco", "nome": "nome"}
  coluna = ORDENACOES.get(param, "id")          # nunca interpole o param direto
  ```
- Placeholder varia: `?` (sqlite, mysql), `%s` (psycopg), `$1` (node-postgres), `:nome` (SQLAlchemy text).
- Filtro opcional monta a query por partes, mas só de trechos **fixos**:
  ```python
  sql, params = "SELECT * FROM produtos WHERE 1=1", []
  if categoria:
      sql += " AND categoria = ?"; params.append(categoria)
  ```
- `LIKE`: o `%` vai no parâmetro, não na string SQL.

**Validar:** nenhuma chamada de query com `+`, f-string ou template literal no primeiro argumento. Teste de fumaça: enviar `' OR '1'='1` no login deve retornar 401, não 200.

---

## T-03 — Quebrar God File em camadas

**Antes** — `AppManager.js` (141 linhas) cria conexão, roda DDL, semeia, registra rotas e implementa checkout.

**Depois**
```js
// infra/db.js — só conexão
const sqlite3 = require('sqlite3');
const { promisify } = require('util');

function createDb(url) {
  const db = new sqlite3.Database(url);
  return { all: promisify(db.all.bind(db)), get: promisify(db.get.bind(db)), run: promisify(db.run.bind(db)) };
}
module.exports = { createDb };
```
```js
// models/enrollmentModel.js — só persistência
class EnrollmentModel {
  constructor(db) { this.db = db; }
  create(userId, courseId) {
    return this.db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
  }
}
module.exports = { EnrollmentModel };
```
```js
// controllers/checkoutController.js — só caso de uso
class CheckoutController {
  constructor(users, enrollments, payments, gateway) { /* ... */ }
  async execute({ name, email, password, courseId, card }) { /* orquestra */ }
}
```
```js
// routes/checkoutRoutes.js — só HTTP
router.post('/api/checkout', async (req, res, next) => {
  try { res.status(201).json(await controller.execute(req.body)); }
  catch (err) { next(err); }
});
```

**Cuidados**
- Mova **um domínio por vez**, rodando o smoke entre cada um. Quebrar os 4 domínios de uma vez torna impossível saber qual movimentação quebrou.
- Use `git mv` quando for movimentação pura de arquivo.
- Copie o corpo da função sem reescrever a lógica. Otimização entra depois, em transformação própria.
- Migre o DDL e o seed para um comando explícito (`init_db`, `seed.js`), fora do import do módulo.

**Validar:** nenhum arquivo importa de uma camada acima da sua; smoke idêntico ao baseline após cada domínio movido.

---

## T-04 — Extrair regra de negócio da rota

**Antes**
```python
@app.route("/produtos", methods=["POST"])
def criar_produto():
    data = request.get_json()
    if data["preco"] < 0:
        return jsonify({"erro": "preço inválido"}), 400
    if len(data["nome"]) < 2 or len(data["nome"]) > 200:
        return jsonify({"erro": "nome inválido"}), 400
    if data["categoria"] not in ["eletronicos", "roupas", "alimentos"]:
        return jsonify({"erro": "categoria inválida"}), 400
    return jsonify(models.criar_produto(data))
```

**Depois**
```python
# controllers/produto_controller.py
class ProdutoController:
    def __init__(self, repo): self.repo = repo

    def criar(self, dados: dict) -> dict:
        produto = Produto.from_dict(dados)     # invariantes no model
        return self.repo.inserir(produto)
```
```python
# models/produto.py
CATEGORIAS_VALIDAS = frozenset({"eletronicos", "roupas", "alimentos"})
NOME_MIN, NOME_MAX = 2, 200

@dataclass
class Produto:
    nome: str; preco: float; categoria: str; estoque: int

    def __post_init__(self):
        if not NOME_MIN <= len(self.nome) <= NOME_MAX:
            raise ValidationError("nome deve ter entre 2 e 200 caracteres")
        if self.preco < 0:
            raise ValidationError("preco não pode ser negativo")
        if self.categoria not in CATEGORIAS_VALIDAS:
            raise ValidationError(f"categoria deve ser uma de {sorted(CATEGORIAS_VALIDAS)}")
```
```python
# views/produto_routes.py
@bp.post("/produtos")
def criar_produto():
    return jsonify(controller.criar(request.get_json())), 201
```

**Cuidados**
- Regra que valida **o dado em si** (faixa, formato, invariante) vai para o Model. Regra que coordena **o caso de uso** (verificar estoque, aplicar desconto, notificar) vai para o Controller.
- Se a mesma regra existia duplicada entre create e update, ela passa a existir uma vez só — e as duas rotas passam a se comportar igual. **Isso muda o comportamento do update**: registre como mudança intencional no relatório final.
- Quando existir método de model já implementado e nunca chamado (AP-14), use-o em vez de escrever lógica nova.
- `ValidationError` é exceção de domínio, mapeada para 400 pelo error handler (T-07). O Model continua sem conhecer HTTP.

**Validar:** o handler tem ≤ 8 linhas; o controller é chamável de um script sem Flask; smoke preserva os status codes.

---

## T-05 — Repository com injeção de dependência

**Antes**
```python
# models.py
from database import get_db                 # conexão global importada

def get_produto(id):
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
    ...
```

**Depois**
```python
# models/produto_repository.py
class ProdutoRepository:
    def __init__(self, db):                  # dependência injetada
        self.db = db

    def buscar_por_id(self, produto_id: int) -> Produto | None:
        row = self.db.query_one("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        return Produto.from_row(row) if row else None
```
```python
# app.py — composition root
repo = ProdutoRepository(db)
controller = ProdutoController(repo)
```

**Cuidados**
- Repository devolve objeto de domínio, não `sqlite3.Row` nem dict cru — senão o acoplamento ao driver vaza para cima.
- Um repository por agregado, não por tabela.
- A conversão linha→objeto (`from_row`) mora em um lugar só. Ela costuma estar duplicada 3-4 vezes no código de origem.
- Sem herança de "BaseRepository" no primeiro passo. Abstraia só quando houver repetição real.

**Validar:** `rg "^from database import|cursor\.execute" controllers/ views/` não retorna nada.

---

## T-06 — Eliminar estado global

**Antes**
```js
// utils.js
let globalCache = {};        // cresce sem limite
let totalRevenue = 0;        // exportado por valor: mutação nunca se propaga
module.exports = { globalCache, totalRevenue };
```
```python
# database.py
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(DB, check_same_thread=False)   # 1 conexão p/ todas as threads
    return db_connection
```

**Depois**
```js
// infra/cache.js — instância com limite, criada na composition root
class Cache {
  constructor({ maxSize = 500, ttlMs = 60000 } = {}) { this.store = new Map(); /* ... */ }
  get(k) { /* ... */ }
  set(k, v) { if (this.store.size >= this.maxSize) this.store.delete(this.store.keys().next().value); /* ... */ }
}
module.exports = { Cache };
```
```python
# infra/database.py — conexão por request, sem global
class Database:
    def __init__(self, path): self.path = path

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
```

**Cuidados**
- `check_same_thread=False` não torna a conexão thread-safe: só desliga o aviso. Conexão por request (ou pool) é a correção.
- Valor agregado que era global (`totalRevenue`) passa a ser calculado por query ou guardado no banco. Contador em memória é perdido no restart e não existe entre workers.
- Flask: `g` + `teardown_appcontext` resolve o ciclo por request.
- Toda instância passa a ser criada na composition root e injetada.

**Validar:** `rg "^(let|var) \w+ = (\{\}|\[\]|0)|global \w+"` só retorna constantes; duas requisições concorrentes não corrompem estado.

---

## T-07 — Centralizar error handling

**Antes** — o mesmo bloco em 14 handlers:
```python
try:
    ...
except Exception as e:
    return jsonify({"erro": str(e)}), 500     # vaza schema e caminho
```

**Depois**
```python
# models/errors.py
class DomainError(Exception): status = 400
class ValidationError(DomainError): status = 400
class NotFoundError(DomainError): status = 404
class UnauthorizedError(DomainError): status = 401
```
```python
# middlewares/error_handler.py
import logging
log = logging.getLogger(__name__)

def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def handle_domain(e):
        return jsonify({"erro": str(e)}), e.status

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        log.exception("erro não tratado")             # detalhe vai para o log
        return jsonify({"erro": "erro interno"}), 500  # cliente recebe mensagem genérica
```
```js
// middlewares/errorHandler.js — Express: 4 argumentos, registrado por último
function errorHandler(err, req, res, next) {
  if (err instanceof DomainError) return res.status(err.status).json({ erro: err.message });
  logger.error({ err }, 'erro não tratado');
  res.status(500).json({ erro: 'erro interno' });
}
```

**Cuidados**
- **`str(e)` nunca vai para o cliente.** Detalhe no log, mensagem genérica na resposta.
- Express: o middleware de erro tem **4 parâmetros** e é registrado **depois** de todas as rotas. Handler async precisa de `next(err)` — erro em promise não chega ao middleware sozinho.
- Não altere os status codes que o baseline registrou. Se um caminho hoje devolve 500 onde deveria ser 404, corrija **e registre como breaking change** — o smoke vai acusar.
- Troque `except:` pelado por exceção específica. `except:` captura até `KeyboardInterrupt`.
- Nenhum callback pode ignorar `err`.

**Validar:** `rg "except\s*:|catch\s*\{\s*\}|str\(e\)"` vazio; os handlers não têm mais `try/except`; rota inexistente devolve JSON, não HTML.

---

## T-08 — Resolver N+1

**Antes**
```python
pedidos = db.query("SELECT * FROM pedidos WHERE usuario_id = ?", (uid,))
for pedido in pedidos:
    itens = db.query("SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido["id"],))
    for item in itens:
        nome = db.query_one("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],))
```

**Depois**
```python
rows = db.query("""
    SELECT p.id AS pedido_id, p.total, p.status,
           i.quantidade, i.preco_unitario,
           pr.id AS produto_id, pr.nome AS produto_nome
      FROM pedidos p
      LEFT JOIN itens_pedido i ON i.pedido_id = p.id
      LEFT JOIN produtos pr    ON pr.id = i.produto_id
     WHERE p.usuario_id = ?
     ORDER BY p.id
""", (uid,))
pedidos = agrupar_por_pedido(rows)      # 1 query no lugar de 1 + N + N*M
```

Com ORM:
```python
# antes: 1 + 2N queries
tasks = Task.query.all()
for t in tasks:
    user = User.query.get(t.user_id)

# depois: 1 query
tasks = db.session.execute(
    select(Task).options(joinedload(Task.user), joinedload(Task.category))
).unique().scalars().all()
```

Agregação:
```python
# antes: 4 queries de count
# depois: 1
select(Task.status, func.count()).group_by(Task.status)
```

**Cuidados**
- `LEFT JOIN` preserva o pai sem filhos; `INNER JOIN` o descarta — a escolha errada muda o resultado da API.
- JOIN duplica as colunas do pai: agrupe ao montar o objeto.
- SQLAlchemy: `joinedload` para 1:1/N:1, `selectinload` para coleções grandes; `.unique()` é obrigatório com `joinedload` em coleção.
- Delete em laço vira `ON DELETE CASCADE` ou `delete()` em massa.
- Mantenha o **formato de saída idêntico**. O smoke compara status, mas mudança de shape quebra o cliente.

**Validar:** conte as queries antes e depois (log do driver, `echo=True` no SQLAlchemy); o body da resposta permanece equivalente.

---

## T-09 — Camada de validação de entrada

**Antes**
```python
data = request.get_json()
if data["preco"] < 0:                      # TypeError se vier "10" (string) → 500
    return jsonify({"erro": "inválido"}), 400
priority = int(request.args.get("priority"))   # 500 em ?priority=abc
```

**Depois**
```python
# views/schemas.py
class ProdutoInput(Schema):
    nome = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    preco = fields.Float(required=True, validate=validate.Range(min=0))
    categoria = fields.Str(required=True, validate=validate.OneOf(sorted(CATEGORIAS_VALIDAS)))
    estoque = fields.Int(required=True, validate=validate.Range(min=0))
```
```python
# middlewares/validate.py
def validar(schema):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            try:
                kw["dados"] = schema().load(request.get_json() or {})
            except MarshmallowValidationError as e:
                raise ValidationError(e.messages)     # vira 400 no handler central
            return fn(*a, **kw)
        return wrapper
    return decorator

@bp.post("/produtos")
@validar(ProdutoInput)
def criar_produto(dados):
    return jsonify(controller.criar(dados)), 201
```
```js
// Express
const schema = z.object({ eml: z.string().email(), c_id: z.number().int().positive() });
router.post('/api/checkout', validate(schema), handler);
```

**Cuidados**
- Validação de **formato** fica na View (é tradução de HTTP). Invariante de **domínio** fica no Model (T-04). As duas existem; não são redundantes.
- Se o projeto já declara uma lib de validação no manifesto e não a usa, use-a — não instale outra.
- Query param também é entrada: converta com default e faixa, nunca `int()` cru.
- Autorização entra como decorator/middleware na mesma camada (`@require_auth`, `@require_role("admin")`) — resolve o AP-05 sem espalhar `if` pelos handlers.
- **A mensagem de erro muda de formato.** Se o baseline registrava texto plano, isso é breaking change: registre.

**Validar:** enviar tipo errado devolve 400, não 500; campo obrigatório ausente devolve 400.

---

## T-10 — Hash de senha e serialização segura

**Antes**
```python
# grava e compara em texto puro
cursor.execute("INSERT INTO usuarios (senha) VALUES ('" + senha + "')")
if row["senha"] == senha: ...
```
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()     # MD5 sem salt
def to_dict(self): return {"id": self.id, "password": self.password}   # vaza o hash
```

**Depois**
```python
# models/usuario.py
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario:
    def definir_senha(self, senha: str) -> None:
        if len(senha) < SENHA_MIN_LEN:
            raise ValidationError(f"senha deve ter ao menos {SENHA_MIN_LEN} caracteres")
        self.senha_hash = generate_password_hash(senha)    # salt embutido

    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)  # comparação em tempo constante
```
```python
# views/serializers.py — a regra do que sai mora aqui
def usuario_publico(u) -> dict:
    return {"id": u.id, "nome": u.nome, "email": u.email, "criado_em": u.criado_em.isoformat()}
```

**Cuidados**
- Nunca compare hash com `==` (timing attack). Use a função de verificação da biblioteca.
- Alternativas: `bcrypt`, `argon2-cffi`, `werkzeug.security`. Node: `bcrypt`, `argon2`, `node:crypto.scrypt`.
- Senhas existentes em texto puro/MD5 não são convertíveis. Opções: forçar redefinição, ou re-hash no próximo login bem-sucedido. **Migração de dado existente precisa de aval do usuário.**
- Serializer com allowlist de campos, nunca `to_dict()` devolvendo tudo. Campo novo no model não vaza por acidente.
- Token: se o projeto usa token falso previsível, substituir por JWT assinado **muda o contrato** — proponha no relatório, não execute por conta própria.
- Remover o campo `password` da resposta **é** breaking change. É um dos poucos que vale executar mesmo assim — registre explicitamente.

**Validar:** `rg -i "md5|sha1|password.*==" ` vazio; nenhuma resposta contém campo de senha/hash; login válido continua funcionando.

---

## T-11 — Substituir API deprecated

**Antes / Depois**
```python
datetime.utcnow()                  →  datetime.now(timezone.utc)
User.query.get(uid)                →  db.session.get(User, uid)
Task.query.filter_by(x=1).all()    →  db.session.execute(select(Task).filter_by(x=1)).scalars().all()
"total: " + str(v)                 →  f"total: {v}"
```
```js
new Buffer(x)                      →  Buffer.from(x)
url.parse(u)                       →  new URL(u)
db.all(sql, cb)                    →  await promisify(db.all.bind(db))(sql)
let x = 5  // nunca reatribuído    →  const x = 5
```

**Cuidados**
- `utcnow()` devolve datetime **naive**; `now(timezone.utc)` devolve **aware**. Comparar os dois levanta `TypeError`. Troque **todas** as ocorrências de uma vez, incluindo `default=`/`onupdate=` nos models e o seed.
- Datetime aware serializado com `.isoformat()` passa a incluir `+00:00`. O smoke não pega (status igual), mas o cliente vê diferença — registre.
- Só troque o que está de fato deprecado **na versão declarada no manifesto**.
- Onda 6: essas trocas são amplas e mecânicas. Feitas antes das estruturais, poluem o diff.

**Validar:** boot com warnings ligados (`python -W error::DeprecationWarning app.py`, `node --throw-deprecation`) sem disparar nada; smoke verde.

---

## T-12 — Extrair constantes nomeadas

**Antes**
```python
if total > 10000:   desconto = total * 0.1
elif total > 5000:  desconto = total * 0.05
elif total > 1000:  desconto = total * 0.02
if data["categoria"] not in ["eletronicos", "roupas", "alimentos"]: ...
```

**Depois**
```python
# models/constantes.py
FAIXAS_DESCONTO = (          # (valor mínimo, taxa) — da maior para a menor
    (10_000, 0.10),
    (5_000,  0.05),
    (1_000,  0.02),
)
CATEGORIAS_VALIDAS = frozenset({"eletronicos", "roupas", "alimentos"})
STATUS_PEDIDO = frozenset({"pendente", "pago", "enviado", "entregue", "cancelado"})

def calcular_desconto(total: float) -> float:
    for minimo, taxa in FAIXAS_DESCONTO:
        if total > minimo:
            return round(total * taxa, 2)
    return 0.0
```

**Cuidados**
- A constante mora na camada que **detém a regra** — domínio no Model, limite de HTTP na View, config de ambiente no Config.
- Se a lista já existe em um módulo de helpers não usado (AP-14), importe de lá em vez de criar outra.
- Constante usada em um único lugar e autoexplicativa (`round(x, 2)`) não precisa de nome. Não troque um número mágico por uma constante mágica.
- Junte nesta onda a higiene do AP-21: imports mortos, `print` → `logging`, `type(x) ==` → `isinstance`, `x = x + 1` → `+=`.

**Validar:** cada valor literal de domínio aparece uma vez só; smoke verde.

---

## T-13 — Conexão e transação

**Antes**
```python
cursor.execute("INSERT INTO pedidos ...")
pedido_id = cursor.lastrowid
for item in itens:
    if produto["estoque"] < item["qtd"]:
        return {"erro": "sem estoque"}          # sai sem rollback: pedido já inserido
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ? ...")
conn.commit()
```

**Depois**
```python
# infra/database.py
@contextmanager
def transaction(self):
    conn = sqlite3.connect(self.path)
    conn.row_factory = sqlite3.Row
    conn.execute("BEGIN IMMEDIATE")       # trava escritores desde já
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```
```python
# models/pedido_repository.py
def criar(self, usuario_id, itens):
    with self.db.transaction() as conn:
        pedido_id = conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_INICIAL, 0),
        ).lastrowid
        for item in itens:
            afetadas = conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item.qtd, item.produto_id, item.qtd),
            ).rowcount
            if afetadas == 0:                       # decremento condicional resolve a corrida
                raise ValidationError(f"estoque insuficiente para o produto {item.produto_id}")
            conn.execute("INSERT INTO itens_pedido (...) VALUES (?, ?, ?, ?)", (...))
        return pedido_id                            # commit/rollback pelo context manager
```

**Cuidados**
- Erro dentro do bloco **levanta exceção**, não retorna dict de erro — retornar cedo pula o rollback.
- Ler estoque e depois decrementar é corrida. `UPDATE ... WHERE estoque >= ?` + checagem de `rowcount` decide atomicamente.
- SQLite precisa de `BEGIN IMMEDIATE` para travar escritores; `BEGIN` padrão é deferred.
- Node: `BEGIN`/`COMMIT`/`ROLLBACK` explícitos, com `ROLLBACK` no `catch`.
- Adicione as FKs ausentes com `ON DELETE CASCADE` — mas alterar schema exige migração do banco existente: proponha e confirme.
- A transação é aberta pelo Controller ou pelo Repository do agregado, nunca pela View.

**Validar:** forçar falha no meio do fluxo e conferir que nada foi persistido; duas requisições concorrentes não deixam estoque negativo.

---

## T-14 — Callback hell → async/await

**Antes**
```js
db.get('SELECT * FROM users WHERE email=?', [e], function (err, user) {
  if (err) return res.send('erro');
  db.run('INSERT INTO enrollments ...', [uid, cid], function (err2) {
    db.run('INSERT INTO payments ...', [this.lastID], function (err3) {
      db.run('INSERT INTO audit_logs ...', [], () => res.json({ ok: true }));
    });
  });
});
```

**Depois**
```js
// infra/db.js
const { promisify } = require('util');
function createDb(url) {
  const db = new sqlite3.Database(url);
  const run = (sql, params = []) => new Promise((resolve, reject) =>
    db.run(sql, params, function (err) {                 // function: precisa do this.lastID
      err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes });
    }));
  return { run, all: promisify(db.all.bind(db)), get: promisify(db.get.bind(db)) };
}
```
```js
// controllers/checkoutController.js
async execute({ email, courseId, card }) {
  const user = await this.users.findOrCreate(email);
  const payment = await this.gateway.charge(card, courseId);
  if (!payment.approved) throw new PaymentDeniedError(payment.reason);
  const enrollment = await this.enrollments.create(user.id, courseId);
  await this.payments.record(enrollment.id, payment);
  return { enrollmentId: enrollment.id, status: payment.status };
}
```

Contagem manual de pendências vira `Promise.all`:
```js
// antes: coursesPending--/enrPending-- e res.json quando zera (pendura para sempre se der erro)
const courses = await this.courses.listAll();
const report = await Promise.all(courses.map(c => this.buildCourseReport(c)));
```

**Cuidados**
- `db.run` precisa de `function` (não arrow) para acessar `this.lastID` — por isso ele é promisificado à mão, não com `promisify`. `db.all`/`db.get` aceitam `promisify` direto.
- Com `async/await`, `const self = this` deixa de ser necessário: arrow preserva o escopo.
- Handler async precisa de `try/catch` com `next(err)` (ou wrapper `asyncHandler`), senão a rejeição não chega ao error handler.
- `Promise.all` falha no primeiro erro. Se resultados parciais forem aceitáveis, use `Promise.allSettled`.
- Converta **um fluxo por vez**, rodando o smoke entre eles.

**Validar:** `rg "function\s*\([^)]*err"` só retorna o wrapper de promisificação; erro em query devolve 500 pelo handler central em vez de derrubar o processo; requisição nunca fica pendurada.
