# harness/ — strict verification wrapper (RPI-DS-001b)

`verify_strict.py` decides whether a candidate proof of a GDT-Ladder item is accepted.
It is a separate component; DeepSeek-Prover-V1.5's `prover/lean/verifier.py` stays as it
is upstream.

```bash
# proof mode: candidate is the proof text that follows the item's `:= by`
python3 harness/verify_strict.py --item gdt/gdt_empty --proof cand.lean --lean4checker --json out.json
# full-code mode: candidate is a whole file starting with the item's header + definitions
python3 harness/verify_strict.py --item gdt/gdt_empty --full-code cand_full.lean
# tests: 13 cases with kernel replay, 3 preliminary-mode cases, 2 counting guards
LEAN4CHECKER=<lean4checker@v4.9.0-rc1 binary> python3 harness/tests/run_tests.py
# REPL adapter vs direct verifier (DeepSeek REPL xinhjBrant/repl@3334a97)
RPI_REPL=<repl binary> LEAN4CHECKER=<…> python3 harness/tests/run_repl_tests.py
```

Requirements: the `formalize-now/lean49` project built (`lake build`), with the full Mathlib
cache, because items import `Mathlib`. Each run takes about 4–8 s and about 3.5 GB of RAM.

## Status (RPI-DS-001c)

| Status | Meaning |
|---|---|
| `certified` | C1–C8 passed, including independent kernel replay; the only status that counts as solved |
| `preliminary` | C1–C7 passed, C8 not run (fast screening, e.g. `harness/repl_adapter.py`) |
| `rejected` | any check failed |

`accepted` is true exactly for `certified`. Use `count_certified(records)` to tally
results: it re-checks each record's C1–C8 evidence and raises on a record that claims
`certified` without it. Exit codes: 0 certified, 2 preliminary, 1 rejected.

## Checks

| Check | Requirement |
|---|---|
| C1 | `lean` exits 0 with no error message from candidate text |
| C2 | The trusted trailing `#eval` check ran, so a file that stops early (`#exit`) fails |
| C3 | `GDT.Challenge.<name>` exists and is a theorem |
| C4 | Its type is alpha-equivalent to `GDT.Expected.<name>`, the trusted statement elaborated before any candidate text |
| C5 | Its axioms (Lean's `#print axioms` collector) ⊆ {propext, Quot.sound, Classical.choice} |
| C6 | The file declares no axioms of its own (compiler specialisation artefacts excepted and recorded) |
| C7 | No kernel- or elaborator-weakening option (`debug.skipKernelTC`, …) |
| C8 | lean4checker replays the compiled candidate module |

The token scan (`token_scan` in the output) is recorded for review. Acceptance comes from
the checks on the elaborated declarations. The output also reports
`v15_complete_equivalent`: the V1.5 rule applied to the same compile, for comparison.

Results of the current test run: `tests/results.json`; summary in
`reports/RPI-DS-001b_BUILD_AND_VERIFICATION.md` §4.
