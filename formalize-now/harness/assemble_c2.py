#!/usr/bin/env python3
"""RPI-DS-001d.2: theorem-level C2 assembler (PREREGISTRATION.md §5, Amendment A2).

Input: a target challenge theorem (or any item) and candidate C2 proofs for the target
and the lemmas in its closure. Each candidate is a record
    {"lemma": short name, "proof": tactic body, "sample_index": int,
     "per_item_status": "certified" | "preliminary" | "rejected",
     "provenance": "model" | "reference_fixture" | "independent_fixture",
     "generation_id": completion sha256 (required for provenance "model")}

Procedure (the first failing step determines the outcome):
 1. Closure and order: closure(T) from the Stage 0 KERNEL dependencies
    (manifest/gdt_manifest_v2.json, kernel_deps), topologically sorted with source
    order as tie-break; a cycle or an unknown name aborts.
 2. Selection: for each member of closure(T) ∪ {T}, the candidate with the smallest
    sample_index among those with per_item_status == "certified". Two different proofs
    with the same (lemma, sample_index) are a CONFLICT. A member with no certified
    candidate makes the assembly INCOMPLETE. No fallback of any kind: reference proofs
    are never inserted for a missing member.
 3. Assembly: trusted header + definitions; trusted expected statements of every member
    (namespace GDT.Expected, elaborated before any candidate text); then every member in
    dependency order, trusted statement + candidate body (indented under `:= by`);
    then a trusted check of EVERY member.
 4. Certification: `lean` compile with -o, then lean4checker replay of the module.
    Required for every member: present, theorem, type alpha-equivalent to its expected
    statement, axioms ⊆ {propext, Quot.sound, Classical.choice}; no declared axioms;
    no weakening options; C8 replay passes. Outcome: certified or rejected.
 5. Claim level (separate from certification):
      c2_success        certified, every member's provenance is "model" with a
                        generation_id, and no member body contains reference-proof text
      fixture_only      certified, but at least one member is a fixture
      reference_text_detected  certified and claimed as model output, but a body line
                        matches a reference-proof line (held for review, not counted)
      none              not certified
Only `c2_success` may enter confirmatory C2 counts.
"""
import hashlib, json, os, re, subprocess, sys, tempfile, time
from pathlib import Path
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import verify_strict as vs

F = vs.F
MAN = json.loads((F / "manifest/gdt_manifest_v2.json").read_text())
THMS = {d["short"]: d for d in MAN["declarations"] if d["kind"] == "theorem"}
DEPS = {s: [x.split(".")[-1] for x in d["kernel_deps"] if x.startswith("GDT.Challenge.")] for s, d in THMS.items()}

class AssemblyError(Exception):
    pass

def closure(target):
    if target not in THMS:
        raise AssemblyError(f"unknown target {target}")
    seen, todo = set(), list(DEPS[target])
    while todo:
        x = todo.pop()
        if x not in THMS:
            raise AssemblyError(f"unknown dependency {x}")
        if x not in seen:
            seen.add(x); todo += DEPS[x]
    return seen

def topo_order(members):
    """Kahn's algorithm over kernel deps restricted to `members`; ties broken by source line."""
    members = set(members)
    indeg = {m: sum(1 for d in DEPS[m] if d in members) for m in members}
    ready = sorted((m for m in members if indeg[m] == 0), key=lambda m: THMS[m]["source_line"])
    out = []
    while ready:
        m = ready.pop(0); out.append(m)
        for u in sorted(members, key=lambda m: THMS[m]["source_line"]):
            if m in DEPS[u]:
                indeg[u] -= 1
                if indeg[u] == 0:
                    ready.append(u); ready.sort(key=lambda m: THMS[m]["source_line"])
    if len(out) != len(members):
        raise AssemblyError("dependency cycle")
    pos = {m: i for i, m in enumerate(out)}
    assert all(pos[d] < pos[m] for m in out for d in DEPS[m] if d in members)
    return out

def reference_lines():
    ref = vs.REF.read_text()
    lines = set()
    for m in re.finditer(r":= by\n(.*?)(?=\n(?:theorem|lemma|def|/--|end )|\Z)", ref, flags=re.S):
        for l in m.group(1).split("\n"):
            t = " ".join(l.split())
            if len(t) >= 20: lines.add(t)
    public = set()
    for l in (F / "benchmark/gdt_items_v2.jsonl").read_text().splitlines():
        it = json.loads(l)
        for fld in ("header", "definitions", "formal_statement"):
            public |= {" ".join(x.split()) for x in it[fld].split("\n")}
    return lines - public

