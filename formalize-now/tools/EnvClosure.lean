/-
RPI-DS-001c: which modules does the kernel-checked content of the 39 certified
reference proofs depend on? Computes the transitive constant closure (types and
values) of every GDT.Challenge theorem in GDTBench.SolutionRef and reports the
modules those constants come from, flagging any constant defined in the modules
that differ between this environment and DeepSeek's exact one
(Batteries.Tactic.Lint.Frontend: Batteries f96a344 vs 42b5ddd).
Run inside lean49/:  lake env lean ../tools/EnvClosure.lean
-/
import GDTBench.SolutionRef
open Lean

partial def closure (env : Environment) : List Name → NameSet → NameSet
  | [], s => s
  | n :: rest, s =>
    if s.contains n then closure env rest s else
    let s := s.insert n
    match env.find? n with
    | some ci =>
      let cs := ci.type.getUsedConstants.toList ++
        (match ci with
         | .thmInfo t => t.value.getUsedConstants.toList
         | .defnInfo d => d.value.getUsedConstants.toList
         | .opaqueInfo o => o.value.getUsedConstants.toList
         | .inductInfo i => i.ctors
         | .ctorInfo c => [c.induct]
         | .recInfo r => [r.getInduct]
         | _ => [])
      closure env (cs ++ rest) s
    | none => closure env rest s

#eval show CoreM Unit from do
  let env ← getEnv
  let roots := env.constants.toList.filterMap fun (n, ci) =>
    if (`GDT.Challenge).isPrefixOf n && !n.isInternal && (ci matches .thmInfo _) then some n else none
  let cl := closure env roots {}
  let mut mods : NameMap Nat := {}
  for n in cl.toList do
    let m := match env.getModuleIdxFor? n with
      | some i => env.header.moduleNames[i.toNat]!
      | none => `_current
    mods := mods.insert m ((mods.findD m 0) + 1)
  let flagged := [`Batteries.Tactic.Lint.Frontend]
  let hits := flagged.filter (mods.contains ·)
  let top := (mods.toList.toArray.qsort (fun a b => a.2 > b.2)).toList.take 15
  IO.println s!"roots={roots.length} closure_constants={cl.size} modules={mods.size}"
  IO.println s!"constants_from_differing_modules={hits}"
  IO.println s!"batteries_modules_in_closure={(mods.toList.filter (fun (m, _) => (`Batteries).isPrefixOf m)).map (·.1)}"
  IO.println s!"top_modules={top}"
