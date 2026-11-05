#!/usr/bin/env python3
"""RPI-DS-001a: mechanical Lean 4.34 -> Lean 4.9 translation of GDT files.

Only the transformations listed in TRANSFORMS are applied, and every applied
transformation is recorded (file, line, rule, before, after) in
manifest/translation_log.json. Theorem statements, definitions and proofs are
otherwise copied byte-for-byte. Output files carry a provenance header.

Usage: backport49.py <GDT repo> <out lean49 dir> <manifest dir>
"""
import hashlib, json, re, sys
from pathlib import Path

gdt, outdir, mdir = map(Path, sys.argv[1:4])
log = []

TRANSFORMS = [
    ("T1", "delete `module` header line (module system absent in Lean 4.9)",
     re.compile(r"^module(\s.*)?$"), None),
    ("T2", "`public import X` -> `import X` (visibility modifiers absent in Lean 4.9)",
     re.compile(r"^public import (\S+)\s*$"), lambda m: f"import {m.group(1)}"),
    ("T3", "delete `@[expose] public section` (module-system export control absent in Lean 4.9)",
     re.compile(r"^@\[expose\] public section\s*$"), None),
    ("T4", "import path `GeneralDivisorTheorem.Basic` -> `GDTBench.Defs` (local module name)",
     re.compile(r"^import GeneralDivisorTheorem\.Basic\s*$"), lambda m: "import GDTBench.Defs"),
]

def translate(src: Path, dst: Path, title: str):
    raw = src.read_text()
    out = []
    for i, line in enumerate(raw.split("\n"), 1):
        new = line
        for rid, desc, rx, rep in TRANSFORMS:
            m = rx.match(new)
            if m:
                after = None if rep is None else rep(m)
                log.append(dict(file=str(src.relative_to(gdt)), line=i, rule=rid,
                                before=new, after=after))
                new = after
                if new is None:
                    break
        if new is not None:
            out.append(new)
    sha = hashlib.sha256(raw.encode()).hexdigest()
    hdr = (f"-- RPI-DS-001a TRANSLATED FILE ({title}).\n"
           f"-- Source: thinkthoughts/general-divisor-theorem/{src.relative_to(gdt)}\n"
           f"-- Source sha256: {sha}\n"
           f"-- Rules applied: see formalize-now/manifest/translation_log.json\n"
           f"-- Everything else is copied verbatim from the source file.\n")
    dst.write_text(hdr + "\n".join(out))
    return sha

shas = {}
shas["Defs"] = translate(gdt / "GeneralDivisorTheorem/Basic.lean", outdir / "GDTBench/Defs.lean", "definitions")
shas["Challenge"] = translate(gdt / "Challenge/GeneralDivisorTheorem.lean", outdir / "GDTBench/Challenge.lean", "challenge statements")
shas["SolutionPort"] = translate(gdt / "Solution/GeneralDivisorTheorem.lean", outdir / "GDTBench/SolutionPort.lean", "unchanged human proofs, compatibility probe")

# Ladder: helper-lemma statements from the manifest, proofs replaced by `sorry`
man = json.loads((mdir / "gdt_manifest.json").read_text())
helpers = sorted((d for d in man["declarations"] if d["role"] == "helper_lemma"), key=lambda d: d["source_line"])
sol_lines = (gdt / "Solution/GeneralDivisorTheorem.lean").read_text().split("\n")
body = []
for d in helpers:
    # exact source text from the declaration line up to the top-level `:=`
    chunk = "\n".join(sol_lines[d["source_line"] - 1:])
    depth, cut = 0, None
    for i, ch in enumerate(chunk):
        if ch in "([{⦃": depth += 1
        elif ch in ")]}⦄": depth -= 1
        elif chunk.startswith(":=", i) and depth == 0:
            cut = i; break
    sig = chunk[:cut].rstrip()
    body.append(f"-- source: Solution/GeneralDivisorTheorem.lean:{d['source_line']}\n{sig} :=\n  sorry\n")
ladder = ("-- RPI-DS-001a GENERATED FILE (ladder statements).\n"
          "-- Each signature is copied verbatim from the source line cited above it;\n"
          "-- each proof is replaced by `sorry` (benchmark item, intentionally unproved).\n"
          f"-- Solution sha256: {shas['SolutionPort']}\n"
          "import GDTBench.Defs\nimport Mathlib.Data.Nat.Squarefree\n\n"
          "namespace GDT.Challenge\n\nopen GDT\n\n" + "\n".join(body) + "\nend GDT.Challenge\n")
(outdir / "GDTBench/Ladder.lean").write_text(ladder)
log.append(dict(file="Solution/GeneralDivisorTheorem.lean", line=None, rule="L1",
                before="32 helper lemma proofs", after="`sorry` in GDTBench/Ladder.lean (statements verbatim)"))
(mdir / "translation_log.json").write_text(json.dumps(dict(
    rules=[dict(id=r[0], description=r[1]) for r in TRANSFORMS] +
          [dict(id="L1", description="Ladder: helper-lemma signature verbatim, proof -> sorry")],
    source_sha256=shas, applied=log), indent=1, ensure_ascii=False) + "\n")
print(len(log), "transformations;", len(helpers), "ladder items")
