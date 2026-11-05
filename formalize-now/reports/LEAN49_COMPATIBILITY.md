# Lean 4.9 compatibility report

**Result.** Every GDT definition and statement translates to the model's Lean 4.9
environment with header-only edits and elaborates without error. Of the unchanged human
proofs, 19 of 39 are kernel-clean under Lean 4.9. Nine fail with errors that fall into
five classes, and 11 more inherit `sorryAx` from those nine.

## 1. Environment comparison

| Item | Original GDT | DeepSeek V1.5/V2 harness | Benchmark environment used here |
|---|---|---|---|
| Lean | 4.34.0-rc2 | 4.9.0-rc1 (`lean-toolchain` of fork `xinhjBrant/mathlib4@2f65ba7f`) | 4.9.0-rc1 |
| Mathlib | `85e3a25` (v4.34.0-rc2) | fork `2f65ba7f` ("align", 2024-08-07) | upstream `d1d1e4b7` (2024-06-12), the fork's parent |
| Mathlib sources vs fork | — | — | identical: `git diff d1d1e4b7 2f65ba7f -- Mathlib Mathlib.lean` is empty |
| Batteries | per Mathlib v4.34 | `42b5ddd` | `f96a344`; one commit apart, a linter-frontend fix (`Batteries/Tactic/Lint/Frontend.lean`) |
| Module system | yes (`module`, `public import`, `@[expose]`) | absent | absent |
| Prompt header | — | `import Mathlib`, `import Aesop`, `maxHeartbeats 0`, `open BigOperators Real Nat Topology Rat` (`prover/utils.py`) | same, tested in §3 |
| Completeness check | Comparator + axiom whitelist | REPL messages: no errors, no `sorries`, no warning containing `declaration uses 'sorry'` or `failed` (`prover/lean/verifier.py:53`) | REPL-equivalent compile + `#print axioms` |

Notes:

- The paper states Lean 4.9.0-**rc2**, and the pinned fork toolchain is 4.9.0-**rc1**.
  Stage 0 follows the pinned file. Asking upstream which version was used is a candidate
  issue.
- The fork's own Mathlib cache was unavailable: the first ~1,900 of 4,650 requests
  downloaded 0 files, and the attempt was stopped. The fork changes only
  `lakefile.lean` (adds REPL, `pp.proofs.withType false`, CI-only options) and the
  manifest, which alters every cache hash. Upstream `d1d1e4b7` downloaded completely
  (4,650 files in 61 s). It provides the same Mathlib sources at the cost of the one
  Batteries linter commit above.
- `lean49/lakefile.lean` pins upstream `d1d1e4b7`. `lake update && lake exe cache get &&
  lake build` reproduces the GDTBench build in 85 s, including package clones
  (`logs/lean49_lake_build*.log`).
- The V1.5 `complete` flag matches the Lean 4.9 sorry message text with straight quotes.
  Lean 4.34 prints `` declaration uses `sorry` `` with backticks, so that check would
  silently pass sorry-using proofs if the harness were moved to a current toolchain. The
  benchmark keeps 4.9 and adds an axiom check, which closes both gaps.

## 2. Translation

Four mechanical rules plus the ladder rule; 14 line edits in total, each logged with file,
line, before and after in `manifest/translation_log.json`:

| Rule | Edit | Lines |
|---|---|---|
| T1 | delete `module` | 3 |
| T2 | `public import X` → `import X` | 5 |
| T3 | delete `@[expose] public section` | 3 |
| T4 | `import GeneralDivisorTheorem.Basic` → `import GDTBench.Defs` | 2 |
| L1 | ladder: helper-lemma signature verbatim, proof → `sorry` | 32 items |

Lean 4.9 lacks the module system, so `@[expose]` disappears. In 4.34 it makes definition
bodies visible to importers; in 4.9 every importer already sees every body. The
translated definitions therefore keep their bodies verbatim, and unfolding behaves as in
the original. Statement, definition and proof text is otherwise copied byte for byte.

## 3. Elaboration results (Lean 4.9.0-rc1)

