#!/usr/bin/env python3
"""RPI-DS-001d: extraction + trusted-assembly tests on SYNTHETIC completions (no model).

Each case is a completion shaped like DeepSeek-Prover-V2 output. The pipeline under
test is the one the smoke test will use:
    extract() -> REPL preliminary screen -> direct verification with lean4checker.
Synthetic proof bodies reuse reference proofs ONLY inside this test file; prompts never
contain them (harness/prompts.py leak check).
usage: run_extract_tests.py  (needs RPI_REPL, LEAN4CHECKER; writes tests/extract_results.json)
"""
import json, sys
from pathlib import Path
H = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(H)); sys.path.insert(0, str(H / "tests"))
import verify_strict as vs
from extract import extract
from repl_adapter import Repl, verify_repl
from run_tests import ref_body

def item(i): return vs.load_item(i)
E, C, P = "gdt/gdt_empty", "gdt/coprime_add_mul_right", "gdt/gdt_periodic"
PLAN = "### Proof plan\n1. Unfold the definitions.\n2. Conclude.\n\n### Lean 4 proof\n"

def cot(iid, body, header=None, stmt=None, before="", after_decl="", close=True):
    it = item(iid)
    st = stmt or it["formal_statement"]
    ind = "\n".join("  " + l if l.strip() else l for l in body.split("\n"))
    st = st.replace(":= by\n  sorry", ":= by\n" + ind)
    code = (header if header is not None else it["header"] + it["definitions"]) + "\n" + before + st + after_decl
    return PLAN + "```lean4\n" + code + ("\n```\n\nThe proof is complete." if close else "")

def term_mode(comp, short):
    i = comp.index(f"theorem {short}"); j = comp.index(":= by\n", i)
    return comp[:j] + ":=\n" + comp[j + len(":= by\n"):]

def noncot(body, tail="\n```"):
    return "\n".join("  " + l if l.strip() else l for l in body.split("\n")) + tail

eb, cb = ref_body("gdt_empty"), ref_body("coprime_add_mul_right")
e_stmt = item(E)["formal_statement"]
CASES = [
 # id, item, fmt, completion, finish_reason, expected extract category, expected final status (None = not verified)
 ("X1_cot_full_file_echo", E, "cot", cot(E, eb), "stop", "extracted", "certified"),
 ("X2_cot_header_drift_maxHeartbeats", E, "cot",
  cot(E, eb, header=item(E)["header"].replace("maxHeartbeats 0", "maxHeartbeats 400000") + item(E)["definitions"]), "stop", "extracted", "certified"),
 ("X3_cot_weakened_statement_echo", E, "cot",
  cot(E, "rfl", stmt=e_stmt.replace("S N L m a = ∅", "S N L m a = S N L m a")), "stop", "extracted", "rejected"),
 ("X4_cot_aux_lemma_before_target", C, "cot",
  cot(C, "exact rpi_aux", before="theorem rpi_aux {k c e : ℕ} : Nat.Coprime (k + e * c) e ↔ Nat.Coprime k e := by\n  simp\n\n"), "stop", "extracted", "rejected"),
 ("X5_cot_no_code_block", E, "cot", PLAN + "I could not find a proof.", "stop", "no_code_block", None),
 ("X6_cot_truncated_open_block", E, "cot", cot(E, eb, close=False), "length", "truncated", None),
 ("X7_cot_target_missing", E, "cot", cot(E, eb).replace("theorem gdt_empty", "theorem gdt_empty_v2"), "stop", "target_missing", None),
 ("X8_cot_duplicate_target", E, "cot", cot(E, eb, after_decl="\n\ntheorem gdt_empty : True := trivial"), "stop", "ambiguous_target", None),
 ("X9_cot_term_mode", E, "cot", term_mode(cot(E, eb), "gdt_empty"), "stop", "term_mode_proof", None),
 ("X10_cot_exit_inside_body", E, "cot", cot(E, "skip\n#exit"), "stop", "extracted", "rejected"),
 ("X11_cot_sorry_body", E, "cot", cot(E, "sorry"), "stop", "extracted", "rejected"),
 ("X12_noncot_continuation", C, "noncot", noncot(cb), "stop", "extracted", "certified"),
 ("X13_noncot_trailing_commentary", C, "noncot", noncot(cb, tail="\n```\n\nThis completes the proof."), "stop", "extracted", "certified"),
 ("X14_noncot_truncated", C, "noncot", noncot(cb, tail=""), "length", "truncated", None),
 ("X15_cot_gdt_periodic_reference_body_needs_lemmas", P, "cot", cot(P, ref_body("gdt_periodic")), "stop", "extracted", "rejected"),
]

def main():
    repl = Repl(); out, fails = [], 0
    for cid, iid, fmt, comp, fin, exp_cat, exp_status in CASES:
        x = extract(comp, item(iid), fmt, fin)
        row = dict(case=cid, item=iid, format=fmt, category=x["category"], expected_category=exp_cat,
                   diagnostics=x["diagnostics"])
        ok = x["category"] == exp_cat
        if x["category"] == "extracted":
            pre = verify_repl(repl, iid, x["proof"], "proof")            # preliminary screen
            row["repl_status"] = pre["status"]
            final = verify_repl(repl, iid, x["proof"], "proof", certify=True) if pre["status"] == "preliminary" else pre
            row["final_status"] = final["status"]; row["reasons"] = final["reasons"]
            ok = ok and final["status"] == exp_status
        else:
            row["final_status"] = None
            ok = ok and exp_status is None
        row["passed"] = ok; fails += not ok; out.append(row)
        print(f"{cid:50s} cat={x['category']:16s} final={str(row['final_status']):10s} {'PASS' if ok else 'FAIL'}"
              f"  stmt_echo={x['diagnostics'].get('statement_echo_matches')} extra={x['diagnostics'].get('extra_declarations')}")
    repl.close()
    (H / "tests/extract_results.json").write_text(json.dumps(dict(failures=fails, cases=out), indent=1, ensure_ascii=False) + "\n")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
