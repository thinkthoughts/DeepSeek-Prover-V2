#!/usr/bin/env python3
"""RPI-DS-001b: combine the Lean certification output with textual checks.

1. signatures: every declaration's text up to its top-level `:=` is byte-identical
   in SolutionPort.lean (original proofs) and SolutionRef.lean (repaired proofs);
2. placeholder scan of SolutionRef.lean (additional safeguard only);
3. Lean SigCheck JSON: alpha-equivalent types + whitelist axioms; any strict
   difference must be a binder-name difference (hygienic `_@` names, or a leading
   `_` on a hypothesis name, which the original Solution already uses);
4. writes manifest/certification_lean49.json and fills `verification` in
   manifest/proof_port_log.json.
usage: certify49.py <sigcheck.log>
"""
import json, re, sys
from pathlib import Path
F = Path(__file__).resolve().parent.parent
DECL = re.compile(r"^(theorem|lemma|def|instance)\s+(\S+)", re.M)
def sigs(path):
    t = path.read_text(); hits = list(DECL.finditer(t)); out = {}
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(t); depth = 0
        for j in range(m.start(), end):
            c = t[j]
            if c in "([{⦃": depth += 1
            elif c in ")]}⦄": depth -= 1
            elif t.startswith(":=", j) and depth == 0:
                out[m.group(2)] = t[m.start():j]; break
    return out
port = sigs(F / "lean49/GDTBench/SolutionPort.lean"); ref = sigs(F / "lean49/GDTBench/SolutionRef.lean")
sig_ok = {n: port.get(n) == ref.get(n) for n in port}
assert set(port) == set(ref)
reftext = (F / "lean49/GDTBench/SolutionRef.lean").read_text()
code = re.sub(r"/-.*?-/", "", reftext, flags=re.S); code = re.sub(r"--[^\n]*", "", code)
FORBID = ["sorry", "admit", "apply?", "exact?", "native_decide", "decide!", "implemented_by", "extern", "axiom", "unsafe", "opaque", "debug.skipKernelTC"]
hits = {w: len(re.findall(rf"(?<![\w.]){re.escape(w)}(?![\w])", code)) for w in FORBID}
raw = Path(sys.argv[1]).read_text()
lean = json.loads(raw.split("@@RPI_JSON_BEGIN", 1)[1].split("@@RPI_JSON_END", 1)[0])
def benign(d):
    if d is None: return True
    a, b = d
    if "._@." in a and "._@." in b: return a.split("._@.")[0] == b.split("._@.")[0]
    return a.lstrip("_") == b.lstrip("_")
rows = []
for r in lean["rows"]:
    short = r["name"].split(".")[-1]
    r["signature_text_unchanged_vs_original_solution"] = sig_ok.get(short)
    r["strict_difference_is_binder_name_only"] = r["type_equal_strict"] or benign(r.get("strict_difference"))
    r["certified"] = (r["status"] == "certified" and r["signature_text_unchanged_vs_original_solution"]
                      and r["strict_difference_is_binder_name_only"])
    rows.append(r)
cert = dict(schema="rpi-ds-001b/certification/v1", environment="Lean 4.9.0-rc1, Mathlib d1d1e4b7",
            module="GDTBench.SolutionRef", expected_module="GDTBench.Expected",
            rule="theorem; type alpha-equivalent to expected; axioms subset of {propext, Quot.sound, Classical.choice}; signature text identical to original Solution; strict differences binder names only",
            expected_count=lean["expected_count"], certified=sum(r["certified"] for r in rows),
            unexpected_theorems=lean["unexpected_theorems"], placeholder_scan=hits,
            signatures_compared=len(sig_ok), signatures_identical=sum(sig_ok.values()),
            definitions_file="lean49/GDTBench/Defs.lean (RPI-DS-001a translation, unchanged in 001b; see `git diff 31d818a -- formalize-now/lean49/GDTBench/Defs.lean`)",
            rows=rows)
(F / "manifest/certification_lean49.json").write_text(json.dumps(cert, indent=1, ensure_ascii=False) + "\n")
logp = F / "manifest/proof_port_log.json"; log = json.loads(logp.read_text())
byname = {r["name"].split(".")[-1]: r for r in rows}
for e in log["edits"]:
    r = byname[e["decl"]]
    e["verification"] = dict(elaborates=True, certified=r["certified"], axioms=r["axioms"],
                             type_alpha_equivalent=r["type_eqv"], signature_text_unchanged=r["signature_text_unchanged_vs_original_solution"],
                             commands=["cd formalize-now/lean49 && lake build", "cd formalize-now/lean49 && lake env lean ../tools/SigCheck.lean"])
logp.write_text(json.dumps(log, indent=1, ensure_ascii=False) + "\n")
print("certified", cert["certified"], "/", cert["expected_count"], "| scan", {k: v for k, v in hits.items() if v}, "| sigs unchanged", all(sig_ok.values()))
