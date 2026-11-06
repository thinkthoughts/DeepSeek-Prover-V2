#!/usr/bin/env python3
"""RPI-DS-001c: exercise the instrumentation on CPU with the two Cauto-certified items
and one rejected candidate (no inference). Writes logs/instrument_demo.jsonl."""
import sys
from pathlib import Path
H = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(H))
import verify_strict as vs
from instrument import Recorder
rec = Recorder(H.parent / "logs/instrument_demo.jsonl", run_id="rpi-ds-001c-cpu-demo")
for i, (item, cand) in enumerate([("gdt/coprime_add_mul_right", "simp"), ("gdt/S_eq_filter_Ico", "aesop"), ("gdt/gdt_empty", "sorry")]):
    res, m, u = rec.measure_verification(vs.verify, item, cand, "proof", True)
    r = rec.record(condition="Cauto", mode="tactic", item=item, sample_index=i, seed=None, verification=(m, u),
                   status=res["status"], path=res.get("path"))
    print(item, res["status"], m, sorted(r["unavailable"]))
