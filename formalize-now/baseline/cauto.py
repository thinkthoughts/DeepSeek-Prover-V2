#!/usr/bin/env python3
"""RPI-DS-001c Cauto: CPU-only tactic baseline on the 39 GDT-Ladder items.

For each tactic script T in TACTICS, one Lean file is generated containing the
trusted header and definitions and all 39 item statements, each closed by T (no
reference proof text is used; statements are taken verbatim from
benchmark/gdt_items_v2.jsonl). Each declaration runs under
`set_option maxHeartbeats 200000 in` (the V1.5 header sets 0 = unlimited) so a
failure to terminate is recorded as a timeout. Per-declaration elaboration time
comes from monotonic timestamps printed between declarations (`IO.monoMsNow`;
Lean 4.9 elaborates the file sequentially). A declaration counts as a CANDIDATE solve when it
compiles without error; every candidate is then re-verified individually by
harness/verify_strict.py with independent kernel replay, and only `certified`
results count as solved.

`exact?` / `apply?` are excluded: they are proof-search commands whose 4.9 front
end has a documented sorry-suppression bug, and they would make the baseline a
library-search experiment rather than an automation baseline.
"""
import json, re, subprocess, sys, time
from pathlib import Path
F = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(F / "harness"))
import verify_strict as vs

DEFS = "GDT.rad, GDT.d, GDT.R, GDT.Tmin, GDT.Admissible, GDT.accepted, GDT.S, GDT.IsPeriod"
TACTICS = {
    "simp": "simp",
    "simp_all": "simp_all",
    "omega": "omega",
    "norm_num": "norm_num",
    "decide": "decide",
    "aesop": "aesop",
    "linarith": "linarith",
    "simp_all_defs": f"simp_all [{DEFS}]",
    "intros_simp_all_defs_omega": f"intros; simp_all [{DEFS}] <;> omega",
    "norm_num_defs_aesop": f"norm_num [{DEFS}] <;> aesop",
}
HEARTBEATS = 200000
items = [json.loads(l) for l in (F / "benchmark/gdt_items_v2.jsonl").read_text().splitlines()]

def build(tac):
    src = items[0]["header"] + items[0]["definitions"] + "\n"
    stamp = lambda tag: f'#eval show IO Unit from do IO.println s!"@@T {tag} {{← IO.monoMsNow}}"\n\n'

    starts = {}
    for it in items:
        st = it["formal_statement"]
        assert st.count(":= by\n  sorry") == 1
        st = re.sub(r"^(theorem|lemma) ", rf"set_option maxHeartbeats {HEARTBEATS} in\n\1 ", st, count=1, flags=re.M)
        st = st.replace(":= by\n  sorry", ":= by\n  " + tac)
        decl_line = (src + st.split("set_option maxHeartbeats")[0]).count("\n") + 2
        starts[it["id"]] = decl_line
        src += stamp("begin " + it["id"]) + st + "\n\n" + stamp("end " + it["id"])
    return src, starts

def run(name, tac, outdir):
    src, starts = build(tac)
    path = outdir / f"cauto_{name}.lean"; path.write_text(src)
    t0 = time.time()
    p = subprocess.run(["lake", "env", "lean", str(path)], cwd=vs.LEAN49, capture_output=True, text=True, timeout=3600)
    wall = time.time() - t0
    out = p.stdout + p.stderr
    (outdir / f"cauto_{name}.log").write_text(out + f"\n# exit={p.returncode} wall_s={wall:.1f}\n")
    msgs = vs.parse_messages(out)
    order = sorted(starts.items(), key=lambda kv: kv[1])
    def owner(line):
        o = None
        for iid, l in order:
            if l - 1 <= line: o = iid
        return o
    res = {iid: dict(errors=[], timeout=False, elab_ms=None) for iid in starts}
    for m in msgs:
        iid = owner(m["line"])
        if iid is None: continue
        if m["severity"] == "error":
            res[iid]["errors"].append(m["data"][:200])
            if "heartbeats" in m["data"] or "timeout" in m["data"]: res[iid]["timeout"] = True
    t = {}
    for m in re.finditer(r"@@T (begin|end) (\S+) (\d+)", out):
        t.setdefault(m.group(2), {})[m.group(1)] = int(m.group(3))
    for iid, v in t.items():
        if iid in res and "begin" in v and "end" in v:
            res[iid]["elab_ms"] = v["end"] - v["begin"]
    return res, round(wall, 1), p.returncode

def main():
    outdir = F / "baseline/runs"; outdir.mkdir(parents=True, exist_ok=True)
    table, runs = {it["id"]: {} for it in items}, {}
    for name, tac in TACTICS.items():
        res, wall, rc = run(name, tac, outdir)
        runs[name] = dict(tactic=tac, file_wall_s=wall, exit=rc)
        for iid, r in res.items():
            table[iid][name] = dict(candidate=not r["errors"], timeout=r["timeout"], elab_ms=r["elab_ms"],
                                    first_error=r["errors"][0] if r["errors"] else None)
        print(f"{name:28s} wall={wall:6.1f}s candidates={sum(not r['errors'] for r in res.values())} timeouts={sum(r['timeout'] for r in res.values())}", flush=True)
    # strict certification of every candidate (independent kernel replay)
    for iid, row in table.items():
        for name, cell in row.items():
            if cell["candidate"]:
                r = vs.verify(iid, TACTICS[name], "proof", use_l4c=True)
                cell["strict_status"] = r["status"]; cell["strict_reasons"] = r["reasons"]
                print(f"  verify {iid:46s} {name:28s} -> {r['status']}", flush=True)
    solved = {iid: sorted(n for n, c in row.items() if c.get("strict_status") == "certified") for iid, row in table.items()}
    summary = dict(schema="rpi-ds-001c/cauto/v1", heartbeats_per_declaration=HEARTBEATS, tactics=TACTICS, runs=runs,
                   items=len(items), solved_items=sorted(i for i, s in solved.items() if s),
                   solved_count=sum(1 for s in solved.values() if s), solved_by=solved, table=table)
    (F / "baseline/cauto_results.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    print("SOLVED", summary["solved_count"], "/", len(items), summary["solved_items"])

if __name__ == "__main__":
    main()
