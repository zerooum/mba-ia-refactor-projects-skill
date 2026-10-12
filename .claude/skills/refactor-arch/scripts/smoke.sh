#!/usr/bin/env bash
# smoke.sh — dispara todas as rotas de rotas.tsv e grava status + body por rota.
#
# Uso:
#   bash smoke.sh <diretorio-de-saida>
#
# Variaveis de ambiente:
#   BASE_URL  (padrao: http://localhost:5000)
#   ROTAS     (padrao: .refactor-arch/rotas.tsv)
#
# Formato de rotas.tsv (campos separados por TAB):
#   METODO<TAB>PATH<TAB>BODY_JSON     ("-" quando nao houver body)
#
# Saida, por rota:
#   <dir>/NNN-METODO-slug.status   -> codigo HTTP (ou 000 se a conexao falhou)
#   <dir>/NNN-METODO-slug.body     -> corpo da resposta
#
# Comparacao:
#   diff -r .refactor-arch/baseline .refactor-arch/depois --include='*.status'

set -u

OUT_DIR="${1:-}"
BASE_URL="${BASE_URL:-http://localhost:5000}"
ROTAS="${ROTAS:-.refactor-arch/rotas.tsv}"

if [ -z "$OUT_DIR" ]; then
  echo "uso: bash smoke.sh <diretorio-de-saida>" >&2
  exit 2
fi

if [ ! -f "$ROTAS" ]; then
  echo "erro: arquivo de rotas nao encontrado: $ROTAS" >&2
  exit 2
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "erro: curl nao encontrado" >&2
  exit 2
fi

mkdir -p "$OUT_DIR"
rm -f "$OUT_DIR"/*.status "$OUT_DIR"/*.body 2>/dev/null

n=0
ok=0
fail=0

while IFS=$'\t' read -r method path body || [ -n "${method:-}" ]; do
  # ignora linhas vazias e comentarios
  case "${method:-}" in
    ''|'#'*) continue ;;
  esac
  [ -z "${path:-}" ] && continue

  n=$((n + 1))
  slug=$(printf '%s' "$path" | tr -c 'a-zA-Z0-9' '-' | sed 's/--*/-/g; s/^-//; s/-$//')
  [ -z "$slug" ] && slug="root"
  name=$(printf '%03d-%s-%s' "$n" "$method" "$slug")

  if [ "${body:--}" = "-" ] || [ -z "${body:-}" ]; then
    status=$(curl -s -o "$OUT_DIR/$name.body" -w '%{http_code}' \
      -X "$method" "$BASE_URL$path" --max-time 15)
  else
    status=$(curl -s -o "$OUT_DIR/$name.body" -w '%{http_code}' \
      -X "$method" "$BASE_URL$path" \
      -H 'Content-Type: application/json' \
      --data "$body" --max-time 15)
  fi

  printf '%s\n' "$status" > "$OUT_DIR/$name.status"

  case "$status" in
    2*|3*|4*) ok=$((ok + 1));  mark='ok'   ;;
    *)        fail=$((fail + 1)); mark='FAIL' ;;
  esac
  printf '%-6s %-4s %-45s %s\n' "$mark" "$status" "$path" "$method"
done < "$ROTAS"

echo "---"
echo "rotas: $n | respondeu: $ok | falhou (5xx/conexao): $fail"
echo "saida: $OUT_DIR"

[ "$fail" -eq 0 ]
