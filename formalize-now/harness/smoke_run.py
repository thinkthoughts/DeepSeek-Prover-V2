#!/usr/bin/env python3
"""RPI-DS-001d smoke test: at most 2 C0 outputs for gdt_periodic, optionally at most 2
C2 outputs for gcd_with_N_iff_gcd_with_R. ENGINEERING VALIDATION ONLY: results are
excluded from every confirmatory statistic (PREREGISTRATION.md, Amendment A1 §4).

Pipeline per output (identical in --dry-run and --live):
  completion -> harness/extract.py (proof body only)
             -> REPL preliminary screen (harness/repl_adapter.py)
             -> direct verification + lean4checker (certified or rejected)
             -> harness/instrument.py record (tokens, time, memory, energy or `unavailable`)

  --dry-run : CPU only. Completions come from built-in fixtures; no model is loaded.
  --live    : loads the pinned model with vLLM. Refuses to start unless
              RPI_SMOKE_APPROVED=1 is set, a CUDA GPU with >= 40 GB is visible, and
              --max-outputs <= 2. (Not executed in RPI-DS-001d.)

usage: smoke_run.py (--dry-run | --live) [--with-c2] [--max-outputs N] [--mode cot|noncot]
"""
import argparse, hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path
H = Path(__file__).resolve().parent; F = H.parent
sys.path.insert(0, str(H))
import verify_strict as vs
from extract import extract
from repl_adapter import Repl, verify_repl
from instrument import Recorder

PRE = json.loads((F / "preregistration.json").read_text())
MODEL = PRE["model"]["id"]; REVISION = PRE["model"]["revision"]
SAMPLING = dict(temperature=PRE["sampling"]["temperature"], top_p=PRE["sampling"]["top_p"])
MAX_NEW = PRE["sampling"]["max_new_tokens"]
SEED_PREFIX = "rpi-ds-001d-smoke"
TARGETS = [("C0", "gdt_periodic"), ("C2", "gcd_with_N_iff_gcd_with_R")]

def seed(prompt_id, i):
    return int(hashlib.sha256(f"{SEED_PREFIX}{prompt_id}{i}".encode()).hexdigest()[:8], 16)

def prompts(mode):
    rows = {json.loads(l)["id"]: json.loads(l) for l in (F / "benchmark/prompts_v2.jsonl").read_text().splitlines()}
    return rows

def sh(cmd):
    try: return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e: return f"unavailable: {e}"

def run_manifest(args, run_dir):
    m = dict(run_kind="smoke-dry-run" if args.dry_run else "smoke-live", excluded_from_confirmatory=True,
             timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"), host=platform.node(), platform=platform.platform(),
             python=sys.version.split()[0], model=MODEL, revision=REVISION, dtype=PRE["model"]["dtype"],
             sampling=SAMPLING, max_new_tokens=MAX_NEW, seed_prefix=SEED_PREFIX,
             prompts_file="benchmark/prompts_v2.jsonl",
             prompts_sha256=hashlib.sha256((F / "benchmark/prompts_v2.jsonl").read_bytes()).hexdigest(),
             preregistration_sha256=hashlib.sha256((F / "preregistration.json").read_bytes()).hexdigest(),
             amendments=[a["id"] for a in PRE["amendments"]],
             git_head=sh(["git", "-C", str(F), "rev-parse", "HEAD"]),
             lean_toolchain=(F / "lean49/lean-toolchain").read_text().strip(),
             nvidia_smi=sh(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]),
             pip_freeze=sh([sys.executable, "-m", "pip", "freeze"]).splitlines() if not args.dry_run else "not captured in dry run")
    (run_dir / "run_manifest.json").write_text(json.dumps(m, indent=1) + "\n")
    return m

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
        code = prompt.split("```lean4\n", 1)[1].split("\n```", 1)[0]
        t = t.replace("{CODE_SORRY}", code)
    return dict(text=t, finish_reason="stop", prompt_tokens=None, generated_tokens=None, gpu_time_s=None, gpu_energy_j=None)

