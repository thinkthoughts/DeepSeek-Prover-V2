#!/usr/bin/env bash
# Usage: peak_rss.sh <log> <command...>  — runs command, records wall time and the
# peak summed RSS of the process tree (sampled every 0.5 s from /proc).
LOG="$1"; shift
start=$(date +%s.%N); "$@" > "$LOG" 2>&1 & pid=$!; peak=0
while kill -0 $pid 2>/dev/null; do
  tot=0; for p in $pid $(pgrep -P $pid) $(for c in $(pgrep -P $pid); do pgrep -P $c; done); do
    r=$(awk '/VmRSS/{print $2}' /proc/$p/status 2>/dev/null); tot=$((tot + ${r:-0})); done
  [ $tot -gt $peak ] && peak=$tot; sleep 0.5
done; wait $pid; rc=$?
printf '\n# exit=%s wall_s=%.1f peak_tree_rss_kb=%s\n' "$rc" "$(echo "$(date +%s.%N) - $start" | bc)" "$peak" >> "$LOG"; tail -1 "$LOG"; exit $rc
