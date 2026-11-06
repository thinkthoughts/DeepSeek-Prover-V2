# Cauto — CPU-only tactic baseline (RPI-DS-001c)

**Result.** Tactics alone certify 2 of the 39 items, both helper lemmas:

- `coprime_add_mul_right`, solved by 7 of the 10 scripts, including plain `simp`;
- `S_eq_filter_Ico`, solved by `aesop` and by `norm_num [defs] <;> aesop`.

None of the 7 challenge theorems falls to automation. The other 30 helper lemmas also
resist all ten scripts. Every attempt finished within its heartbeat budget, so no run
timed out.

## Setup

- `baseline/cauto.py` runs 10 tactic scripts over all 39 statements, taken verbatim from
  `benchmark/gdt_items_v2.jsonl`. No reference proof text is used.
- Each declaration runs under `set_option maxHeartbeats 200000 in`; the V1.5 header sets 0,
  meaning unlimited.
- Each script is one Lean file of 39 declarations. Per-declaration time comes from
  `IO.monoMsNow` stamps between declarations.
- Every compiling candidate was then re-verified alone by `harness/verify_strict.py` with
  kernel replay. Only `certified` counts.
- `exact?` and `apply?` are excluded. They are library-search commands, and their Lean 4.9
  front end has the documented sorry-suppression bug.

Scripts:

- `simp`
- `simp_all`
- `omega`
- `norm_num`
- `decide`
- `aesop`
- `linarith`
- `simp_all [defs]`
- `intros; simp_all [defs] <;> omega`
- `norm_num [defs] <;> aesop`

Here `defs` = `GDT.rad, GDT.d, GDT.R, GDT.Tmin, GDT.Admissible, GDT.accepted, GDT.S,
GDT.IsPeriod`.

## Cost

| Script | File wall (s) | Σ per-declaration (ms) |
|---|---|---|
| simp | 4.3 | 1,484 |
| simp_all | 5.0 | 2,261 |
| omega | 3.4 | 754 |
| norm_num | 4.5 | 1,764 |
| decide | 3.4 | 667 |
| aesop | 8.0 | 5,300 |
| linarith | 4.9 | 2,175 |
| simp_all [defs] | 10.6 | 7,810 |
| intros; simp_all [defs] <;> omega | 10.7 | 7,865 |
| norm_num [defs] <;> aesop | 17.5 | 14,568 |

File wall time includes about 2.5 s of `import Mathlib`. The whole run, including the 9
strict re-verifications, took 1 min 52 s on 2 vCPU. The slowest single declaration was
`general_divisor_theorem` under `norm_num [defs] <;> aesop`, at 4.4 s before failing.

## Failure modes (381 failed item × script attempts of 390; the other 9 compiled and were certified)

| First error | Count |
|---|---|
| `simp` / `norm_num` / `aesop` made no progress | 134 |
| unsolved goals after simplification | 98 |
| `omega` could not prove the goal | 71 |
| `decide`: statement contains free variables | 39 |
| `linarith` failed | 37 |
| instance synthesis | 2 |

## Interpretation for Stage 1

- **Proof-search challenges:** all 7 challenge theorems and 30 of the 32 lemmas need
  mathematical reasoning beyond these scripts. The GDT definitions (`rad`, `R`, `Tmin`,
  `Admissible`) carry content that unfolding plus automation fails to reach.
- **Automation-level:** `coprime_add_mul_right` and `S_eq_filter_Ico`. Per the
  pre-registration, theorem-level results are reported with and without these two.
- `gdt_empty` has no lemma dependencies, so C0 and C2 coincide for it; it also resists
  every script. It therefore measures direct proving ability on new definitions, with no
  decomposition effect possible.

## Per-item table

✔ = certified by the strict verifier with kernel replay; · = failed. No timeouts occurred.

