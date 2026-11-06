#!/usr/bin/env python3
"""RPI-DS-001e: local spend estimate and budget guard.

THIS IS NOT A PROVIDER-SIDE SPENDING CAP. It estimates spend from the instance launch
time and the hourly rate in gpu/pins.json, warns, and stops the local run. The provider
keeps billing until the instance is TERMINATED in its console or API.

  estimate        : `budget.py status --launch-time ISO8601`
  guard (watchdog): `budget.py guard --launch-time ISO --pid PID [--interval 15]`
                    writes budget_status.json each interval; at `warn_at` logs a warning;
                    at `stop_at` sends SIGTERM to PID (SIGKILL after 30 s) and writes
                    STOPPED_BY_BUDGET with shutdown instructions.
  gate            : `budget.py gate --launch-time ISO --need-usd X` exits 1 if spending X
                    more would pass stop_at (used before setup steps and before inference).
`--clock-scale` multiplies elapsed time (tests only).
"""
import argparse, datetime as dt, json, os, signal, sys, time
from pathlib import Path
PINS = json.loads((Path(__file__).resolve().parent / "pins.json").read_text())
B = PINS["budget"]

def parse(t):
    d = dt.datetime.fromisoformat(t.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)

def spent(launch, scale=1.0, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    hours = max(0.0, (now - launch).total_seconds()) / 3600.0 * scale
    return round(hours * B["rate_per_hour"], 4), round(hours, 4)

def status(launch, scale=1.0):
    usd, h = spent(launch, scale)
    level = "stop" if usd >= B["stop_at"] else "warn" if usd >= B["warn_at"] else "ok"
    return dict(estimated_spend_usd=usd, elapsed_hours=h, rate_per_hour=B["rate_per_hour"], warn_at=B["warn_at"],
                stop_at=B["stop_at"], cap=B["cap"], level=level, remaining_to_stop_usd=round(B["stop_at"] - usd, 4),
                provider_side_cap=False, note=B["note"])

SHUTDOWN = ("Budget stop reached. Collect results (gpu/collect_results.sh), copy them off the instance, "
            "then TERMINATE the instance in the provider console and confirm it is gone from the instance list.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "guard", "gate"])
    ap.add_argument("--launch-time", required=True)
    ap.add_argument("--pid", type=int); ap.add_argument("--interval", type=float, default=15)
    ap.add_argument("--need-usd", type=float, default=0.0); ap.add_argument("--clock-scale", type=float, default=1.0)
    ap.add_argument("--out-dir", default=".")
    a = ap.parse_args(); launch = parse(a.launch_time); out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    if a.cmd == "status":
        print(json.dumps(status(launch, a.clock_scale), indent=1)); return 0
    if a.cmd == "gate":
        s = status(launch, a.clock_scale)
        ok = s["estimated_spend_usd"] + a.need_usd <= B["stop_at"]
        print(json.dumps(dict(s, need_usd=a.need_usd, gate="pass" if ok else "fail"), indent=1))
        return 0 if ok else 1
    warned = False
    while True:
        s = status(launch, a.clock_scale)
        (out / "budget_status.json").write_text(json.dumps(dict(s, checked_at=time.time()), indent=1) + "\n")
        if s["level"] == "warn" and not warned:
            print(f"BUDGET WARNING: estimated ${s['estimated_spend_usd']:.2f} of stop ${B['stop_at']:.2f}", flush=True); warned = True
        if s["level"] == "stop":
            (out / "STOPPED_BY_BUDGET").write_text(json.dumps(s, indent=1) + "\n" + SHUTDOWN + "\n")
            print("BUDGET STOP: " + SHUTDOWN, flush=True)
            if a.pid:
                try:
                    os.kill(a.pid, signal.SIGTERM)
                    for _ in range(30):
                        time.sleep(1); os.kill(a.pid, 0)
                    os.kill(a.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            return 2
        if a.pid:
            try: os.kill(a.pid, 0)
            except ProcessLookupError: return 0
        time.sleep(a.interval)

if __name__ == "__main__":
    sys.exit(main())