| File | Errors | `sorry` warnings | Wall / peak RSS |
|---|---|---|---|
| `GDTBench/Defs.lean` | 0 | 0 | 2.0 s / 1.19 GB |
| `GDTBench/Challenge.lean` (7 statements) | 0 | 7 | 1.5 s / 1.23 GB |
| `GDTBench/Ladder.lean` (32 statements) | 0 | 32 | 1.5 s / 1.26 GB |
| `benchmark/AllItemsCheck.lean` (39 items, V1.5 header, `import Mathlib`) | 0 | 39 | 6.7 s / 3.55 GB |
| `GDTBench/SolutionPort.lean` (unchanged proofs) | 14 in 9 declarations | 0 | 3.6 s / 1.31 GB |

The 3.55 GB peak for `import Mathlib` sits close to the 3.8 GiB VPS limit. Benchmark
checking belongs on the MacBook or a ≥ 8 GB machine.

## 4. Mathematical correspondence (statements)

For each of the 48 declarations, `tools/StatementSurface.append.lean` prints the
elaborated type and the non-GDT constants in it, in both versions.

- **Non-instance constants:** identical for all 48 declarations (`Nat.primeFactors`,
  `Nat.totient`, `Int.ModEq`, `Finset.filter`, `Finset.Ico`, `Nat.gcd`, `Nat.Coprime`,
  `Squarefree`, `Nat.factorization`, …).
- **Instance paths:** 11 declarations reach the same classes through differently named
  instances, e.g. `Nat.instPreorder` vs `PartialOrder.toPreorder ∘
  StrictOrderedSemiring.toPartialOrder`, or `Finset.instMembership` vs `SetLike` membership.
- **Decidability instance:** one case, `canonical_window_card_eq_range_coprime`, uses a
  different `Decidable (Nat.Coprime …)` instance (`Nat.instDecidableCoprime` vs
  `…_mathlib`) inside `Finset.filter`. `Decidable` is a subsingleton, so the filtered sets
  are equal, though the terms differ syntactically.
- **Pretty-printing only:** 6 declarations print differently: `Nat.Prime p` vs `p.Prime`,
  and set-builder vs `Finset.filter` notation.
- **Header effect:** under the V1.5 header, the elaborated constants of all 39 items equal
  those of the header-free build. The only change is notation: `open Nat` prints
  `Nat.totient n` as `φ n`.

Status: name-level and elaboration-level agreement is established. Definitional identity
of the shared Mathlib constants across the two versions (e.g. the definition bodies of
`Nat.primeFactors` and `Nat.totient`) remains **provisional**. These are standard
definitions with stable meanings; RPI-DS-001b can check them mechanically (see the
recommendation).

## 5. Unchanged human proofs under Lean 4.9

`SolutionPort.lean` compiles the original proofs, unchanged, as a probe. A declaration
counts as `kernel_clean` only when it has no error and `#print axioms` shows no
`sorryAx` (`logs/lean49_axiom_probe.log`).

Error classes among the 9 direct failures:

| Class | Declarations | Nature |
|---|---|---|
| `mod_cast` / `exact_mod_cast` result type differs | `exists_repr_mod_R`, `repr_unique`, `exists_accepted`, `exists_coprime_R_neg_t_mod_p`, `gdt_minimal_period` | cast-normalisation behaviour changed between versions |
| renamed lemma | `gdt_empty` (`Finset.eq_empty_iff_forall_notMem`, 2024 name `…_not_mem`) | Mathlib API rename |
| `Finset.induction` case arity | `prod_primes_squarefree` | eliminator signature changed |
| `omega` incomplete | `gdt_density` | `omega` capability differs |
| `unsolved goals` after simp/rw | `S_eq_filter_Ico` | simp-set / lemma-form drift |

Kernel-clean in Lean 4.9: 19, including challenge theorem `gdt_periodic`. The 11
inherited failures trace through kernel dependencies to the 9 direct failures. For
example, `rad_squarefree` depends on `prod_primes_squarefree`.

