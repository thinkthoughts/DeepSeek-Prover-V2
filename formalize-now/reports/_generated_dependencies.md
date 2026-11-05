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
