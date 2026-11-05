# Verified dependency report — GDT at `ec66260` (Lean 4.34.0-rc2)

**Result.** All 48 GDT declarations have kernel-level dependency records, taken from
proof terms the Lean kernel accepted. The manifest gives the complete *direct* GDT-to-GDT
dependency graph at kernel level. Mathlib-level dependencies are counted per
declaration and left unlisted (§4).

## 1. Method

`tools/run_extract.sh` concatenates the unmodified `Solution/GeneralDivisorTheorem.lean`
with `tools/ExtractDeps.append.lean` into a temporary file under the GDT repository's
`.lake/`. The script asserts with `cmp` that the prefix is byte-identical to the source.
It then elaborates the file with `lake env lean -DElab.async=false` and deletes it. For
each GDT constant it reads the `ConstantInfo` and records:

- the GDT constants in the type and in the value, following compiler-generated
  auxiliaries (`_proof_n`, `match_n`, …) of the same file transitively;
- the result of `Lean.collectAxioms`;
- a structural hash and the pretty-printed form of the type.

The same appendix runs on the Challenge file. `tools/build_manifest.py` then adds
syntactic references (identifier matches in comment-stripped source) and stores both
notions side by side.

Why concatenation: importing `Solution.GeneralDivisorTheorem` through the module system
exposed theorem *types* but no theorem *values* to the extractor (`has_value: false` for
all 39 theorems, also with `import all`). Elaborating the source text in the same process
gives the values that the kernel checked.

## 2. Findings

- **Inventory:** 9 definitions (`rad`, `d`, `R`, `Tmin`, `Admissible`, `accepted`,
  `acceptedDecidable`, `S`, `IsPeriod`), 7 challenge theorems, 32 helper lemmas.
- **Axioms:** every theorem uses {`propext`, `Quot.sound`, `Classical.choice`}, and
  `gcd_mod_eq` uses {`propext`, `Quot.sound`}. Neither `sorryAx` nor any further axiom
  appears. This matches the GDT Comparator whitelist.
- **Challenge = Solution statements:** for all 7 challenge theorems, the elaborated type
  in the Challenge file and in the Solution file share the structural hash and the
  pretty-printed form. The 9 definitions also agree. This partially stands in for the
  Comparator run, which was unavailable here (see BUILD_AND_VERIFICATION.md).
- **Packaging:** `general_divisor_theorem` depends at kernel level on `gdt_empty`,
  `gdt_periodic`, `gdt_minimal_period`, `gdt_count_per_period` and `gdt_correction_factor`.
  `gdt_density` is a separate theorem outside the package; this confirms the review's
  finding F.
- **Lemmas outside every challenge theorem's closure:** `exists_witness_avoiding_dvd` and
  `rad_factorization_eq_one` are proved, and no challenge theorem reaches them
  transitively. They stay in the ladder as items, flagged `reachable_from_challenge: false`
  in RPI-DS-001b.
- **Ladder depth:** transitive GDT lemma dependencies per challenge theorem:

  | Theorem | Direct GDT lemma deps | Transitive |
  |---|---|---|
  | gdt_empty | 0 | 0 |
  | gdt_periodic | 2 | 7 |
  | gdt_correction_factor | 3 | 8 |
  | gdt_minimal_period | 10 | 21 |
  | gdt_count_per_period | 3 | 22 |
  | gdt_density | 3 | 25 |
  | general_divisor_theorem | 5 | 33 |

## 3. Kernel dependencies versus syntactic references

Ten declarations differ between the two notions. Every case comes from the matcher, and
none from a dependency error:

- *Kernel-only `acceptedDecidable`* (8 declarations): the `DecidablePred` instance enters
  the term through instance resolution, and the source never names it.
- *Kernel-only `d`, `rad` in `R_pos`*: arise from unfolding `R` inside the proof.
- *Syntactic-only `R` in `gcd_mod_eq`*: `R` there is a bound variable `(n R : ℕ)`, so the
  text match is a false positive.

This is the concrete reason the manifest keeps kernel dependencies as the authoritative
field.

## 4. Established and provisional

- Established: the direct GDT→GDT kernel graph (48 nodes), per-declaration axioms, and
  Challenge/Solution statement agreement in Lean 4.34.
- Provisional: Mathlib-level dependencies, recorded only as a count
  (`mathlib_value_consts`). Proof-local `have` structure lies inside proof terms and is
  outside this inventory.

## 5. Table (generated from `manifest/gdt_manifest.json`)

