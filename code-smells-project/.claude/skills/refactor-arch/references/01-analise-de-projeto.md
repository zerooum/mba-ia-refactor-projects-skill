# 01 — Análise de Projeto

Heurísticas para detectar stack e mapear a arquitetura atual (Fase 1).

**Índice:** [Linguagem](#1-linguagem-e-gerenciador) · [Framework](#2-framework-web) · [Banco](#3-banco-e-camada-de-acesso) · [Entrypoint](#4-entrypoint-e-porta) · [Config e testes](#5-configuração-e-testes) · [Métricas](#6-métricas-de-código) · [Rotas](#7-inventário-de-rotas) · [Domínio](#8-domínio) · [Nível de organização](#9-nível-de-organização) · [Ordem de execução](#10-ordem-de-execução)

---

## 1. Linguagem e gerenciador

Detecte pelo manifesto, não pela extensão dos arquivos. O manifesto também dá a versão do framework.

| Arquivo presente | Linguagem | Gerenciador | Onde está a versão da dependência |
|---|---|---|---|
| `requirements.txt` | Python | pip | `flask==3.1.1` na própria linha |
| `pyproject.toml` | Python | poetry / pdm / uv | `[project.dependencies]` ou `[tool.poetry.dependencies]` |
| `Pipfile` | Python | pipenv | `[packages]` |
| `package.json` | JS/TS | npm / yarn / pnpm | `dependencies` |
| `tsconfig.json` junto | TypeScript | — | — |
| `go.mod` | Go | go modules | `require` |
| `composer.json` | PHP | composer | `require` |
| `Gemfile` | Ruby | bundler | `Gemfile.lock` |
| `pom.xml` / `build.gradle` | Java/Kotlin | maven / gradle | `<dependency>` / `implementation` |
| `Cargo.toml` | Rust | cargo | `[dependencies]` |
| `*.csproj` | C# | dotnet | `<PackageReference>` |

Versão da linguagem: `python_requires`, `engines.node`, `go 1.x`, `<java.version>`. Ausente → reporte só a major (`Python 3`).

Se houver mais de um manifesto, o projeto é poliglota: audite cada subprojeto separadamente e diga isso ao usuário.

---

## 2. Framework web

Cruze duas evidências: **import/dependência** e **assinatura de rota**. Só a dependência não prova uso.

| Framework | Dependência | Assinatura de rota |
|---|---|---|
| Flask | `flask` | `@app.route(`, `@bp.route(`, `Blueprint(` |
| FastAPI | `fastapi` | `@app.get(`, `@router.post(`, `APIRouter(` |
| Django | `django` | `urlpatterns`, `path(`, `re_path(` |
| Express | `express` | `app.get(`, `router.post(`, `app.use(` |
| NestJS | `@nestjs/core` | `@Controller(`, `@Get(` |
| Fastify | `fastify` | `fastify.get(`, `.register(` |
| Spring | `spring-boot-starter-web` | `@RestController`, `@GetMapping` |
| Laravel | `laravel/framework` | `Route::get(` em `routes/` |
| Rails | `rails` | `config/routes.rb` |
| Gin / Echo | `gin-gonic/gin`, `labstack/echo` | `r.GET(`, `e.GET(` |

Comando genérico:

```bash
rg -n "@app\.(route|get|post|put|delete)|@(bp|router)\.|app\.(get|post|put|delete|use)\(|Blueprint\(|APIRouter\(|Route::|@(Get|Post)Mapping|@RestController"
```

Nenhuma rota encontrada → não é app web. Ajuste o alvo: MVC continua valendo (Model/Controller), mas "View" vira a camada de entrada que existir (CLI, worker, consumer).

---

## 3. Banco e camada de acesso

Duas perguntas separadas: **qual banco** e **como se fala com ele**. A segunda define quase toda a Fase 3.

| Sinal | Banco |
|---|---|
| `sqlite3`, `.db`, `:memory:` | SQLite |
| `psycopg`, `pg`, `postgres://` | PostgreSQL |
| `mysql`, `pymysql`, `mysql://` | MySQL/MariaDB |
| `pymongo`, `mongoose`, `mongodb://` | MongoDB |
| `redis` | Redis |

| Sinal | Camada de acesso | Consequência |
|---|---|---|
| `import sqlite3`, `cursor.execute`, `db.run(` | **Driver cru** | Risco alto de AP-02 (SQL injection). Fase 3 precisa de repositórios + queries parametrizadas. |
| `SQLAlchemy`, `Sequelize`, `Prisma`, `TypeORM`, `ActiveRecord`, `Django ORM` | **ORM** | Injection improvável; procure N+1 (AP-15) e uso de API legada do ORM (AP-18). |
| `flask_sqlalchemy` sem `relationship` usado | ORM subutilizado | Serialização manual e N+1 são quase certos. |

Tabelas: leia o DDL (`CREATE TABLE`), as classes de model, ou o arquivo de migrations.

```bash
rg -n "CREATE TABLE|db\.Column|@Column|class .*\(db\.Model\)|Schema\("
```

Anote também **o que falta no schema**: ausência de `REFERENCES`/`FOREIGN KEY`, ausência de `UNIQUE` em email, ausência de `NOT NULL`. Isso alimenta findings.

---

## 4. Entrypoint e porta

```bash
rg -n "app\.run\(|app\.listen\(|uvicorn\.run|if __name__|http\.createServer|\.Run\(" --glob '!node_modules'
```

Confirme com o manifesto: `scripts.start`/`scripts.dev` no `package.json`, `[project.scripts]` no `pyproject.toml`, `Procfile`, `Dockerfile` (`CMD`/`ENTRYPOINT`), `docker-compose.yml`.

Registre: comando de boot, porta, host, flag de debug. Porta hardcoded e `debug=True` já são achados (AP-01 / AP-19) — anote para a Fase 2.

---

## 5. Configuração e testes

**Config** — de onde a app lê porta, credenciais, `SECRET_KEY`, URL do banco:

```bash
rg -n "os\.environ|os\.getenv|getenv\(|process\.env|load_dotenv|dotenv|config\[|SECRET|PASSWORD|API_KEY|TOKEN" \
  --glob '!node_modules' --glob '!.claude' --glob '!.refactor-arch' --glob '!reports'
ls -a | rg "^\.env"
```

| Encontrado | Linha `Config:` |
|---|---|
| Só leitura de env | `env vars` |
| `load_dotenv` / `dotenv` + `.env` presente | `.env` (diga se `.env` está no `.gitignore`) |
| Valor literal atribuído no código | `literal em app.py:12` — liste todas as ocorrências |
| Mistura | Liste as fontes separadas por ` + ` |

Registre só **onde** — nunca copie o valor para o terminal ou para `.refactor-arch/`.

**Testes** — a Fase 3 depende do smoke; testes existentes são uma segunda rede de segurança.

```bash
find . \( -name 'test_*.py' -o -name '*_test.py' -o -name '*.test.[jt]s' -o -name '*.spec.[jt]s' -o -name '*_test.go' \) \
  -not -path './node_modules/*' -not -path './.venv/*' | wc -l
```

Framework de teste vem do manifesto (`pytest`, `jest`, `vitest`, `mocha`, `junit`) ou de `pytest.ini`/`jest.config.*`. Zero arquivos → `nenhum`.

---

## 6. Métricas de código

Contagem de arquivos-fonte e LOC — só o código da aplicação, sem dependências:

```bash
find . -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.go' \) \
  -not -path './node_modules/*' -not -path './.venv/*' -not -path './__pycache__/*' \
  -not -path './.git/*' -not -path './.claude/*' -not -path './.refactor-arch/*' \
  | xargs wc -l | sort -n
```

- `Source files:` = número de linhas da saída menos a linha `total`.
- `LOC` = valor da linha `total`.
- `Largest files:` = os 3 maiores (últimos antes do `total`). Arquivo com 300+ LOC é candidato a God File (AP-03) — anote para a Fase 2.

---

## 7. Inventário de rotas

Cada rota vira uma linha em `.refactor-arch/rotas.tsv`:

```
GET	/produtos	-
GET	/produtos/1	-
POST	/produtos	{"nome":"Teste","preco":10.0,"categoria":"eletronicos","estoque":5}
```

Regras para montar o arquivo:

- **Path params precisam de valor real.** Troque `/produtos/<int:id>` por um id que exista no seed. Sem seed, crie o recurso primeiro (ordene o TSV para que o POST venha antes do GET que depende dele).
- **Query params relevantes entram no path.** `/produtos/busca?q=note&preco_min=10`.
- **Body só onde o método exige.** Use payload válido, tirado do código de validação ou de artefatos existentes (`api.http`, `*.rest`, coleção Postman, `README`).
- **Rotas destrutivas vão por último** (`DELETE`, `/admin/reset-db`), ou ficam de fora se destruírem o estado que as outras usam — nesse caso registre a exclusão no relatório.
- **Rota registrada num arquivo e implementada em outro é comum.** Siga a cadeia: `app.py` registra `/produtos` → `controllers.listar_produtos` → `models.get_produtos`. O TSV documenta o path; a cadeia documenta o acoplamento.

Cheque se já existe artefato de smoke no projeto (`api.http`, `requests.http`, `*.postman_collection.json`) — é fonte melhor que adivinhar payload.

`Routes:` conta **endpoints distintos no código** (método + path template), não linhas do TSV — o TSV pode repetir um endpoint com payloads diferentes. A quebra por método (`GET n · POST n · ...`) omite métodos com zero.

---

## 8. Domínio

Deduza de três fontes, nessa ordem: nomes de tabela → paths das rotas → `README`. Escreva em uma linha, no vocabulário do negócio.

Desconfie do nome do diretório e do `package.json`: eles mentem com frequência (um projeto chamado "ecommerce" pode ser um LMS de cursos). O schema não mente.

---

## 9. Nível de organização

Classifique em um dos três. **A receita da Fase 3 muda conforme o nível.**

### Nível 1 — Monolito flat
Arquivos na raiz, sem diretórios de camada, ou uma classe única concentrando tudo.
Sinais: `app.py` + `models.py` + `controllers.py` soltos; um `AppManager.js` com DB, DDL, seed e rotas; arquivo único com 300+ linhas cobrindo mais de um domínio.

### Nível 2 — Camadas nominais
Diretórios de camada existem, mas a responsabilidade não foi separada. **É o caso mais enganoso.** Confirme com os três testes:

```bash
# Teste 1 — o módulo de service é importado em algum lugar?
rg -n "from services|require.*services|import .*Service"

# Teste 2 — as rotas fazem query direto? (camada pulada)
rg -n "\.query\.|cursor\.execute|db\.(all|get|run)\(" --glob '*route*' --glob '*view*' --glob '*controller*'

# Teste 3 — métodos de model definidos e nunca chamados?
rg -n "def (validate_|is_|can_)" models/   # depois grepe cada nome no resto do projeto
```

Service nunca importado → **camada fantasma** (AP-14). Rota consultando o banco → **camada pulada** (AP-10).

### Nível 3 — Camadas reais
Cada camada tem responsabilidade própria, a dependência flui numa direção só, rotas são finas. Aqui a auditoria foca em segurança, performance e higiene, não em reestruturação.

Registre o nível **e a evidência** que o sustenta — ela vai para o relatório.

---

## 10. Ordem de execução

Cada passo alimenta linhas do bloco `PHASE 1: PROJECT ANALYSIS`:

| # | Passo | Linhas do bloco |
|---|---|---|
| 1 | Manifesto → linguagem, versões, dependências | `Language`, `Package mgr`, `Framework`, `Dependencies` |
| 2 | Grep de rotas → framework + inventário | `Framework`, `Routes` |
| 3 | Grep de DDL/models → banco, tabelas, camada de acesso, restrições | `Database`, `Data access`, `DB tables`, `Schema gaps` |
| 4 | Grep de entrypoint → comando de boot, host, porta, debug | `Entrypoint` |
| 5 | Grep de config + busca de testes | `Config`, `Tests` |
| 6 | `find` + `wc -l` nos fontes → contagem, LOC, maiores arquivos | `Source files`, `Largest files` |
| 7 | Rotas + tabelas + README → domínio | `Domain` |
| 8 | Classificar nível de organização com os três testes | `Architecture` |
| 9 | Montar `rotas.tsv` e capturar baseline (`06-validacao.md`) | `Baseline` |
| 10 | Resultado do `git status` da Fase 0 | `Git` |
