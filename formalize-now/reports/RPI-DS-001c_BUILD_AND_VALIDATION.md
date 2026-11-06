# Build and validation report — RPI-DS-001c

**Result.** After the 001c changes, all 39 reference proofs remain certified. The other
results:

- strict-verifier tests: 18/18;
- REPL adapter against the direct verifier: 16/16 agreement, certify mode 5/5;
- Cauto tactic baseline: 2/39 certified;
- pre-registration fixed, with 0 reference-proof matches in the 184 prompts.

Everything ran on CPU, with no model download and no inference.

## Environment

| Item | Value |
|---|---|
| Machine | 2 vCPU (Intel Xeon @ 2.10 GHz), 7 GiB RAM, no swap; no RAPL, no GPU |
| Lean / Mathlib | 4.9.0-rc1 / `d1d1e4b72c6e009edd97cabe1d661b021fe8eeae` (`lean49/lake-manifest.json`) |
| lean4checker | `leanprover/lean4checker@9da7f4a3` (v4.9.0-rc1) |
| REPL | `xinhjBrant/repl@3334a97b268ecc67beb36a75787f7e831208a724` (built in 12 s) |
| Model metadata | `deepseek-ai/DeepSeek-Prover-V2-7B@a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b` (API metadata only; weights not downloaded) |
| Branch base | `1848b81f` (RPI-DS-001b) |

## Validation run (`tools/validate_001c.sh`, total 7 min 1 s)

| Step | Result | Wall | Peak tree RSS | Log |
|---|---|---|---|---|
| Clean `lake build` | exit 0, 0 errors | 4.9 s | 2.86 GB | `logs/lean49_lake_build_001c.log` |
| SigCheck + certify49 | 39/39 certified; signatures identical; placeholder scan empty | 7.7 s | 1.58 GB | `logs/lean49_sigcheck.log`, `manifest/certification_lean49.json` |
| lean4checker `GDTBench.SolutionRef` | pass | 1.5 s | 1.52 GB | `logs/lean4checker_GDTBench.SolutionRef.log` |
| lean4checker `--fresh` | pass | 300.2 s | 1.66 GB | `logs/lean4checker_fresh_GDTBench.SolutionRef.log` |
| Strict verifier tests | 18/18 (13 original with kernel replay, 3 preliminary-mode, 2 counting guards) | 44.4 s | 3.91 GB | `logs/strict_verifier_tests.log`, `harness/tests/results.json` |
| REPL adapter differential tests | 16/16 agree; certify mode 5/5 | 62.1 s | 7.84 GB* | `logs/repl_adapter_tests.log`, `harness/tests/repl_results.json` |

\* Summed RSS of the REPL process and a concurrent direct `lean` run. Both memory-map the
same Mathlib `.olean` files, so shared pages are counted twice. Each process alone peaks
near 3.5–3.9 GB.

Also run in this patch:

- Cauto baseline: `logs/cauto_run.log`, 1 min 52 s.
- Environment closure: `logs/env_closure.log`, 2.3 s.
- Instrumentation demo: `logs/instrument_demo.jsonl`.

## Changes in 001c

1. **`harness/verify_strict.py`**
   - Statuses `rejected` / `preliminary` / `certified`. `accepted` is now true only for
     `certified`.
   - `count_certified()` re-checks the C1–C8 evidence of every record it counts and raises
     on a record that claims `certified` without it.
   - Exit codes: 0 certified, 2 preliminary, 1 rejected.
   - Source assembly and check evaluation (`assemble`, `apply_check_result`) are shared
     with the REPL adapter.
2. **`harness/repl_adapter.py`**
   - One DeepSeek REPL per worker, imports sent once, each candidate run on env 0, and the
     same trusted assembly and C1–C7 rules.
   - The REPL path yields at most `preliminary`. `certify=True` re-runs the candidate
     through the direct path with lean4checker, and any C1–C7 disagreement between the two
     paths rejects.
3. **`baseline/cauto.py`**: the tactic baseline. Results in `baseline/cauto_results.json`,
   with per-script Lean files and logs in `baseline/runs/`.
4. **`harness/prompts.py`**: deterministic prompts for C0/C0h/C1/C2 × CoT/non-CoT, with a
   reference-proof leakage check that refuses to write prompts on any match.
5. **`harness/instrument.py`**: per-attempt cost records with explicit `unavailable`
   reasons.
6. **`tools/EnvClosure.lean`**: the constant and module closure of the certified proofs.
7. **`PREREGISTRATION.md`** and **`preregistration.json`**.

## Behavioural notes

- **REPL buffering.** The REPL writes through C stdio, so a long-lived REPL needs `stdbuf
  -oL`; without it the first attempt stalled. DeepSeek's one-shot invocation reads from a
  file and is unaffected.
- **C8 reach in the current tests.** All candidates in the test set that are invalid fail
  some check among C1–C7 before kernel replay. The `native_decide` case, for example, is
  caught by C5 (`Lean.ofReduceBool`). C8 therefore guards against elaborator-level issues
  outside the current test set, and it is required for `certified` regardless.
- **V1.5 rule on the same messages.** The V1.5 completeness rule, applied to REPL messages,
  accepts 4 of the 10 invalid cases (I4, I5, I7, I8), the same four as on the direct path.

## Remaining issues

1. The exact DeepSeek fork build was deferred (`reports/ENVIRONMENT_COMPATIBILITY_001c.md`
   §4). The Batteries difference lies outside the certified proofs' closure.
2. Token counts, GPU time and GPU energy wait for inference. CPU package energy is
   unavailable on this host (no RAPL).
3. The rc1/rc2 wording in DeepSeek's papers is unresolved from public artifacts.
