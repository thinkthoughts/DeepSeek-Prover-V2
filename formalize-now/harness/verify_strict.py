#!/usr/bin/env python3
"""RPI-DS-001b strict verification wrapper for GDT-Ladder candidates.

Separately identifiable from, and leaving unmodified, DeepSeek-Prover-V1.5's
`prover/lean/verifier.py`. That verifier marks a proof `complete` when the REPL
reports no error, no `sorries`, and no warning containing "declaration uses
'sorry'" or "failed" (verifier.py:53). This wrapper treats an error-free compile
as necessary and insufficient. A candidate is ACCEPTED only when all hold:

  C1 compile   : `lean` exits 0 and reports no error message;
  C2 check ran : the trusted trailing check printed its result (a candidate that
                 stops elaboration early, e.g. with `#exit`, fails here);
  C3 present   : the expected constant exists and is a `theorem`;
  C4 statement : its elaborated type is alpha-equivalent (`Expr.eqv`) to the trusted
                 expected statement, which is elaborated BEFORE any candidate text;
  C5 axioms    : its axioms are a subset of {propext, Quot.sound, Classical.choice};
  C6 no new axioms : the file declares no `axiom` of its own (compiler
                 specialisation artefacts `…._at.…._spec_n` excepted, see code);
  C7 options   : no kernel/elaborator-weakening option (`debug.skipKernelTC`, …);
  C8 kernel    : (optional, --lean4checker) the compiled module replays through
                 lean4checker.
A token scan (sorry, admit, apply?, native_decide, …) is recorded as an additional
signal only; decisions come from C1–C8 on the elaborated declarations.

Status (RPI-DS-001c)
  rejected     : any of C1–C7 failed, or C8 ran and failed;
  preliminary  : C1–C7 passed and C8 (independent kernel replay) was NOT run;
  certified    : C1–C8 all passed.
Only `certified` results count as solved: `accepted` is True exactly for
`certified`, and `count_certified()` re-validates every record it counts.
Exit code: 0 certified, 2 preliminary, 1 rejected.

Modes
  proof     : candidate = proof text after the item's `:= by`; the wrapper assembles
              trusted prefix + trusted statement + candidate proof.
  full-code : candidate = a whole Lean file (V1.5/V2 output style). It must begin with
              the item's trusted prefix (header + definitions) byte-for-byte; the
              trusted expected statement is inserted right after that prefix.

usage: verify_strict.py --item <id> (--proof FILE | --full-code FILE) [--lean4checker] [--json OUT]
"""
import argparse, json, os, re, subprocess, sys, tempfile, time
from pathlib import Path

F = Path(__file__).resolve().parent.parent           # formalize-now/
LEAN49 = F / "lean49"
ITEMS = F / "benchmark/gdt_items.jsonl"
L4C = os.environ.get("LEAN4CHECKER", str(Path.home() / "lean4checker/.lake/build/bin/lean4checker"))
ALLOWED = ["propext", "Quot.sound", "Classical.choice"]
FORBIDDEN_OPTIONS = ["debug.skipKernelTC", "Elab.async", "maxRecDepth 0"]
SCAN = ["sorry", "admit", "apply?", "exact?", "native_decide", "decide!", "implemented_by",
        "extern", "axiom", "unsafe", "#exit", "debug.skipKernelTC", "run_cmd", "#eval", "elab", "macro"]

def load_item(item_id):
    for line in ITEMS.read_text().splitlines():
        it = json.loads(line)
        if it["id"] == item_id:
            return it
    raise SystemExit(f"unknown item {item_id}")

def expected_block(item):
    # trusted statement, renamed into GDT.Expected; proof `sorry` (never audited)
    st = item["formal_statement"].replace("namespace GDT.Challenge", "namespace GDT.Expected") \
                                 .replace("end GDT.Challenge", "end GDT.Expected")
    return st + "\n"

def check_block(name):
    short = name.split("/")[-1]
    return f'''
open Lean in
#eval show CoreM Unit from do
  let env ← getEnv
  let target := `GDT.Challenge.{short}
  let expected := `GDT.Expected.{short}
  let axiomsOf (c : Name) : Array Name :=
    (((Lean.Elab.Command.CollectAxioms.collect c).run env).run {{}}).2.axioms
  let localAxioms := env.constants.map₂.toList.filterMap fun (n, ci) =>
    if ci matches .axiomInfo _ then some n.toString else none
  let res ← match env.find? target, env.find? expected with
    | some ci, some eci => pure (Json.mkObj [
        ("present", toJson true), ("is_theorem", toJson (ci matches .thmInfo _)),
        ("type_alpha_equivalent", toJson (ci.type == eci.type)),
        ("axioms", toJson ((axiomsOf target).map toString)),
        ("local_axioms", toJson localAxioms)])
    | none, _ => pure (Json.mkObj [("present", toJson false), ("local_axioms", toJson localAxioms)])
    | _, none => pure (Json.mkObj [("present", toJson false), ("expected_missing", toJson true)])
  IO.println ("@@RPI_CHECK " ++ res.compress)
'''

