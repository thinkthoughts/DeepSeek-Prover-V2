# Recommendation — RPI-DS-001d

> **Correction (2026-11-05, RPI-DS-001d):** the pilot needs a GPU with ≥ 40 GB. A 24 GB
> card cannot hold the KV cache for the pre-registered 16,384-token CoT budget alongside
> the 13.8 GB of weights. See `SMOKE_INTERFACE_REVIEW_001d.md` §4.

**Next experiment: a pilot run of the pre-registered design on one GPU, with C0 and C2 on
`gdt_periodic` and its 7-lemma closure, followed directly by the full run if the pilot's
pipeline checks pass.**

## Why a pilot first

The CPU side is complete:

- 39/39 certified references;
- a strict verifier with mandatory kernel replay;
- a REPL adapter that agrees with the direct path;
- a Cauto baseline;
- a fixed pre-registration.

What remains untested is the pipeline from generation to certification:

- code-block extraction;
- full-code prefix matching against real 7B outputs;
- truncation handling;
- token accounting;
- GPU energy counters.

`gdt_periodic` is the smallest challenge theorem with a non-trivial closure (7 lemmas). The
pilot is about 256 C0 attempts plus 256 C2 attempts, a GPU-hour or less on one 24 GB card.
Every pre-registered measurement is exercised at small cost.

## Pilot scope (counts as an amendment-free dry run)

1. On the GPU host, pin vLLM and CUDA and download the 7B at revision `a8d9e144`. Record
   the run manifest: GPU model, driver, vLLM version and the NVML energy counter.
2. Build the exact DeepSeek fork environment there (≥ 16 cores) and run
   `tools/validate_001c.sh` in it. This removes the last environment difference
   (Batteries).
3. Generate C0 and C2 for `gdt_periodic` and its closure, CoT mode, with seeds per the
   pre-registration. Screen with the REPL adapter, then certify every success via the
   direct path with lean4checker.
4. Check, without looking at outcomes:
   - extraction categories behave as specified (`no_code_block`, `truncated`,
     `prefix_mismatch`);
   - instrumentation fields are filled;
   - an assembled C2 file can be produced and certified when its lemmas succeed.
5. If any pipeline step needs a change, record it as a dated amendment in
   `PREREGISTRATION.md` §12 *before* the full run. The pilot's outcomes are reported
   separately from the confirmatory run.

## Full run (after the pilot)

All four conditions, both modes, the full budget schedule of §4/§6. The sample count is
about 3,936 C0 + 3,936 C0h + 1,248 C1 + 1,248 C2 per mode. Then the per-theorem analysis
and the 200-reordering robustness check of §9, reported against the interpretation rules
of §10.

## Gate

- [x] Certified reference proofs (001b; re-checked in 001c)
- [x] Mandatory kernel replay for `certified` (001c)
- [x] REPL adapter agrees with the direct verifier (001c)
- [x] Cauto baseline (001c)
- [x] Pre-registration and prompts fixed, 0 leakage (001c)
- [ ] GPU host and model revision pinned in a run manifest
- [ ] Exact DeepSeek environment validated (optional for the pilot; required before
  reporting environment-exact claims)
