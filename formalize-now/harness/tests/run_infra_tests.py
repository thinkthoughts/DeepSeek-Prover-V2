#!/usr/bin/env python3
"""RPI-DS-001e: CPU tests for the GPU execution kit (no GPU, no model weights).

I1-I3  gpu/verify_model.py: real pinned tokenizer.json passes; corrupted copy fails;
       directory without weights fails
I4-I6  gpu/budget.py: spend arithmetic; gate; guard stops a dummy process (accelerated
       clock) and writes STOPPED_BY_BUDGET; reports provider_side_cap = false
I7     gpu/preflight.py --cpu-test: report written; GPU checks `unavailable`; FAILS
I8     smoke_run.py --live refusals: no approval / no preflight / failed preflight /
       stale preflight / HEAD mismatch
I9     dry run interrupted after 1 output (RPI_TEST_CRASH_AFTER) then --resume: every
       (condition, item, sample) recorded exactly once, all completions saved
I10    cost-record validation of every attempts.jsonl row
I11    gpu/collect_results.sh: archive + checksum verify; inner MANIFEST verifies
I12    gpu/setup_gpu.sh: bash syntax check and DRY_RUN=1 run (prints, executes nothing)
usage: run_infra_tests.py   (needs RPI_REPL, LEAN4CHECKER; TOKENIZER_JSON = pinned tokenizer.json)
"""
import datetime as dt, json, os, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path
H = Path(__file__).resolve().parent.parent; F = H.parent; G = F / "gpu"
results, fails = [], 0
def record(test, ok, **kw):
    global fails
    fails += not ok
    results.append(dict(test=test, passed=bool(ok), **kw))
    print(f"{test:56s} {'PASS' if ok else 'FAIL'} {json.dumps(kw)[:200] if not ok else ''}", flush=True)
def run(cmd, env=None, cwd=None, timeout=900):
    e = dict(os.environ); e.update(env or {})
    p = subprocess.run(cmd, capture_output=True, text=True, env=e, cwd=cwd or F, timeout=timeout)
    return p.returncode, p.stdout + p.stderr
iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
now = dt.datetime.now(dt.timezone.utc)

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    # I1-I3
    tok = Path(os.environ.get("TOKENIZER_JSON", str(Path.home() / "rpi/tok/tokenizer.json")))
    md = td / "model"; md.mkdir(); shutil.copy(tok, md / "tokenizer.json")
    rc, _ = run([sys.executable, str(G / "verify_model.py"), str(md), "--only", "tokenizer.json"])
    record("I1_verify_model_pinned_tokenizer_passes", rc == 0)
    bad = td / "bad"; bad.mkdir(); b = bytearray((md / "tokenizer.json").read_bytes()); b[100] ^= 1
    (bad / "tokenizer.json").write_bytes(b)
    rc, _ = run([sys.executable, str(G / "verify_model.py"), str(bad), "--only", "tokenizer.json"])
    record("I2_verify_model_corrupted_fails", rc == 1)
    rc, out = run([sys.executable, str(G / "verify_model.py"), str(md)])
    record("I3_verify_model_missing_weights_fails", rc == 1 and '"present": false' in out)
    # I4-I6
    rc, out = run([sys.executable, str(G / "budget.py"), "status", "--launch-time", iso(now - dt.timedelta(hours=1))])
    s = json.loads(out)
    record("I4_budget_arithmetic", abs(s["estimated_spend_usd"] - 1.09) < 0.01 and s["level"] == "ok" and s["provider_side_cap"] is False, status=s)
    rc1, _ = run([sys.executable, str(G / "budget.py"), "gate", "--launch-time", iso(now - dt.timedelta(hours=1)), "--need-usd", "0.3"])
    rc2, _ = run([sys.executable, str(G / "budget.py"), "gate", "--launch-time", iso(now - dt.timedelta(hours=3.5)), "--need-usd", "0.3"])
    record("I5_budget_gate_pass_and_fail", rc1 == 0 and rc2 == 1, pass_rc=rc1, fail_rc=rc2)
    dummy = subprocess.Popen(["sleep", "600"])
    t0 = time.time()
    rc, out = run([sys.executable, str(G / "budget.py"), "guard", "--launch-time", iso(now), "--pid", str(dummy.pid),
                   "--interval", "0.5", "--clock-scale", "20000", "--out-dir", str(td / "guard")], timeout=120)
    dead = dummy.poll() is not None
    if not dead: dummy.kill()
    record("I6_budget_guard_stops_process", rc == 2 and dead and (td / "guard/STOPPED_BY_BUDGET").exists() and "TERMINATE" in out,
           rc=rc, seconds=round(time.time() - t0, 1))
    # I7
    pf = td / "pf.json"
    rc, out = run([sys.executable, str(G / "preflight.py"), "--cpu-test", "--out", str(pf)], cwd=F / "lean49", timeout=1800)
    rep = json.loads(pf.read_text()) if pf.exists() else {}
    ch = rep.get("checks", {})
    record("I7_preflight_cpu_test_structure", rc == 1 and rep.get("passed") is False and "unavailable" in ch.get("gpu_present", {})
           and ch.get("reference_certification_39", {}).get("ok") is True and ch.get("lean4checker_reference", {}).get("ok") is True,
           failing=[k for k, v in ch.items() if not v["ok"]])
    # I8
    head = subprocess.run(["git", "-C", str(F), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    import hashlib
    pins_sha = hashlib.sha256((G / "pins.json").read_bytes()).hexdigest()
    good = dict(passed=True, mode="full", created_at=time.time(), git_head=head, pins_sha256=pins_sha)
    cases = {"no_approval": ({}, None, "RPI_SMOKE_APPROVED"),
             "no_preflight": ({"RPI_SMOKE_APPROVED": "1"}, None, "no preflight report"),
             "failed_preflight": ({"RPI_SMOKE_APPROVED": "1"}, dict(good, passed=False), "preflight not passed"),
             "stale_preflight": ({"RPI_SMOKE_APPROVED": "1"}, dict(good, created_at=time.time() - 7200), "older than 60 min"),
             "head_mismatch": ({"RPI_SMOKE_APPROVED": "1"}, dict(good, git_head="0" * 40), "git HEAD changed"),
             "no_launch_time": ({"RPI_SMOKE_APPROVED": "1"}, good, "LAUNCH_TIME unset")}
    refused = {}
    for name, (env, report, needle) in cases.items():
        p = td / f"pf_{name}.json"
        if report is not None: p.write_text(json.dumps(report))
        env = dict(env, RPI_PREFLIGHT=str(p)); env.pop("LAUNCH_TIME", None)
        e = {k: v for k, v in os.environ.items() if k != "LAUNCH_TIME"}; e.update(env)
        q = subprocess.run([sys.executable, str(H / "smoke_run.py"), "--live"], capture_output=True, text=True, env=e, cwd=F, timeout=300)
        refused[name] = q.returncode != 0 and needle in (q.stdout + q.stderr)
    record("I8_live_gate_refusals", all(refused.values()), cases=refused)
    # I9
    runs_before = set((F / "runs").glob("smoke-dry-*")) if (F / "runs").exists() else set()
    rc, out = run([sys.executable, str(H / "smoke_run.py"), "--dry-run", "--with-c2"], env={"RPI_TEST_CRASH_AFTER": "1"})
    new = sorted(set((F / "runs").glob("smoke-dry-*")) - runs_before)
    crashed = rc != 0 and "RPI_TEST_CRASH_AFTER" in out and len(new) == 1
    rd = new[-1] if new else None
    rc2, out2 = run([sys.executable, str(H / "smoke_run.py"), "--dry-run", "--with-c2", "--resume", str(rd)]) if rd else (1, "")
    rows = [json.loads(l) for l in (rd / "attempts.jsonl").read_text().splitlines()] if rd else []
    keys = [(r["condition"], r["item"], r["sample_index"]) for r in rows]
    comps = sorted(p.name for p in rd.glob("*.completion.txt")) if rd else []
    record("I9_interrupt_then_resume_no_duplicates", crashed and rc2 == 0 and len(keys) == 4 and len(set(keys)) == 4 and len(comps) == 4
           and (rd / "summary.json").exists(), crashed=crashed, resumed_rc=rc2, rows=len(keys), unique=len(set(keys)), completions=len(comps))
    # I10
    REQ = ["run_id", "condition", "mode", "item", "sample_index", "seed", "prompt_tokens", "generated_tokens", "finish_reason",
           "gpu_time_s", "gpu_energy_j", "status", "unavailable", "counters", "timestamp"]
    MEAS = ["prompt_tokens", "generated_tokens", "finish_reason", "gpu_time_s", "gpu_energy_j", "cpu_package_energy_j"]
    probs = []
    for r in rows:
        miss = [k for k in REQ if k not in r]
        undoc = [k for k in MEAS if k in r and r[k] is None and k not in r["unavailable"]]
        if miss or undoc or r["status"] not in {"certified", "preliminary", "rejected", "no_code_block", "truncated", "target_missing",
                                                "ambiguous_target", "term_mode_proof", "empty_proof"}:
            probs.append(dict(item=r.get("item"), missing=miss, undocumented_nulls=undoc, status=r.get("status")))
    record("I10_cost_records_valid_and_nulls_documented", rows and not probs, problems=probs)
    # I11
    st = td / "state"; st.mkdir(); (st / "setup.log").write_text("test\n")
    rc, out = run(["bash", str(G / "collect_results.sh"), str(st)], env={"OUT_DIR": str(td)})
    arch = sorted(td.glob("rpi_results_*.tar.gz")); ck = sorted(td.glob("rpi_results_*.sha256"))
    ok11 = rc == 0 and arch and ck and subprocess.run(["sha256sum", "-c", ck[0].name], cwd=td, capture_output=True).returncode == 0
    if ok11:
        ex = td / "x"; ex.mkdir(); subprocess.run(["tar", "-xzf", str(arch[0]), "-C", str(ex)], check=True)
        inner = next(ex.iterdir())
        ok11 = subprocess.run(["sha256sum", "-c", "MANIFEST.sha256"], cwd=inner, capture_output=True).returncode == 0 and (inner / "runs").exists()
    record("I11_collect_results_archive_verifies", ok11)
    # I12
    rc1, _ = run(["bash", "-n", str(G / "setup_gpu.sh")])
    rc2, out = run(["bash", str(G / "setup_gpu.sh")], env={"DRY_RUN": "1", "LAUNCH_TIME": iso(now), "STATE_DIR": str(td / "setupstate")})
    record("I12_setup_script_syntax_and_dry_run", rc1 == 0 and rc2 == 0 and "phase 5-done" in out and f"vllm==" in out,
           rc_syntax=rc1, rc_dry=rc2, tail=out[-300:] if rc2 else "")
    for d in new: shutil.rmtree(d, ignore_errors=True)

(H / "tests/infra_results.json").write_text(json.dumps(dict(failures=fails, results=results), indent=1) + "\n")
sys.exit(1 if fails else 0)
