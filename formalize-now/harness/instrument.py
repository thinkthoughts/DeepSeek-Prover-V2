#!/usr/bin/env python3
"""RPI-DS-001c: cost instrumentation for GDT-Ladder runs.

Every measurement is recorded together with its availability. A quantity that
cannot be measured on the current machine is written as `null` with a reason in
`unavailable`, and is never estimated or filled in. Device energy is recorded only
from hardware counters (NVML total energy for GPUs, RAPL for CPU packages); with
neither present, energy stays `null`.

Per attempt (one generation + its verification) the record holds:
  attempt identity : run_id, condition, mode, item, sample_index, seed
  generation       : prompt_tokens, generated_tokens, finish_reason, gpu_time_s,
                     gpu_energy_j (filled by the inference runner; null on CPU-only runs)
  verification     : verify_wall_s, verify_cpu_s (children user+sys), verify_peak_rss_kb,
                     status (rejected / preliminary / certified), path (direct / repl)
  energy           : cpu_package_energy_j (RAPL delta), gpu_energy_j
Environmental-impact statements need facility PUE and grid carbon intensity at run
time; neither is measured here, and no such claim follows from these records.
"""
import json, os, resource, subprocess, threading, time
from pathlib import Path

RAPL = Path("/sys/class/powercap/intel-rapl:0/energy_uj")

def probe():
    av = {}
    av["rapl_cpu_energy"] = RAPL.exists() and os.access(RAPL, os.R_OK)
    try:
        import pynvml  # noqa: F401
        av["nvml"] = True
    except Exception:
        av["nvml"] = False
    av["nvidia_smi"] = subprocess.run(["which", "nvidia-smi"], capture_output=True).returncode == 0
    return av

class PeakRSS(threading.Thread):
    """Samples the summed RSS of this process's descendants every 0.2 s."""
    def __init__(self):
        super().__init__(daemon=True); self.peak = 0; self.stop = threading.Event()
    def _desc(self, pid):
        out = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True).stdout.split()
        return out + [d for c in out for d in self._desc(int(c))]
    def run(self):
        me = os.getpid()
        while not self.stop.is_set():
            tot = 0
            for p in self._desc(me):
                try:
                    for l in open(f"/proc/{p}/status"):
                        if l.startswith("VmRSS"): tot += int(l.split()[1])
                except OSError: pass
            self.peak = max(self.peak, tot); time.sleep(0.2)

class Recorder:
    def __init__(self, path, run_id):
        self.path = Path(path); self.run_id = run_id; self.available = probe()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def measure_verification(self, fn, *a, **kw):
        unavailable = {}
        e0 = int(RAPL.read_text()) if self.available["rapl_cpu_energy"] else None
        r0 = resource.getrusage(resource.RUSAGE_CHILDREN); t0 = time.time()
        mon = PeakRSS(); mon.start()
        res = fn(*a, **kw)
        mon.stop.set(); mon.join()
        r1 = resource.getrusage(resource.RUSAGE_CHILDREN); t1 = time.time()
        e1 = int(RAPL.read_text()) if self.available["rapl_cpu_energy"] else None
        if e0 is None: unavailable["cpu_package_energy_j"] = "RAPL counter absent or unreadable on this machine"
        m = dict(verify_wall_s=round(t1 - t0, 3),
                 verify_cpu_s=round((r1.ru_utime - r0.ru_utime) + (r1.ru_stime - r0.ru_stime), 3),
                 verify_peak_rss_kb=mon.peak,
                 cpu_package_energy_j=None if e0 is None else round((e1 - e0) / 1e6, 3))
        return res, m, unavailable

    def record(self, *, condition, mode, item, sample_index, seed, generation=None, verification=None, status=None, path=None):
        gen = dict(prompt_tokens=None, generated_tokens=None, finish_reason=None, gpu_time_s=None, gpu_energy_j=None)
        unavailable = {}
        if generation: gen.update(generation)
        else: unavailable.update({k: "no inference in this run (CPU-only)" for k in gen})
        if not (self.available["nvml"] or self.available["nvidia_smi"]):
            unavailable["gpu_energy_j"] = "no GPU / NVML on this machine"
        v, vu = (verification or ({}, {}))
        unavailable.update(vu)
        rec = dict(run_id=self.run_id, condition=condition, mode=mode, item=item, sample_index=sample_index, seed=seed,
                   **gen, **v, status=status, path=path, unavailable=unavailable, counters=self.available,
                   timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        with open(self.path, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec
