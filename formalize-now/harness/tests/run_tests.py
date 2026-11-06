#!/usr/bin/env python3
"""RPI-DS-001b wrapper tests: valid and deliberately invalid candidates.
Each case states the expected decision of verify_strict.py; the run also records
what DeepSeek-Prover-V1.5's `complete` criterion would decide on the same compile.
usage: run_tests.py   (writes harness/tests/results.json; needs LEAN4CHECKER)
"""
import json, re, sys
from pathlib import Path
H = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(H))
from verify_strict import verify, load_item, count_certified
F = H.parent
ref = (F / "lean49/GDTBench/SolutionRef.lean").read_text()

def ref_body(name):
    m = re.search(rf"^(theorem|lemma) {name}\b.*?:= by\n(.*?)(?=^(theorem|lemma|def|end) )", ref, flags=re.S | re.M)
    body = re.split(r"\n/--", m.group(2))[0]          # drop the next declaration's docstring
    return "\n".join(l[2:] if l.startswith("  ") else l for l in body.rstrip().split("\n"))

def full(item_id, between="", stmt_override=None, proof=None):
    it = load_item(item_id)
    stmt = stmt_override or it["formal_statement"]
    head = stmt.rsplit(":= by\n  sorry", 1)[0] + ":= by\n"
    body = "\n".join("  " + l if l.strip() else l for l in (proof or ref_body(item_id.split('/')[-1])).split("\n"))
    return it["header"] + it["definitions"] + "\n" + between + head + body + "\n\nend GDT.Challenge\n"

E = "gdt/gdt_empty"; C = "gdt/coprime_add_mul_right"
empty_stmt = load_item(E)["formal_statement"]
CASES = [
 ("V1_valid_proof_gdt_empty", E, "proof", ref_body("gdt_empty"), True),
 ("V2_valid_proof_coprime_add_mul_right", C, "proof", ref_body("coprime_add_mul_right"), True),
 ("V3_valid_full_code_gdt_empty", E, "full-code", full(E), True),
 ("I1_sorry", E, "proof", "sorry", False),
 ("I2_admit", E, "proof", "admit", False),
 ("I3_compile_error", E, "proof", "exact foo_bar_baz", False),
 ("I4_weakened_statement_full_code", E, "full-code",
  full(E, stmt_override=empty_stmt.replace("S N L m a = ∅", "S N L m a = S N L m a"), proof="rfl"), False),
 ("I5_local_axiom_full_code", E, "full-code",
  full(E, between="axiom rpi_cheat : False\n\n", proof="exact rpi_cheat.elim"), False),
 ("I6_exit_after_partial_proof", E, "proof", "skip\n#exit", False),
 ("I7_native_decide_dependency", E, "full-code",
  full(E, between="theorem rpi_aux : 2 + 2 = 4 := by native_decide\n\n",
       proof="have _h := rpi_aux\n" + ref_body("gdt_empty")), False),
 ("I8_renamed_theorem_full_code", E, "full-code",
  full(E, stmt_override=empty_stmt.replace("theorem gdt_empty", "theorem gdt_empty'"), proof=ref_body("gdt_empty")), False),
 ("I9_prefix_tampering_full_code", E, "full-code",
  full(E).replace("def Tmin (N m : ℕ) : ℕ := m * R N m", "def Tmin (N m : ℕ) : ℕ := 0"), False),
 ("I10_skipKernelTC_option", E, "full-code",
  full(E, between="set_option debug.skipKernelTC true\n\n"), False),
]

# RPI-DS-001c: the 13 original cases run WITH kernel replay (expected certified/rejected);
# the P cases run WITHOUT it and must come out `preliminary` (or rejected), never certified.
STATUS_CASES = [(c[0], c[1], c[2], c[3], "certified" if c[4] else "rejected", True) for c in CASES] + [
 ("P1_valid_proof_without_kernel_replay", E, "proof", ref_body("gdt_empty"), "preliminary", False),
 ("P2_valid_full_code_without_kernel_replay", E, "full-code", full(E), "preliminary", False),
 ("P3_local_axiom_without_kernel_replay", E, "full-code",
  full(E, between="axiom rpi_cheat : False\n\n", proof="exact rpi_cheat.elim"), "rejected", False),
]

def main():
    out, fails, recs = [], 0, {}
    for cid, item, mode, cand, expect, l4c in STATUS_CASES:
        r = verify(item, cand, mode, l4c)
        recs[cid] = r
        ok = r["status"] == expect and r["accepted"] == (expect == "certified")
        fails += not ok
        out.append(dict(case=cid, item=item, mode=mode, kernel_replay_requested=l4c, expected_status=expect,
                        status=r["status"], accepted=r["accepted"], test_passed=ok, reasons=r["reasons"],
                        v15_complete_equivalent=r.get("v15_complete_equivalent"), token_scan=r.get("token_scan"),
                        lean_check=r.get("lean_check"), wall_s=r.get("wall_s"), checks=r.get("checks"),
                        first_messages=[m["data"][:160] for m in r.get("messages", []) if m["severity"] == "error"][:2]))
        print(f"{cid:44s} expect={expect:11s} got={r['status']:11s} {'PASS' if ok else 'FAIL'}  v15={r.get('v15_complete_equivalent')}  {r['reasons']}")
    # counting tests
    counting = []
    n = count_certified([recs["V1_valid_proof_gdt_empty"], recs["P1_valid_proof_without_kernel_replay"],
                         recs["I1_sorry"]])
    counting.append(dict(test="T1_only_certified_counted", expected=1, got=n, passed=n == 1))
    forged = dict(recs["P1_valid_proof_without_kernel_replay"], status="certified")
    try:
        count_certified([forged]); raised = False
    except ValueError:
        raised = True
    counting.append(dict(test="T2_forged_certified_status_raises", expected="ValueError", got="ValueError" if raised else "counted", passed=raised))
    for c in counting:
        fails += not c["passed"]; print(f"{c['test']:44s} {'PASS' if c['passed'] else 'FAIL'}  got={c['got']}")
    (H / "tests/results.json").write_text(json.dumps(dict(failures=fails, cases=out, counting=counting), indent=1, ensure_ascii=False) + "\n")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