def live_generator(max_len):
    if os.environ.get("RPI_SMOKE_APPROVED") != "1":
        raise SystemExit("live run refused: set RPI_SMOKE_APPROVED=1 after approval")
    import torch
    if not torch.cuda.is_available() or torch.cuda.get_device_properties(0).total_memory < 40e9:
        raise SystemExit("live run refused: needs a CUDA GPU with >= 40 GB (see SMOKE_INTERFACE_REVIEW_001d.md)")
    from vllm import LLM, SamplingParams
    llm = LLM(model=MODEL, revision=REVISION, tokenizer_revision=REVISION, dtype="bfloat16",
              max_model_len=max_len, gpu_memory_utilization=0.90, enforce_eager=False)
    try:
        import pynvml; pynvml.nvmlInit(); hdl = pynvml.nvmlDeviceGetHandleByIndex(0)
        energy = lambda: pynvml.nvmlDeviceGetTotalEnergyConsumption(hdl) / 1000.0   # mJ -> J
    except Exception:
        energy = None
    def gen(prompt, s, max_tokens):
        sp = SamplingParams(**SAMPLING, max_tokens=max_tokens, seed=s, n=1)
        e0 = energy() if energy else None; t0 = time.time()
        o = llm.generate([prompt], sp)[0]
        dt = time.time() - t0; e1 = energy() if energy else None
        c = o.outputs[0]
        return dict(text=c.text, finish_reason=c.finish_reason, prompt_tokens=len(o.prompt_token_ids),
                    generated_tokens=len(c.token_ids), gpu_time_s=round(dt, 3),
                    gpu_energy_j=None if e0 is None else round(e1 - e0, 3))
    return gen

def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--dry-run", action="store_true"); g.add_argument("--live", action="store_true")
    ap.add_argument("--with-c2", action="store_true"); ap.add_argument("--max-outputs", type=int, default=2)
    ap.add_argument("--mode", choices=["cot", "noncot"], default="cot")
    a = ap.parse_args()
    if not 1 <= a.max_outputs <= 2:
        raise SystemExit("smoke test is capped at 2 outputs per target")
    run_dir = F / "runs" / ("smoke-" + ("dry-" if a.dry_run else "live-") + time.strftime("%Y%m%dT%H%M%S"))
    run_dir.mkdir(parents=True)
    man = run_manifest(a, run_dir)
    P = prompts(a.mode)
    gen = None if a.dry_run else live_generator(max_len=MAX_NEW[a.mode] + 4096)
    rec = Recorder(run_dir / "attempts.jsonl", run_id=run_dir.name)
    repl = Repl(); summary = []
    for cond, short in TARGETS[: 2 if a.with_c2 else 1]:
        pid = f"{cond}/{a.mode}/{short}"; prompt = P[pid]["prompt"]; item = vs.load_item(f"gdt/{short}")
        for i in range(a.max_outputs):
            s = seed(pid, i)
            g = fixture(cond, prompt, i, a.mode) if a.dry_run else gen(prompt, s, MAX_NEW[a.mode])
            (run_dir / f"{cond}_{short}_{i}.completion.txt").write_text(g["text"])
            x = extract(g["text"], item, a.mode, g["finish_reason"])
            status, reasons, vm, vu = x["category"], [], {}, {}
            if x["category"] == "extracted":
                pre, vm, vu = rec.measure_verification(verify_repl, repl, item["id"], x["proof"], "proof")
                status, reasons = pre["status"], pre["reasons"]
                if pre["status"] == "preliminary":
                    fin, vm2, vu2 = rec.measure_verification(verify_repl, repl, item["id"], x["proof"], "proof", True)
                    status, reasons = fin["status"], fin["reasons"]; vm = dict(screen=vm, certify=vm2); vu.update(vu2)
            gen_fields = None if a.dry_run else {k: g[k] for k in ("prompt_tokens", "generated_tokens", "finish_reason", "gpu_time_s", "gpu_energy_j")}
            r = rec.record(condition=cond, mode=a.mode, item=item["id"], sample_index=i, seed=s, generation=gen_fields,
                           verification=(vm, vu), status=status, path="repl+direct")
            row = dict(prompt_id=pid, sample=i, seed=s, extract_category=x["category"], status=status, reasons=reasons,
                       diagnostics=x["diagnostics"])
            summary.append(row); print(json.dumps(row, ensure_ascii=False)[:300])
    repl.close()
    (run_dir / "summary.json").write_text(json.dumps(dict(manifest=man, results=summary,
        certified=sum(r["status"] == "certified" for r in summary)), indent=1, ensure_ascii=False) + "\n")
    print("run dir:", run_dir)

if __name__ == "__main__":
    main()
