#!/usr/bin/env python3
"""RPI-DS-001d/001e smoke test: at most 2 C0 outputs for gdt_periodic, optionally at most
2 C2 outputs for gcd_with_N_iff_gcd_with_R. ENGINEERING VALIDATION ONLY: results are
excluded from every confirmatory statistic (PREREGISTRATION.md, Amendment A1 §4).

Pipeline per output (identical in --dry-run and --live):
  completion (saved + fsync'd before anything else)
    -> harness/extract.py (proof body only)
    -> REPL preliminary screen -> direct verification + lean4checker (certified/rejected)
       (C2 targets: verification context = certified reference closure, C9 = direct deps)
    -> attempts.jsonl row (appended + fsync'd): tokens, time, memory, energy or `unavailable`

  --dry-run : CPU. Built-in fixture completions; no model is loaded.
  --live    : vLLM with gpu/pins.json settings. Launch gate (all required):
                RPI_SMOKE_APPROVED=1;
                a passing full preflight report (RPI_PREFLIGHT, default ~/rpi_state/preflight.json)
                  < 60 min old, same git HEAD and pins sha256;
                LAUNCH_TIME set and the budget gate passing;
                a CUDA GPU with >= pins.gpu.min_memory_gb.
              Between outputs the budget is re-checked; at `stop_at` the run stops cleanly.
  --resume DIR : continue an interrupted run; (target, sample) pairs already recorded are
                 skipped, so no sample is generated or counted twice.
  RPI_TEST_CRASH_AFTER=N (tests only): raise after N recorded attempts.
"""
import argparse, hashlib, json, os, platform, subprocess, sys, threading, time
from pathlib import Path
H = Path(__file__).resolve().parent; F = H.parent
sys.path.insert(0, str(H)); sys.path.insert(0, str(F / "gpu"))
import verify_strict as vs
from extract import extract
from repl_adapter import Repl, verify_repl
from instrument import Recorder

PRE = json.loads((F / "preregistration.json").read_text())
PINS = json.loads((F / "gpu/pins.json").read_text())
MODEL, REVISION = PINS["model"]["id"], PINS["model"]["revision"]
assert (MODEL, REVISION) == (PRE["model"]["id"], PRE["model"]["revision"]), "pins and pre-registration disagree"
INF = PINS["inference"]
SAMPLING = dict(temperature=INF["temperature"], top_p=INF["top_p"])
MAX_NEW = INF["max_new_tokens"]
SEED_PREFIX = "rpi-ds-001d-smoke"
TARGETS = [("C0", "gdt_periodic"), ("C2", "gcd_with_N_iff_gcd_with_R")]

def seed(prompt_id, i):
    return int(hashlib.sha256(f"{SEED_PREFIX}{prompt_id}{i}".encode()).hexdigest()[:8], 16)

def write_sync(path, text, mode="w"):
    with open(path, mode) as f:
        f.write(text); f.flush(); os.fsync(f.fileno())

def sh(cmd):
    try: return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e: return f"unavailable: {e}"

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run_manifest(args, run_dir):
    m = dict(run_kind="smoke-dry-run" if args.dry_run else "smoke-live", excluded_from_confirmatory=True,
             timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"), host=platform.node(), platform=platform.platform(),
             python=sys.version.split()[0], model=MODEL, revision=REVISION, dtype=PINS["model"]["dtype"],
             sampling=SAMPLING, max_new_tokens=MAX_NEW, max_model_len=INF["max_model_len"],
             gpu_memory_utilization=INF["gpu_memory_utilization"], seed_prefix=SEED_PREFIX,
             prompts_file="benchmark/prompts_v2.jsonl", prompts_sha256=sha(F / "benchmark/prompts_v2.jsonl"),
             preregistration_sha256=sha(F / "preregistration.json"), pins_sha256=sha(F / "gpu/pins.json"),
             amendments=[a["id"] for a in PRE["amendments"]], git_head=sh(["git", "-C", str(F), "rev-parse", "HEAD"]),
             lean_toolchain=(F / "lean49/lean-toolchain").read_text().strip(), launch_time=os.environ.get("LAUNCH_TIME"),
             nvidia_smi=sh(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]),
             pip_freeze=sh([sys.executable, "-m", "pip", "freeze"]).splitlines() if not args.dry_run else "not captured in dry run")
    p = run_dir / "run_manifest.json"
    if not p.exists():
        write_sync(p, json.dumps(m, indent=1) + "\n")
    return json.loads(p.read_text())

FIXTURES = {   # dry-run completions exercising format branches; NOT model output
    "C0": ["### Plan\nUse periodicity.\n\n```lean4\n{CODE_SORRY}\n```",
           "### Plan\nI am unable to complete the proof."],
    "C2": ["### Plan\nUse the premises.\n\n```lean4\n{CODE_SORRY}\n```"],
    "noncot": ["  sorry\n```", "  exact foo_bar_baz\n```"],
}

