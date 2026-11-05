# Recommendation — RPI-DS-001b

**Next patch: port the 9 failing human proofs to Lean 4.9, unchanged in statement, and
certify all 39 GDT theorems kernel-clean in the benchmark environment.** CPU only,
estimated at a few hours.

## Why this is the smallest justified step

Stage 1 must be able to tell "the model failed" apart from "the statement is unprovable
with 2024 Mathlib". Today the benchmark environment holds a reference proof for 19 of 39
items. The 20 gaps trace to 9 root failures in five classes, and five of them share one
class (`mod_cast`). Each fix is local to a proof body; the signatures stay fixed.

## Scope

1. Create `lean49/GDTBench/SolutionRef.lean`: a copy of `SolutionPort.lean` with proof-body
   edits only. Log each edit in `manifest/proof_port_log.json` (declaration, error class,
   before/after, reason). A script checks that every signature still matches `Ladder.lean`
   / `Challenge.lean` byte for byte.
2. Fix in dependency order, roots first: `prod_primes_squarefree` (unlocks `rad_squarefree`
   and its dependants), `gdt_empty`, the five `mod_cast` cases, `S_eq_filter_Ico`,
   `gdt_density`.
3. Acceptance: `lake build` with 0 errors and 0 `sorry`, plus `#print axioms` within the
   whitelist for all 39. Also run lean4checker on the module.
4. Add a mechanical definitional check for the Mathlib constants in the statements:
   pretty-print each constant's definition body (`Nat.primeFactors`, `Nat.totient`,
   `Int.ModEq`, `Finset.filter`, `Finset.Ico`, `Nat.factorization`, `Squarefree`, …) in
   both versions. Record agreement or explain each difference. This moves §4 of the
   compatibility report from provisional toward established.
5. Add `reachable_from_challenge` to the items, using the two unreachable helpers found in
   Stage 0, and add the harness patch: an axiom gate plus an apply?/sorry/admit token scan
   wrapped around the V1.5 `verify_lean4_file`. Unit-test it with the two-grandmothers
   pair, with and without the distinctness hypothesis.

## Expected outcomes

- **Best case:** 39/39 reference proofs, a fully certified benchmark, and Stage 1's GPU
  gate reduced to hardware access.
- **Partial:** a few proofs resist porting. Those items get the label
  `reference_proof: absent_in_lean49` and stay in the benchmark with that caveat; the
  statements stay as they are.
- **Byproduct:** the error-class log is itself a small Lean/Mathlib drift study
  (`omega`, `mod_cast`, induction eliminators). It feeds your lean-readingpoint work.

## Defer

The exact DeepSeek environment build (fork + Batteries `42b5ddd`), GPU sampling, and
Stage 2 decomposers.
