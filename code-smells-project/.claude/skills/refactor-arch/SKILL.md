---
name: refactor-arch
description: Use when the user asks to audit, analyze or refactor a codebase toward MVC — triggers include "/refactor-arch", "auditoria de arquitetura", "refatorar para MVC", "code smells", "anti-patterns", "projeto legado", "God Class", "separar camadas", "relatório de auditoria". Works on any language or framework (Python/Flask, Node/Express, and others) and on any level of existing organization, from a single-file monolith to partially layered projects.
---

# refactor-arch

Auditoria arquitetural e refatoração para MVC em 3 fases sequenciais, agnóstica de stack.

## Contrato de execução

Execute **Fase 0 → 1 → 2 → GATE → 3**, nessa ordem, sem pular etapa.
Crie um todo para cada fase antes de começar.

Os arquivos de referência abaixo carregam o conhecimento de domínio. Leia cada um **no início da fase que o usa**, não antes:

| Fase | Leia |
|---|---|
| 1 | `references/01-analise-de-projeto.md` |
| 2 | `references/02-catalogo-anti-patterns.md`, `references/03-template-relatorio.md` |
| 3 | `references/04-guidelines-mvc.md`, `references/05-playbook-refatoracao.md` |
| 1 e 3 | `references/06-validacao.md` |

---

## Regras invioláveis

Valem nas 3 fases. Se um raciocínio seu levar a violar uma delas, o raciocínio está errado.

| Regra | O que significa na prática |
|---|---|
| **Nenhuma escrita antes do GATE** | Até o usuário aceitar o relatório da Fase 2, você só lê. As únicas escritas permitidas são `.refactor-arch/` e `reports/`. |
| **Finding sem `arquivo:linha` não existe** | Todo achado exige que você tenha aberto o arquivo e conferido a linha. Nunca cite linha vinda de memória ou de estimativa. |
| **O contrato HTTP não muda** | Mesmo path, mesmo método, mesmo status code, mesmas chaves no JSON de resposta. Se uma correção exigir quebrar isso, ela vira item "Breaking changes propostos" no relatório e só acontece com aval explícito. |
| **Refatorar é mover, não reescrever** | A regra de negócio existente é transportada para a camada certa. Você não inventa comportamento novo nem "melhora" a regra de negócio de passagem. |
| **Segredo nunca migra de lugar em texto puro** | Vai para variável de ambiente. `.env.example` recebe placeholder (`CHANGE_ME`), nunca o valor real. `.env` entra no `.gitignore`. |
| **Onda que quebra o smoke é revertida** | Não se acumula quebra "para arrumar no final". Reverte, corrige a abordagem, repete. |

### Racionalizações proibidas

| Pensamento | Realidade |
|---|---|
| "O problema é óbvio, já corrijo enquanto audito" | A Fase 2 existe para o humano decidir. Corrigir antes do GATE queima a decisão dele. |
| "Achei a linha mais ou menos, depois confiro" | Linha errada no relatório invalida o relatório inteiro. Confira antes de escrever. |
| "Esse endpoint é feio, vou renomear" | Renomear rota quebra o cliente. É breaking change, não refatoração. |
| "A app nem subia antes, não dá pra comparar" | Se não sobe, isso é o primeiro finding CRITICAL. O baseline vira "não boota" e a Fase 3 tem que fazer subir. |
| "São só 3 arquivos, faço tudo de uma vez" | Ondas existem para localizar a quebra. Sem elas, um smoke vermelho não diz o que causou. |
| "O projeto já tem `services/`, então tem camada de serviço" | Diretório não é camada. Confira se o módulo é importado e se a dependência flui numa direção só. |

---

## Fase 0 — Preflight

