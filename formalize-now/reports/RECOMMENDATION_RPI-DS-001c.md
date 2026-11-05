# Recommendation — RPI-DS-001c

**Next patch: connect the strict wrapper to DeepSeek's REPL path and run the CPU-only
Cauto baseline on all 39 items. Model inference stays gated behind that patch.**

## Why this step

The reference benchmark is now certified (39/39). Two things stand between it and a
trustworthy Stage 1 measurement:

1. Stage 1 will score thousands of candidates through DeepSeek's REPL-based harness.
   The strict wrapper currently calls `lean` directly, at about 3.5 GB and 4–8 s per
   candidate. A REPL adapter, which keeps one Mathlib-loaded environment per worker and
   runs the C2–C7 checks through REPL commands, makes the wrapper usable at Stage 1
   volume. The adapter must give the same decisions as the direct path on the 13 test
   cases.
2. The tactic-only control (Cauto: `simp`, `omega`, `decide`, `aesop`, `norm_num`,
   `linarith` per item) measures how many ladder items are trivial before any model is
   involved. It runs on CPU and directly sets how Stage 1 results can be read.

## Scope

- Build the exact DeepSeek environment once: fork `2f65ba7f`, Batteries `42b5ddd`,
  `xinhjBrant/repl`. Mathlib is built from source, an estimated several CPU-hours. Then
  rerun `tools/SigCheck.lean` and the 13 wrapper tests in it. This removes the last
  environment caveat (the one-commit Batteries difference).
- `harness/repl_adapter.py`: the same C1–C8 decisions through the REPL, with a
  differential test against `verify_strict.py`.
- `harness/cauto.py`: run Cauto on the 39 items through the strict wrapper, and record
  the solved set, wall time and peak memory per item.
- Pre-register the Stage 1 direction and both budget-matching rules (equal samples;
  equal generated tokens), as SPEC §1 requires.

## Gate for Stage 1 (model inference)

- [x] 39/39 reference proofs certified (RPI-DS-001b)
- [x] Strict wrapper with valid/invalid tests (RPI-DS-001b)
- [ ] REPL adapter agrees with the direct wrapper on all tests
- [ ] Cauto baseline recorded
- [ ] Pre-registration committed
- [ ] GPU access confirmed
