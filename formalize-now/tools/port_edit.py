#!/usr/bin/env python3
"""RPI-DS-001b: apply one logged proof-body edit to lean49/GDTBench/SolutionRef.lean.

usage: port_edit.py <edits.json>   (list of {decl, old, new, error, reason})
Each `old` must occur exactly once inside the named declaration and strictly
after the declaration's top-level `:=` (i.e. inside the proof body). Edits are
appended to manifest/proof_port_log.json with verification "pending";
tools/certify49.py fills in verification results.
"""
import json, re, sys
from pathlib import Path
F = Path(__file__).resolve().parent.parent
REF = F / "lean49/GDTBench/SolutionRef.lean"
LOG = F / "manifest/proof_port_log.json"
DECL = re.compile(r"^(theorem|lemma|def|instance)\s+(\S+)", re.M)

def body_span(text, name):
    hits = list(DECL.finditer(text))
    for i, m in enumerate(hits):
        if m.group(2) == name:
            end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
            depth = 0
            for j in range(m.start(), end):
                ch = text[j]
                if ch in "([{⦃": depth += 1
                elif ch in ")]}⦄": depth -= 1
                elif text.startswith(":=", j) and depth == 0:
                    return j + 2, end
    raise SystemExit(f"declaration {name} not found")

log = json.loads(LOG.read_text()) if LOG.exists() else {"schema": "rpi-ds-001b/proof-port-log/v1", "edits": []}
for e in json.loads(Path(sys.argv[1]).read_text()):
    text = REF.read_text()
    lo, hi = body_span(text, e["decl"])
    seg = text[lo:hi]
    n = seg.count(e["old"])
    if n != 1:
        raise SystemExit(f"{e['decl']}: fragment occurs {n} times in proof body")
    REF.write_text(text[:lo] + seg.replace(e["old"], e["new"], 1) + text[hi:])
    line = text.count("\n", 0, lo + seg.index(e["old"])) + 1
    log["edits"].append(dict(id=f"E{len(log['edits']) + 1:02d}", decl=e["decl"], line_in_SolutionPort=None,
                             line_in_SolutionRef=line, original=e["old"], revised=e["new"],
                             error_addressed=e["error"], reason=e["reason"], verification="pending"))
    print("applied", e["decl"], "at line", line)
LOG.write_text(json.dumps(log, indent=1, ensure_ascii=False) + "\n")