1. Confirme que o diretório de trabalho é a **raiz do projeto-alvo** (onde está `requirements.txt`, `package.json`, `pyproject.toml`, `go.mod` ou equivalente). Se não for, pergunte qual é.
2. Rode `git status --short`. A refatoração é **in-place na branch atual**.
   - Árvore limpa → siga.
   - Árvore suja → **mostre o que está pendente** e diga se algum arquivo pendente está no escopo da refatoração. As Fases 1 e 2 são read-only e seguem normalmente; a decisão sobre commitar entra no GATE, que é onde a escrita começa.
   - Sem git → avise que não haverá rollback automático. Isso muda o GATE: sem checkpoint possível, a opção de commit vira "faça backup manual antes".
3. Crie `.refactor-arch/` e adicione ao `.gitignore` (é diretório de trabalho, não entregável).

---

## Fase 1 — Análise

Leia `references/01-analise-de-projeto.md` e aplique as heurísticas.

**Produza:**

1. **Detecção de stack** — linguagem + versão, gerenciador de pacotes, framework + versão, dependências relevantes, banco, camada de acesso a dados (driver cru vs ORM), entrypoint, host, porta, debug.
2. **Configuração e testes** — de onde vêm as configurações (env / `.env` / literal no código) e se existe suíte de testes.
3. **Métricas de código** — contagem de arquivos-fonte, LOC total, os 3 maiores arquivos.
4. **Schema** — tabelas e restrições ausentes (FK, `UNIQUE`, `NOT NULL`).
5. **Domínio** — o que a aplicação faz, em uma linha, deduzido das rotas e das tabelas.
6. **Nível de organização** — monolito flat / camadas nominais / camadas reais (critério no arquivo de referência).
7. **Inventário de rotas** em `.refactor-arch/rotas.tsv`, uma por linha, formato `MÉTODO<TAB>PATH<TAB>BODY_JSON` (use `-` quando não houver body). Esse arquivo é o contrato que a Fase 3 tem que preservar.
8. **Baseline de comportamento** — siga `references/06-validacao.md`: suba a aplicação, rode `scripts/smoke.sh .refactor-arch/baseline`, derrube a aplicação. Se algo não subir, registre como achado e siga.

