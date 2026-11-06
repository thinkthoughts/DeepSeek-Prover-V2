#!/usr/bin/env python3
"""RPI-DS-001e: verify downloaded model files against gpu/pins.json.

Large files: size + sha256 (Hugging Face LFS hashes at the pinned revision).
Small files: size + git blob sha1 (sha1(b"blob <size>\\0" + content)), and sha256 where pinned.
Any missing, extra-size or mismatched file fails. No network access.
usage: verify_model.py <model_dir> [--only name ...] [--json out]
"""
import hashlib, json, sys
from pathlib import Path
PINS = json.loads((Path(__file__).resolve().parent / "pins.json").read_text())

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()

def blob_sha1(p):
    data = Path(p).read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()

def verify(model_dir, only=None):
    rows, ok = [], True
    for name, spec in PINS["model"]["files"].items():
        if only and name not in only: continue
        p = Path(model_dir) / name
        r = dict(file=name, present=p.exists())
        if p.exists():
            r["size_ok"] = p.stat().st_size == spec["size"]
            if "sha256" in spec: r["sha256_ok"] = sha256(p) == spec["sha256"]
            if "git_blob_sha1" in spec: r["blob_sha1_ok"] = blob_sha1(p) == spec["git_blob_sha1"]
        r["ok"] = r["present"] and all(v for k, v in r.items() if k.endswith("_ok"))
        ok &= r["ok"]; rows.append(r)
    return dict(model=PINS["model"]["id"], revision=PINS["model"]["revision"], ok=ok, files=rows)

if __name__ == "__main__":
    args = sys.argv[1:]
    only = args[args.index("--only") + 1:] if "--only" in args else None
    out = args[args.index("--json") + 1] if "--json" in args else None
    if only and out: only = [o for o in only if o != "--json" and o != out]
    res = verify(args[0], only)
    s = json.dumps(res, indent=1)
    if out: Path(out).write_text(s + "\n")
    print(s); sys.exit(0 if res["ok"] else 1)
