#!/usr/bin/env bash
# RPI-DS-001e: GPU instance PREPARATION (no inference). Inspectable and dry-runnable on CPU.
#
#   LAUNCH_TIME=2026-11-06T17:02:00Z gpu/setup_gpu.sh            # on the GPU instance
#   DRY_RUN=1 LAUNCH_TIME=... gpu/setup_gpu.sh                   # print every command, run none
#
# Run from the repository root (the clone of formalize-now/gdt-ladder-stage0).
# LAUNCH_TIME = the instance launch time shown by the provider (UTC). It feeds the
# budget gate; setup stops before inference if setup spend passes
# pins.budget.max_setup_spend_before_inference.
#
# Installs ONLY what gpu/pins.json names. It never substitutes a model revision,
# a quantized model or another vLLM/torch version: a failed install stops the script.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"; F="$REPO/formalize-now"; G="$F/gpu"
STATE="${STATE_DIR:-$HOME/rpi_state}"; MODEL_DIR="${MODEL_DIR:-$HOME/models/DeepSeek-Prover-V2-7B}"
VENV="${VENV:-$HOME/rpi-venv}"; TOOLS="${TOOLS_DIR:-$HOME/rpi-tools}"
DRY="${DRY_RUN:-0}"; : "${LAUNCH_TIME:?set LAUNCH_TIME to the provider launch time (UTC ISO-8601)}"
pin() { python3 -c "import json,sys; d=json.load(open('$G/pins.json')); print(eval('d'+sys.argv[1]))" "$1"; }
VLLM=$(pin '["python"]["packages"]["vllm"]'); MODEL=$(pin '["model"]["id"]'); REV=$(pin '["model"]["revision"]')
LEAN4CHECKER_REV=$(pin '["lean"]["lean4checker"]'); REPL_REV=$(pin '["lean"]["repl"]')
MAXSETUP=$(pin '["budget"]["max_setup_spend_before_inference"]')
mkdir -p "$STATE"; LOG="$STATE/setup.log"
run() { echo "+ $*" | tee -a "$LOG"; [ "$DRY" = 1 ] || eval "$@" 2>&1 | tee -a "$LOG"; }
phase() { echo "== phase $1 ($(date -u +%FT%TZ))" | tee -a "$LOG"; echo "{\"phase\":\"$1\",\"start\":\"$(date -u +%FT%TZ)\"}" >> "$STATE/phases.jsonl"; }
gate() {  # stop when estimated spend since launch already exceeds the setup allowance
  local s; s=$(python3 "$G/budget.py" status --launch-time "$LAUNCH_TIME" | python3 -c "import json,sys;print(json.load(sys.stdin)['estimated_spend_usd'])")
  echo "budget: estimated \$$s spent; setup allowance \$$MAXSETUP" | tee -a "$LOG"
  python3 -c "import sys; sys.exit(0 if $s <= $MAXSETUP else 1)" || { echo "SETUP BUDGET EXCEEDED: stop here, collect logs, terminate the instance." | tee -a "$LOG"; exit 3; }
}

phase 0-host-checks
run "uname -a; lsb_release -ds || cat /etc/os-release | head -2"
run "nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader"
run "df -BG --output=avail \"\$HOME\" | tail -1; free -g | awk '/Mem:/{print \$2\" GB RAM\"}'"
run "python3 '$G/preflight.py' --host-only --out '$STATE/host_check.json'"
gate

phase 1-python-env
run "python3.12 -m venv '$VENV' || python3 -m venv '$VENV'"
run "'$VENV/bin/pip' install --upgrade pip"
run "'$VENV/bin/pip' install 'vllm==$VLLM' nvidia-ml-py huggingface_hub tokenizers"
run "'$VENV/bin/pip' freeze > '$STATE/pip_freeze.txt'"
gate

phase 2-model
run "'$VENV/bin/python' -c \"from huggingface_hub import snapshot_download; snapshot_download('$MODEL', revision='$REV', local_dir='$MODEL_DIR', allow_patterns=['*.json','*.safetensors'])\""
run "'$VENV/bin/python' '$G/verify_model.py' '$MODEL_DIR' --json '$STATE/model_verification.json'"
gate

phase 3-lean
run "command -v elan || (curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none)"
run "source \"\$HOME/.elan/env\" && cd '$F/lean49' && lake update && lake exe cache get && lake build"
run "mkdir -p '$TOOLS' && cd '$TOOLS' && ( [ -d lean4checker ] || git clone -q https://github.com/leanprover/lean4checker ) && cd lean4checker && git checkout -q $LEAN4CHECKER_REV && source \"\$HOME/.elan/env\" && lake build"
run "cd '$TOOLS' && ( [ -d repl ] || git clone -q https://github.com/xinhjBrant/repl.git ) && cd repl && git checkout -q $REPL_REV && source \"\$HOME/.elan/env\" && lake build"
gate

phase 4-cpu-validation
run "source \"\$HOME/.elan/env\" && cd '$F/lean49' && lake env lean ../tools/SigCheck.lean > '$STATE/sigcheck.log' 2>&1 && cd '$F' && python3 tools/certify49.py '$STATE/sigcheck.log'"
run "source \"\$HOME/.elan/env\" && cd '$F/lean49' && lake env '$TOOLS/lean4checker/.lake/build/bin/lean4checker' GDTBench.SolutionRef"
run "source \"\$HOME/.elan/env\" && cd '$F' && LEAN4CHECKER='$TOOLS/lean4checker/.lake/build/bin/lean4checker' RPI_REPL='$TOOLS/repl/.lake/build/bin/repl' python3 harness/smoke_run.py --dry-run --with-c2"

phase 5-done
echo "Setup complete. Next: gpu/preflight.py (full), then the approved launch command in reports/GPU_EXECUTION_CHECKLIST_001e.md" | tee -a "$LOG"
