/-
RPI-DS-001e: recompute, in the Lean 4.9 benchmark environment, the GDT lemmas each
certified reference proof USES (kernel constants of its proof term), with the same
rule as the strict verifier's C9 check. Compared by tests against the Stage 0 kernel
dependency manifest (computed in Lean 4.34 from the original GDT Solution).
Run inside lean49/:  lake env lean ../tools/UsedLemmas49.lean
-/
import GDTBench.SolutionRef
open Lean

#eval show CoreM Unit from do
  let env ← getEnv
  let usedLemmas (thm : Name) : List String := Id.run do
    let start : List Name := match env.find? thm with
      | some (.thmInfo t) => t.value.getUsedConstants.toList
      | _ => []
    let mut todo := start
    let mut seen : NameSet := {}
    let mut out : List String := []
    for _ in [0:1000000] do
      match todo with
      | [] => break
      | n :: rest =>
        todo := rest
        if seen.contains n then continue
        seen := seen.insert n
        let comps := n.components
        if comps.length ≥ 3 && comps[0]! == `GDT && comps[1]! == `Challenge then
          let base := (`GDT ++ comps[1]!) ++ comps[2]!
          if base == thm && n != thm then
            match env.find? n with
            | some (.thmInfo t) => todo := t.value.getUsedConstants.toList ++ todo
            | some (.defnInfo d) => todo := d.value.getUsedConstants.toList ++ todo
            | _ => pure ()
          else if base != thm then
            unless out.contains comps[2]!.toString do out := out ++ [comps[2]!.toString]
    return out
  let mut rows : Array Json := #[]
  for (n, ci) in env.constants.toList do
    if (`GDT.Challenge).isPrefixOf n && n.components.length == 3 && (ci matches .thmInfo _) then
      rows := rows.push (Json.mkObj [("name", toJson n.components[2]!.toString),
                                     ("used_lemmas", toJson (usedLemmas n))])
  IO.println ("@@RPI_USED " ++ (Json.arr rows).compress)
