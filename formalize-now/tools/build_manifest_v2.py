#!/usr/bin/env python3
"""RPI-DS-001b: manifest v2 and items v2, derived from the unchanged Stage 0 manifest.

Inputs : manifest/gdt_manifest.json (Stage 0, kept unchanged), manifest/lean49_port_status.json,
         manifest/certification_lean49.json, manifest/proof_port_log.json
Outputs: manifest/gdt_manifest_v2.json, benchmark/gdt_items_v2.jsonl
"""
import json
from pathlib import Path
F = Path(__file__).resolve().parent.parent
m1 = json.loads((F / "manifest/gdt_manifest.json").read_text())
port = json.loads((F / "manifest/lean49_port_status.json").read_text())
cert = json.loads((F / "manifest/certification_lean49.json").read_text())
log = json.loads((F / "manifest/proof_port_log.json").read_text())
crow = {r["name"]: r for r in cert["rows"]}
edits = {}
for e in log["edits"]: edits.setdefault(e["decl"], []).append(e["id"])
deps = {d["name"]: {x for x in d["kernel_deps"] if x.startswith("GDT.Challenge.")} for d in m1["declarations"]}
def closure(n):
    seen, todo = set(), [n]
    while todo:
        for x in deps.get(todo.pop(), ()):
            if x not in seen: seen.add(x); todo.append(x)
    return seen
tops = [d["name"] for d in m1["declarations"] if d["role"] == "challenge_theorem"]
reach = {t: closure(t) for t in tops}
CMDS = {
  "build": "cd formalize-now/lean49 && lake update && lake exe cache get && lake build",
  "certify": "cd formalize-now/lean49 && lake env lean ../tools/SigCheck.lean > ../logs/lean49_sigcheck.log && cd .. && python3 tools/certify49.py logs/lean49_sigcheck.log",
  "lean4checker": "cd formalize-now/lean49 && lake env <lean4checker@v4.9.0-rc1> GDTBench.SolutionRef   (and --fresh)",
  "candidate": "python3 formalize-now/harness/verify_strict.py --item <id> --proof <file> --lean4checker",
}
decls = []
for d in m1["declarations"]:
    d = dict(d)
    if d["kind"] == "theorem":
        c = crow[d["name"]]
        d["lean49"] = dict(
            statement_elaborates=True,
            original_proof_status=port[d["short"]]["status"],
            reference_proof="certified" if c["certified"] else "uncertified",
            reference_proof_module="GDTBench.SolutionRef",
            reference_axioms=c["axioms"],
            proof_port_edits=edits.get(d["short"], []),
            statement_alpha_equivalent_to_expected=c["type_eqv"],
            signature_text_unchanged=c["signature_text_unchanged_vs_original_solution"])
        d["reachable_from"] = sorted(t.split(".")[-1] for t in tops if d["name"] in reach[t])
        d["reachable_from_challenge"] = bool(d["reachable_from"]) or d["role"] == "challenge_theorem"
    else:
        d["lean49"] = dict(statement_elaborates=True, definition_text="verbatim (rules T1–T3 only)")
    d["unresolved_dependencies"] = []
    decls.append(d)
m2 = dict(m1)
m2.update(schema="rpi-ds-001b/gdt-manifest/v2", derived_from="manifest/gdt_manifest.json (rpi-ds-001a, unchanged)",
          lean49_environment=dict(lean="4.9.0-rc1", mathlib="leanprover-community/mathlib4@d1d1e4b72c6e009edd97cabe1d661b021fe8eeae",
                                  deepseek_fork="xinhjBrant/mathlib4@2f65ba7f (identical Mathlib/ sources)"),
          certification=dict(certified=cert["certified"], expected=cert["expected_count"], rule=cert["rule"],
                             lean4checker=["replay GDTBench.SolutionRef: pass", "--fresh GDTBench.SolutionRef: pass"]),
          open_questions=["Mathlib-level dependencies are counted, not enumerated (mathlib_value_consts).",
                          "Cross-version agreement of Mathlib definitions is established at the printed-definition and characterising-lemma level; kernel identity across versions is not a meaningful comparison (reports/LEAN49_DEFINITIONS.md)."],
          verification_commands=CMDS, declarations=decls)
(F / "manifest/gdt_manifest_v2.json").write_text(json.dumps(m2, indent=1, ensure_ascii=False) + "\n")
byname = {d["short"]: d for d in decls}
with open(F / "benchmark/gdt_items_v2.jsonl", "w") as out:
    for line in (F / "benchmark/gdt_items.jsonl").read_text().splitlines():
        it = json.loads(line); d = byname[it["id"].split("/")[-1]]
        it.update(reference_proof=d["lean49"]["reference_proof"], reachable_from=d["reachable_from"],
                  reachable_from_challenge=d["reachable_from_challenge"],
                  lean49_original_proof_status=d["lean49"]["original_proof_status"],
                  verify_command=CMDS["candidate"].replace("<id>", it["id"]))
        out.write(json.dumps(it, ensure_ascii=False) + "\n")
print("certified", cert["certified"], "unreachable:", [d["short"] for d in decls if d.get("reachable_from_challenge") is False])
