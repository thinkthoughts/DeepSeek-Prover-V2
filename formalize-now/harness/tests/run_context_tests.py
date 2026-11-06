#!/usr/bin/env python3
"""RPI-DS-001d: tests for the trusted C2 verification context (reference_deps=True).

R1–R39: every item's own reference proof body, placed under the trusted DeepSeek V1.5
        header + definitions + statement, with the item's dependency closure supplied as
        certified reference declarations. Expected: certified (direct path, kernel replay).
        This also shows that all 39 reference proofs elaborate under the prompt header
        (`import Mathlib`, `open BigOperators Real Nat Topology Rat`).
N1:     a C2 candidate citing a lemma outside its dependency closure. Expected: rejected.
N2:     without reference_deps, a body citing a dependency. Expected: rejected (C1).
usage: run_context_tests.py  (needs LEAN4CHECKER; writes tests/context_results.json)
"""
import json, sys, time
from pathlib import Path
H = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(H)); sys.path.insert(0, str(H / "tests"))
import verify_strict as vs
from run_tests import ref_body

def main():
    items = [json.loads(l)["id"] for l in (H.parent / "benchmark/gdt_items_v2.jsonl").read_text().splitlines()]
    rows, fails = [], 0
    for iid in items:
        t0 = time.time()
        r = vs.verify(iid, ref_body(iid.split("/")[-1]), "proof", use_l4c=True, reference_deps=True)
        ok = r["status"] == "certified"; fails += not ok
        rows.append(dict(case=f"R_{iid}", status=r["status"], reasons=r["reasons"], context=len(r.get("reference_context", [])),
                         wall_s=round(time.time() - t0, 1), passed=ok,
                         first_errors=[m["data"][:200] for m in r.get("messages", []) if m["severity"] == "error"][:2]))
        print(f"R {iid:48s} ctx={len(r.get('reference_context', [])):2d} {r['status']:10s} {'PASS' if ok else 'FAIL'} {r['reasons']}", flush=True)
    neg = [("N1_cites_lemma_outside_closure", "gdt/gcd_with_N_iff_gcd_with_R", "exact (gdt_periodic hN hm h 0).1", True),
           ("N2_cites_dependency_without_context", "gdt/gcd_with_N_iff_gcd_with_R", ref_body("gcd_with_N_iff_gcd_with_R"), False)]
    for cid, iid, body, ctx in neg:
        r = vs.verify(iid, body, "proof", use_l4c=True, reference_deps=ctx)
        ok = r["status"] == "rejected"; fails += not ok
        rows.append(dict(case=cid, status=r["status"], reasons=r["reasons"], passed=ok))
        print(f"{cid:50s} {r['status']:10s} {'PASS' if ok else 'FAIL'} {r['reasons']}", flush=True)
    (H / "tests/context_results.json").write_text(json.dumps(dict(failures=fails, cases=rows), indent=1, ensure_ascii=False) + "\n")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
