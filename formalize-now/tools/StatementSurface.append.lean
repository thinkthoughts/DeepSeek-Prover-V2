
/-
RPI-DS-001a appendix (statement surface). Appended to a copy of a GDT Solution
file and elaborated in either Lean 4.34 or Lean 4.9. For every GDT declaration it
prints the pretty-printed statement and the non-GDT constants occurring in it.
Agreement of these lists across versions is evidence for, and never a proof of,
unchanged mathematical meaning: a constant may keep its name and change its
definition.
-/
open Lean in
#eval show MetaM Unit from do
  let env ← getEnv
  let mut out : Array Json := #[]
  for (n, ci) in env.constants.toList do
    if (`GDT).isPrefixOf n && !n.isInternal && !n.isInternalDetail then
      let cs := ci.type.getUsedConstants.toList.filter (fun c => !(`GDT).isPrefixOf c)
      let cs := (cs.map toString).toArray.qsort (· < ·)
      let pp ← Meta.ppExpr ci.type
      out := out.push <| Json.mkObj [("name", toJson n.toString), ("type_pp", toJson (toString pp)), ("type_consts", toJson cs)]
  IO.println "@@RPI_JSON_BEGIN"
  IO.println (Json.arr (out.qsort (fun a b => a.compress < b.compress))).compress
  IO.println "@@RPI_JSON_END"
