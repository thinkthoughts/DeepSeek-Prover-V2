#!/usr/bin/env bash
# RPI-DS-001e: package results for transfer OFF the GPU instance (run before terminating).
#   gpu/collect_results.sh [STATE_DIR]      -> ~/rpi_results_<UTC>.tar.gz + .sha256
# Then, from your own machine (not the instance):
#   scp ubuntu@<instance-ip>:~/rpi_results_*.tar.gz* .   &&  sha256sum -c rpi_results_*.sha256
# Nothing here pushes to GitHub; results enter the repository only after review.
set -euo pipefail
F="$(cd "$(dirname "$0")/.." && pwd)"; STATE="${1:-${STATE_DIR:-$HOME/rpi_state}}"
TS=$(date -u +%Y%m%dT%H%M%SZ); OUT="${OUT_DIR:-$HOME}/rpi_results_$TS.tar.gz"
TMP=$(mktemp -d); mkdir -p "$TMP/rpi_results_$TS"
[ -d "$F/runs" ] && cp -r "$F/runs" "$TMP/rpi_results_$TS/"
[ -d "$STATE" ] && cp -r "$STATE" "$TMP/rpi_results_$TS/state"
git -C "$F" rev-parse HEAD > "$TMP/rpi_results_$TS/git_head.txt"
cp "$F/gpu/pins.json" "$F/preregistration.json" "$TMP/rpi_results_$TS/"
( cd "$TMP/rpi_results_$TS" && find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 sha256sum > MANIFEST.sha256 )
tar -C "$TMP" -czf "$OUT" "rpi_results_$TS"
( cd "$(dirname "$OUT")" && sha256sum "$(basename "$OUT")" > "$(basename "$OUT" .tar.gz).sha256" )
rm -rf "$TMP"
echo "archive: $OUT"; echo "checksum: ${OUT%.tar.gz}.sha256"
echo "NEXT: copy both files off the instance, verify the checksum locally, then TERMINATE the instance."
