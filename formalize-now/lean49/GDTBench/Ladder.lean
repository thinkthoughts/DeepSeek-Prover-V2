-- RPI-DS-001a GENERATED FILE (ladder statements).
-- Each signature is copied verbatim from the source line cited above it;
-- each proof is replaced by `sorry` (benchmark item, intentionally unproved).
-- Solution sha256: 419c1670799f6cdbddcffa5fb532b5b8c0608d1aadfc0ce2a3fb50f1ea0dba8f
import GDTBench.Defs
import Mathlib.Data.Nat.Squarefree

namespace GDT.Challenge

open GDT

-- source: Solution/GeneralDivisorTheorem.lean:56
lemma d_dvd_rad {N m : ℕ} (hN : 0 < N) : d N m ∣ rad N :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:64
lemma d_mul_R_eq_rad {N m : ℕ} (hN : 0 < N) : d N m * R N m = rad N :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:68
lemma prime_coprime_prod {a : ℕ} (ha : a.Prime) {s : Finset ℕ}
    (hs : ∀ p ∈ s, p.Prime) (ha_not : a ∉ s) :
    Nat.Coprime a (∏ p ∈ s, p) :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:95
lemma prod_primes_squarefree {s : Finset ℕ} (hs : ∀ p ∈ s, p.Prime) :
    Squarefree (∏ p ∈ s, p) :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:112
lemma rad_squarefree (n : ℕ) : Squarefree (rad n) :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:117
lemma coprime_d_R {N m : ℕ} (hN : 0 < N) :
    Nat.Coprime (d N m) (R N m) :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:124
lemma rad_dvd_self (n : ℕ) : rad n ∣ n :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:129
lemma coprime_iff_coprime_rad {k n : ℕ} (hn : n ≠ 0) :
    Nat.Coprime k n ↔ Nat.Coprime k (rad n) :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:166
lemma coprime_of_modEq_natAbs {k : ℕ} {a : ℤ} {e : ℕ}
    (hk : (k : ℤ) ≡ a [ZMOD (e : ℤ)]) (ha : Nat.gcd a.natAbs e = 1) :
    Nat.Coprime k e :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:187
lemma gcd_with_N_iff_gcd_with_R
    {N m k : ℕ} (hN : 0 < N) (_hm : 0 < m) {a : ℤ}
    (ha : Admissible N m a)
    (hk : (k : ℤ) ≡ a [ZMOD (m : ℤ)]) :
    Nat.gcd k N = 1 ↔ Nat.gcd k (R N m) = 1 :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:207
lemma coprime_add_mul_right {k c e : ℕ} :
    Nat.Coprime (k + e * c) e ↔ Nat.Coprime k e :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:277
lemma periodic_window_card_eq {P : ℕ → Prop} [DecidablePred P] {T : ℕ}
    (hP : ∀ n, P (n + T) ↔ P n) (b : ℕ) :
    ((Finset.Ico b (b + T)).filter P).card =
      ((Finset.Ico 0 T).filter P).card :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:348
lemma coprime_m_R {N m : ℕ} (hN : 0 < N) :
    Nat.Coprime m (R N m) :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:399
lemma accepted_iff_coprime_R {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) (n : ℕ) :
    accepted N m a n ↔
      (n : ℤ) ≡ a [ZMOD (m : ℤ)] ∧ Nat.gcd n (R N m) = 1 :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:411
lemma rad_pos (n : ℕ) : 0 < rad n :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:417
lemma R_pos {N m : ℕ} (hN : 0 < N) : 0 < R N m :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:427
lemma exists_repr_mod_R {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ} {r : ℕ}
    (hr : r < R N m) :
    ∃ n, n < Tmin N m ∧
      (n : ℤ) ≡ a [ZMOD (m : ℤ)] ∧
      n % R N m = r :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:467
lemma repr_unique {N m : ℕ} (hN : 0 < N) (_hm : 0 < m) {a : ℤ} {n1 n2 : ℕ}
    (h1 : n1 < Tmin N m) (h2 : n2 < Tmin N m)
    (hmod1 : (n1 : ℤ) ≡ a [ZMOD (m : ℤ)])
    (hmod2 : (n2 : ℤ) ≡ a [ZMOD (m : ℤ)])
    (hReq : n1 % R N m = n2 % R N m) : n1 = n2 :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:488
lemma gcd_mod_eq (n R : ℕ) :
    Nat.gcd n R = Nat.gcd (n % R) R :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:492
lemma exists_accepted {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) : ∃ n, accepted N m a n :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:531
lemma primeFactors_forall_dvd_imp_dvd {n t : ℕ} (_hn : 0 < n)
    (hall : ∀ p ∈ n.primeFactors, p ∣ t) : rad n ∣ t :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:576
lemma exists_witness_avoiding_dvd {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) {p : ℕ} (hp : p.Prime) (hpR : p ∣ R N m) :
    ∃ n1, accepted N m a n1 ∧ ¬ (p ∣ n1) :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:591
lemma squarefree_prime_dvd_split {n p : ℕ} (hsf : Squarefree n) (hp : p.Prime)
    (hpn : p ∣ n) : Nat.Coprime p (n / p) ∧ p * (n / p) = n :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:604
lemma R_squarefree {N m : ℕ} (hN : 0 < N) : Squarefree (R N m) :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:608
lemma exists_coprime_R_neg_t_mod_p {N m : ℕ} (hN : 0 < N) {p t : ℕ} (hp : p.Prime)
    (hpR : p ∣ R N m) (hpt : ¬ p ∣ t) :
    ∃ r, r < R N m ∧ Nat.Coprime r (R N m) ∧ (r : ℤ) ≡ -(t : ℤ) [ZMOD (p : ℤ)] :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:664
lemma rad_eq_self_of_squarefree {n : ℕ} (_hn : 0 < n) (hsf : Squarefree n) :
    rad n = n :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:772
lemma canonical_window_card_eq_range_coprime {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (_h : Admissible N m a) :
    ((Finset.Ico 0 (Tmin N m)).filter
        (fun (n : ℕ) => (n : ℤ) ≡ a [ZMOD (m : ℤ)] ∧ Nat.gcd n (R N m) = 1)).card =
      ((Finset.range (R N m)).filter
        (fun r => Nat.gcd r (R N m) = 1)).card :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:799
lemma count_canonical_period {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) :
    ((Finset.Ico 0 (Tmin N m)).filter (accepted N m a)).card =
      Nat.totient (R N m) :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:818
lemma card_filter_Ico_split {P : ℕ → Prop} [DecidablePred P] {a b c : ℕ}
    (hab : a ≤ b) (hbc : b ≤ c) :
    ((Finset.Ico a c).filter P).card =
      ((Finset.Ico a b).filter P).card +
        ((Finset.Ico b c).filter P).card :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:836
lemma S_eq_filter_Ico (N L m : ℕ) (a : ℤ) :
    S N L m a =
      (Finset.Ico 1 (L + 1)).filter (accepted N m a) :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:882
lemma rad_factorization_eq_one {n : ℕ} (_hn : 0 < n) {p : ℕ}
    (hp : p ∈ n.primeFactors) :
    (rad n).factorization p = 1 :=
  sorry

-- source: Solution/GeneralDivisorTheorem.lean:902
lemma totient_rad_mul (n : ℕ) (_hn : 0 < n) :
    n * Nat.totient (rad n) = rad n * Nat.totient n :=
  sorry

end GDT.Challenge
