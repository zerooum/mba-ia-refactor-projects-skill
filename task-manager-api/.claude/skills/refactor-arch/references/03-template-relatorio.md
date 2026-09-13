# 03 — Template do Relatório de Auditoria

Formato da saída da Fase 2. Copie a estrutura literalmente e preencha.

Destino: `reports/audit-<slug-do-projeto>.md`.

---

## Regra de renderização — leia antes de escrever

O relatório é um arquivo **`.md`**. Ele será lido renderizado, não como texto puro. Duas construções quebram se você escrever "como sai no terminal":

| Construção | O que o Markdown faz com ela | Consequência |
|---|---|---|
| Linha de `=====` logo abaixo de um texto | Vira heading setext (`<h1>`) | O banner `====` some e o título fica **sem** as duas linhas ao redor |
| Linhas consecutivas sem linha em branco entre elas | Vira um parágrafo só | `Project:`, `Stack:`, `Files:` saem **concatenados numa linha só** |

Portanto, obrigatoriamente:

- **Todo bloco de banner (cabeçalho e rodapé) vai dentro de uma code fence** ` ``` `. É o que preserva o `====` e o alinhamento das colunas.
- **Todo campo de finding é um item de lista com label em negrito**, nunca linha solta.
- **Tabelas ficam em bloco próprio**, fora da lista de bullets — tabela indentada dentro de um `-` não renderiza.

---

## Campos obrigatórios

Finding sem um destes campos está incompleto — não o publique:

| Campo | Regra |
|---|---|
| `### [SEVERIDADE]` | Exatamente `CRITICAL`, `HIGH`, `MEDIUM` ou `LOW`, no título do finding |
| `(AP-xx)` | ID do catálogo, no título |
| `**File:**` | `` `caminho/relativo.ext:linha` `` ou `:linha-linha`. **Linha conferida lendo o arquivo.** |
| `**Description:**` | O que está errado, em uma ou duas frases, citando o identificador real do código |
| `**Impact:**` | A consequência concreta, não a categoria abstrata |
| `**Recommendation:**` | Ação + `T-xx` do playbook |

`**Occurrences:**` é obrigatório quando o mesmo anti-pattern aparece mais de uma vez: número + sub-lista das linhas.

Ordem dos findings: CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, mais ocorrências primeiro.

---

## Template

````markdown
```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-diretório>
Stack:   <Linguagem + Framework + versão>
Files:   <N> analyzed | <N> lines of code
Routes:  <N> endpoints
Date:    <YYYY-MM-DD>
================================
```

## Summary

| Severidade | Findings |
|---|---|
| CRITICAL | <n> |
| HIGH | <n> |
| MEDIUM | <n> |
| LOW | <n> |
| **Total** | **<n>** |

## Findings

### [CRITICAL] <Nome do anti-pattern> (AP-xx)

- **File:** `<arquivo:linha>`
- **Description:** <o que está errado>
- **Impact:** <consequência concreta>
- **Recommendation:** <ação> (T-xx)

### [HIGH] <Nome do anti-pattern> (AP-xx)

- **File:** `<arquivo:linha>`
- **Occurrences:** <N>
  - `<arquivo:linha>` — <detalhe>
  - `<arquivo:linha>` — <detalhe>
- **Description:** <...>
- **Impact:** <...>
- **Recommendation:** <...> (T-xx)

<... demais findings ...>

## APIs Deprecated

| Obsoleto | Ocorrências | Equivalente moderno |
|---|---|---|
| `<api>` | `<arquivo:linha>` (<N>x) | `<substituto>` |

## Breaking changes propostos

<Correções que alteram o contrato HTTP, numeradas. "Nenhum." se não houver.
Cada item precisa de aval explícito antes da Fase 3.>

## Baseline de comportamento

<N>/<N> requisições responderam. Excluídas do smoke: <rotas e por quê>.

```
================================
Total: <N> findings
================================
```
````

---

## Exemplo preenchido

````markdown
### [CRITICAL] SQL Injection por concatenação (AP-02)

- **File:** `models.py:109-111`
- **Occurrences:** 22
  - `models.py:109-111` — `login_usuario`: email e senha concatenados na cláusula WHERE
  - `models.py:28` — `get_produto_por_id`
  - `models.py:291` — busca com `LIKE` montada por concatenação
  - <... 19 demais ...>
- **Description:** Todas as queries de runtime são montadas por concatenação de string com
  valores vindos do corpo da requisição. Nenhuma usa placeholder.
- **Impact:** **Verificado em execução.** `POST /login` com
  `{"email": "admin@loja.com' OR '1'='1", "senha": "qualquer"}` retornou HTTP 200 e
  autenticou como `Admin` sem a senha correta.
- **Recommendation:** Trocar toda montagem por placeholders parametrizados (`?`), como já
  é feito em `database.py:70-73`. (T-02)
````

Repare: a continuação de uma linha longa é **indentada em 2 espaços** para continuar dentro do mesmo bullet. Sem a indentação, ela vira parágrafo separado e perde o alinhamento da lista.

---

## Saída de console

Depois de salvar o arquivo, imprima o sumário **e o índice de findings**, e só então abra o GATE. Aqui o formato de banner é o correto — é terminal, não Markdown:

```
================================
AUDIT COMPLETE
================================
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

[CRITICAL] SQL Injection por concatenação (AP-02)   models.py:109-111  (22x)
[CRITICAL] Credenciais hardcoded (AP-01)            app.py:7           (6x)
[HIGH]     Estado global mutável (AP-09)            database.py:4-11   (3x)
<... um por finding, na ordem do relatório ...>

Total: 14 findings
Report saved: reports/audit-code-smells-project.md
================================
```

O índice é o que permite ao usuário decidir no GATE sem abrir o arquivo.

---

## Erros comuns

| Erro | Correção |
|---|---|
| Banner `====` escrito solto no `.md` | Envolver em code fence — senão vira heading e a linha de cima some |
| `Project:`, `Stack:`, `Files:` em linhas soltas | Mesma coisa: dentro da code fence do cabeçalho |
| `File:`/`Description:`/`Impact:` em linhas soltas | Viram um parágrafo só. Use bullets com label em negrito |
| Tabela indentada dentro de um bullet | Não renderiza. Tabela vai em bloco próprio |
| Linha estimada, não conferida | Abra o arquivo e confirme antes de escrever |
| 20 findings para o mesmo anti-pattern | 1 finding, `**Occurrences:** 20`, linhas na sub-lista |
| `Impact: dificulta a manutenção` | Diga o que quebra: "bypass de login com `' OR '1'='1`" |
| Findings fora de ordem | CRITICAL → LOW, sempre |
| Só salvar o arquivo, sem dizer nada no terminal | O terminal recebe sumário + índice + caminho do arquivo |
| Seção de deprecated omitida quando nada foi achado | Escreva "Nenhuma API deprecated encontrada" — omitir esconde se a checagem rodou |
