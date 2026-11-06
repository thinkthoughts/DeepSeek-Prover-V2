#!/usr/bin/env python3
"""RPI-DS-001e: C2 condition tests over all 39 items (CPU only).

G  dependency graph
   G1 manifest v2 direct deps == Stage 0 raw kernel record (logs/deps_solution.json, Lean 4.34)
   G2 every dependency is one of the 39 items; the graph is acyclic; dependencies precede
      their users in source order
   G3 independent recomputation in Lean 4.9 (tools/UsedLemmas49.lean on the certified
      SolutionRef) == manifest direct deps, for all 39 theorems
   G4 the assembler rejects an injected cycle, an unknown dependency and an unknown target
P  prompt artifacts (benchmark/prompts_v2.jsonl, C2, CoT and non-CoT, 39 items each)
   P1 the trusted target statement appears verbatim, exactly once, as the last declaration
   P2 declared context lemmas == the item's DIRECT dependencies, in the committed
      alphabetical order; no
      transitive-only lemma and no target declaration in the context
   P3 no reference-proof line in any prompt (all 184 prompts; target-proof leakage included)
   P4 deterministic: regenerating prompts_v2 reproduces the committed sha256
   P5 every CoT prompt's Lean code (C0, C0h, C1, C2; 92) elaborates through the REPL with
      no error, and its target statement is alpha-equivalent to the trusted statement
usage: run_c2_condition_tests.py  (needs RPI_REPL; writes tests/c2_condition_results.json)
"""
import hashlib, json, re, subprocess, sys, tempfile
from pathlib import Path
H = Path(__file__).resolve().parent.parent; F = H.parent
sys.path.insert(0, str(H))
import verify_strict as vs
import assemble_c2 as A
from repl_adapter import Repl

results, fails = [], 0
def record(test, ok, **kw):
    global fails
    fails += not ok
    results.append(dict(test=test, passed=bool(ok), **kw))
    print(f"{test:58s} {'PASS' if ok else 'FAIL'} {json.dumps(kw, ensure_ascii=False)[:160] if not ok else ''}", flush=True)

man = json.loads((F / "manifest/gdt_manifest_v2.json").read_text())
thms = {d["short"]: d for d in man["declarations"] if d["kind"] == "theorem"}
direct = {s: sorted(x.split(".")[-1] for x in d["kernel_deps"] if x.startswith("GDT.Challenge.")) for s, d in thms.items()}
order = sorted(thms, key=lambda s: thms[s]["source_line"])

# ---- G1
raw = {x["name"].split(".")[-1]: x for x in json.loads((F / "logs/deps_solution.json").read_text()) if x["kind"] == "theorem"}
g1 = {s: sorted({y.split(".")[-1] for y in raw[s]["value_deps"] + raw[s]["type_deps"] if y.startswith("GDT.Challenge.")}) for s in thms}
mism = {s: (direct[s], g1[s]) for s in thms if direct[s] != g1[s]}
record("G1_manifest_equals_stage0_kernel_record", not mism and len(thms) == 39, mismatches=mism)
# ---- G2
unknown = {s: [d for d in direct[s] if d not in thms] for s in thms}
unknown = {k: v for k, v in unknown.items() if v}
try:
    topo = A.topo_order(set(thms)); acyclic = True
except A.AssemblyError:
    acyclic = False
later = [(s, d) for s in thms for d in direct[s] if thms[d]["source_line"] >= thms[s]["source_line"]]
record("G2_known_acyclic_source_ordered", not unknown and acyclic and not later, unknown=unknown, later=later)
# ---- G3
p = subprocess.run(["lake", "env", "lean", "../tools/UsedLemmas49.lean"], cwd=vs.LEAN49, capture_output=True, text=True, timeout=900)
m = re.search(r"@@RPI_USED (\[.*\])", p.stdout)
used = {r["name"]: sorted(r["used_lemmas"]) for r in json.loads(m.group(1))} if m else {}
mism3 = {s: dict(manifest=direct[s], lean49=used.get(s)) for s in thms if used.get(s) != direct[s]}
record("G3_lean49_used_lemmas_equal_manifest_direct_deps", m is not None and len(used) == 39 and not mism3, discrepancies=mism3)
# ---- G4
saved = dict(A.DEPS)
try:
    A.DEPS["rad_dvd_self"] = A.DEPS["rad_dvd_self"] + ["coprime_iff_coprime_rad"]   # rad_dvd_self <-> coprime_iff_coprime_rad
    r = A.assemble("coprime_iff_coprime_rad", [])
    cyc = r["outcome"] == "error" and "cycle" in r.get("error", "")
    A.DEPS.clear(); A.DEPS.update(saved)
    A.DEPS["rad_dvd_self"] = ["no_such_lemma"]
    r2 = A.assemble("coprime_iff_coprime_rad", [])
    unk = r2["outcome"] == "error" and "unknown dependency" in r2.get("error", "")