| Declaration | Role | Line | Kernel deps (GDT) | Syntactic-only | Kernel-only | Axioms |
|---|---|---|---|---|---|---|
| `rad` | definition | GeneralDivisorTheorem:23 | — | — | — | Classical.choice, Quot.sound, propext |
| `d` | definition | GeneralDivisorTheorem:25 | rad | — | — | Classical.choice, Quot.sound, propext |
| `R` | definition | GeneralDivisorTheorem:27 | d, rad | — | — | Classical.choice, Quot.sound, propext |
| `Tmin` | definition | GeneralDivisorTheorem:29 | R | — | — | Classical.choice, Quot.sound, propext |
| `Admissible` | definition | GeneralDivisorTheorem:31 | d | — | — | Classical.choice, Quot.sound, propext |
| `accepted` | definition | GeneralDivisorTheorem:34 | — | — | — | none |
| `acceptedDecidable` | definition | GeneralDivisorTheorem:37 | accepted | — | — | none |
| `S` | definition | GeneralDivisorTheorem:43 | accepted, acceptedDecidable | — | acceptedDecidable | Classical.choice, Quot.sound, propext |
| `IsPeriod` | definition | GeneralDivisorTheorem:46 | accepted | — | — | none |
| `gdt_empty` | challenge_theorem | Solution:25 | Admissible, S, accepted, acceptedDecidable, d, rad | — | acceptedDecidable | Classical.choice, Quot.sound, propext |
| `d_dvd_rad` | helper_lemma | Solution:56 | d, rad | — | — | Classical.choice, Quot.sound, propext |
| `d_mul_R_eq_rad` | helper_lemma | Solution:64 | d_dvd_rad, R, d, rad | — | — | Classical.choice, Quot.sound, propext |
| `prime_coprime_prod` | helper_lemma | Solution:68 | — | — | — | Classical.choice, Quot.sound, propext |
| `prod_primes_squarefree` | helper_lemma | Solution:95 | prime_coprime_prod | — | — | Classical.choice, Quot.sound, propext |
| `rad_squarefree` | helper_lemma | Solution:112 | prod_primes_squarefree, rad | — | — | Classical.choice, Quot.sound, propext |
| `coprime_d_R` | helper_lemma | Solution:117 | d_mul_R_eq_rad, rad_squarefree, R, d, rad | — | — | Classical.choice, Quot.sound, propext |
| `rad_dvd_self` | helper_lemma | Solution:124 | rad | — | — | Classical.choice, Quot.sound, propext |
| `coprime_iff_coprime_rad` | helper_lemma | Solution:129 | rad_dvd_self, rad | — | — | Classical.choice, Quot.sound, propext |
| `coprime_of_modEq_natAbs` | helper_lemma | Solution:166 | — | — | — | Classical.choice, Quot.sound, propext |
| `gcd_with_N_iff_gcd_with_R` | helper_lemma | Solution:187 | Admissible, coprime_iff_coprime_rad, coprime_of_modEq_natAbs, d_mul_R_eq_rad, rad_dvd_self, R, d, rad | — | — | Classical.choice, Quot.sound, propext |
| `coprime_add_mul_right` | helper_lemma | Solution:207 | — | — | — | Classical.choice, Quot.sound, propext |
| `gdt_periodic` | challenge_theorem | Solution:234 | Admissible, coprime_add_mul_right, gcd_with_N_iff_gcd_with_R, IsPeriod, R, Tmin, accepted | — | — | Classical.choice, Quot.sound, propext |
| `periodic_window_card_eq` | helper_lemma | Solution:277 | — | — | — | Classical.choice, Quot.sound, propext |
| `coprime_m_R` | helper_lemma | Solution:348 | coprime_d_R, d_mul_R_eq_rad, rad_dvd_self, R, d, rad | — | — | Classical.choice, Quot.sound, propext |
| `accepted_iff_coprime_R` | helper_lemma | Solution:399 | Admissible, gcd_with_N_iff_gcd_with_R, R, accepted | — | — | Classical.choice, Quot.sound, propext |
| `rad_pos` | helper_lemma | Solution:411 | rad | — | — | Classical.choice, Quot.sound, propext |
| `R_pos` | helper_lemma | Solution:417 | d_mul_R_eq_rad, rad_pos, R, d, rad | — | d, rad | Classical.choice, Quot.sound, propext |
| `exists_repr_mod_R` | helper_lemma | Solution:427 | R_pos, coprime_m_R, R, Tmin | — | — | Classical.choice, Quot.sound, propext |
| `repr_unique` | helper_lemma | Solution:467 | coprime_m_R, R, Tmin | — | — | Classical.choice, Quot.sound, propext |
| `gcd_mod_eq` | helper_lemma | Solution:488 | — | R | — | Quot.sound, propext |
| `exists_accepted` | helper_lemma | Solution:492 | Admissible, R_pos, coprime_m_R, gcd_mod_eq, gcd_with_N_iff_gcd_with_R, R, accepted | — | — | Classical.choice, Quot.sound, propext |
| `primeFactors_forall_dvd_imp_dvd` | helper_lemma | Solution:531 | prime_coprime_prod, rad | — | — | Classical.choice, Quot.sound, propext |
| `exists_witness_avoiding_dvd` | helper_lemma | Solution:576 | Admissible, exists_accepted, gcd_with_N_iff_gcd_with_R, R, accepted | — | — | Classical.choice, Quot.sound, propext |
| `squarefree_prime_dvd_split` | helper_lemma | Solution:591 | — | — | — | Classical.choice, Quot.sound, propext |
| `R_squarefree` | helper_lemma | Solution:604 | d_mul_R_eq_rad, rad_squarefree, R, d, rad | — | — | Classical.choice, Quot.sound, propext |
| `exists_coprime_R_neg_t_mod_p` | helper_lemma | Solution:608 | R_pos, R_squarefree, gcd_mod_eq, squarefree_prime_dvd_split, R | — | — | Classical.choice, Quot.sound, propext |
| `rad_eq_self_of_squarefree` | helper_lemma | Solution:664 | rad | — | — | Classical.choice, Quot.sound, propext |
| `gdt_minimal_period` | challenge_theorem | Solution:669 | Admissible, R_pos, R_squarefree, coprime_m_R, exists_accepted, exists_coprime_R_neg_t_mod_p, exists_repr_mod_R, gcd_mod_eq, gcd_with_N_iff_gcd_with_R, primeFactors_forall_dvd_imp_dvd, rad_eq_self_of_squarefree, IsPeriod, R, Tmin, accepted, rad | — | — | Classical.choice, Quot.sound, propext |
| `canonical_window_card_eq_range_coprime` | helper_lemma | Solution:772 | Admissible, R_pos, exists_repr_mod_R, gcd_mod_eq, repr_unique, R, Tmin | — | — | Classical.choice, Quot.sound, propext |
| `count_canonical_period` | helper_lemma | Solution:799 | Admissible, accepted_iff_coprime_R, canonical_window_card_eq_range_coprime, R, Tmin, accepted, acceptedDecidable | — | acceptedDecidable | Classical.choice, Quot.sound, propext |
| `gdt_count_per_period` | challenge_theorem | Solution:811 | Admissible, count_canonical_period, gdt_periodic, periodic_window_card_eq, R, Tmin, accepted, acceptedDecidable | — | acceptedDecidable | Classical.choice, Quot.sound, propext |
| `card_filter_Ico_split` | helper_lemma | Solution:818 | — | — | — | Classical.choice, Quot.sound, propext |
| `S_eq_filter_Ico` | helper_lemma | Solution:836 | S, accepted, acceptedDecidable | — | acceptedDecidable | Classical.choice, Quot.sound, propext |
| `gdt_density` | challenge_theorem | Solution:845 | Admissible, S_eq_filter_Ico, card_filter_Ico_split, gdt_count_per_period, R, S, Tmin, accepted, acceptedDecidable | — | acceptedDecidable | Classical.choice, Quot.sound, propext |
| `rad_factorization_eq_one` | helper_lemma | Solution:882 | rad_pos, rad_squarefree, rad | — | — | Classical.choice, Quot.sound, propext |
| `totient_rad_mul` | helper_lemma | Solution:902 | rad_pos, rad | — | — | Classical.choice, Quot.sound, propext |
| `gdt_correction_factor` | challenge_theorem | Solution:946 | coprime_d_R, d_mul_R_eq_rad, totient_rad_mul, R, d, rad | — | — | Classical.choice, Quot.sound, propext |
| `general_divisor_theorem` | challenge_theorem | Solution:968 | Admissible, gdt_correction_factor, gdt_count_per_period, gdt_empty, gdt_minimal_period, gdt_periodic, IsPeriod, R, S, Tmin, accepted, acceptedDecidable, d | — | acceptedDecidable | Classical.choice, Quot.sound, propext |
