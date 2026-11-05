import Lake
open Lake DSL

/-
RPI-DS-001a Lean 4.9 benchmark environment.
Mathlib is pinned to upstream commit d1d1e4b72 (2024-06-12): the parent of
DeepSeek's fork commit xinhjBrant/mathlib4@2f65ba7f, whose `Mathlib/` sources are
byte-identical to it (only lakefile/manifest differ). Upstream is used because
its build cache is downloadable; see reports/LEAN49_COMPATIBILITY.md.
-/
package gdtbench where
  leanOptions := #[⟨`autoImplicit, false⟩, ⟨`relaxedAutoImplicit, false⟩]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4" @ "d1d1e4b72c6e009edd97cabe1d661b021fe8eeae"

@[default_target]
lean_lib GDTBench where
  roots := #[`GDTBench.Defs, `GDTBench.Challenge, `GDTBench.Ladder,
    `GDTBench.SolutionRef, `GDTBench.Expected]
