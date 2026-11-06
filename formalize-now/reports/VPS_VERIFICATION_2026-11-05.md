# RPI-DS-001c — Independent VPS verification checkpoint

Date reported: 2026-11-05 (America/Denver). Machine: `srv838187`.

This record captures commands and exit statuses reported from the user's VPS terminal.
The terminal output was reviewed in the project conversation; the commands were not
executed directly by the author of this record. It is independent of Claude's
original Stage 001a–001c build machine, but not a newly reconstructed upstream
DeepSeek evaluation run.

## Source and environment

- Repository: `thinkthoughts/DeepSeek-Prover-V2`
- Branch: `formalize-now/gdt-ladder-stage0`
- HEAD: `342ca2b981627ef51fb531003bba06d24fc3db7f`
- Lean: 4.9.0-rc1, as pinned by `formalize-now/lean49/lean-toolchain`
- Mathlib: `d1d1e4b7`, as pinned by Stage 001c
- Standalone `lean4checker`: `leanprover/lean4checker@9da7f4a3`, built locally

## Observed outcomes

| Check | VPS command | Reported outcome |
| --- | --- | --- |
| Benchmark build | `lake build GDTBench` | Build completed successfully |
| Signature/axiom extraction | `lake env lean ../tools/SigCheck.lean > ../logs/vps_sigcheck.log 2>&1` | Completed |
| Certification | `python3 ../tools/certify49.py ../logs/vps_sigcheck.log` | `certified 39 / 39 \| scan {} \| sigs unchanged True` |
| Module kernel replay | `lake env ~/lean4checker/.lake/build/bin/lean4checker GDTBench.SolutionRef` | Exit code 0 |
| Fresh environment replay | `lake env ~/lean4checker/.lake/build/bin/lean4checker --fresh GDTBench.SolutionRef` | Exit code 0 |

The two kernel replays emitted no error output in the reported terminal transcript.
This verifies the **reference proof artifact**, not a generated DeepSeek proof or
an improvement in proof-search performance.

## Remaining gates

1. Independently inspect exact command/toolchain revisions if producing a formal
   public verification certificate.
2. Complete a handful-of-outputs inference interface smoke test before a 512-attempt
   pilot; do not count it as a confirmatory measurement.
3. Pin the GPU host, driver, runtime, model revision, and measurement availability.
4. Preserve the Stage 001c pre-registration. Record any prompt/extraction changes
   made after observing outputs as dated amendments and keep smoke-test outcomes separate.
