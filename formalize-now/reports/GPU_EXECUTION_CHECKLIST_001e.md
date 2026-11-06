# GPU execution checklist — RPI-DS-001e (bounded smoke test)

**Scope.** At most 2 C0 outputs for `gdt_periodic` and, optionally, 2 C2 outputs for
`gcd_with_N_iff_gcd_with_R`, on one NVIDIA RTX A6000 (48 GB) at $1.09/hour. This is an
engineering validation and is excluded from confirmatory statistics (Amendment A1 §4).

**Budget.** The cap is $5.00, about 4.6 hours, set in `gpu/pins.json`:

| Threshold | Spend | Hours |
|---|---|---|
| Setup must finish by | $1.50 | ≈ 1.4 h |
| Warning | $3.00 | ≈ 2.75 h |
| Local stop | $4.00 | ≈ 3.7 h |
| Reserve for collection and shutdown | $0.50 | |

The local guard estimates spend from the launch time. **It is not a provider-side
spending cap: the instance bills until it is terminated.**

## Requirements

| Item | Requirement | Source |
|---|---|---|
| GPU | ≥ 40 GB (A6000 48 GB: ≈ 24 GiB KV after the 12.9 GiB weights, ≈ 52K tokens, enough for 2 concurrent 19.5K-token CoT sequences) | `SMOKE_INTERFACE_REVIEW_001d.md` §4 |
| NVIDIA driver | R580 or newer: torch 2.13.0 (required by vLLM 0.32.0) ships CUDA 13.0 user-space libraries; the preflight checks it | `gpu/pins.json` |
| OS / Python | Ubuntu with CUDA driver; Python 3.12 (vLLM 0.32.0 requires 3.11–3.14) | PyPI metadata |
| Disk | ≥ 60 GB free: weights 13.8 GB, Python/CUDA wheels ≈ 10–15 GB, Lean toolchain + Mathlib cache ≈ 6 GB | |
| RAM | ≥ 32 GB: weight loading, REPL ≈ 3.5 GB plus direct Lean check ≈ 3.9 GB at once | |
| Network | GitHub, PyPI, Hugging Face, Mathlib cache (Azure blob) | |

## Expected startup time (estimates)

| Phase | Duration |
|---|---|
| Python env (`vllm==0.32.0`, torch 2.13 and CUDA wheels) | 5–10 min |
| Model download (13.8 GB) and hash verification | 3–10 min |
| elan, `lake update`, Mathlib cache, `lake build` | 3–6 min |
| lean4checker and REPL builds | about 1 min |
| CPU validation (certification, kernel replay, dry run) | about 1 min |
| **Total setup** | **≈ 15–30 min (≈ $0.30–0.55)** |
| Smoke generation | ≤ 6 min for C0, ≤ 12 min with C2 |
| Verification | about 1 min |

## Steps

### A. Before launching (your machine)

- [ ] The branch head to run is pushed, and you note its hash.
- [ ] A Lambda A6000 instance is available. Note the **launch time (UTC)** shown by
      Lambda: it becomes `LAUNCH_TIME`.

### B. On the instance: preparation, no inference

```bash
git clone -b formalize-now/gdt-ladder-stage0 https://github.com/thinkthoughts/DeepSeek-Prover-V2 && cd DeepSeek-Prover-V2
git rev-parse HEAD                                   # must equal the hash you noted
export LAUNCH_TIME=<launch time, e.g. 2026-11-07T16:05:00Z>
nohup python3 formalize-now/gpu/budget.py guard --launch-time $LAUNCH_TIME --interval 30 \
  --out-dir ~/rpi_state > ~/rpi_state_guard.log 2>&1 &   # warning + STOP file (no PID yet)
bash formalize-now/gpu/setup_gpu.sh                  # stops with exit 3 if setup passes $1.50
```

- [ ] `setup_gpu.sh` ends with "Setup complete"; `~/rpi_state/model_verification.json` has `"ok": true`.

