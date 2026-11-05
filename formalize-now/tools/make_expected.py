#!/usr/bin/env python3
"""RPI-DS-001b: build lean49/GDTBench/Expected.lean, the reference signatures.

Expected.lean = Challenge.lean + Ladder.lean (both derived verbatim from the GDT
source in RPI-DS-001a) with the namespace `GDT.Challenge` renamed to
`GDT.Expected`, so the expected statements and the repaired proofs load together
and their elaborated types can be compared with `Expr` equality
(tools/SigCheck.lean). No statement type mentions a `GDT.Challenge` constant
(asserted below from the Stage 0 kernel record), so the rename touches only the
declared names.
"""
import json
from pathlib import Path
F = Path(__file__).resolve().parent.parent
kern = json.loads((F / "logs/deps_solution.json").read_text())
assert not any("Challenge" in x for d in kern for x in d["type_deps"])
def body(p):
    t = (F / p).read_text()
    t = "\n".join(l for l in t.split("\n") if not l.startswith("import ") and not l.startswith("-- RPI"))
    return t.replace("namespace GDT.Challenge", "namespace GDT.Expected").replace("end GDT.Challenge", "end GDT.Expected")
out = ("-- RPI-DS-001b GENERATED: expected signatures (Challenge + Ladder, namespace renamed).\n"
       "-- Proofs are `sorry` by design; only the declared types are used (tools/SigCheck.lean).\n"
       "import GDTBench.Defs\nimport Mathlib.Data.Nat.Squarefree\n"
       + body("lean49/GDTBench/Challenge.lean") + "\n" + body("lean49/GDTBench/Ladder.lean") + "\n")
(F / "lean49/GDTBench/Expected.lean").write_text(out)
print("ok:", out.count("sorry"), "statements")
