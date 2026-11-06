# RPI-DS-001d.2 — Theorem-level C2 assembler

**Result.** `harness/assemble_c2.py` builds the complete proof of an unchanged target
theorem from per-lemma candidate proofs. The members are its kernel-dependency closure
plus the target, in verified dependency order. The assembled file is certified with the
strict checks and lean4checker replay.

The 22 controlled fixture tests all pass (`harness/tests/run_assembly_tests.py`). They
cover successful, missing, invalid, injected, conflicting, re-ordered and extraneous
candidates, and every challenge theorem up to `general_divisor_theorem` with 34 members.

Reference proofs appear only as labelled fixtures. A claimed C2 success requires model
provenance and no reference-proof text. The pre-registration is preserved, with
Amendment A2 appended. Everything ran on CPU, with no inference.

## Procedure

| Step | Rule | Failure outcome |
|---|---|---|
| 1. Closure | closure(T) from Stage 0 **kernel** dependencies (`manifest/gdt_manifest_v2.json`) | `error` (unknown name) |
| 2. Order | topological sort (Kahn) over kernel deps within the closure, source-line tie-break; asserted that every dependency precedes its user | `error` (cycle) |
| 3. Selection | per member, the smallest `sample_index` with per-item status `certified` | `conflict` (two different proofs at one index); `incomplete` (no certified candidate); **no substitution** |
| 4. Assembly | trusted header + definitions → trusted expected statements of *all* members (`GDT.Expected`) → members in order, each as trusted statement + indented candidate body → trusted check of all members | — |
| 5. Certification | compile with `-o`; every member a theorem, alpha-equivalent to its expected statement, axioms ⊆ {propext, Quot.sound, Classical.choice}; no declared axioms; no weakening options; lean4checker replay of the module | `rejected` |
| 6. Claim | `c2_success` only if certified, all members `model` with a generation id, and no body line equal to a reference-proof line (≥ 20 characters, public statement text excluded) | `fixture_only`, `reference_text_detected`, `none` |

The per-item status is used only to *select* candidates. The assembled file is
re-verified in full, so a per-item record marked "certified" in error still fails (cases
V1 and C3).

## Fixture tests (22/22)

| Case | Target (members) | Outcome / claim | What it shows |
|---|---|---|---|
| A1 | `gdt_periodic` (8) | certified / fixture_only | reference fixtures assemble and certify; never claimable |
| A2 | `d_mul_R_eq_rad` (2) | certified / c2_success | independently written proofs plus simulated model provenance give the only claimable level |
| A3 | `d_mul_R_eq_rad` (2) | certified / reference_text_detected | a reference proof labelled as model output is caught |
| A4 | `d_mul_R_eq_rad` (2) | certified / fixture_only | one fixture member blocks the claim |
| M1 | `gdt_periodic` | incomplete | missing `gcd_with_N_iff_gcd_with_R`; no compile attempted, no fallback |
| M2 | `gdt_periodic` | incomplete | missing target proof |
| M3 | `gdt_periodic` | incomplete | only a `preliminary` candidate for `rad_dvd_self` |
| V1 | `gdt_periodic` | rejected | `sorry` body falsely marked certified: axiom check fails |
| V2 | `gdt_periodic` | rejected | compile error in one member |
| V3 | `gdt_periodic` | rejected | `end GDT.Challenge` / theorem injection inside a body |
| V4 | `gdt_periodic` | rejected | `axiom` injection inside a body |
| C1 | `gdt_periodic` | conflict | two different proofs at `rad_dvd_self`, sample 0 |
| C2 | `gdt_periodic` | certified / fixture_only | sample 0 rejected per-item, sample 1 certified: sample 1 selected |
| C3 | `gdt_periodic` | rejected | a wrong sample-0 proof marked certified is selected, and the assembled file rejects it |
| O1 | `gdt_periodic` | certified / fixture_only | shuffled input plus 2 extraneous candidates (reported, ignored); order recomputed |
| E1 | unknown | error | unknown target |
| S × 6 | `gdt_empty` (1), `gdt_minimal_period` (22), `gdt_count_per_period` (23), `gdt_density` (26), `gdt_correction_factor` (9), `general_divisor_theorem` (34) | certified / fixture_only | assembly scales over all challenge theorems: compile 2.5–8.9 s, kernel replay 1.6–2.1 s |

"Simulated model provenance" is a label set inside the test to exercise the claim logic.
No model output exists; these results live only in `harness/tests/assembly_results.json`.

## Interface for Stage 1

```bash
python3 harness/assemble_c2.py --target gdt_periodic --candidates c2_candidates.jsonl --json out.json
```

Candidates are JSONL records `{lemma, proof, sample_index, per_item_status, provenance,
generation_id}`, where `proof` is the extracted body from `harness/extract.py` and
`per_item_status` comes from `verify_strict.verify(..., reference_deps=True,
use_l4c=True)`. Budget truncation at b is done by the caller (`sample_index < b`).

## Remaining before the pilot

- The live generation path (`harness/smoke_run.py --live`) is unexercised and needs the
  approved ≥ 40 GB GPU smoke test.
- A driver that runs per-item C2 verification over generated samples and then calls the
  assembler per theorem and budget remains to be written. It wires existing components
  together; the semantics are fixed by Amendments A1 and A2.