### C. Preflight (no inference)

```bash
export MODEL_DIR=~/models/DeepSeek-Prover-V2-7B RPI_VENV_PY=~/rpi-venv/bin/python \
       LEAN4CHECKER=~/rpi-tools/lean4checker/.lake/build/bin/lean4checker RPI_REPL=~/rpi-tools/repl/.lake/build/bin/repl
cd formalize-now/lean49 && ~/rpi-venv/bin/python ../gpu/preflight.py --out ~/rpi_state/preflight.json; cd ../..
```

- [ ] Prints `PASSED`: GPU ≥ 40 GB, driver ≥ 580, vLLM 0.32.0 / torch 2.13.0 with CUDA,
      model hashes, 39/39 certification, lean4checker, budget room.
- [ ] If it prints `FAILED`, **stop**: collect (step E) and terminate (step F). No
      substitutions: no other vLLM, torch or model revision, no quantization.

### D. Launch gate and bounded smoke test (explicit approval)

```bash
export RPI_SMOKE_APPROVED=1      # set only after you approve the launch
~/rpi-venv/bin/python formalize-now/harness/smoke_run.py --live --mode cot &
python3 formalize-now/gpu/budget.py guard --launch-time $LAUNCH_TIME --pid $! --interval 15 --out-dir ~/rpi_state
```

- [ ] The gate passes: approval set, preflight passed < 60 min ago, same HEAD and pins,
      budget room.
- [ ] Every completion and record is written and fsync'd as it is produced
      (`formalize-now/runs/smoke-live-*/`).
- [ ] If interrupted, resume with `--resume <run dir>`; recorded samples are skipped.
- [ ] Optional, only if the C0 path behaved: rerun with `--with-c2 --resume <run dir>`.

### E. Collect and transfer

```bash
bash formalize-now/gpu/collect_results.sh ~/rpi_state
# from your own machine:
scp ubuntu@<instance-ip>:~/rpi_results_*.tar.gz* . && sha256sum -c rpi_results_*.sha256
```

- [ ] The checksum verifies on your machine; the archive holds `runs/`, `state/`,
      `pins.json`, `preregistration.json` and `git_head.txt`.

### F. Shutdown (mandatory)

- [ ] **Terminate** the instance in the Lambda Cloud console (or API). Stopping the
      processes or shutting down the OS ends no billing.
- [ ] Confirm the instance list shows no running instance.
- [ ] Check the billing page for the final charge and record it beside the run.
- [ ] Note actual setup and run times against the estimates above.

## What the live run measures

| Quantity | Source | Unavailable when |
|---|---|---|
| Prompt and generated tokens, finish reason | vLLM output | — |
| Generation wall time | timer around `llm.generate` | — |
| GPU energy (J) | NVML `TotalEnergyConsumption` difference; whole device, idle included | NVML absent (recorded) |
| GPU peak memory, mean power | NVML sampled every 0.5 s | NVML absent (recorded) |
| Lean verification wall/CPU time, peak RSS | `harness/instrument.py` | — |
| CPU package energy | RAPL | usually absent on cloud VMs (recorded) |

Environmental impact is not inferred from these numbers: that needs facility PUE and grid
carbon intensity.

## Untestable without a GPU

1. vLLM 0.32.0 / torch 2.13.0 installation and CUDA initialisation on the instance's
   driver.
2. Model loading at `max_model_len` 20480, `gpu_memory_utilization` 0.90 on 48 GB, and the
   actual KV-cache capacity.
3. Real completion formats from DeepSeek-Prover-V2-7B and their extraction categories.
4. Per-request seeds in vLLM sampling, and reproducibility on this stack.
5. NVML energy, memory and power readings.
6. Throughput, actual generation time and actual setup time and cost.
7. Hugging Face download speed and the hash verification of the two weight shards (the
   tokenizer hash was verified on CPU).
8. `setup_gpu.sh` executed for real (it was syntax-checked and dry-run).