These results bear on Stage 1 in two ways. First, every statement is provable in
principle, since the mathematics is unchanged. Second, the human proofs supply a
ground-truth reference in the benchmark environment for 19 items today. The other 20
need a proof port (RPI-DS-001b) before "unprovable in 2024 Mathlib" can be ruled out as a
cause of model failure.

## 6. Table: proof status (generated)

Counts: {"kernel_clean": 19, "inherits_sorryAx": 11, "direct_error": 9}

| Declaration | Role | Lean 4.9 status of the unchanged proof | First error |
|---|---|---|---|
| `R_pos` | helper_lemma | kernel_clean | — |
| `accepted_iff_coprime_R` | helper_lemma | kernel_clean | — |
| `card_filter_Ico_split` | helper_lemma | kernel_clean | — |
| `coprime_add_mul_right` | helper_lemma | kernel_clean | — |
| `coprime_iff_coprime_rad` | helper_lemma | kernel_clean | — |
| `coprime_of_modEq_natAbs` | helper_lemma | kernel_clean | — |
| `d_dvd_rad` | helper_lemma | kernel_clean | — |
| `d_mul_R_eq_rad` | helper_lemma | kernel_clean | — |
| `gcd_mod_eq` | helper_lemma | kernel_clean | — |
| `gcd_with_N_iff_gcd_with_R` | helper_lemma | kernel_clean | — |
| `gdt_periodic` | challenge_theorem | kernel_clean | — |
| `periodic_window_card_eq` | helper_lemma | kernel_clean | — |
| `primeFactors_forall_dvd_imp_dvd` | helper_lemma | kernel_clean | — |
| `prime_coprime_prod` | helper_lemma | kernel_clean | — |
| `rad_dvd_self` | helper_lemma | kernel_clean | — |
| `rad_eq_self_of_squarefree` | helper_lemma | kernel_clean | — |
| `rad_pos` | helper_lemma | kernel_clean | — |
| `squarefree_prime_dvd_split` | helper_lemma | kernel_clean | — |
| `totient_rad_mul` | helper_lemma | kernel_clean | — |
| `R_squarefree` | helper_lemma | inherits_sorryAx | — |
| `canonical_window_card_eq_range_coprime` | helper_lemma | inherits_sorryAx | — |
| `coprime_d_R` | helper_lemma | inherits_sorryAx | — |
| `coprime_m_R` | helper_lemma | inherits_sorryAx | — |
| `count_canonical_period` | helper_lemma | inherits_sorryAx | — |
| `exists_witness_avoiding_dvd` | helper_lemma | inherits_sorryAx | — |
| `gdt_correction_factor` | challenge_theorem | inherits_sorryAx | — |
| `gdt_count_per_period` | challenge_theorem | inherits_sorryAx | — |
| `general_divisor_theorem` | challenge_theorem | inherits_sorryAx | — |
| `rad_factorization_eq_one` | helper_lemma | inherits_sorryAx | — |
| `rad_squarefree` | helper_lemma | inherits_sorryAx | — |
| `S_eq_filter_Ico` | helper_lemma | direct_error | unsolved goals |
| `exists_accepted` | helper_lemma | direct_error | mod_cast has type |
| `exists_coprime_R_neg_t_mod_p` | helper_lemma | direct_error | mod_cast has type |
| `exists_repr_mod_R` | helper_lemma | direct_error | mod_cast has type |
| `gdt_density` | challenge_theorem | direct_error | omega could not prove the goal: |
| `gdt_empty` | challenge_theorem | direct_error | unknown constant 'Finset.eq_empty_iff_forall_notMem.mpr' |
| `gdt_minimal_period` | challenge_theorem | direct_error | mod_cast has type |
| `prod_primes_squarefree` | helper_lemma | direct_error | too many variable names provided at alternative 'insert', #4 provided, but #2 expected |
| `repr_unique` | helper_lemma | direct_error | mod_cast has type |

## 7. Table: statement surface (generated)

