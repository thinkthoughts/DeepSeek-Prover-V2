#!/usr/bin/env python3
"""RPI-DS-001c: REPL adapter vs direct strict verifier on identical candidates.
Uses the same 16 candidate cases as run_tests.py. Compares, per case, the REPL
C1–C7 vector and status with the direct path (direct run without kernel replay,
so both paths are compared at the `preliminary` level), then certifies the valid
cases and two invalid ones through the adapter's certify mode.
usage: run_repl_tests.py  (needs RPI_REPL and LEAN4CHECKER; writes tests/repl_results.json)
"""
import json, sys, time
from pathlib import Path
H = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(H)); sys.path.insert(0, str(H / "tests"))
import verify_strict as vs
from repl_adapter import Repl, verify_repl
from run_tests import STATUS_CASES

def main():
    repl = Repl(); print("REPL import Mathlib:", repl.import_s, "s")
    rows, disagreements = [], 0
    for cid, item, mode, cand, _expect, _l4c in STATUS_CASES:
        t0 = time.time(); d = vs.verify(item, cand, mode, use_l4c=False); td = time.time() - t0
        r = verify_repl(repl, item, cand, mode)
        keys = vs.REQUIRED + (["prefix"] if mode == "full-code" else [])
        same = all(d["checks"].get(k) == r["checks"].get(k) for k in keys) and d["status"] == r["status"]
        disagreements += not same
        rows.append(dict(case=cid, direct_status=d["status"], repl_status=r["status"], agree=same,
                         direct_checks={k: d["checks"].get(k) for k in keys}, repl_checks={k: r["checks"].get(k) for k in keys},
                         repl_sorries_in_candidate=r.get("repl_sorries_in_candidate"),
                         v15_complete_on_repl_messages=r.get("v15_complete_equivalent"),
                         direct_wall_s=round(td, 1), repl_wall_s=r.get("wall_s")))
        print(f"{cid:44s} direct={d['status']:11s} repl={r['status']:11s} {'AGREE' if same else 'DISAGREE'}  v15(repl msgs)={r.get('v15_complete_equivalent')}  t_direct={td:.1f}s t_repl={r.get('wall_s')}s")
    cert = []
    for cid, item, mode, cand, expect, _ in STATUS_CASES:
        if cid in ("V1_valid_proof_gdt_empty", "V2_valid_proof_coprime_add_mul_right", "V3_valid_full_code_gdt_empty",
                   "I4_weakened_statement_full_code", "I5_local_axiom_full_code"):
            r = verify_repl(repl, item, cand, mode, certify=True)
            ok = r["status"] == expect
            disagreements += not ok
            cert.append(dict(case=cid, expected=expect, status=r["status"], passed=ok,
                             direct_recheck=r.get("direct_recheck", {}).get("status"), reasons=r["reasons"]))
            print(f"certify {cid:36s} expect={expect:10s} got={r['status']:10s} {'PASS' if ok else 'FAIL'}")
    repl.close()
    (H / "tests/repl_results.json").write_text(json.dumps(dict(repl_import_s=repl.import_s, disagreements=disagreements,
        comparison=rows, certify_mode=cert), indent=1, ensure_ascii=False) + "\n")
    sys.exit(1 if disagreements else 0)

if __name__ == "__main__":
    main()
