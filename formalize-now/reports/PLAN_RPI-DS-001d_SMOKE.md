# RPI-DS-001d — Minimal 7B inference smoke-test plan

Status: planning only. No GPU run has been performed.

## Question

Can the pinned DeepSeek-Prover-V2-7B model produce output that our trusted
GDT-Ladder verifier can safely extract, elaborate, and certify without altering
the original `gdt_periodic` statement?

This is an **interface check**, not yet a test of whether decomposition raises
the success rate. A failure to prove `gdt_periodic` in a few samples is not
evidence against the decomposition hypothesis.

## Inputs and limits

- Use the Stage 001c pre-registered model revision, toolchain, and CoT prompt.
- Start with `gdt_periodic`, condition C0. Generate **at most two** outputs.
- Optionally generate **at most two** outputs for one C2 lemma after the C0
  extraction path behaves correctly.
- No retraining, 671B inference, or multi-thousand-sample run.
- Inspect host capacity and estimated costs before loading model weights.

## Checks in order

1. Record GPU model, memory, driver, CUDA/vLLM versions, model revision, and
   instrumentation availability in an immutable run manifest.
2. Verify model prompt format and completion text without letting the generated
   code overwrite the trusted header, definitions, or theorem signature.
3. Test code-block extraction and proof-body isolation. Log whether the model
   emits the whole file, the body alone, commentary, or a truncated response.
4. Run the REPL preliminary screen, then direct verification and mandatory
   `lean4checker` replay for any candidate that passes screening.
5. Record exact prompts and raw outputs, generated/prompt token counts,
   wall time, memory, and device-energy values or explicit unavailability.
6. Classify failures: output-format mismatch, truncation, elaboration failure,
   unresolved goals, theorem mismatch, or unexpected axiom.

## Pre-registration boundary

Stage 001c's frozen design is the intended confirmatory experiment. Any
extractor or prompt amendment discovered during this smoke test must be logged
before the later 512-attempt C0/C2 pilot; smoke samples must be excluded from
confirmatory totals. Do not silently loosen statement or axiom checks to accept
a completion.

## Go/no-go

- **Go to a bounded pilot:** full output-to-verifier path functions, raw data and
  costs are recorded, and no specification or trust-boundary defect remains.
- **Repair first:** prefix mismatch, parser failures, verifier disagreement, or
  absent measurement provenance prevents interpreting outputs reliably.
- **Defer:** GPU cost, capacity, or model compatibility is unsuitable.

The subsequent experiment compares C0/C0h/C1/C2 under the fixed budget rules
in `PREREGISTRATION.md`; this smoke test makes no performance claim.
