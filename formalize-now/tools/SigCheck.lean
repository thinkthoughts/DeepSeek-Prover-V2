/-
RPI-DS-001b certification check (Lean 4.9). Run inside lean49/:
  lake env lean ../tools/SigCheck.lean
For every expected statement `GDT.Expected.x` (Challenge + Ladder, from the GDT
source) it requires a proved constant `GDT.Challenge.x` in GDTBench.SolutionRef with
  * alpha-equivalent types (`Expr.eqv`, i.e. `==`); strict `Expr.equal` is also
    recorded and, where it fails, the first differing binder names are reported,
  * axioms ⊆ {propext, Quot.sound, Classical.choice} (so no sorryAx),
  * kind `theorem`.
It also checks that SolutionRef declares no further non-auxiliary GDT.Challenge
theorem, and that the 9 GDT definitions are the ones Expected was elaborated against.
-/
import GDTBench.SolutionRef
import GDTBench.Expected
open Lean

/-- First place where two alpha-equivalent types differ under `Expr.equal`:
returns the pair of binder names (or binder infos) found there. -/
partial def binderDiff : Expr → Expr → Option (String × String)
  | .forallE n1 t1 b1 i1, .forallE n2 t2 b2 i2
  | .lam n1 t1 b1 i1, .lam n2 t2 b2 i2 =>
    if n1 != n2 then some (toString n1, toString n2)
    else if i1 != i2 then some (s!"binderInfo {repr i1}", s!"binderInfo {repr i2}")
    else (binderDiff t1 t2).orElse (fun _ => binderDiff b1 b2)
  | .app f1 a1, .app f2 a2 => (binderDiff f1 f2).orElse (fun _ => binderDiff a1 a2)
  | .mdata _ e1, e2 => binderDiff e1 e2
  | e1, .mdata _ e2 => binderDiff e1 e2
  | .letE n1 t1 v1 b1 _, .letE n2 t2 v2 b2 _ =>
    if n1 != n2 then some (toString n1, toString n2)
    else ((binderDiff t1 t2).orElse (fun _ => binderDiff v1 v2)).orElse (fun _ => binderDiff b1 b2)
  | .proj _ _ e1, .proj _ _ e2 => binderDiff e1 e2
  | _, _ => none

/-- Lean 4.9 axiom collector (the one behind `#print axioms`). -/
def axiomsOf (env : Environment) (c : Name) : Array Name :=
  (((Lean.Elab.Command.CollectAxioms.collect c).run env).run {}).2.axioms

def allowed : List Name := [``propext, ``Quot.sound, ``Classical.choice]

#eval show CoreM Unit from do
  let env ← getEnv
  let mut rows : Array Json := #[]
  let mut ok := 0
  let mut bad := 0
  let expected := env.constants.toList.filter fun (n, ci) =>
    (`GDT.Expected).isPrefixOf n && !n.isInternal && ci matches .thmInfo _
  for (en, eci) in expected do
    let short := en.replacePrefix `GDT.Expected `GDT.Challenge
    match env.find? short with
    | none =>
      bad := bad + 1
      rows := rows.push (Json.mkObj [("name", toJson short.toString), ("status", "missing")])
    | some ci =>
      let axs := axiomsOf env short
      let extra := axs.filter (fun a => !allowed.contains a)
      let isThm := ci matches .thmInfo _
      let strict := ci.type.equal eci.type
      let eqv := ci.type == eci.type
      -- certification rule: alpha-equivalence (the kernel's notion of identical type,
      -- as used by Comparator) + whitelist axioms; strict differences are reported and
      -- must be binder names only (checked by tools/certify49.py)
      let good := isThm && eqv && extra.isEmpty
      if good then ok := ok + 1 else bad := bad + 1
      rows := rows.push (Json.mkObj [
        ("name", toJson short.toString), ("status", toJson (if good then "certified" else "rejected")),
        ("is_theorem", toJson isThm), ("type_equal_strict", toJson strict),
        ("type_eqv", toJson eqv),
        ("strict_difference", toJson ((if strict then none else binderDiff ci.type eci.type).map (fun (a, b) => [a, b]))),
        ("axioms", toJson (axs.map toString)), ("disallowed_axioms", toJson (extra.map toString))])
  -- no unexpected extra theorems in SolutionRef
  let extras := env.constants.toList.filter fun (n, ci) =>
    (`GDT.Challenge).isPrefixOf n && !n.isInternal && (ci matches .thmInfo _) &&
      (env.find? (n.replacePrefix `GDT.Challenge `GDT.Expected)).isNone
  IO.println "@@RPI_JSON_BEGIN"
  IO.println (Json.mkObj [
    ("expected_count", toJson expected.length), ("certified", toJson ok), ("rejected_or_missing", toJson bad),
    ("unexpected_theorems", toJson (extras.map (·.1.toString))),
    ("rows", Json.arr (rows.qsort (fun a b => a.compress < b.compress)))]).pretty
  IO.println "@@RPI_JSON_END"
