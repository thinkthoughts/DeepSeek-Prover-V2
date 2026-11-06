import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat

namespace GDT


def rad (n : ℕ) : ℕ := n.primeFactors.prod id

def d (N m : ℕ) : ℕ := rad (Nat.gcd m N)

def R (N m : ℕ) : ℕ := rad N / d N m

def Tmin (N m : ℕ) : ℕ := m * R N m

def Admissible (N m : ℕ) (a : ℤ) : Prop :=
  Nat.gcd a.natAbs (d N m) = 1

def accepted (N m : ℕ) (a : ℤ) (n : ℕ) : Prop :=
  (n : ℤ) ≡ a [ZMOD (m : ℤ)] ∧ Nat.gcd n N = 1

instance acceptedDecidable (N m : ℕ) (a : ℤ) :
    DecidablePred (accepted N m a) := by
  intro n
  unfold accepted
  apply instDecidableAnd

def S (N L m : ℕ) (a : ℤ) : Finset ℕ :=
  (Finset.Icc 1 L).filter (accepted N m a)

def IsPeriod (N m : ℕ) (a : ℤ) (t : ℕ) : Prop :=
  ∀ n : ℕ, accepted N m a (n + t) ↔ accepted N m a n

end GDT

#eval show IO Unit from do IO.println s!"@@T begin gdt/gdt_empty {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
theorem gdt_empty {N m L : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : ¬ Admissible N m a) :
    S N L m a = ∅ := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/gdt_empty {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/gdt_periodic {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
theorem gdt_periodic {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) :
    IsPeriod N m a (Tmin N m) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/gdt_periodic {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/gdt_minimal_period {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
theorem gdt_minimal_period {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) {t : ℕ} (ht : 0 < t) (hp : IsPeriod N m a t) :
    Tmin N m ∣ t := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/gdt_minimal_period {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/gdt_count_per_period {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
theorem gdt_count_per_period {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) (b : ℕ) :
    ((Finset.Ico b (b + Tmin N m)).filter (accepted N m a)).card =
      Nat.totient (R N m) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/gdt_count_per_period {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/gdt_density {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
theorem gdt_density {N m q s : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) (hs : s < Tmin N m) :
    (S N (q * Tmin N m + s) m a).card =
      q * Nat.totient (R N m) + (S N s m a).card := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/gdt_density {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/gdt_correction_factor {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
theorem gdt_correction_factor {N m : ℕ} (hN : 0 < N) (hm : 0 < m) :
    Nat.totient (R N m) * N * Nat.totient (d N m) =
      d N m * R N m * Nat.totient N := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/gdt_correction_factor {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/general_divisor_theorem {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
theorem general_divisor_theorem {N m L : ℕ} (hN : 0 < N) (hm : 0 < m) (a : ℤ) :
    (¬ Admissible N m a → S N L m a = ∅) ∧
    (Admissible N m a →
      IsPeriod N m a (Tmin N m) ∧
      (∀ t : ℕ, 0 < t → IsPeriod N m a t → Tmin N m ∣ t) ∧
      (∀ b : ℕ,
        ((Finset.Ico b (b + Tmin N m)).filter (accepted N m a)).card =
          Nat.totient (R N m))) ∧
    Nat.totient (R N m) * N * Nat.totient (d N m) =
      d N m * R N m * Nat.totient N := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/general_divisor_theorem {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/d_dvd_rad {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma d_dvd_rad {N m : ℕ} (hN : 0 < N) : d N m ∣ rad N := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/d_dvd_rad {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/d_mul_R_eq_rad {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma d_mul_R_eq_rad {N m : ℕ} (hN : 0 < N) : d N m * R N m = rad N := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/d_mul_R_eq_rad {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/prime_coprime_prod {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma prime_coprime_prod {a : ℕ} (ha : a.Prime) {s : Finset ℕ}
    (hs : ∀ p ∈ s, p.Prime) (ha_not : a ∉ s) :
    Nat.Coprime a (∏ p ∈ s, p) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/prime_coprime_prod {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/prod_primes_squarefree {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma prod_primes_squarefree {s : Finset ℕ} (hs : ∀ p ∈ s, p.Prime) :
    Squarefree (∏ p ∈ s, p) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/prod_primes_squarefree {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/rad_squarefree {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma rad_squarefree (n : ℕ) : Squarefree (rad n) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/rad_squarefree {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/coprime_d_R {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma coprime_d_R {N m : ℕ} (hN : 0 < N) :
    Nat.Coprime (d N m) (R N m) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/coprime_d_R {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/rad_dvd_self {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma rad_dvd_self (n : ℕ) : rad n ∣ n := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/rad_dvd_self {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/coprime_iff_coprime_rad {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma coprime_iff_coprime_rad {k n : ℕ} (hn : n ≠ 0) :
    Nat.Coprime k n ↔ Nat.Coprime k (rad n) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/coprime_iff_coprime_rad {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/coprime_of_modEq_natAbs {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma coprime_of_modEq_natAbs {k : ℕ} {a : ℤ} {e : ℕ}
    (hk : (k : ℤ) ≡ a [ZMOD (e : ℤ)]) (ha : Nat.gcd a.natAbs e = 1) :
    Nat.Coprime k e := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/coprime_of_modEq_natAbs {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/gcd_with_N_iff_gcd_with_R {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma gcd_with_N_iff_gcd_with_R
    {N m k : ℕ} (hN : 0 < N) (_hm : 0 < m) {a : ℤ}
    (ha : Admissible N m a)
    (hk : (k : ℤ) ≡ a [ZMOD (m : ℤ)]) :
    Nat.gcd k N = 1 ↔ Nat.gcd k (R N m) = 1 := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/gcd_with_N_iff_gcd_with_R {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/coprime_add_mul_right {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma coprime_add_mul_right {k c e : ℕ} :
    Nat.Coprime (k + e * c) e ↔ Nat.Coprime k e := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/coprime_add_mul_right {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/periodic_window_card_eq {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma periodic_window_card_eq {P : ℕ → Prop} [DecidablePred P] {T : ℕ}
    (hP : ∀ n, P (n + T) ↔ P n) (b : ℕ) :
    ((Finset.Ico b (b + T)).filter P).card =
      ((Finset.Ico 0 T).filter P).card := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/periodic_window_card_eq {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/coprime_m_R {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma coprime_m_R {N m : ℕ} (hN : 0 < N) :
    Nat.Coprime m (R N m) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/coprime_m_R {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/accepted_iff_coprime_R {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma accepted_iff_coprime_R {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) (n : ℕ) :
    accepted N m a n ↔
      (n : ℤ) ≡ a [ZMOD (m : ℤ)] ∧ Nat.gcd n (R N m) = 1 := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/accepted_iff_coprime_R {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/rad_pos {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma rad_pos (n : ℕ) : 0 < rad n := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/rad_pos {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/R_pos {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma R_pos {N m : ℕ} (hN : 0 < N) : 0 < R N m := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/R_pos {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/exists_repr_mod_R {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma exists_repr_mod_R {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ} {r : ℕ}
    (hr : r < R N m) :
    ∃ n, n < Tmin N m ∧
      (n : ℤ) ≡ a [ZMOD (m : ℤ)] ∧
      n % R N m = r := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/exists_repr_mod_R {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/repr_unique {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma repr_unique {N m : ℕ} (hN : 0 < N) (_hm : 0 < m) {a : ℤ} {n1 n2 : ℕ}
    (h1 : n1 < Tmin N m) (h2 : n2 < Tmin N m)
    (hmod1 : (n1 : ℤ) ≡ a [ZMOD (m : ℤ)])
    (hmod2 : (n2 : ℤ) ≡ a [ZMOD (m : ℤ)])
    (hReq : n1 % R N m = n2 % R N m) : n1 = n2 := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/repr_unique {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/gcd_mod_eq {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma gcd_mod_eq (n R : ℕ) :
    Nat.gcd n R = Nat.gcd (n % R) R := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/gcd_mod_eq {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/exists_accepted {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma exists_accepted {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) : ∃ n, accepted N m a n := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/exists_accepted {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/primeFactors_forall_dvd_imp_dvd {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma primeFactors_forall_dvd_imp_dvd {n t : ℕ} (_hn : 0 < n)
    (hall : ∀ p ∈ n.primeFactors, p ∣ t) : rad n ∣ t := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/primeFactors_forall_dvd_imp_dvd {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/exists_witness_avoiding_dvd {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma exists_witness_avoiding_dvd {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) {p : ℕ} (hp : p.Prime) (hpR : p ∣ R N m) :
    ∃ n1, accepted N m a n1 ∧ ¬ (p ∣ n1) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/exists_witness_avoiding_dvd {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/squarefree_prime_dvd_split {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma squarefree_prime_dvd_split {n p : ℕ} (hsf : Squarefree n) (hp : p.Prime)
    (hpn : p ∣ n) : Nat.Coprime p (n / p) ∧ p * (n / p) = n := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/squarefree_prime_dvd_split {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/R_squarefree {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma R_squarefree {N m : ℕ} (hN : 0 < N) : Squarefree (R N m) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/R_squarefree {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/exists_coprime_R_neg_t_mod_p {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma exists_coprime_R_neg_t_mod_p {N m : ℕ} (hN : 0 < N) {p t : ℕ} (hp : p.Prime)
    (hpR : p ∣ R N m) (hpt : ¬ p ∣ t) :
    ∃ r, r < R N m ∧ Nat.Coprime r (R N m) ∧ (r : ℤ) ≡ -(t : ℤ) [ZMOD (p : ℤ)] := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/exists_coprime_R_neg_t_mod_p {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/rad_eq_self_of_squarefree {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma rad_eq_self_of_squarefree {n : ℕ} (_hn : 0 < n) (hsf : Squarefree n) :
    rad n = n := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/rad_eq_self_of_squarefree {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/canonical_window_card_eq_range_coprime {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma canonical_window_card_eq_range_coprime {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (_h : Admissible N m a) :
    ((Finset.Ico 0 (Tmin N m)).filter
        (fun (n : ℕ) => (n : ℤ) ≡ a [ZMOD (m : ℤ)] ∧ Nat.gcd n (R N m) = 1)).card =
      ((Finset.range (R N m)).filter
        (fun r => Nat.gcd r (R N m) = 1)).card := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/canonical_window_card_eq_range_coprime {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/count_canonical_period {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma count_canonical_period {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) :
    ((Finset.Ico 0 (Tmin N m)).filter (accepted N m a)).card =
      Nat.totient (R N m) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/count_canonical_period {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/card_filter_Ico_split {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma card_filter_Ico_split {P : ℕ → Prop} [DecidablePred P] {a b c : ℕ}
    (hab : a ≤ b) (hbc : b ≤ c) :
    ((Finset.Ico a c).filter P).card =
      ((Finset.Ico a b).filter P).card +
        ((Finset.Ico b c).filter P).card := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/card_filter_Ico_split {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/S_eq_filter_Ico {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma S_eq_filter_Ico (N L m : ℕ) (a : ℤ) :
    S N L m a =
      (Finset.Ico 1 (L + 1)).filter (accepted N m a) := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/S_eq_filter_Ico {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/rad_factorization_eq_one {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma rad_factorization_eq_one {n : ℕ} (_hn : 0 < n) {p : ℕ}
    (hp : p ∈ n.primeFactors) :
    (rad n).factorization p = 1 := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/rad_factorization_eq_one {← IO.monoMsNow}"

#eval show IO Unit from do IO.println s!"@@T begin gdt/totient_rad_mul {← IO.monoMsNow}"

namespace GDT.Challenge
open GDT

set_option maxHeartbeats 200000 in
lemma totient_rad_mul (n : ℕ) (_hn : 0 < n) :
    n * Nat.totient (rad n) = rad n * Nat.totient n := by
  simp_all

end GDT.Challenge

#eval show IO Unit from do IO.println s!"@@T end gdt/totient_rad_mul {← IO.monoMsNow}"