def select(target, candidates):
    members = closure(target) | {target}
    by = {}
    for c in candidates:
        by.setdefault(c["lemma"], []).append(c)
    extraneous = sorted(set(by) - members)
    chosen, missing, conflicts = {}, [], []
    for m in sorted(members):
        cs = by.get(m, [])
        keyed = {}
        for c in cs:
            k = c["sample_index"]
            if k in keyed and keyed[k]["proof"] != c["proof"]:
                conflicts.append(dict(lemma=m, sample_index=k))
            keyed[k] = c
        cert = sorted((c for c in cs if c.get("per_item_status") == "certified"), key=lambda c: c["sample_index"])
        if cert:
            chosen[m] = cert[0]
        else:
            missing.append(m)
    return members, chosen, missing, conflicts, extraneous

def stmt_text(short):
    st = vs.load_item(f"gdt/{short}")["formal_statement"]
    return st.split("namespace GDT.Challenge\nopen GDT\n\n", 1)[1].rsplit(":= by\n  sorry", 1)[0].rstrip()

def check_all_block(order):
    names = ", ".join(f"`{m}" for m in order)
    return f'''
open Lean in
#eval show CoreM Unit from do
  let env ← getEnv
  let axiomsOf (c : Name) : Array Name :=
    (((Lean.Elab.Command.CollectAxioms.collect c).run env).run {{}}).2.axioms
  let localAxioms := env.constants.map₂.toList.filterMap fun (n, ci) =>
    if ci matches .axiomInfo _ then some n.toString else none
  let mut rows : Array Json := #[]
  for s in ([{names}] : List Name) do
    let t := `GDT.Challenge ++ s
    let e := `GDT.Expected ++ s
    match env.find? t, env.find? e with
    | some ci, some eci =>
      rows := rows.push (Json.mkObj [("name", toJson s.toString), ("present", toJson true),
        ("is_theorem", toJson (ci matches .thmInfo _)), ("type_alpha_equivalent", toJson (ci.type == eci.type)),
        ("axioms", toJson ((axiomsOf t).map toString))])
    | _, _ => rows := rows.push (Json.mkObj [("name", toJson s.toString), ("present", toJson false)])
  IO.println ("@@RPI_ASSEMBLY " ++ (Json.mkObj [("members", Json.arr rows), ("local_axioms", toJson localAxioms)]).compress)
'''

def build_source(target, order, chosen):
    it = vs.load_item(f"gdt/{target}")
    prefix = it["header"] + it["definitions"] + "\n"
    expected = "namespace GDT.Expected\nopen GDT\n\n" + "\n\n".join(stmt_text(m) + " := by\n  sorry" for m in order) + "\n\nend GDT.Expected\n\n"
    body = "namespace GDT.Challenge\nopen GDT\n\n"
    for m in order:
        ind = "\n".join("  " + l if l.strip() else l for l in chosen[m]["proof"].rstrip("\n").split("\n"))
        body += stmt_text(m) + " := by\n" + ind + "\n\n"
    body += "end GDT.Challenge\n"
    exp_lines = range(prefix.count("\n") + 1, (prefix + expected).count("\n") + 1)
    return prefix + expected + body + "\n" + check_all_block(order), exp_lines

