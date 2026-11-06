#!/usr/bin/env python3
"""RPI-DS-001c: REPL adapter for the strict GDT-Ladder verifier.

Runs candidates through DeepSeek's REPL (xinhjBrant/repl@3334a97, the REPL that
DeepSeek-Prover-V1.5's `verifier.py` drives with `lake exe repl`) while keeping
every acceptance condition of `verify_strict.py`:

  * the source is built by the SAME trusted `assemble()` (expected statement
    elaborated before any candidate text, trailing check block appended);
  * C1–C7 are computed from the REPL's messages and the trailing check's output,
    never from the absence of error messages alone;
  * the REPL produces no .olean, so it cannot perform independent kernel replay:
    REPL results are at most `preliminary`. With certify=True the adapter re-runs
    the identical candidate through the direct path with lean4checker (C8) and
    requires the REPL and direct C1–C7 vectors to agree; any disagreement rejects.

Process model: one REPL process per worker; `import Mathlib\\nimport Aesop` is sent
once (env 0) and each candidate is sent as a command on env 0. REPL environments are
immutable snapshots, so candidates cannot affect one another.
"""
import json, os, subprocess, time
from pathlib import Path
import verify_strict as vs

REPL = os.environ.get("RPI_REPL", str(Path.home() / "repl-deepseek/.lake/build/bin/repl"))
IMPORTS = "import Mathlib\nimport Aesop\n"

class Repl:
    def __init__(self):
        # stdbuf: the REPL writes through C stdio, which block-buffers when piped
        self.p = subprocess.Popen(["lake", "env", "stdbuf", "-oL", REPL], cwd=vs.LEAN49, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        t0 = time.time()
        r = self.send({"cmd": IMPORTS.rstrip("\n")})
        assert r.get("env") == 0 and not any(m["severity"] == "error" for m in r.get("messages", [])), r
        self.import_s = round(time.time() - t0, 1)

    def send(self, obj):
        self.p.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n\n"); self.p.stdin.flush()
        buf = []
        while True:
            line = self.p.stdout.readline()
            if line == "":
                raise RuntimeError("REPL terminated: " + self.p.stderr.read()[-2000:])
            if line.strip() == "" and buf:
                try:
                    return json.loads("".join(buf))
                except json.JSONDecodeError:
                    continue            # blank line inside a pretty-printed value
            elif line.strip():
                buf.append(line)

    def close(self):
        try: self.p.stdin.close(); self.p.wait(timeout=30)
        except Exception: self.p.kill()

def verify_repl(repl, item_id, candidate, mode, certify=False):
    item, prefix, source, rec = vs.assemble(item_id, candidate, mode)
    rec["path"] = "repl"
    if source is None:
        return rec
    assert source.startswith(IMPORTS), "item header must begin with the V1.5 imports"
    body = source[len(IMPORTS):]
    offset = IMPORTS.count("\n")                 # REPL line numbers are relative to `body`
    exp = vs.expected_lines(item, prefix)
    t0 = time.time()
    r = repl.send({"cmd": body, "env": 0})
    rec["wall_s"] = round(time.time() - t0, 1)
    msgs = [dict(severity=m["severity"], line=m["pos"]["line"] + offset, data=m["data"]) for m in r.get("messages", [])]
    cand = [m for m in msgs if m["line"] not in exp]
    rec["messages"] = [dict(m, data=m["data"][:400]) for m in cand if m["severity"] != "info"]
    rec["repl_sorries_in_candidate"] = [s["pos"]["line"] + offset for s in r.get("sorries", [])
                                        if s["pos"]["line"] + offset not in exp]
    rec["checks"]["C1_compile"] = "env" in r and not any(m["severity"] == "error" for m in cand)
    chk = None
    for m in msgs:
        if m["severity"] == "info" and m["data"].startswith("@@RPI_CHECK "):
            chk = json.loads(m["data"][len("@@RPI_CHECK "):])
    vs.apply_check_result(rec, chk)
    rec["v15_complete_equivalent"] = vs.v15_complete(cand, bool(rec["repl_sorries_in_candidate"]))
    rec = vs.finalize(rec)                        # at most `preliminary`: no C8 on this path
    if certify and rec["status"] == "preliminary":
        d = vs.verify(item_id, candidate, mode, use_l4c=True)
        agree = all(d["checks"].get(k) == rec["checks"].get(k) for k in vs.REQUIRED)
        rec["direct_recheck"] = dict(status=d["status"], checks=d["checks"], agree_on_C1_C7=agree)
        rec["checks"]["C8_lean4checker"] = d["checks"].get("C8_lean4checker", False) and agree
        rec = vs.finalize(rec)
        if not agree:
            rec["status"], rec["certified"], rec["accepted"] = "rejected", False, False
            rec["reasons"].append("repl_direct_disagreement")
    return rec