def fixture(cond, prompt, i, mode):
    key = "noncot" if mode == "noncot" else cond
    t = FIXTURES[key][i % len(FIXTURES[key])]
    if "{CODE_SORRY}" in t:
        t = t.replace("{CODE_SORRY}", prompt.split("```lean4\n", 1)[1].split("\n```", 1)[0])
    return dict(text=t, finish_reason="stop", prompt_tokens=None, generated_tokens=None, gpu_time_s=None,
                gpu_energy_j=None, gpu_mem_peak_mib=None, gpu_power_mean_w=None)

def live_gate():
    if os.environ.get("RPI_SMOKE_APPROVED") != "1":
        raise SystemExit("live run refused: set RPI_SMOKE_APPROVED=1 after explicit approval")
    pf = Path(os.environ.get("RPI_PREFLIGHT", str(Path.home() / "rpi_state/preflight.json")))
    if not pf.exists():
        raise SystemExit(f"live run refused: no preflight report at {pf} (run gpu/preflight.py)")
    r = json.loads(pf.read_text())
    head = sh(["git", "-C", str(F), "rev-parse", "HEAD"])
    problems = [p for p, bad in [("preflight not passed", not r.get("passed")), ("preflight not in full mode", r.get("mode") != "full"),
                                 ("preflight older than 60 min", time.time() - r.get("created_at", 0) > 3600),
                                 ("git HEAD changed since preflight", r.get("git_head") != head),
                                 ("pins changed since preflight", r.get("pins_sha256") != sha(F / "gpu/pins.json"))] if bad]
    if problems:
        raise SystemExit("live run refused: " + "; ".join(problems))
    budget_ok(need=0.30, hard=True)

def budget_ok(need=0.0, hard=False):
    lt = os.environ.get("LAUNCH_TIME")
    if not lt:
        if hard: raise SystemExit("live run refused: LAUNCH_TIME unset")
        return True, None
    from budget import status, parse
    s = status(parse(lt))
    ok = s["estimated_spend_usd"] + need <= PINS["budget"]["stop_at"]
    if hard and not ok:
        raise SystemExit(f"live run refused by budget gate: {s}")
    return ok, s

