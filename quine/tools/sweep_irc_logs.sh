#!/bin/bash
# Barrido de los logs IRC de la comunidad esolangs: busca 'malbolge' en todos los meses
# disponibles de #esoteric (freenode, 2002-12..2021-06) y #esolangs (libera, 2021-05..hoy).
#
# Uso:  ./sweep_irc_logs.sh [salida.txt]
# Salida: bloques "### <canal>/<YYYY-MM>" seguidos de las lineas que mencionan malbolge.
#
# Nota: filtra por streaming (no guarda los ~600 MB de logs completos).
set -u
OUT="${1:-hits.txt}"
BASEURL="https://logs.esolangs.org"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

: > "$OUT"

fetch_index() {
  local base="$1" dest="$2"
  curl -sSL --max-time 90 "$BASEURL/$base/all.html" -o "$dest" || return 1
  [ -s "$dest" ] || return 1
}

probe_month() {
  local base="$1" month="$2"
  local hits
  hits=$(curl -sSL --max-time 120 "$BASEURL/$base/$month.txt" 2>/dev/null | grep -ai 'malbolge')
  if [ -n "$hits" ]; then
    { printf '### %s/%s\n' "$base" "$month"; printf '%s\n' "$hits"; } >> "$OUT"
  fi
}

export -f probe_month
export OUT BASEURL

total=0
for base in freenode-esoteric libera-esolangs; do
  idx="$WORK/$base.html"
  if ! fetch_index "$base" "$idx"; then
    echo "AVISO: no se pudo bajar el indice de $base" >&2
    continue
  fi
  months=$(grep -oE '[0-9]{4}-[0-9]{2}\.txt' "$idx" | sed 's/\.txt$//' | sort -u)
  n=$(printf '%s\n' "$months" | wc -l)
  echo "$base: $n meses" >&2
  total=$((total + n))
  printf '%s\n' "$months" | xargs -P 8 -I{} bash -c 'probe_month "$1" "$2"' _ "$base" {}
done

echo "TOTAL meses: $total" >&2
echo "Meses con menciones: $(grep -c '^###' "$OUT" || true)" >&2
echo "Lineas con menciones: $(grep -vc '^###' "$OUT" || true)" >&2
