#!/usr/bin/env python3
"""RPI-DS-001e: preflight before any inference. Writes a JSON report; exit 0 only if
every required check passes. `smoke_run.py --live` refuses to start without a passing
report that is < 60 min old and matches the current git HEAD and pins.

  preflight.py --out preflight.json                 # full (GPU instance)
  preflight.py --host-only --out host_check.json    # disk/RAM/GPU presence (setup phase 0)
  preflight.py --cpu-test --out pf.json             # CPU structure test: GPU checks report
                                                    # `unavailable` and the report FAILS
Env: MODEL_DIR, RPI_VENV_PY (python with vllm), LEAN4CHECKER, RPI_REPL, LAUNCH_TIME.
"""
import hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
G = Path(__file__).resolve().parent; F = G.parent
sys.path.insert(0, str(G))
PINS = json.loads((G / "pins.json").read_text())

def sh(cmd, timeout=600, cwd=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, shell=isinstance(cmd, str))
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:
        return 127, str(e)

def pins_sha():
    return hashlib.sha256((G / "pins.json").read_bytes()).hexdigest()

def main():
    a = sys.argv[1:]
    out = Path(a[a.index("--out") + 1]) if "--out" in a else Path("preflight.json")
    host_only, cpu_test = "--host-only" in a, "--cpu-test" in a
    checks = {}
    def c(name, ok, **info):
        checks[name] = dict(ok=bool(ok), **info)
    # host
    st = shutil.disk_usage(os.environ.get("HOME", "/"))
    c("disk_free_gb", st.free / 1e9 >= PINS["host"]["min_disk_free_gb"], value=round(st.free / 1e9, 1), need=PINS["host"]["min_disk_free_gb"])
    ram = int(open("/proc/meminfo").read().split()[1]) / 1e6
    c("ram_gb", ram >= PINS["host"]["min_ram_gb"], value=round(ram, 1), need=PINS["host"]["min_ram_gb"])
    rc, smi = sh(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"])
    if rc == 0 and smi:
        name, mem, drv = [x.strip() for x in smi.split("\n")[0].split(",")]
        c("gpu_present", True, name=name)
        c("gpu_memory_gb", float(mem) / 1024 >= PINS["gpu"]["min_memory_gb"], value=round(float(mem) / 1024, 1), need=PINS["gpu"]["min_memory_gb"])
        c("driver_version", int(drv.split(".")[0]) >= PINS["gpu"]["min_driver_major"], value=drv, need_major=PINS["gpu"]["min_driver_major"])
    else:
        for k in ("gpu_present", "gpu_memory_gb", "driver_version"):
            c(k, False, unavailable="nvidia-smi not found or failed (no GPU on this host)")
    if not host_only:
        py = os.environ.get("RPI_VENV_PY", str(Path.home() / "rpi-venv/bin/python"))
        rc, v = sh([py, "-c", "import vllm, torch; print(vllm.__version__, torch.__version__, torch.version.cuda, torch.cuda.is_available())"])
        if rc == 0:
            vv, tv, cu, avail = v.split()[-4:]
            c("vllm_version", vv == PINS["python"]["packages"]["vllm"], value=vv, need=PINS["python"]["packages"]["vllm"])
            c("torch_version", tv.split("+")[0] == PINS["python"]["packages"]["torch"], value=tv, cuda=cu)
            c("torch_cuda_available", avail == "True", value=avail)
        else:
            for k in ("vllm_version", "torch_version", "torch_cuda_available"):
                c(k, False, unavailable="vllm/torch not importable: " + v[-200:])
        rc, nv = sh([py, "-c", "import pynvml; pynvml.nvmlInit(); h=pynvml.nvmlDeviceGetHandleByIndex(0); print(pynvml.nvmlDeviceGetTotalEnergyConsumption(h))"])
        c("nvml_energy_counter", rc == 0, value=nv[-80:], note="optional for inference; required for energy records")
        from verify_model import verify
        md = os.environ.get("MODEL_DIR", str(Path.home() / "models/DeepSeek-Prover-V2-7B"))
        mv = verify(md) if Path(md).exists() else dict(ok=False, files=[], unavailable=f"{md} absent")
        c("model_files_pinned", mv["ok"], model_dir=md, detail=[f for f in mv.get("files", []) if not f.get("ok")])
        l4c = os.environ.get("LEAN4CHECKER", ""); repl = os.environ.get("RPI_REPL", "")
        c("lean4checker_binary", bool(l4c) and Path(l4c).exists(), value=l4c)
        c("repl_binary", bool(repl) and Path(repl).exists(), value=repl)
        rc, o = sh("lake env lean ../tools/SigCheck.lean > /tmp/rpi_pf_sig.log 2>&1 && cd .. && python3 tools/certify49.py /tmp/rpi_pf_sig.log",
                   timeout=900, cwd=str(F / "lean49"))
        c("reference_certification_39", rc == 0 and "certified 39 / 39" in o and "sigs unchanged True" in o, value=o[-120:])
        if l4c and Path(l4c).exists():
            rc, o = sh([ "lake", "env", l4c, "GDTBench.SolutionRef"], timeout=900, cwd=str(F / "lean49"))
            c("lean4checker_reference", rc == 0, value=o[-120:])
        else:
            c("lean4checker_reference", False, unavailable="LEAN4CHECKER unset")
        lt = os.environ.get("LAUNCH_TIME")
        if lt:
            from budget import status
            from budget import parse
            s = status(parse(lt)); need = 0.30   # smoke generation + verification allowance
            c("budget_room_for_smoke", s["estimated_spend_usd"] + need <= PINS["budget"]["stop_at"] and
              s["estimated_spend_usd"] <= PINS["budget"]["max_setup_spend_before_inference"], **s)
        else:
            c("budget_room_for_smoke", False, unavailable="LAUNCH_TIME unset")
    rc, head = sh(["git", "-C", str(F), "rev-parse", "HEAD"])
    rep = dict(schema="rpi-ds-001e/preflight/v1", created_at=time.time(), created_at_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               mode="host-only" if host_only else ("cpu-test" if cpu_test else "full"), git_head=head, pins_sha256=pins_sha(),
               checks=checks, passed=all(v["ok"] for k, v in checks.items() if k != "nvml_energy_counter"))
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: v["ok"] for k, v in checks.items()}, indent=1)); print("PASSED" if rep["passed"] else "FAILED")
    sys.exit(0 if rep["passed"] else 1)

if __name__ == "__main__":
    main()
