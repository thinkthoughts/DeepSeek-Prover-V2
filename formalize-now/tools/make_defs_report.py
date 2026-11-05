#!/usr/bin/env python3
"""RPI-DS-001b: classify cross-version agreement of Mathlib definitions/lemmas
from logs/mathlib_defs_lean434.json and logs/mathlib_defs_lean49.json
(produced by tools/MathlibDefs.lean). Writes reports/_generated_definitions.md."""
import json, re
from pathlib import Path
F = Path(__file__).resolve().parent.parent
a = {x["name"]: x for x in json.loads((F / "logs/mathlib_defs_lean434.json").read_text())}
b = {x["name"]: x for x in json.loads((F / "logs/mathlib_defs_lean49.json").read_text())}
def norm(s):
    s = re.sub(r"\[inst(_\d+)? : ([^\]]+)\]", r"[\2]", s)       # instance binder display
    s = re.sub(r"Nat\.Prime (\w+)", r"\1.Prime", s)                  # dot-notation display
    s = re.sub(r"\{(\w+) ∈ ([^|{}]+?) \| ([^{}]+?)\}", lambda m: f"(Finset.filter (fun {m[1]} => {m[3]}) ({m[2].strip()}))", s)
    return s
rows = ["| Constant | Kind | Statement/type | Body | Classification |", "|---|---|---|---|---|"]
for n, x in a.items():
    y = b[n]
    if not (x["present"] and y["present"]):
        rows.append(f"| `{n}` | — | — | — | present in 4.34: {x['present']}, in 4.9: {y['present']} |"); continue
    t = x["type_pp"] == y["type_pp"]; v = x["value_pp"] == y["value_pp"]
    tn = norm(x["type_pp"]) == norm(y["type_pp"]); vn = norm(x["value_pp"]) == norm(y["value_pp"])
    if t and v: cls = "A: identical printed type and body"
    elif (t or tn) and (v or vn): cls = "B: identical up to display (instance binders, dot/set-builder notation)"
    else: cls = "C: differs in printed form; see notes"
    rows.append(f"| `{n}` | {x['kind']} | {'same' if t else ('same up to display' if tn else 'differs')} | "
                f"{'—' if not x['value_pp'] else ('same' if v else ('same up to display' if vn else 'differs'))} | {cls} |")
(F / "reports/_generated_definitions.md").write_text("\n".join(rows) + "\n")
print("\n".join(r for r in rows if "C:" in r))