**Imprima exatamente neste formato.** Todas as linhas são obrigatórias, na ordem abaixo. Atributo que não se aplica ou não foi encontrado recebe `não detectado` ou `nenhum` — a linha nunca some.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão>
Package mgr:   <gerenciador> (<manifesto>)
Framework:     <framework + versão>
Dependencies:  <libs relevantes + versão>
Database:      <banco> (<arquivo, ou "URL via env">)
Data access:   <driver cru: nome | ORM: nome>
Entrypoint:    <comando de boot> → <host>:<porta> (debug <on|off>)
Config:        <env vars | .env | literal em arquivo:linha>
Tests:         <framework de teste + N arquivos | nenhum>
Domain:        <domínio em uma linha>
Architecture:  <nível de organização + descrição curta>
Source files:  <N> files analyzed, <LOC> LOC
Largest files: <arquivo> (<LOC>), <arquivo> (<LOC>), <arquivo> (<LOC>)
DB tables:     <tabelas>
Schema gaps:   <restrições ausentes | nenhuma>
Routes:        <N> endpoints mapped (GET <n> · POST <n> · PUT <n> · DELETE <n>)
Baseline:      <N/N endpoints respondendo | app não boota: motivo>
Git:           <branch> · <árvore limpa | N arquivos pendentes | sem git>
================================
```

Em `Config`, cite onde a configuração está (`app.py:12`), **nunca o valor** — segredo impresso no terminal vaza igual segredo no código.

---

## Fase 2 — Auditoria

Leia `references/02-catalogo-anti-patterns.md` e `references/03-template-relatorio.md`.

1. **Varra o código contra o catálogo inteiro.** Para cada anti-pattern, rode os sinais de detecção listados (comandos `rg`) e **depois leia o trecho** — o grep localiza candidatos, a leitura confirma. Aplique a seção "Guardas anti-falso-positivo" antes de registrar qualquer achado.
2. **Percorra os arquivos-fonte inteiros pelo menos uma vez.** Grep sozinho não encontra God Class, camada fantasma, duplicação nem regra de negócio fora de lugar.
3. **Agrupe ocorrências repetidas do mesmo anti-pattern em um finding só**, listando todas as linhas. 20 SQL injections no mesmo arquivo são 1 finding com 20 linhas, não 20 findings.
4. **Escreva o relatório** no formato de `03-template-relatorio.md`, ordenado CRITICAL → HIGH → MEDIUM → LOW. Salve em `reports/audit-<slug-do-projeto>.md` (crie `reports/` se preciso).
5. **Imprima no terminal o sumário e o índice de findings** (severidade · nome · arquivo:linha), e o caminho do arquivo. O relatório completo é o arquivo; o terminal dá a visão que o usuário precisa para decidir no GATE.

**Mínimos de qualidade** (se não atingir, você não terminou a auditoria — volte ao passo 2):
- ≥ 5 findings
- ≥ 1 CRITICAL ou HIGH
- Todo finding com `arquivo:linha` conferido
- Detecção de APIs deprecated executada (mesmo que o resultado seja "nenhuma encontrada")

### GATE — obrigatório

Pare. Use **AskUserQuestion** com estas opções:

- **Prosseguir com a Fase 3** — refatora in-place na branch atual
- **Commit de checkpoint e prosseguir** — `git add -A && git commit` do estado atual antes de tocar em qualquer coisa (é o mecanismo de rollback)
- **Abortar** — fica só o relatório

Não escreva nenhum arquivo de código enquanto essa pergunta não for respondida. Um "sim" implícito não existe: a resposta tem que vir do usuário.

---

## Fase 3 — Refatoração

Leia `references/04-guidelines-mvc.md` e `references/05-playbook-refatoracao.md`.

### 3.1 Planeje

Escreva `.refactor-arch/plano-refatoracao.md` mapeando, em tabela: `finding (AP-xx) → transformação (T-xx) → arquivos afetados → onda`.

A estrutura alvo depende do nível de organização detectado na Fase 1 — `04-guidelines-mvc.md` traz a receita para cada nível. Monolito flat e projeto com camadas nominais **não recebem o mesmo tratamento**.

### 3.2 Execute em ondas

Ordem fixa. Após **cada** onda: suba a app, rode `scripts/smoke.sh`, compare com o baseline. Vermelho → reverta a onda, corrija a abordagem, repita.

| # | Onda | Transformações típicas |
|---|---|---|
| 1 | Config e segredos | T-01 |
| 2 | Camada de dados | T-02, T-05, T-13 |
| 3 | Camada de negócio | T-03, T-04, T-08, T-14 |
| 4 | Views / rotas | T-03, T-06 |
| 5 | Error handling e validação | T-07, T-09, T-10 |
| 6 | Higiene | T-11, T-12 |

Mova código com `git mv` quando for movimentação pura, para o diff mostrar rename em vez de delete+add.

### 3.3 Valide

Siga `references/06-validacao.md`. Aprovação exige **todos**:

- App boota sem exceção
- `scripts/smoke.sh .refactor-arch/depois` + `diff` dos `.status` contra o baseline: zero divergência
- Estrutura de diretórios segue `04-guidelines-mvc.md`
- Nenhum segredo literal restante no código-fonte
- Zero finding CRITICAL ou HIGH remanescente

Se algum critério falhar, **diga qual falhou e por quê**. Não declare sucesso parcial como sucesso.

**Imprima:**

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore da estrutura final>

## Findings Resolved
CRITICAL: <n>/<n> | HIGH: <n>/<n> | MEDIUM: <n>/<n> | LOW: <n>/<n>

## Validation
  [x|!] Application boots without errors
  [x|!] All <N> endpoints match baseline status
  [x|!] No hardcoded secrets in source
  [x|!] Zero CRITICAL/HIGH findings remaining
================================
```

Use `[x]` só para o que você verificou rodando. Item não verificado é `[!]` com a explicação ao lado.