| Item | Role | simp | simp_all | omega | norm_num | decide | aesop | linarith | simp_all_defs | intros_simp_all_defs_omega | norm_num_defs_aesop | Slowest (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `gdt_empty` | challenge theorem | · | · | · | · | · | · | · | · | · | · | 2811 |
| `gdt_periodic` | challenge theorem | · | · | · | · | · | · | · | · | · | · | 855 |
| `gdt_minimal_period` | challenge theorem | · | · | · | · | · | · | · | · | · | · | 325 |
| `gdt_count_per_period` | challenge theorem | · | · | · | · | · | · | · | · | · | · | 277 |
| `gdt_density` | challenge theorem | · | · | · | · | · | · | · | · | · | · | 347 |
| `gdt_correction_factor` | challenge theorem | · | · | · | · | · | · | · | · | · | · | 163 |
| `general_divisor_theorem` | challenge theorem | · | · | · | · | · | · | · | · | · | · | 4411 |
| `d_dvd_rad` | helper lemma | · | · | · | · | · | · | · | · | · | · | 124 |
| `d_mul_R_eq_rad` | helper lemma | · | · | · | · | · | · | · | · | · | · | 119 |
| `prime_coprime_prod` | helper lemma | · | · | · | · | · | · | · | · | · | · | 62 |
| `prod_primes_squarefree` | helper lemma | · | · | · | · | · | · | · | · | · | · | 110 |
| `rad_squarefree` | helper lemma | · | · | · | · | · | · | · | · | · | · | 143 |
| `coprime_d_R` | helper lemma | · | · | · | · | · | · | · | · | · | · | 84 |
| `rad_dvd_self` | helper lemma | · | · | · | · | · | · | · | · | · | · | 91 |
| `coprime_iff_coprime_rad` | helper lemma | · | · | · | · | · | · | · | · | · | · | 115 |
| `coprime_of_modEq_natAbs` | helper lemma | · | · | · | · | · | · | · | · | · | · | 60 |
| `gcd_with_N_iff_gcd_with_R` | helper lemma | · | · | · | · | · | · | · | · | · | · | 170 |
| `coprime_add_mul_right` | helper lemma | ✔ certified | ✔ certified | · | ✔ certified | · | ✔ certified | · | ✔ certified | ✔ certified | ✔ certified | 30 |
| `periodic_window_card_eq` | helper lemma | · | · | · | · | · | · | · | · | · | · | 156 |
| `coprime_m_R` | helper lemma | · | · | · | · | · | · | · | · | · | · | 81 |
| `accepted_iff_coprime_R` | helper lemma | · | · | · | · | · | · | · | · | · | · | 218 |
| `rad_pos` | helper lemma | · | · | · | · | · | · | · | · | · | · | 284 |
| `R_pos` | helper lemma | · | · | · | · | · | · | · | · | · | · | 92 |
| `exists_repr_mod_R` | helper lemma | · | · | · | · | · | · | · | · | · | · | 316 |
| `repr_unique` | helper lemma | · | · | · | · | · | · | · | · | · | · | 221 |
| `gcd_mod_eq` | helper lemma | · | · | · | · | · | · | · | · | · | · | 52 |
| `exists_accepted` | helper lemma | · | · | · | · | · | · | · | · | · | · | 142 |
| `primeFactors_forall_dvd_imp_dvd` | helper lemma | · | · | · | · | · | · | · | · | · | · | 649 |
| `exists_witness_avoiding_dvd` | helper lemma | · | · | · | · | · | · | · | · | · | · | 308 |
| `squarefree_prime_dvd_split` | helper lemma | · | · | · | · | · | · | · | · | · | · | 143 |
| `R_squarefree` | helper lemma | · | · | · | · | · | · | · | · | · | · | 226 |
| `exists_coprime_R_neg_t_mod_p` | helper lemma | · | · | · | · | · | · | · | · | · | · | 559 |
| `rad_eq_self_of_squarefree` | helper lemma | · | · | · | · | · | · | · | · | · | · | 73 |
| `canonical_window_card_eq_range_coprime` | helper lemma | · | · | · | · | · | · | · | · | · | · | 344 |
| `count_canonical_period` | helper lemma | · | · | · | · | · | · | · | · | · | · | 180 |
| `card_filter_Ico_split` | helper lemma | · | · | · | · | · | · | · | · | · | · | 109 |
| `S_eq_filter_Ico` | helper lemma | · | · | · | · | · | ✔ certified | · | · | · | ✔ certified | 117 |
| `rad_factorization_eq_one` | helper lemma | · | · | · | · | · | · | · | · | · | · | 267 |
| `totient_rad_mul` | helper lemma | · | · | · | · | · | · | · | · | · | · | 113 |