| Declaration | pp 4.34 = pp 4.9 | non-instance constants equal | instance-path differences | item (V1.5 header) constants = translated |
|---|---|---|---|---|
| `Admissible` | True | True | — | True |
| `R_pos` | True | True | — | True |
| `R_squarefree` | True | True | — | True |
| `S_eq_filter_Ico` | True | True | Nat.instPreorder, Nat.instStrictOrderedSemiring, PartialOrder.toPreorder, StrictOrderedSemiring.toPartialOrder | True |
| `accepted_iff_coprime_R` | True | True | — | True |
| `canonical_window_card_eq_range_coprime` | False | True | Nat.instDecidableCoprime, Nat.instDecidableCoprime_mathlib, Nat.instPreorder, Nat.instStrictOrderedSemiring, PartialOrder.toPreorder, StrictOrderedSemiring.toPartialOrder | True |
| `card_filter_Ico_split` | True | True | Nat.instPreorder, Nat.instStrictOrderedSemiring, PartialOrder.toPreorder, StrictOrderedSemiring.toPartialOrder | True |
| `coprime_add_mul_right` | True | True | — | True |
| `coprime_d_R` | True | True | — | True |
| `coprime_iff_coprime_rad` | True | True | — | True |
| `coprime_m_R` | True | True | — | True |
| `coprime_of_modEq_natAbs` | True | True | — | True |
| `count_canonical_period` | True | True | Nat.instPreorder, Nat.instStrictOrderedSemiring, PartialOrder.toPreorder, StrictOrderedSemiring.toPartialOrder | True |
| `d_dvd_rad` | True | True | — | True |
| `d_mul_R_eq_rad` | True | True | — | True |
| `exists_accepted` | True | True | — | True |
| `exists_coprime_R_neg_t_mod_p` | False | True | — | True |
| `exists_repr_mod_R` | True | True | — | True |
| `exists_witness_avoiding_dvd` | False | True | — | True |
| `gcd_mod_eq` | True | True | — | True |
| `gcd_with_N_iff_gcd_with_R` | True | True | — | True |
| `gdt_correction_factor` | True | True | — | True |
| `gdt_count_per_period` | True | True | Nat.instPreorder, Nat.instStrictOrderedSemiring, PartialOrder.toPreorder, StrictOrderedSemiring.toPartialOrder | True |
| `gdt_density` | True | True | — | True |
| `gdt_empty` | True | True | — | True |
| `gdt_minimal_period` | True | True | — | True |
| `gdt_periodic` | True | True | — | True |
| `general_divisor_theorem` | True | True | Nat.instPreorder, Nat.instStrictOrderedSemiring, PartialOrder.toPreorder, StrictOrderedSemiring.toPartialOrder | True |
| `periodic_window_card_eq` | True | True | Nat.instPreorder, Nat.instStrictOrderedSemiring, PartialOrder.toPreorder, StrictOrderedSemiring.toPartialOrder | True |
| `primeFactors_forall_dvd_imp_dvd` | True | True | Finset.instMembership, Finset.instSetLike, SetLike.instMembership | True |
| `prime_coprime_prod` | False | True | Finset.instMembership, Finset.instSetLike, SetLike.instMembership | True |
| `prod_primes_squarefree` | False | True | Finset.instMembership, Finset.instSetLike, SetLike.instMembership | True |
| `rad_dvd_self` | True | True | — | True |
| `rad_eq_self_of_squarefree` | True | True | — | True |
| `rad_factorization_eq_one` | True | True | Finset.instMembership, Finset.instSetLike, LinearOrderedCommMonoidWithZero.toZero, MulZeroClass.toZero, Nat.instLinearOrderedCommMonoidWithZero, Nat.instMulZeroClass, SetLike.instMembership | True |
| `rad_pos` | True | True | — | True |
| `rad_squarefree` | True | True | — | True |
| `repr_unique` | True | True | — | True |
| `squarefree_prime_dvd_split` | False | True | — | True |
| `totient_rad_mul` | True | True | — | True |
| `IsPeriod` | True | True | — | True |
| `R` | True | True | — | True |
| `S` | True | True | — | True |
| `Tmin` | True | True | — | True |
| `accepted` | True | True | — | True |
| `acceptedDecidable` | True | True | — | True |
| `d` | True | True | — | True |
| `rad` | True | True | — | True |
