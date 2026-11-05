#!/usr/bin/env bash
# Usage: lean49_check.sh <mathlib dir (Lean 4.9 env)> <build dir> <log name> <lean args...>
# Runs `lean` inside the Lean 4.9 Mathlib environment with <build dir> on LEAN_PATH,
# logging output, exit status, wall time and peak RSS (from /proc via a sampler).
set -uo pipefail
ML="$1"; B="$2"; NAME="$3"; shift 3
LOG="$(cd "$(dirname "$0")/.." && pwd)/logs/lean49_${NAME}.log"
cd "$ML"
LP="$(lake env printenv LEAN_PATH):$B"
start=$(date +%s.%N)
LEAN_PATH="$LP" lake env lean "$@" > "$LOG" 2>&1 &
pid=$!; peak=0
while kill -0 $pid 2>/dev/null; do
  for p in $pid $(pgrep -P $pid); do
    r=$(awk '/VmRSS/{print $2}' /proc/$p/status 2>/dev/null || echo 0); [ "${r:-0}" -gt "$peak" ] && peak=$r
  done; sleep 0.5
done
wait $pid; rc=$?
end=$(date +%s.%N)
printf '\n# exit=%s wall_s=%.1f peak_rss_kb=%s\n' "$rc" "$(echo "$end - $start" | bc)" "$peak" >> "$LOG"
echo "$NAME exit=$rc"; tail -1 "$LOG"
