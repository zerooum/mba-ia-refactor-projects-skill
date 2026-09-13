# 06 — Validação

Como capturar o baseline (Fase 1) e provar que a refatoração não quebrou nada (Fase 3).

Sem suíte de testes, a única prova objetiva é: **a app sobe e todos os endpoints respondem o mesmo status de antes.**

---

## 1. Subir a aplicação

Comando vem do manifesto e do entrypoint detectados na Fase 1.

| Stack | Boot | Porta padrão |
|---|---|---|
| Flask | `python app.py` ou `flask --app app run` | 5000 |
| FastAPI | `uvicorn main:app` | 8000 |
| Django | `python manage.py runserver` | 8000 |
| Express | `npm start` (veja `scripts` no `package.json`) | 3000 |
| Go | `go run .` | variável |

Rode **em background** e guarde o log:

```bash
cd <projeto>
python app.py > .refactor-arch/boot.log 2>&1 &
echo $! > .refactor-arch/app.pid
```

Prepare o ambiente antes: `pip install -r requirements.txt` / `npm install`, `.env` presente (a partir do `.env.example`), seed rodado se o README exigir.

### Espere por condição, nunca por `sleep` fixo

```bash
for i in $(seq 1 40); do
  curl -sf -o /dev/null "http://localhost:$PORT/" && break
  sleep 0.25
done
```

Se estourar o timeout, **leia `.refactor-arch/boot.log`**. `Address already in use` significa instância anterior viva — mate pelo pid antes de tentar de novo.

### Derrubar

```bash
kill "$(cat .refactor-arch/app.pid)" 2>/dev/null
```

Sempre derrube antes de editar código. App servindo o módulo antigo produz smoke enganoso.

---

## 2. Smoke test

```bash
# Fase 1 — antes de qualquer mudança
bash .claude/skills/refactor-arch/scripts/smoke.sh .refactor-arch/baseline

# Fase 3 — após cada onda e no fim
bash .claude/skills/refactor-arch/scripts/smoke.sh .refactor-arch/depois
```

O script lê `.refactor-arch/rotas.tsv` e grava, por rota, um `.status` (código HTTP) e um `.body`.

Variáveis: `BASE_URL` (padrão `http://localhost:5000`), `ROTAS` (padrão `.refactor-arch/rotas.tsv`).

### Comparar

```bash
diff -r .refactor-arch/baseline .refactor-arch/depois --include='*.status' && echo "SMOKE OK"
```

**Zero divergência de status é obrigatório.** Divergência tem exatamente dois desfechos: é regressão (conserte) ou é melhoria intencional já registrada como breaking change no relatório (documente no resultado final). Não existe terceira opção.

Os `.body` não entram no `diff` automático: id autoincremento, timestamp e ordem mudam legitimamente. Inspecione manualmente as rotas que o relatório indicou como afetadas e confirme que as **chaves** do JSON continuam iguais.

---

## 3. Baseline quebrado

Se a app não sobe **antes** da refatoração:

1. Registre como finding CRITICAL na Fase 2, com o erro do `boot.log`.
2. `rotas.tsv` continua sendo montado (por leitura do código) — ele é o contrato alvo.
3. O baseline vira "app não boota".
4. Fazer a app subir é o primeiro item da Fase 3, e a validação final passa a exigir: boota + todas as rotas respondem status não-5xx.

Se só algumas rotas falham no baseline, registre quais e por quê. Elas **continuam falhando igual** após a refatoração, a menos que a correção estivesse no escopo — nesse caso a melhoria é esperada e documentada.

---

## 4. Validação após cada onda

Sem exceção, ao fim de cada onda da Fase 3:

1. Derrube a app
2. Suba de novo
3. Rode o smoke em diretório próprio (`.refactor-arch/onda-<n>`)
4. `diff` contra o baseline

Vermelho → **reverta a onda** (`git checkout -- <arquivos>` ou `git stash`), repense, refaça. Não siga para a onda seguinte com o smoke quebrado: a partir daí você não sabe mais qual mudança causou o quê.

---

## 5. Checagem final

Além do smoke:

```bash
# nenhum segredo literal restante
rg -n -i "(secret|password|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]{4,}" --glob '!*.example' --glob '!node_modules'

# nenhuma query montada por concatenação
rg -n "(execute|query|run)\s*\(\s*[\"'].*(SELECT|INSERT|UPDATE|DELETE).*[\"']\s*\+" -i
rg -n "f[\"'].*(SELECT|INSERT|UPDATE|DELETE).*\{" -i

# nenhuma API deprecated catalogada
rg -n "datetime\.utcnow|\.query\.get\(|new Buffer\(|url\.parse\("

# nenhum erro engolido
rg -n "except\s*:|catch\s*\{\s*\}"

# camadas: view não consulta banco, model não conhece HTTP
rg -n "cursor\.execute|\.query\.|db\.session" --glob '*rout*' --glob '*view*'
rg -n "request\.|jsonify|res\.json" --glob '*model*'

# boot sem warning de deprecação
python -W error::DeprecationWarning app.py    # ou: node --throw-deprecation src/app.js
```

Todos vazios + smoke verde = Fase 3 aprovada.

---

## 6. Relatar

Marque `[x]` **apenas** o que você verificou rodando o comando. Item não verificado é `[!]` com o motivo ao lado.

Quando algo falhar, diga o que falhou, o comando que provou a falha e a saída dele. Sucesso parcial relatado como sucesso é pior que falha relatada.
