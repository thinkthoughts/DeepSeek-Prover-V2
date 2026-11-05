#!/usr/bin/env bash
# Usage: axiom_probe49.sh <mathlib dir> <build dir>
# Appends `#print axioms` for every declaration in the manifest to a temporary copy
# of lean49/GDTBench/SolutionPort.lean and elaborates it under Lean 4.9.
set -euo pipefail
ML="$1"; B="$2"; F="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$F/lean49/GDTBench/_AxiomProbe.lean"
cp "$F/lean49/GDTBench/SolutionPort.lean" "$TMP"
python3 -c "
import json;m=json.load(open('$F/manifest/gdt_manifest.json'))
for d in m['declarations']:
  if d['kind']=='theorem': print('#print axioms', d['name'])" >> "$TMP"
"$F/tools/lean49_check.sh" "$ML" "$B" axiom_probe --root="$F/lean49" "$TMP" || true
rm -f "$TMP"
