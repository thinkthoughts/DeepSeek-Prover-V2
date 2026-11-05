#!/usr/bin/env python3
"""RPI-DS-001a: generate data tables for the dependency and compatibility reports
from the manifest and Lean logs. Writes manifest/lean49_port_status.json and
reports/_generated_*.md (included verbatim in the hand-written reports)."""
import json, re
from pathlib import Path
F = Path(__file__).resolve().parent.parent
man = json.loads((F / "manifest/gdt_manifest.json").read_text())
decls = {d["name"]: d for d in man["declarations"]}
short = lambda n: n.split(".")[-1]

# --- dependency table
rows = ["| Declaration | Role | Line | Kernel deps (GDT) | Syntactic-only | Kernel-only | Axioms |", "|---|---|---|---|---|---|---|"]
for d in sorted(man["declarations"], key=lambda d: (d["source_file"], d["source_line"])):
    kd = [short(x) for x in d["kernel_deps"]]
    rows.append(f"| `{d['short']}` | {d['role']} | {d['source_file'].split('/')[0]}:{d['source_line']} | {', '.join(kd) or '—'} | "
                f"{', '.join(short(x) for x in d['syntactic_only']) or '—'} | {', '.join(short(x) for x in d['kernel_only']) or '—'} | "
                f"{', '.join(d['axioms']) or 'none'} |")
(F / "reports/_generated_dependencies.md").write_text("\n".join(rows) + "\n")

# --- Lean 4.9 port status
src = (F / "lean49/GDTBench/SolutionPort.lean").read_text().split("\n")
starts = [(i + 1, m.group(2)) for i, l in enumerate(src) if (m := re.match(r"^(theorem|lemma|def|instance)\s+(\S+)", l))]
log = (F / "logs/lean49_SolutionPort.log").read_text()
errs = re.findall(r":(\d+):\d+: error: (.*?)(?=\n\S+\.lean:\d+:\d+:|\n# exit)", log, flags=re.S)
direct = {}
for ln, msg in errs:
    d = [n for (l, n) in starts if l <= int(ln)][-1]
    direct.setdefault(d, []).append(msg.strip().split("\n")[0][:120])
ax = dict(re.findall(r"'GDT\.Challenge\.(\S+)' depends on axioms: \[([^\]]*)\]", (F / "logs/lean49_axiom_probe.log").read_text()))
status = {}
for d in man["declarations"]:
    if d["kind"] != "theorem": continue
    s = d["short"]; a = ax.get(s)
    if s in direct: st = "direct_error"
    elif a is None: st = "not_reported"
    elif "sorryAx" in a: st = "inherits_sorryAx"
    else: st = "kernel_clean"
    status[s] = dict(status=st, errors=direct.get(s, []), axioms_lean49=[x.strip() for x in a.split(",")] if a else None,
                     role=d["role"])
(F / "manifest/lean49_port_status.json").write_text(json.dumps(status, indent=1, ensure_ascii=False) + "\n")
rows = ["| Declaration | Role | Lean 4.9 status of the unchanged proof | First error |", "|---|---|---|---|"]
order = {"kernel_clean": 0, "inherits_sorryAx": 1, "direct_error": 2, "not_reported": 3}
for s, v in sorted(status.items(), key=lambda kv: (order[kv[1]["status"]], kv[0])):
    rows.append(f"| `{s}` | {v['role']} | {v['status']} | {(v['errors'][0] if v['errors'] else '—').replace('|', '/')} |")
counts = {}
for v in status.values(): counts[v["status"]] = counts.get(v["status"], 0) + 1
(F / "reports/_generated_lean49_port.md").write_text(f"Counts: {json.dumps(counts)}\n\n" + "\n".join(rows) + "\n")

# --- statement surface comparison
a = {x["name"]: x for x in json.loads((F / "logs/surface_lean434.json").read_text())}
b = {x["name"]: x for x in json.loads((F / "logs/surface_lean49.json").read_text())}
c = {x["name"]: x for x in json.loads((F / "logs/surface_items_lean49.json").read_text())}
inst = lambda n: ("inst" in n) or re.search(r"\.to[A-Z]", n) is not None
rows = ["| Declaration | pp 4.34 = pp 4.9 | non-instance constants equal | instance-path differences | item (V1.5 header) constants = translated |", "|---|---|---|---|---|"]
for n in sorted(a):
    da = set(a[n]["type_consts"]); db = set(b[n]["type_consts"])
    head_eq = {x for x in da if not inst(x)} == {x for x in db if not inst(x)}
    rows.append(f"| `{short(n)}` | {a[n]['type_pp'] == b[n]['type_pp']} | {head_eq} | {', '.join(sorted(da ^ db)) or '—'} | "
                f"{(c[n]['type_consts'] == b[n]['type_consts']) if n in c else 'n/a'} |")
(F / "reports/_generated_surface.md").write_text("\n".join(rows) + "\n")
print(counts)
