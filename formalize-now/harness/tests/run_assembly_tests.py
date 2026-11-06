#!/usr/bin/env python3
"""RPI-DS-001d.2: controlled-fixture tests for the theorem-level C2 assembler.

Fixture provenance:
  reference_fixture    reference proof bodies from SolutionRef.lean (test use only)
  independent_fixture  proofs written for these tests, distinct from the reference text
  model (SIMULATED)    a provenance label set by the test to exercise the claim logic;
                       no model output exists. Results are stored in this test file only
                       and never enter benchmark statistics.
usage: run_assembly_tests.py  (needs LEAN4CHECKER; writes tests/assembly_results.json)
"""
import json, random, sys
from pathlib import Path
H = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(H)); sys.path.insert(0, str(H / "tests"))
import assemble_c2 as A
from run_tests import ref_body

def cand(lemma, proof, prov="reference_fixture", idx=0, status="certified", gid=None):
    return dict(lemma=lemma, proof=proof, sample_index=idx, per_item_status=status, provenance=prov, generation_id=gid)

def ref_set(target, prov="reference_fixture"):
    return [cand(m, ref_body(m), prov) for m in sorted(A.closure(target) | {target})]

# independently written proofs (differ from the reference text line by line)
IND_D_DVD_RAD = ("simp only [GDT.d, GDT.rad]\n"
                 "apply Finset.prod_dvd_prod_of_subset\n"
                 "exact Nat.primeFactors_mono (Nat.gcd_dvd_right _ _) (Nat.pos_iff_ne_zero.mp hN)")
IND_D_MUL_R = "simp only [GDT.R]\nrw [Nat.mul_div_cancel' (d_dvd_rad hN)]"
SIM = lambda lemma, proof: cand(lemma, proof, prov="model", gid="SIMULATED-" + lemma)

P = "gdt_periodic"
def without(cs, lemma): return [c for c in cs if c["lemma"] != lemma]
def replace(cs, lemma, **kw): return [dict(c, **kw) if c["lemma"] == lemma else c for c in cs]
shuffled = ref_set(P) + [cand("rad_pos", ref_body("rad_pos")), cand("totient_rad_mul", ref_body("totient_rad_mul"))]
random.Random(7).shuffle(shuffled)

CASES = [
 ("A1_success_reference_fixtures", P, ref_set(P), "certified", "fixture_only"),
 ("A2_success_independent_simulated_model", "d_mul_R_eq_rad",
  [SIM("d_dvd_rad", IND_D_DVD_RAD), SIM("d_mul_R_eq_rad", IND_D_MUL_R)], "certified", "c2_success"),
 ("A3_simulated_model_with_reference_text", "d_mul_R_eq_rad",
  [SIM("d_dvd_rad", ref_body("d_dvd_rad")), SIM("d_mul_R_eq_rad", IND_D_MUL_R)], "certified", "reference_text_detected"),
 ("A4_mixed_fixture_and_simulated_model", "d_mul_R_eq_rad",
  [cand("d_dvd_rad", IND_D_DVD_RAD, prov="independent_fixture"), SIM("d_mul_R_eq_rad", IND_D_MUL_R)], "certified", "fixture_only"),
 ("M1_missing_lemma_no_fallback", P, without(ref_set(P), "gcd_with_N_iff_gcd_with_R"), "incomplete", "none"),
 ("M2_missing_target", P, without(ref_set(P), P), "incomplete", "none"),
 ("M3_only_preliminary_candidate", P, replace(ref_set(P), "rad_dvd_self", per_item_status="preliminary"), "incomplete", "none"),
 ("V1_invalid_sorry_marked_certified", P, replace(ref_set(P), "coprime_add_mul_right", proof="sorry"), "rejected", "none"),
 ("V2_invalid_compile_error", P, replace(ref_set(P), "rad_dvd_self", proof="exact foo_bar_baz"), "rejected", "none"),
 ("V3_namespace_escape_injection", P,
  replace(ref_set(P), "coprime_add_mul_right", proof="simp\nend GDT.Challenge\n\ntheorem gdt_periodic : True := trivial"), "rejected", "none"),
 ("V4_local_axiom_injection", P,
  replace(ref_set(P), "rad_dvd_self", proof="exact rpi_cheat.elim\naxiom rpi_cheat : False"), "rejected", "none"),
 ("C1_conflict_same_sample_index", P,
  ref_set(P) + [cand("rad_dvd_self", "exact Nat.prod_primeFactors_dvd n", idx=0)], "conflict", "none"),
 ("C2_first_certified_selected", P,
  replace(ref_set(P), "rad_dvd_self", sample_index=1) + [cand("rad_dvd_self", "exact foo_bar_baz", idx=0, status="rejected")], "certified", "fixture_only"),
 ("C3_lower_index_certified_but_wrong", P,
  replace(ref_set(P), "rad_dvd_self", sample_index=1) + [cand("rad_dvd_self", "exact foo_bar_baz", idx=0, status="certified")], "rejected", "none"),
 ("O1_shuffled_with_extraneous", P, shuffled, "certified", "fixture_only"),
 ("E1_unknown_target", "no_such_theorem", [], "error", "none"),
] + [(f"S_{t}_reference_fixtures", t, ref_set(t), "certified", "fixture_only")
     for t in ["gdt_empty", "gdt_minimal_period", "gdt_count_per_period", "gdt_density",
               "gdt_correction_factor", "general_divisor_theorem"]]

def main():
    rows, fails = [], 0
    for cid, target, cands, exp_out, exp_claim in CASES:
        r = A.assemble(target, cands)
        ok = r["outcome"] == exp_out and r["claim"] == exp_claim
        if cid == "C2_first_certified_selected":
            ok = ok and r["chosen"]["rad_dvd_self"]["sample_index"] == 1
        if cid == "O1_shuffled_with_extraneous":
            ok = ok and r["extraneous_candidates"] == ["rad_pos", "totient_rad_mul"]
        if cid.startswith("M1"):
            ok = ok and r.get("missing") == ["gcd_with_N_iff_gcd_with_R"] and "certification" not in r
        fails += not ok
        cert = r.get("certification", {})
        rows.append(dict(case=cid, target=target, expected=[exp_out, exp_claim], outcome=r["outcome"], claim=r["claim"],
                         passed=ok, order=r.get("order"), missing=r.get("missing"), conflicts=r.get("conflicts"),
                         extraneous=r.get("extraneous_candidates"), reference_text_hits=r.get("reference_text_hits"),
                         checks=cert.get("checks"), errors=cert.get("errors", [])[:2], members=cert.get("members"),
                         compile_wall_s=cert.get("compile_wall_s"), lean4checker_wall_s=cert.get("lean4checker_wall_s"),
                         simulated_provenance=any(c.get("provenance") == "model" for c in cands)))
        print(f"{cid:42s} outcome={r['outcome']:10s} claim={r['claim']:24s} {'PASS' if ok else 'FAIL'}"
              f"  {[k for k, v in (cert.get('checks') or {}).items() if not v] or ''} {r.get('missing') or r.get('conflicts') or r.get('error') or ''}", flush=True)
    (H / "tests/assembly_results.json").write_text(json.dumps(dict(failures=fails, cases=rows), indent=1, ensure_ascii=False) + "\n")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