def scan(text):
    code = re.sub(r"/-.*?-/", "", text, flags=re.S)
    code = re.sub(r"--[^\n]*", "", code)
    return {w: len(re.findall(rf"(?<![\w.]){re.escape(w)}(?![\w])", code)) for w in SCAN if
            re.search(rf"(?<![\w.]){re.escape(w)}(?![\w])", code)}

def v15_complete(messages, sorries_reported):
    """DeepSeek-Prover-V1.5 verifier.py:53 decision, applied to the same messages."""
    errors = [m for m in messages if m["severity"] == "error"]
    warnings = [m for m in messages if m["severity"] == "warning"]
    passed = not errors
    return passed and not sorries_reported and not any(
        "declaration uses 'sorry'" in w["data"] or "failed" in w["data"] for w in warnings)

MSG = re.compile(r"^(?P<file>[^\n:]+\.lean):(?P<line>\d+):(?P<col>\d+): (?P<sev>error|warning|info): ", re.M)

def parse_messages(out):
    ms = list(MSG.finditer(out)); res = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(out)
        res.append(dict(severity=m["sev"], line=int(m["line"]), data=out[m.end():end].strip()))
    return res

REF = F / "lean49/GDTBench/SolutionRef.lean"
DEPS_V2 = F / "manifest/gdt_manifest_v2.json"

def reference_context(item_id):
    """RPI-DS-001d: trusted verification-only context for C2 (PREREGISTRATION.md §5).
    Returns the certified reference declarations of the item's full kernel-dependency
    closure, in source order, wrapped in `namespace GDT.Challenge`. Never used in prompts."""
    import re as _re
    man = json.loads(DEPS_V2.read_text())
    deps = {d["short"]: [x.split(".")[-1] for x in d["kernel_deps"] if x.startswith("GDT.Challenge.")]
            for d in man["declarations"] if d["kind"] == "theorem"}
    order = [d["short"] for d in sorted((d for d in man["declarations"] if d["kind"] == "theorem"), key=lambda d: d["source_line"])]
    seen, todo = set(), list(deps[item_id.split("/")[-1]])
    while todo:
        x = todo.pop()
        if x not in seen: seen.add(x); todo += deps[x]
    ref = REF.read_text()
    starts = [(m.start(), m.group(2)) for m in _re.finditer(r"^(theorem|lemma)\s+(\S+)", ref, _re.M)]
    ends = [m.start() for m in _re.finditer(r"^(theorem|lemma|/--|end GDT)", ref, _re.M)]
    blocks = {}
    for pos, name in starts:
        nxt = min(e for e in ends if e > pos)
        blocks[name] = ref[pos:nxt].rstrip() + "\n"
    names = [n for n in order if n in seen]
    if not names:
        return "", []
    return ("namespace GDT.Challenge\nopen GDT\n\n" + "\n".join(blocks[n] for n in names) + "\nend GDT.Challenge\n\n"), names

def assemble(item_id, candidate, mode, reference_deps=False):
    """Trusted assembly shared by the direct path and the REPL adapter.
    Returns (item, prefix, source, rec); source is None when the full-code prefix
    check fails (rec is then already final)."""
    item = load_item(item_id)
    prefix = item["header"] + item["definitions"] + "\n"
    rec = dict(item=item_id, mode=mode, checks={}, reasons=[])
    if mode == "proof":
        stmt = item["formal_statement"]
        assert stmt.rstrip().endswith("end GDT.Challenge")
        head = stmt.rsplit(":= by\n  sorry", 1)[0] + ":= by\n"
        body = "\n".join("  " + l if l.strip() else l for l in candidate.rstrip("\n").split("\n"))
        cand_part = head + body + "\n\nend GDT.Challenge\n"
        ctx, ctx_names = reference_context(item_id) if reference_deps else ("", [])
        rec["reference_context"] = ctx_names
        source = prefix + expected_block(item) + "\n" + ctx + cand_part
    else:
        if not candidate.startswith(prefix):
            rec["checks"]["prefix"] = False
            rec = finalize(rec)
            rec["reasons"] = ["prefix: full-code candidate does not start with the trusted header and definitions"]
            return item, prefix, None, rec
        rec["checks"]["prefix"] = True
        source = prefix + expected_block(item) + "\n" + candidate[len(prefix):]
    source += "\n" + check_block(item_id)
    rec["token_scan"] = scan(candidate)
    rec["checks"]["C7_options"] = not any(o in candidate for o in FORBIDDEN_OPTIONS)
    return item, prefix, source, rec

def expected_lines(item, prefix):
    """1-based line range of the trusted expected block inside the assembled source."""
    return range(prefix.count("\n") + 1, (prefix + expected_block(item)).count("\n") + 2)

SPEC = re.compile(r"\._at\..*\._spec_\d+$")

def apply_check_result(rec, chk_json):
    """C2–C6 from the trusted trailing check's JSON (None when it did not run)."""
    rec["checks"]["C2_check_ran"] = chk_json is not None
    res = chk_json or {}
    rec["lean_check"] = res
    rec["checks"]["C3_present_theorem"] = bool(res.get("present") and res.get("is_theorem"))
    rec["checks"]["C4_statement"] = bool(res.get("type_alpha_equivalent"))
    axs = res.get("axioms")
    rec["checks"]["C5_axioms"] = axs is not None and all(a in ALLOWED for a in axs)
    # compiler specialisations (`f._at.g._spec_n`) are registered as axiom-like
    # declarations by Lean 4.9's code generator; they are recorded but excluded here.
    # Soundness rests on C5: any axiom the target theorem reaches, whatever its
    # name, falls outside the whitelist and rejects the candidate.
    rec["local_axioms_compiler_specialisations"] = [a for a in res.get("local_axioms", []) if SPEC.search(a)]
    rec["local_axioms_declared"] = [a for a in res.get("local_axioms", []) if not SPEC.search(a)]
    rec["checks"]["C6_no_local_axioms"] = chk_json is not None and not rec["local_axioms_declared"]
    return rec

def verify(item_id, candidate, mode, use_l4c=False, reference_deps=False):
    item, prefix, source, rec = assemble(item_id, candidate, mode, reference_deps)
    if source is None:
        return rec
    with tempfile.TemporaryDirectory(dir=LEAN49) as td:
        mod = "RPICandidate"
        path = Path(td) / f"{mod}.lean"; path.write_text(source)
        olean = Path(td) / f"{mod}.olean"
        t0 = time.time()
        p = subprocess.run(["lake", "env", "lean", f"--root={td}", "-o", str(olean), str(path)],
                           cwd=LEAN49, capture_output=True, text=True, timeout=900)
        rec["wall_s"] = round(time.time() - t0, 1)
        out = p.stdout + p.stderr
        msgs = parse_messages(out)
        # messages from the trusted expected block (its `sorry`) are excluded from C1
        exp = expected_lines(item, prefix)
        cand_msgs = [m for m in msgs if m["line"] not in exp]
        rec["messages"] = [dict(m, data=m["data"][:400]) for m in cand_msgs if m["severity"] != "info"]
        rec["checks"]["C1_compile"] = p.returncode == 0 and not any(m["severity"] == "error" for m in cand_msgs)
        chk = re.search(r"@@RPI_CHECK (\{.*\})", out)
        apply_check_result(rec, json.loads(chk.group(1)) if chk else None)
        if use_l4c and all(rec["checks"].get(k) for k in REQUIRED):
            env = dict(os.environ)
            lp = subprocess.run(["lake", "env", "printenv", "LEAN_PATH"], cwd=LEAN49, capture_output=True, text=True).stdout.strip()
            env["LEAN_PATH"] = lp + ":" + td
            q = subprocess.run([L4C, mod], cwd=LEAN49, capture_output=True, text=True, env=env, timeout=900)
            rec["checks"]["C8_lean4checker"] = q.returncode == 0
            rec["lean4checker_output"] = (q.stdout + q.stderr)[-400:]
        # V1.5 decision on the same compile, for comparison (no REPL `sorries` field: use sorry warnings)
        sorry_warn = any("declaration uses 'sorry'" in m["data"] for m in cand_msgs)
        rec["v15_complete_equivalent"] = v15_complete(cand_msgs, sorry_warn)
    rec["path"] = "direct"
    return finalize(rec)

REQUIRED = ["C1_compile", "C2_check_ran", "C3_present_theorem", "C4_statement",
            "C5_axioms", "C6_no_local_axioms", "C7_options"]

def finalize(rec):
    checks = rec["checks"]
    failed = [k for k, v in checks.items() if v is False]
    if failed or not all(checks.get(k) for k in REQUIRED):
        status = "rejected"
    elif checks.get("C8_lean4checker") is True:
        status = "certified"
    else:
        status = "preliminary"
    rec["status"] = status
    rec["certified"] = status == "certified"
    rec["accepted"] = rec["certified"]            # accepted means certified, nothing weaker
    rec["kernel_replay"] = "passed" if checks.get("C8_lean4checker") is True else (
        "failed" if checks.get("C8_lean4checker") is False else "not_run")
    rec["reasons"] = failed + ([] if status != "preliminary" else ["C8_lean4checker_not_run"])
    return rec

def count_certified(records):
    """Count solved results. A record counts only if its status is `certified` AND its
    check vector independently shows C1–C8 all True; anything else is excluded, and a
    record claiming `certified` without that evidence raises."""
    n = 0
    for r in records:
        checks = r.get("checks", {})
        evidence = all(checks.get(k) is True for k in REQUIRED + ["C8_lean4checker"])
        if r.get("status") == "certified":
            if not evidence:
                raise ValueError(f"record {r.get('item')} claims certified without C1–C8 evidence")
            n += 1
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--item", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--proof"); g.add_argument("--full-code")
    ap.add_argument("--lean4checker", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    mode = "proof" if a.proof else "full-code"
    cand = Path(a.proof or a.full_code).read_text()
    rec = verify(a.item, cand, mode, a.lean4checker)
    s = json.dumps(rec, indent=1, ensure_ascii=False)
    if a.json: Path(a.json).write_text(s + "\n")
    print(s)
    sys.exit({"certified": 0, "preliminary": 2}.get(rec["status"], 1))

if __name__ == "__main__":
    main()
