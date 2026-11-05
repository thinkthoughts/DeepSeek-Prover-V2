# Lean 4.9 definition correspondence — RPI-DS-001b

**Result.** Every Mathlib definition that occurs in the GDT statements has the same
mathematical content in Lean 4.34 (Mathlib v4.34.0-rc2) and Lean 4.9 (Mathlib
`d1d1e4b7`), so the translated statements have their original mathematical meaning.
The probe inspected 44 names (26 definitions and 18 characterising lemmas):

- 21 print identically;
- 8 differ only in display;
- 10 differ in printed form through a rename, a compiled-form change of the same
  recursion, or binder names (§3);
- 5 exist in one version or neither: the `factors`/`primeFactorsList` rename, one
  lemma name present only in 4.9, and two instance names probed that exist in neither.

One caveat: the agreement is established at the printed-definition and
characterising-lemma level, and a kernel-identity comparison across versions is out of
reach.

## 1. Method

`tools/MathlibDefs.lean` is elaborated in each environment. For each listed constant it
prints the kind, the type, the definition body (`ppExpr`) and the constants the body
uses; for each characterising theorem it prints the statement. `tools/make_defs_report.py`
classifies:

- **A:** type and body print identically.
- **B:** identical after normalising display only: `[inst : C]` vs `[C]`, `Nat.Prime p` vs
  `p.Prime`, set-builder vs `Finset.filter`.
- **C:** differs in printed form; each case is explained in §3.

Two kinds of agreement are kept apart:

- **Definitional agreement (printed):** the same definition text over the same named
  constants. This is strong evidence, and it stops short of a proof, because the named
  constants could themselves differ deeper down.
- **Mathematical equivalence:** the characterising lemmas each Mathlib version *proves*
  about the constant (e.g. `Nat.mem_primeFactors`, `Finset.mem_Ico`) have the same
  statements. Each version's kernel has checked its own lemma, so the meaning the GDT
  proofs rely on is established within each version.

## 2. GDT-relevant constants

| Constant | Agreement | Characterising lemma (same statement in both versions) |
|---|---|---|
| `Int.ModEq` | A: `a % n = b % n` | `Int.modEq_iff_dvd`, `Int.emod_emod_of_dvd`, `Int.natCast_modEq_iff`: A |
| `Nat.ModEq`, `Nat.Coprime`, `Nat.gcd`, `Int.natAbs`, `Nat.Prime`, `Dvd.dvd`, `Int.emod`, `Finset.range` | A | `Nat.coprime_iff_gcd_eq_one`, `Int.natAbs_dvd_natAbs`, `Finset.mem_range`, `Finset.card_range`: A |
| `Squarefree` | B: `∀ x, x * x ∣ r → IsUnit x` | `Nat.squarefree_iff_prime_squarefree`: B |
| `Finset.Ico`, `Finset.Icc`, `Finset.filter` | B | `Finset.mem_Ico`, `Finset.mem_Icc`, `Finset.mem_filter`: A |
| `Nat.totient` | B (set-builder vs `Finset.filter`): `#{a ∈ range n ∣ n.Coprime a}` | `Nat.totient_eq_card_coprime`: B |
| `Nat.factorization` | B: support `n.primeFactors`, value `padicValNat p n` at primes | `Nat.factorization_def`: B |
| `Nat.primeFactors` | C-rename: `n.factors.toFinset` (4.9) vs `n.primeFactorsList.toFinset` (4.34) | `Nat.mem_primeFactors : p ∈ n.primeFactors ↔ p.Prime ∧ p ∣ n ∧ n ≠ 0`: B |
| `Finset.card`, `Finset.prod` | C-display: `Multiset.card s.val` vs `s.val.card`; binder names `α β` vs `ι M` | `Finset.prod_insert`: same statement up to binder and universe names |
| `Nat.instLocallyFiniteOrder` | C-display: `Ico a b = List.range' a (b - a)` in both | `Finset.mem_Ico`: A |

## 3. Notes on class C

- **`Nat.primeFactors`:** `Nat.factors` was renamed `Nat.primeFactorsList` (Mathlib, 2024).
  Both are the same recursion: for `k + 2`, emit `m := minFac (k+2)`, then recurse on
  `(k+2)/m`. They differ only in the well-founded-fixpoint wrapper
  (`Nat.factors.proof_1.fix` vs `WellFounded.Nat.fix`).
- **`List.range'`:** 4.9 prints the structural recursion inline; 4.34 refers to a
  compiled auxiliary `List.range'._f`. The defining equations `range' s 0 = []` and
  `range' s (n+1) = s :: range' (s+step) n` are unchanged.
- **`Irreducible`:** one constructor `Irreducible.mk` in both; type parameter renamed `α` → `M`.
- **`Nat.totient_eq_card_coprime`, `Finset.prod_insert`:** display only (notation, binder
  names, order of instance arguments).

## 4. Unresolved correspondence questions