class GpuSampler(threading.Thread):
    def __init__(self, nvml, hdl):
        super().__init__(daemon=True); self.nvml, self.hdl = nvml, hdl
        self.stop = threading.Event(); self.mem = 0; self.pw = []
    def run(self):
        while not self.stop.is_set():
            try:
                self.mem = max(self.mem, self.nvml.nvmlDeviceGetMemoryInfo(self.hdl).used // (1 << 20))
                self.pw.append(self.nvml.nvmlDeviceGetPowerUsage(self.hdl) / 1000.0)
            except Exception: pass
            time.sleep(0.5)

def live_generator():
    import torch
    if not torch.cuda.is_available() or torch.cuda.get_device_properties(0).total_memory < PINS["gpu"]["min_memory_gb"] * 1e9:
        raise SystemExit("live run refused: needs a CUDA GPU with >= %d GB" % PINS["gpu"]["min_memory_gb"])
    from vllm import LLM, SamplingParams
    model_path = os.environ.get("MODEL_DIR", MODEL)
    llm = LLM(model=model_path, revision=None if os.path.isdir(model_path) else REVISION, tokenizer=model_path,
              dtype="bfloat16", max_model_len=INF["max_model_len"], gpu_memory_utilization=INF["gpu_memory_utilization"])
    try:
        import pynvml; pynvml.nvmlInit(); hdl = pynvml.nvmlDeviceGetHandleByIndex(0)
    except Exception:
        pynvml = hdl = None
    def gen(prompt, s, max_tokens):
        sp = SamplingParams(**SAMPLING, max_tokens=max_tokens, seed=s, n=1)
        e0 = pynvml.nvmlDeviceGetTotalEnergyConsumption(hdl) / 1000.0 if pynvml else None
        smp = GpuSampler(pynvml, hdl) if pynvml else None
        if smp: smp.start()
        t0 = time.time(); o = llm.generate([prompt], sp)[0]; dt = time.time() - t0
        if smp: smp.stop.set(); smp.join()
        e1 = pynvml.nvmlDeviceGetTotalEnergyConsumption(hdl) / 1000.0 if pynvml else None
        c = o.outputs[0]
        return dict(text=c.text, finish_reason=c.finish_reason, prompt_tokens=len(o.prompt_token_ids),
                    generated_tokens=len(c.token_ids), gpu_time_s=round(dt, 3),
                    gpu_energy_j=None if e0 is None else round(e1 - e0, 3),
                    gpu_mem_peak_mib=smp.mem if smp else None,
                    gpu_power_mean_w=round(sum(smp.pw) / len(smp.pw), 1) if smp and smp.pw else None)
    return gen

def done_pairs(run_dir):
    p = run_dir / "attempts.jsonl"
    if not p.exists(): return set()
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    return {(r["condition"], r["item"], r["sample_index"]) for r in rows}

def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--dry-run", action="store_true"); g.add_argument("--live", action="store_true")
    ap.add_argument("--with-c2", action="store_true"); ap.add_argument("--max-outputs", type=int, default=2)
    ap.add_argument("--mode", choices=["cot", "noncot"], default="cot"); ap.add_argument("--resume")
    a = ap.parse_args()
    if not 1 <= a.max_outputs <= INF["smoke_max_outputs_per_target"]:
        raise SystemExit("smoke test is capped at %d outputs per target" % INF["smoke_max_outputs_per_target"])
    if a.live: live_gate()
    run_dir = Path(a.resume) if a.resume else F / "runs" / ("smoke-" + ("dry-" if a.dry_run else "live-") + time.strftime("%Y%m%dT%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=True)
    man = run_manifest(a, run_dir)
    prompts = {json.loads(l)["id"]: json.loads(l) for l in (F / "benchmark/prompts_v2.jsonl").read_text().splitlines()}
    gen = None if a.dry_run else live_generator()
    rec = Recorder(run_dir / "attempts.jsonl", run_id=run_dir.name)
    done = done_pairs(run_dir); crash_after = int(os.environ.get("RPI_TEST_CRASH_AFTER", "0")); n_new = 0
    repl = Repl(); stopped = None
    try:
        for cond, short in TARGETS[: 2 if a.with_c2 else 1]:
            pid = f"{cond}/{a.mode}/{short}"; prompt = prompts[pid]["prompt"]; item = vs.load_item(f"gdt/{short}")
            for i in range(a.max_outputs):
                if (cond, item["id"], i) in done:
                    continue
                ok, s = budget_ok(need=0.10)
                if not ok:
                    stopped = dict(reason="budget stop_at reached before next output", status=s); break
                sd = seed(pid, i)
                g = fixture(cond, prompt, i, a.mode) if a.dry_run else gen(prompt, sd, MAX_NEW[a.mode])
                write_sync(run_dir / f"{cond}_{short}_{i}.completion.txt", g["text"])
                write_sync(run_dir / f"{cond}_{short}_{i}.generation.json", json.dumps({k: v for k, v in g.items() if k != "text"}) + "\n")
                x = extract(g["text"], item, a.mode, g["finish_reason"])
                status, reasons, vm, vu = x["category"], [], {}, {}
                ref = cond == "C2"
                if x["category"] == "extracted":
                    pre, vm, vu = rec.measure_verification(verify_repl, repl, item["id"], x["proof"], "proof", False, ref)
                    status, reasons = pre["status"], pre["reasons"]
                    if pre["status"] == "preliminary":
                        fin, vm2, vu2 = rec.measure_verification(verify_repl, repl, item["id"], x["proof"], "proof", True, ref)
                        status, reasons = fin["status"], fin["reasons"]; vm = dict(screen=vm, certify=vm2); vu.update(vu2)
                gen_fields = None if a.dry_run else {k: g[k] for k in ("prompt_tokens", "generated_tokens", "finish_reason", "gpu_time_s", "gpu_energy_j")}
                r = rec.record(condition=cond, mode=a.mode, item=item["id"], sample_index=i, seed=sd, generation=gen_fields,
                               verification=(vm, vu), status=status, path="repl+direct")
                if not a.dry_run:
                    r_extra = dict(gpu_mem_peak_mib=g.get("gpu_mem_peak_mib"), gpu_power_mean_w=g.get("gpu_power_mean_w"))
                    write_sync(run_dir / f"{cond}_{short}_{i}.gpu.json", json.dumps(r_extra) + "\n")
                write_sync(run_dir / "progress.jsonl", json.dumps(dict(prompt_id=pid, sample=i, seed=sd, extract_category=x["category"],
                           status=status, reasons=reasons, diagnostics=x["diagnostics"])) + "\n", mode="a")
                print(json.dumps(dict(prompt_id=pid, sample=i, category=x["category"], status=status)), flush=True)
                n_new += 1
                if crash_after and n_new >= crash_after:
                    raise RuntimeError("RPI_TEST_CRASH_AFTER reached (test-induced interruption)")
            if stopped: break
    finally:
        repl.close()
    rows = [json.loads(l) for l in (run_dir / "progress.jsonl").read_text().splitlines()] if (run_dir / "progress.jsonl").exists() else []
    write_sync(run_dir / "summary.json", json.dumps(dict(manifest=man, results=rows, stopped=stopped,
               certified=sum(r["status"] == "certified" for r in rows)), indent=1, ensure_ascii=False) + "\n")
    print("run dir:", run_dir)

if __name__ == "__main__":
    main()
