| Edit | Declaration | Port line | Error class | Change |
|---|---|---|---|---|
| E01 | `prod_primes_squarefree` | 103 | `Finset.induction` case arity | `\| insert a s ha ih =>` → `\| @insert a s ha ih =>` |
| E02 | `gdt_empty` | 45 | renamed lemma | `Finset.eq_empty_iff_forall_notMem.mpr` → `Finset.eq_empty_iff_forall_not_mem.mpr` |
| E03 | `exists_repr_mod_R` | 459 | `exact_mod_cast` (missing `norm_cast` attribute) | `exact_mod_cast hnm` → `exact Int.natCast_modEq_iff.mpr hnm` |
| E04 | `repr_unique` | 478 | `exact_mod_cast` (missing `norm_cast` attribute) | `exact_mod_cast h` → `exact Int.natCast_modEq_iff.mp h` |
| E05 | `exists_accepted` | 517 | `exact_mod_cast` (missing `norm_cast` attribute) | `exact_mod_cast hk1` → `exact Int.natCast_modEq_iff.mpr hk1` |
| E06 | `exists_coprime_R_neg_t_mod_p` | 664 | `exact_mod_cast` (missing `norm_cast` attribute) | `by exact_mod_cast hr_modeq_rp` → `by exact Int.natCast_modEq_iff.mpr hr_modeq_rp` |
| E07 | `gdt_minimal_period` | 734 | `exact_mod_cast` (missing `norm_cast` attribute) | `exact_mod_cast hn1_modp_nat` → `exact Int.natCast_modEq_iff.mpr hn1_modp_nat` |
| E08 | `S_eq_filter_Ico` | 845 | simp residue | `simp only [Finset.mem_filter, Finset.mem_Icc, Finset.mem_Ico] ⏎   simp` → `simp only [Finset.mem_filter, Finset.mem_Icc, Finset.mem_Ico] ⏎   simp ⏎   intro _ _ ⏎   omega` |
| E09 | `gdt_density` | 864 | `omega` with cast-product atom | `(by omega) (by omega)]` → `(Nat.le_add_left 1 _) (Nat.add_le_add_right (Nat.le_add_right _ _) 1)]` |
