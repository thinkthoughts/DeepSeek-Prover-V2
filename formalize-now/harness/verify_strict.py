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

def verify(item_id, candidate, mode, use_l4c=False):
    item = load_item(item_id)
    prefix = item["header"] + item["definitions"] + "\n"
    rec = dict(item=item_id, mode=mode, checks={}, reasons=[])
    if mode == "proof":
        stmt = item["formal_statement"]
        assert stmt.rstrip().endswith("end GDT.Challenge")
        head = stmt.rsplit(":= by\n  sorry", 1)[0] + ":= by\n"
        body = "\n".join("  " + l if l.strip() else l for l in candidate.rstrip("\n").split("\n"))
        cand_part = head + body + "\n\nend GDT.Challenge\n"
        source = prefix + expected_block(item) + "\n" + cand_part
    else:
        if not candidate.startswith(prefix):
            rec.update(accepted=False, reasons=["full-code candidate does not start with the trusted header and definitions"])
            rec["checks"]["prefix"] = False
            return rec
        rec["checks"]["prefix"] = True
        source = prefix + expected_block(item) + "\n" + candidate[len(prefix):]
    source += "\n" + check_block(item_id)
    rec["token_scan"] = scan(candidate)
    rec["checks"]["C7_options"] = not any(o in candidate for o in FORBIDDEN_OPTIONS)
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
        exp_lines = range(prefix.count("\n") + 1, (prefix + expected_block(item)).count("\n") + 2)
        cand_msgs = [m for m in msgs if m["line"] not in exp_lines]
        rec["messages"] = [dict(m, data=m["data"][:400]) for m in cand_msgs if m["severity"] != "info"]
        rec["checks"]["C1_compile"] = p.returncode == 0 and not any(m["severity"] == "error" for m in cand_msgs)
        chk = re.search(r"@@RPI_CHECK (\{.*\})", out)
        rec["checks"]["C2_check_ran"] = chk is not None
        res = json.loads(chk.group(1)) if chk else {}
        rec["lean_check"] = res
        rec["checks"]["C3_present_theorem"] = bool(res.get("present") and res.get("is_theorem"))
        rec["checks"]["C4_statement"] = bool(res.get("type_alpha_equivalent"))
        axs = res.get("axioms")
        rec["checks"]["C5_axioms"] = axs is not None and all(a in ALLOWED for a in axs)
        # compiler specialisations (`f._at.g._spec_n`) are registered as axiom-like
        # declarations by Lean 4.9's code generator; they are recorded but excluded here.
        # Soundness rests on C5: any axiom the target theorem reaches, whatever its
        # name, falls outside the whitelist and rejects the candidate.
        spec = re.compile(r"\._at\..*\._spec_\d+$")
        rec["local_axioms_compiler_specialisations"] = [a for a in res.get("local_axioms", []) if spec.search(a)]
        rec["local_axioms_declared"] = [a for a in res.get("local_axioms", []) if not spec.search(a)]
        rec["checks"]["C6_no_local_axioms"] = chk is not None and not rec["local_axioms_declared"]
        if use_l4c and rec["checks"]["C1_compile"]:
            env = dict(os.environ)
            lp = subprocess.run(["lake", "env", "printenv", "LEAN_PATH"], cwd=LEAN49, capture_output=True, text=True).stdout.strip()
            env["LEAN_PATH"] = lp + ":" + td
            q = subprocess.run([L4C, mod], cwd=LEAN49, capture_output=True, text=True, env=env, timeout=900)
            rec["checks"]["C8_lean4checker"] = q.returncode == 0
            rec["lean4checker_output"] = (q.stdout + q.stderr)[-400:]
        # V1.5 decision on the same compile, for comparison (no REPL `sorries` field: use sorry warnings)
        sorry_warn = any("declaration uses 'sorry'" in m["data"] for m in cand_msgs)
        rec["v15_complete_equivalent"] = v15_complete(cand_msgs, sorry_warn)
    rec["accepted"] = all(v for k, v in rec["checks"].items())
    rec["reasons"] = [k for k, v in rec["checks"].items() if not v]
    return rec

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
    sys.exit(0 if rec["accepted"] else 1)

if __name__ == "__main__":
    main()
