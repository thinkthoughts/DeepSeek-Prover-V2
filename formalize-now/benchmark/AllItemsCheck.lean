-- RPI-DS-001a GENERATED: all benchmark items under the V1.5 header (elaboration check only).
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

namespace GDT.Challenge
open GDT

theorem gdt_empty {N m L : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : ¬ Admissible N m a) :
    S N L m a = ∅ := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

theorem gdt_periodic {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) :
    IsPeriod N m a (Tmin N m) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

theorem gdt_minimal_period {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) {t : ℕ} (ht : 0 < t) (hp : IsPeriod N m a t) :
    Tmin N m ∣ t := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

theorem gdt_count_per_period {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) (b : ℕ) :
    ((Finset.Ico b (b + Tmin N m)).filter (accepted N m a)).card =
      Nat.totient (R N m) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

theorem gdt_density {N m q s : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) (hs : s < Tmin N m) :
    (S N (q * Tmin N m + s) m a).card =
      q * Nat.totient (R N m) + (S N s m a).card := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

theorem gdt_correction_factor {N m : ℕ} (hN : 0 < N) (hm : 0 < m) :
    Nat.totient (R N m) * N * Nat.totient (d N m) =
      d N m * R N m * Nat.totient N := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

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
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma d_dvd_rad {N m : ℕ} (hN : 0 < N) : d N m ∣ rad N := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma d_mul_R_eq_rad {N m : ℕ} (hN : 0 < N) : d N m * R N m = rad N := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma prime_coprime_prod {a : ℕ} (ha : a.Prime) {s : Finset ℕ}
    (hs : ∀ p ∈ s, p.Prime) (ha_not : a ∉ s) :
    Nat.Coprime a (∏ p ∈ s, p) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma prod_primes_squarefree {s : Finset ℕ} (hs : ∀ p ∈ s, p.Prime) :
    Squarefree (∏ p ∈ s, p) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma rad_squarefree (n : ℕ) : Squarefree (rad n) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma coprime_d_R {N m : ℕ} (hN : 0 < N) :
    Nat.Coprime (d N m) (R N m) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma rad_dvd_self (n : ℕ) : rad n ∣ n := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma coprime_iff_coprime_rad {k n : ℕ} (hn : n ≠ 0) :
    Nat.Coprime k n ↔ Nat.Coprime k (rad n) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma coprime_of_modEq_natAbs {k : ℕ} {a : ℤ} {e : ℕ}
    (hk : (k : ℤ) ≡ a [ZMOD (e : ℤ)]) (ha : Nat.gcd a.natAbs e = 1) :
    Nat.Coprime k e := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma gcd_with_N_iff_gcd_with_R
    {N m k : ℕ} (hN : 0 < N) (_hm : 0 < m) {a : ℤ}
    (ha : Admissible N m a)
    (hk : (k : ℤ) ≡ a [ZMOD (m : ℤ)]) :
    Nat.gcd k N = 1 ↔ Nat.gcd k (R N m) = 1 := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma coprime_add_mul_right {k c e : ℕ} :
    Nat.Coprime (k + e * c) e ↔ Nat.Coprime k e := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma periodic_window_card_eq {P : ℕ → Prop} [DecidablePred P] {T : ℕ}
    (hP : ∀ n, P (n + T) ↔ P n) (b : ℕ) :
    ((Finset.Ico b (b + T)).filter P).card =
      ((Finset.Ico 0 T).filter P).card := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma coprime_m_R {N m : ℕ} (hN : 0 < N) :
    Nat.Coprime m (R N m) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma accepted_iff_coprime_R {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) (n : ℕ) :
    accepted N m a n ↔
      (n : ℤ) ≡ a [ZMOD (m : ℤ)] ∧ Nat.gcd n (R N m) = 1 := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma rad_pos (n : ℕ) : 0 < rad n := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma R_pos {N m : ℕ} (hN : 0 < N) : 0 < R N m := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma exists_repr_mod_R {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ} {r : ℕ}
    (hr : r < R N m) :
    ∃ n, n < Tmin N m ∧
      (n : ℤ) ≡ a [ZMOD (m : ℤ)] ∧
      n % R N m = r := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma repr_unique {N m : ℕ} (hN : 0 < N) (_hm : 0 < m) {a : ℤ} {n1 n2 : ℕ}
    (h1 : n1 < Tmin N m) (h2 : n2 < Tmin N m)
    (hmod1 : (n1 : ℤ) ≡ a [ZMOD (m : ℤ)])
    (hmod2 : (n2 : ℤ) ≡ a [ZMOD (m : ℤ)])
    (hReq : n1 % R N m = n2 % R N m) : n1 = n2 := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma gcd_mod_eq (n R : ℕ) :
    Nat.gcd n R = Nat.gcd (n % R) R := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma exists_accepted {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) : ∃ n, accepted N m a n := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma primeFactors_forall_dvd_imp_dvd {n t : ℕ} (_hn : 0 < n)
    (hall : ∀ p ∈ n.primeFactors, p ∣ t) : rad n ∣ t := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma exists_witness_avoiding_dvd {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) {p : ℕ} (hp : p.Prime) (hpR : p ∣ R N m) :
    ∃ n1, accepted N m a n1 ∧ ¬ (p ∣ n1) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma squarefree_prime_dvd_split {n p : ℕ} (hsf : Squarefree n) (hp : p.Prime)
    (hpn : p ∣ n) : Nat.Coprime p (n / p) ∧ p * (n / p) = n := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma R_squarefree {N m : ℕ} (hN : 0 < N) : Squarefree (R N m) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma exists_coprime_R_neg_t_mod_p {N m : ℕ} (hN : 0 < N) {p t : ℕ} (hp : p.Prime)
    (hpR : p ∣ R N m) (hpt : ¬ p ∣ t) :
    ∃ r, r < R N m ∧ Nat.Coprime r (R N m) ∧ (r : ℤ) ≡ -(t : ℤ) [ZMOD (p : ℤ)] := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma rad_eq_self_of_squarefree {n : ℕ} (_hn : 0 < n) (hsf : Squarefree n) :
    rad n = n := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma canonical_window_card_eq_range_coprime {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (_h : Admissible N m a) :
    ((Finset.Ico 0 (Tmin N m)).filter
        (fun (n : ℕ) => (n : ℤ) ≡ a [ZMOD (m : ℤ)] ∧ Nat.gcd n (R N m) = 1)).card =
      ((Finset.range (R N m)).filter
        (fun r => Nat.gcd r (R N m) = 1)).card := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma count_canonical_period {N m : ℕ} (hN : 0 < N) (hm : 0 < m) {a : ℤ}
    (h : Admissible N m a) :
    ((Finset.Ico 0 (Tmin N m)).filter (accepted N m a)).card =
      Nat.totient (R N m) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma card_filter_Ico_split {P : ℕ → Prop} [DecidablePred P] {a b c : ℕ}
    (hab : a ≤ b) (hbc : b ≤ c) :
    ((Finset.Ico a c).filter P).card =
      ((Finset.Ico a b).filter P).card +
        ((Finset.Ico b c).filter P).card := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma S_eq_filter_Ico (N L m : ℕ) (a : ℤ) :
    S N L m a =
      (Finset.Ico 1 (L + 1)).filter (accepted N m a) := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma rad_factorization_eq_one {n : ℕ} (_hn : 0 < n) {p : ℕ}
    (hp : p ∈ n.primeFactors) :
    (rad n).factorization p = 1 := by
  sorry

end GDT.Challenge

namespace GDT.Challenge
open GDT

lemma totient_rad_mul (n : ℕ) (_hn : 0 < n) :
    n * Nat.totient (rad n) = rad n * Nat.totient n := by
  sorry

end GDT.Challenge
