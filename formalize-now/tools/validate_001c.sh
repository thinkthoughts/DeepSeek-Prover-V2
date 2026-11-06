#!/usr/bin/env bash
# RPI-DS-001c full validation: build, certification, kernel replay, verifier tests,
# REPL differential tests. Requires LEAN4CHECKER and RPI_REPL.
set -uo pipefail
F="$(cd "$(dirname "$0")/.." && pwd)"; L="$F/logs"; cd "$F/lean49"
rm -rf .lake/build
"$F/tools/peak_rss.sh" "$L/lean49_lake_build_001c.log" lake build; echo "build=$?"
"$F/tools/peak_rss.sh" "$L/lean49_sigcheck.log" lake env lean ../tools/SigCheck.lean; echo "sigcheck=$?"
cd "$F" && python3 tools/certify49.py logs/lean49_sigcheck.log; echo "certify=$?"
cd "$F/lean49"
"$F/tools/peak_rss.sh" "$L/lean4checker_GDTBench.SolutionRef.log" lake env "$LEAN4CHECKER" GDTBench.SolutionRef; echo "l4c=$?"
"$F/tools/peak_rss.sh" "$L/lean4checker_fresh_GDTBench.SolutionRef.log" lake env "$LEAN4CHECKER" --fresh GDTBench.SolutionRef; echo "l4c_fresh=$?"
cd "$F"
"$F/tools/peak_rss.sh" "$L/strict_verifier_tests.log" python3 -u harness/tests/run_tests.py; echo "strict_tests=$?"
"$F/tools/peak_rss.sh" "$L/repl_adapter_tests.log" python3 -u harness/tests/run_repl_tests.py; echo "repl_tests=$?"