def certify_source(source, exp_lines, order):
    rec = dict(checks={})
    with tempfile.TemporaryDirectory(dir=vs.LEAN49) as td:
        mod = "RPIAssembly"; path = Path(td) / f"{mod}.lean"; path.write_text(source)
        t0 = time.time()
        p = subprocess.run(["lake", "env", "lean", f"--root={td}", "-o", str(Path(td) / f"{mod}.olean"), str(path)],
                           cwd=vs.LEAN49, capture_output=True, text=True, timeout=1800)
        rec["compile_wall_s"] = round(time.time() - t0, 1)
        out = p.stdout + p.stderr
        msgs = [m for m in vs.parse_messages(out) if m["line"] not in exp_lines]
        rec["errors"] = [dict(line=m["line"], data=m["data"][:300]) for m in msgs if m["severity"] == "error"][:10]
        rec["checks"]["compile"] = p.returncode == 0 and not rec["errors"]
        mm = re.search(r"@@RPI_ASSEMBLY (\{.*\})", out)
        rec["checks"]["check_ran"] = mm is not None
        res = json.loads(mm.group(1)) if mm else {"members": [], "local_axioms": []}
        rows = {r["name"]: r for r in res["members"]}
        rec["members"] = rows
        rec["checks"]["all_present_theorems"] = mm is not None and all(rows.get(m, {}).get("present") and rows[m].get("is_theorem") for m in order)
        rec["checks"]["all_statements_alpha_equivalent"] = mm is not None and all(rows.get(m, {}).get("type_alpha_equivalent") for m in order)
        rec["checks"]["all_axioms_whitelisted"] = mm is not None and all(
            rows.get(m, {}).get("axioms") is not None and all(a in vs.ALLOWED for a in rows[m]["axioms"]) for m in order)
        declared = [a for a in res["local_axioms"] if not vs.SPEC.search(a)]
        rec["declared_axioms"] = declared
        rec["checks"]["no_declared_axioms"] = mm is not None and not declared
        rec["checks"]["no_weakening_options"] = not any(o in source for o in vs.FORBIDDEN_OPTIONS)
        if all(rec["checks"].values()):
            env = dict(os.environ)
            lp = subprocess.run(["lake", "env", "printenv", "LEAN_PATH"], cwd=vs.LEAN49, capture_output=True, text=True).stdout.strip()
            env["LEAN_PATH"] = lp + ":" + td
            t1 = time.time()
            q = subprocess.run([vs.L4C, mod], cwd=vs.LEAN49, capture_output=True, text=True, env=env, timeout=1800)
            rec["lean4checker_wall_s"] = round(time.time() - t1, 1)
            rec["checks"]["lean4checker"] = q.returncode == 0
        else:
            rec["checks"]["lean4checker"] = False
            rec["lean4checker_skipped"] = True
    rec["certified"] = all(rec["checks"].values())
    return rec

def assemble(target, candidates, keep_source=None):
    out = dict(target=target, schema="rpi-ds-001d.2/assembly/v1")
    try:
        members, chosen, missing, conflicts, extraneous = select(target, candidates)
        order = topo_order(members)
    except AssemblyError as e:
        return dict(out, outcome="error", claim="none", error=str(e))
    out.update(order=order, extraneous_candidates=extraneous,
               chosen={m: dict(sample_index=c["sample_index"], provenance=c.get("provenance"),
                               generation_id=c.get("generation_id"),
                               proof_sha256=hashlib.sha256(c["proof"].encode()).hexdigest()) for m, c in chosen.items()})
    if conflicts:
        return dict(out, outcome="conflict", claim="none", conflicts=conflicts)
    if missing:
        return dict(out, outcome="incomplete", claim="none", missing=missing)
    source, exp = build_source(target, order, chosen)
    out["source_sha256"] = hashlib.sha256(source.encode()).hexdigest()
    if keep_source:
        Path(keep_source).write_text(source)
    rec = certify_source(source, exp, order)
    out["certification"] = rec
    if not rec["certified"]:
        return dict(out, outcome="rejected", claim="none")
    ref = reference_lines()
    hits = {m: sorted({" ".join(l.split()) for l in chosen[m]["proof"].split("\n")} & ref)[:3] for m in order}
    hits = {m: h for m, h in hits.items() if h}
    out["reference_text_hits"] = hits
    all_model = all(chosen[m].get("provenance") == "model" and chosen[m].get("generation_id") for m in order)
    if not all_model:
        claim = "fixture_only"
    elif hits:
        claim = "reference_text_detected"
    else:
        claim = "c2_success"
    return dict(out, outcome="certified", claim=claim)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--target", required=True); ap.add_argument("--candidates", required=True)
    ap.add_argument("--json"); ap.add_argument("--keep-source")
    a = ap.parse_args()
    cands = [json.loads(l) for l in Path(a.candidates).read_text().splitlines() if l.strip()]
    r = assemble(a.target, cands, a.keep_source)
    s = json.dumps(r, indent=1, ensure_ascii=False)
    if a.json: Path(a.json).write_text(s + "\n")
    print(s)
    sys.exit(0 if r["outcome"] == "certified" else 1)