finally:
    A.DEPS.clear(); A.DEPS.update(saved)
r3 = A.assemble("no_such_theorem", [])
record("G4_cycle_unknown_dependency_unknown_target_rejected", cyc and unk and r3["outcome"] == "error",
       cycle=cyc, unknown_dependency=unk, unknown_target=r3["outcome"])

# ---- P1/P2
prompts = {json.loads(l)["id"]: json.loads(l) for l in (F / "benchmark/prompts_v2.jsonl").read_text().splitlines()}
DECL = re.compile(r"^(?:theorem|lemma)\s+(\S+)", re.M)
bad1, bad2 = {}, {}
for mode in ("cot", "noncot"):
    for s in order:
        pr = prompts[f"C2/{mode}/{s}"]["prompt"]
        stmt = A.stmt_text(s)
        names = DECL.findall(pr)
        if pr.count(stmt) != 1 or not names or names[-1] != s or names.count(s) != 1:
            bad1[f"{mode}/{s}"] = dict(count=pr.count(stmt), last=names[-1] if names else None)
        ctx = names[:-1]
        # committed prompts_v2 convention (Amendment A1 hash): direct deps in alphabetical
        # order; context statements depend only on the definitions, so order is immaterial
        # to elaboration (P5) and fixed for reproducibility (P4)
        if ctx != sorted(direct[s]):
            bad2[f"{mode}/{s}"] = dict(context=ctx, direct=direct[s])
record("P1_trusted_statement_verbatim_once_last", not bad1, failures=bad1)
record("P2_context_is_exactly_direct_dependencies_in_order", not bad2, failures=bad2,
       transitive_only_total=sum(len(A.closure(s)) - len(direct[s]) for s in thms))
# ---- P3/P4
pm = json.loads((F / "benchmark/prompts_v2.manifest.json").read_text())
record("P3_no_reference_proof_lines_in_prompts", pm["leaks"] == [] and pm["reference_proof_lines_checked"] > 0,
       lines_checked=pm["reference_proof_lines_checked"])
with tempfile.TemporaryDirectory() as td:
    before = hashlib.sha256((F / "benchmark/prompts_v2.jsonl").read_bytes()).hexdigest()
    subprocess.run([sys.executable, str(H / "prompts.py"), "--version", "2"], check=True, capture_output=True)
    after = hashlib.sha256((F / "benchmark/prompts_v2.jsonl").read_bytes()).hexdigest()
record("P4_prompts_v2_deterministic", before == after == pm["sha256"], committed=pm["sha256"][:16], regenerated=after[:16])

# ---- P5
repl = Repl(); bad5 = {}
for pid, pr in prompts.items():
    if "/cot/" not in pid: continue
    cond, _, short = pid.split("/")
    code = pr["prompt"].split("```lean4\n", 1)[1].rsplit("\n```", 1)[0]
    assert code.startswith("import Mathlib\nimport Aesop\n")
    item = vs.load_item(f"gdt/{short}")
    body = code[len("import Mathlib\nimport Aesop\n"):] + "\n\n" + vs.expected_block(item) + "\n" + vs.check_block(f"gdt/{short}")
    r = repl.send({"cmd": body, "env": 0})
    errs = [m["data"][:160] for m in r.get("messages", []) if m["severity"] == "error"]
    chk = [m["data"] for m in r.get("messages", []) if m["data"].startswith("@@RPI_CHECK ")]
    res = json.loads(chk[0][len("@@RPI_CHECK "):]) if chk else {}
    if errs or not res.get("type_alpha_equivalent"):
        bad5[pid] = dict(errors=errs[:2], alpha=res.get("type_alpha_equivalent"))
repl.close()
record("P5_cot_prompt_code_elaborates_statement_preserved", not bad5, prompts_checked=92, failures=bad5)

(H / "tests/c2_condition_results.json").write_text(json.dumps(dict(failures=fails, results=results), indent=1, ensure_ascii=False) + "\n")
sys.exit(1 if fails else 0)