1. **Kernel identity across versions.** It is undefined, since the environments differ.
   The strongest mechanical check would elaborate the 4.34 statement in 4.9 directly;
   Stage 0 already did that for all 48 GDT statements, so the open part is only the
   meaning of the shared Mathlib names, which §2 covers.
2. **Instance paths.** Stage 0 found 11 statements whose instance terms differ, e.g. the
   `Decidable (Nat.Coprime …)` instance inside `Finset.filter` in
   `canonical_window_card_eq_range_coprime`. `Decidable` is a subsingleton, so the
   filtered finsets are equal. That equality is a lemma (`Finset.filter_congr_decidable`)
   rather than syntax.
3. **Mathlib-level dependencies of proofs.** These are counted, not enumerated. They
   matter for proof reuse, not for statement meaning.

## 5. Generated table

| Constant | Kind | Statement/type | Body | Classification |
|---|---|---|---|---|
| `Nat.primeFactors` | def | same | differs | C: differs in printed form; see notes |
| `Nat.totient` | def | same | differs | C: differs in printed form; see notes |
| `Int.ModEq` | def | same | same | A: identical printed type and body |
| `Nat.ModEq` | def | same | same | A: identical printed type and body |
| `Nat.factorization` | def | same | differs | C: differs in printed form; see notes |
| `Squarefree` | def | same up to display | same | B: identical up to display (instance binders, dot/set-builder notation) |
| `Finset.Ico` | def | same up to display | same | B: identical up to display (instance binders, dot/set-builder notation) |
| `Finset.Icc` | def | same up to display | same | B: identical up to display (instance binders, dot/set-builder notation) |
| `Finset.range` | def | same | same | A: identical printed type and body |
| `Finset.filter` | def | same up to display | same | B: identical up to display (instance binders, dot/set-builder notation) |
| `Finset.card` | def | same | differs | C: differs in printed form; see notes |
| `Finset.prod` | def | differs | differs | C: differs in printed form; see notes |
| `Nat.Coprime` | def | same | same | A: identical printed type and body |
| `Nat.gcd` | def | same | same | A: identical printed type and body |
| `Int.natAbs` | def | same | same | A: identical printed type and body |
| `Nat.Prime` | def | same | same | A: identical printed type and body |
| `Irreducible` | inductive | differs | — | C: differs in printed form; see notes |
| `IsUnit` | def | same up to display | same | B: identical up to display (instance binders, dot/set-builder notation) |
| `Dvd.dvd` | def | same | same | A: identical printed type and body |
| `Int.emod` | def | same | same | A: identical printed type and body |
| `Nat.factors` | — | — | — | present in 4.34: False, in 4.9: True |
| `Nat.primeFactorsList` | — | — | — | present in 4.34: True, in 4.9: False |
| `Nat.instLocallyFiniteOrderNat` | — | — | — | present in 4.34: False, in 4.9: False |
| `instLocallyFiniteOrderNat` | — | — | — | present in 4.34: False, in 4.9: False |
| `Nat.instLocallyFiniteOrder` | def | same | differs | C: differs in printed form; see notes |
| `List.range'` | def | same | differs | C: differs in printed form; see notes |
| `Nat.mem_primeFactors` | theorem | same up to display | — | B: identical up to display (instance binders, dot/set-builder notation) |
| `Nat.totient_eq_card_coprime` | theorem | differs | — | C: differs in printed form; see notes |
| `Finset.mem_Ico` | theorem | same | — | A: identical printed type and body |
| `Finset.mem_Icc` | theorem | same | — | A: identical printed type and body |
| `Finset.mem_range` | theorem | same | — | A: identical printed type and body |
| `Finset.mem_filter` | theorem | same | — | A: identical printed type and body |
| `Finset.card_range` | theorem | same | — | A: identical printed type and body |
| `Int.emod_emod_of_dvd` | theorem | same | — | A: identical printed type and body |
| `Int.modEq_iff_dvd` | theorem | same | — | A: identical printed type and body |
| `Int.natCast_modEq_iff` | theorem | same | — | A: identical printed type and body |
| `Nat.factorization_def` | theorem | same up to display | — | B: identical up to display (instance binders, dot/set-builder notation) |
| `Nat.isUnit_iff` | theorem | same | — | A: identical printed type and body |
| `Nat.squarefree_iff_prime_squarefree` | theorem | same up to display | — | B: identical up to display (instance binders, dot/set-builder notation) |
| `Nat.prime_def_lt''` | — | — | — | present in 4.34: False, in 4.9: True |
| `Finset.prod_insert` | theorem | differs | — | C: differs in printed form; see notes |
| `Nat.coprime_iff_gcd_eq_one` | theorem | same | — | A: identical printed type and body |
| `Int.natAbs_dvd_natAbs` | theorem | same | — | A: identical printed type and body |
| `Nat.Coprime.gcd_eq_one` | theorem | same | — | A: identical printed type and body |
