/-
RPI-DS-001b: print the definitions of the Mathlib constants that occur in GDT
statements, so that Lean 4.34 and Lean 4.9 versions can be compared.
Run from the GDT repo (4.34) or formalize-now/lean49 (4.9): `lake env lean <this file>`.
-/
import Mathlib.Data.Nat.Totient
import Mathlib.Data.Nat.Factorization.Basic
import Mathlib.Data.Nat.Squarefree
import Mathlib.Data.Int.GCD
open Lean Meta

def targets : List Name :=
  [`Nat.primeFactors, `Nat.totient, `Int.ModEq, `Nat.ModEq, `Nat.factorization, `Squarefree,
   `Finset.Ico, `Finset.Icc, `Finset.range, `Finset.filter, `Finset.card, `Finset.prod,
   `Nat.Coprime, `Nat.gcd, `Int.natAbs, `Nat.Prime, `Irreducible, `IsUnit, `Dvd.dvd, `Int.emod,
   `Nat.factors, `Nat.primeFactorsList, `Nat.instLocallyFiniteOrderNat, `instLocallyFiniteOrderNat,
   `Nat.instLocallyFiniteOrder, `List.range',
   -- characterising theorems (compared by statement)
   `Nat.mem_primeFactors, `Nat.totient_eq_card_coprime, `Finset.mem_Ico, `Finset.mem_Icc,
   `Finset.mem_range, `Finset.mem_filter, `Finset.card_range, `Int.emod_emod_of_dvd,
   `Int.modEq_iff_dvd, `Int.natCast_modEq_iff, `Nat.factorization_def, `Nat.isUnit_iff,
   `Nat.squarefree_iff_prime_squarefree, `Nat.prime_def_lt'', `Finset.prod_insert,
   `Nat.coprime_iff_gcd_eq_one, `Int.natAbs_dvd_natAbs, `Nat.Coprime.gcd_eq_one]

#eval show MetaM Unit from do
  let env ← getEnv
  let mut out : Array Json := #[]
  for n in targets do
    match env.find? n with
    | none => out := out.push (Json.mkObj [("name", toJson n.toString), ("present", toJson false)])
    | some ci =>
      let kind := match ci with
        | .defnInfo _ => "def" | .thmInfo _ => "theorem" | .axiomInfo _ => "axiom" | .opaqueInfo _ => "opaque"
        | .inductInfo _ => "inductive" | .ctorInfo _ => "ctor" | .recInfo _ => "rec" | .quotInfo _ => "quot"
      let val? : Option Expr := match ci with
        | .defnInfo d => some d.value | .opaqueInfo o => some o.value | _ => none
      let tpp ← withOptions (fun o => o.setBool `pp.universes false) (ppExpr ci.type)
      let vpp ← match val? with
        | some v => do pure (toString (← ppExpr v))
        | none => pure ""
      let vconsts := (val?.map (·.getUsedConstants.toList.map toString)).getD []
      let ctors := match ci with
        | .inductInfo i => i.ctors.map toString | _ => []
      out := out.push (Json.mkObj [("name", toJson n.toString), ("present", toJson true), ("kind", toJson kind),
        ("type_pp", toJson (toString tpp)), ("value_pp", toJson vpp),
        ("value_available", toJson val?.isSome),
        ("value_consts", toJson ((vconsts.toArray.qsort (· < ·)).toList.eraseDups)), ("ctors", toJson ctors)])
  IO.println "@@RPI_JSON_BEGIN"
  IO.println (Json.arr out).pretty
  IO.println "@@RPI_JSON_END"
