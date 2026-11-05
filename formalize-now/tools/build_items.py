#!/usr/bin/env python3
"""RPI-DS-001a: benchmark item scaffold in DeepSeek-Prover-V1.5/V2 prompt shape.

Each item = V1.5 default header + the translated GDT definitions block +
one statement ending in `:= by\n  sorry` (the model's completion slot).
No proofs are included. Writes benchmark/gdt_items.jsonl and a combined
check file benchmark/AllItemsCheck.lean (all statements under one header),
used only to test that the header and definitions elaborate together.
"""
import json, re, sys
from pathlib import Path
F = Path(sys.argv[1])
HEADER = "import Mathlib\nimport Aesop\n\nset_option maxHeartbeats 0\n\nopen BigOperators Real Nat Topology Rat\n\n"  # prover/utils.py LEAN4_DEFAULT_HEADER
defs = (F / "lean49/GDTBench/Defs.lean").read_text()
defs_body = "\n".join(l for l in defs.split("\n") if not l.startswith("import ") and not l.startswith("-- RPI"))
defs_body = defs_body.strip() + "\n"
man = json.loads((F / "manifest/gdt_manifest.json").read_text())
items = []
srcs = {"challenge_theorem": (F / "lean49/GDTBench/Challenge.lean").read_text(),
        "helper_lemma": (F / "lean49/GDTBench/Ladder.lean").read_text()}
for d in sorted(man["declarations"], key=lambda d: (d["role"] != "challenge_theorem", d["source_line"])):
    if d["role"] == "definition": continue
    text = srcs[d["role"]]
    m = re.search(rf"^(theorem|lemma) {re.escape(d['short'])}\b(.*?):=\s*\n?\s*sorry", text, flags=re.S | re.M)
    assert m, d["short"]
    stmt = f"{m.group(1)} {d['short']}{m.group(2).rstrip()} := by\n  sorry"
    items.append(dict(
        id=f"gdt/{d['short']}", role=d["role"], source_file=d["source_file"], source_line=d["source_line"],
        header=HEADER,
        definitions="namespace GDT\n" + defs_body.split("namespace GDT", 1)[1].split("end GDT")[0] + "end GDT\n",
        formal_statement="namespace GDT.Challenge\nopen GDT\n\n" + stmt + "\n\nend GDT.Challenge",
        kernel_deps=d["kernel_deps"], type_hash_lean434=d["type_hash"]))
with open(F / "benchmark/gdt_items.jsonl", "w") as f:
    for it in items: f.write(json.dumps(it, ensure_ascii=False) + "\n")
combined = HEADER + items[0]["definitions"] + "\n" + "\n\n".join(it["formal_statement"] for it in items) + "\n"
# items share the namespace; names are distinct, so they can coexist in one check file
(F / "benchmark/AllItemsCheck.lean").write_text("-- RPI-DS-001a GENERATED: all benchmark items under the V1.5 header (elaboration check only).\n" + combined)
print(len(items), "items")
