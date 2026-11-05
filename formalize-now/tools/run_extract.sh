#!/usr/bin/env bash
# Usage: run_extract.sh <GDT repo root> <out.json> [Solution|Challenge]
# Concatenates the unmodified Solution file with ExtractDeps.append.lean into a
# temporary file, elaborates it with the GDT toolchain, and writes JSON.
set -euo pipefail
GDT="$1"; OUT="$2"; HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$GDT/.lake/rpi_extract_tmp.lean"
SRC="$GDT/${3:-Solution}/GeneralDivisorTheorem.lean"
cat "$SRC" "$HERE/ExtractDeps.append.lean" > "$TMP"
# guard: the prefix of the temp file is byte-identical to the original Solution
cmp -n "$(stat -c %s "$SRC")" "$SRC" "$TMP"
sha256sum "$SRC" >&2
( cd "$GDT" && lake env lean -DElab.async=false "$TMP" ) > "$OUT.raw" || { cat "$OUT.raw" >&2; exit 1; }
grep -v '@@RPI_JSON' "$OUT.raw" | grep -v '^\[' | grep -v '^ ' | grep -v '^\]' | grep -v '^{' >&2 || true
sed -n '/@@RPI_JSON_BEGIN/,/@@RPI_JSON_END/p' "$OUT.raw" | sed '1d;$d' > "$OUT"
grep -v -e '@@RPI_JSON' "$OUT.raw" | sed -n '/^\/.*: \(warning\|error\|info\)/p' >&2 || true
rm -f "$OUT.raw"
rm -f "$TMP"
