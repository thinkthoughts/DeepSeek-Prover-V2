#!/usr/bin/env bash
# RPI-DS-001e full CPU validation. Requires LEAN4CHECKER, RPI_REPL, TOKENIZER_JSON.
set -uo pipefail
F="$(cd "$(dirname "$0")/.." && pwd)"; L="$F/logs"; T="$F/tools/peak_rss.sh"
step() { local name=$1; shift; "$T" "$L/$name.log" "$@"; echo "$name=$?"; }
cd "$F/lean49" && rm -rf .lake/build
step lean49_lake_build_001e lake build
step lean49_sigcheck lake env lean ../tools/SigCheck.lean
cd "$F"; python3 tools/certify49.py logs/lean49_sigcheck.log; echo "certify=$?"
cd "$F/lean49"
step lean4checker_GDTBench.SolutionRef lake env "$LEAN4CHECKER" GDTBench.SolutionRef
step lean4checker_fresh_GDTBench.SolutionRef lake env "$LEAN4CHECKER" --fresh GDTBench.SolutionRef
cd "$F"
step strict_verifier_tests python3 -u harness/tests/run_tests.py
step repl_adapter_tests python3 -u harness/tests/run_repl_tests.py
step extract_tests python3 -u harness/tests/run_extract_tests.py
step context_tests python3 -u harness/tests/run_context_tests.py
step assembly_tests python3 -u harness/tests/run_assembly_tests.py
step c2_condition_tests python3 -u harness/tests/run_c2_condition_tests.py
step infra_tests python3 -u harness/tests/run_infra_tests.py
step prompts_v1_regen python3 harness/prompts.py --version 1
step prompts_v2_regen python3 harness/prompts.py --version 2
git -C "$F" diff --quiet -- benchmark/prompts_v1.jsonl benchmark/prompts_v2.jsonl benchmark/prompts_v2.manifest.json; echo "prompts_unchanged=$?"
git -C "$F" checkout -q -- benchmark/prompts_v1.manifest.json 2>/dev/null || true
rm -rf "$F/runs"
step smoke_dry_cot python3 -u harness/smoke_run.py --dry-run --with-c2 --mode cot
step smoke_dry_noncot python3 -u harness/smoke_run.py --dry-run --with-c2 --mode noncot
