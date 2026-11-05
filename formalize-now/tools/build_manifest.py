#!/usr/bin/env python3
"""RPI-DS-001a: build the GDT theorem/lemma manifest.

Inputs : GDT repo root, kernel dependency JSON (from run_extract.sh, Solution),
         kernel JSON for Challenge.
Output : manifest/gdt_manifest.json  (one record per source declaration)

Two dependency notions are kept separate:
  kernel_deps    : GDT constants occurring in the elaborated term (verified)
  syntactic_refs : GDT names occurring as identifiers in the source text
                   of the declaration, comments stripped (unverified)
"""
import hashlib, json, re, sys, subprocess
from pathlib import Path

gdt, kern_sol, kern_ch, out = map(Path, sys.argv[1:5])
SOL = gdt / "Solution/GeneralDivisorTheorem.lean"
BAS = gdt / "GeneralDivisorTheorem/Basic.lean"
CH = gdt / "Challenge/GeneralDivisorTheorem.lean"

def strip_comments(s):
    s = re.sub(r"/-.*?-/", lambda m: "\n" * m.group(0).count("\n"), s, flags=re.S)
    return re.sub(r"--[^\n]*", "", s)

DECL = re.compile(r"^(?:@\[[^\]]*\]\s*)?(?:private |protected |noncomputable )*(theorem|lemma|def|instance)\s+([^\s:({]+)", re.M)

def split_decls(path, ns):
    raw = path.read_text()
    text = strip_comments(raw)
    hits = list(DECL.finditer(text))
    res = {}
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        chunk = text[m.start():end]
        chunk = re.split(r"^end\s", chunk, flags=re.M)[0]
        line = text.count("\n", 0, m.start()) + 1
        short = m.group(2)
        res[f"{ns}.{short}"] = dict(keyword=m.group(1), short=short, line=line,
                                    file=str(path.relative_to(gdt)), chunk=chunk)
    return res

def statement_of(chunk):
    # source statement = text up to the first top-level ':=' (signature), whitespace-normalised
    depth = 0
    for i, ch in enumerate(chunk):
        if ch in "([{⦃": depth += 1
        elif ch in ")]}⦄": depth -= 1
        elif chunk.startswith(":=", i) and depth == 0:
            return " ".join(chunk[:i].split())
    return " ".join(chunk.split())

sol = split_decls(SOL, "GDT.Challenge")
bas = split_decls(BAS, "GDT")
ch = split_decls(CH, "GDT.Challenge")
kern = {x["name"]: x for x in json.load(open(kern_sol))}
kch = {x["name"]: x for x in json.load(open(kern_ch))}
src = {**bas, **sol}
# instance in Basic has an explicit name
shorts = {v["short"]: k for k, v in src.items()}

TOP = ["gdt_empty", "gdt_periodic", "gdt_minimal_period", "gdt_count_per_period",
       "gdt_density", "gdt_correction_factor", "general_divisor_theorem"]

records, problems = [], []
for name, k in sorted(kern.items()):
    s = src.get(name)
    if s is None:
        problems.append(f"kernel constant without source match: {name}")
        continue
    body = s["chunk"]
    idents = set(re.findall(r"[A-Za-z_][A-Za-z0-9_'.]*", body))
    syn = set()
    for tok in idents:
        for part in {tok, *tok.split(".")}:
            if part in shorts and shorts[part] != name:
                syn.add(shorts[part])
    kd = set(k["value_deps"]) | set(k["type_deps"])
    role = ("definition" if k["kind"] == "def" else
            "challenge_theorem" if s["short"] in TOP else "helper_lemma")
    rec = dict(
        name=name, short=s["short"], kind=k["kind"], role=role,
        source_file=s["file"], source_line=s["line"],
        source_statement=statement_of(body),
        elaborated_type=k["type_pp"], type_hash=k["type_hash"],
        axioms=k["axioms"],
        kernel_deps=sorted(kd),
        syntactic_refs=sorted(syn),
        syntactic_only=sorted(syn - kd),
        kernel_only=sorted(kd - syn),
        mathlib_value_consts=k["mathlib_value_consts"],
    )
    if role == "challenge_theorem":
        c = kch.get(name)
        rec["challenge_type_hash_match"] = bool(c and c["type_hash"] == k["type_hash"])
        rec["challenge_line"] = ch[name]["line"] if name in ch else None
    records.append(rec)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
rev = subprocess.run(["git", "-C", str(gdt), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
manifest = dict(
    schema="rpi-ds-001a/gdt-manifest/v1",
    source_repo="https://github.com/thinkthoughts/general-divisor-theorem",
    source_commit=rev,
    toolchain=(gdt / "lean-toolchain").read_text().strip(),
    file_sha256={str(p.relative_to(gdt)): sha(p) for p in (BAS, CH, SOL)},
    dependency_semantics=dict(
        kernel_deps="GDT constants in the elaborated type or value (auxiliary _proof_/match_ constants expanded); established by Lean",
        syntactic_refs="GDT short names appearing as identifiers in comment-stripped source; not verified",
    ),
    counts=dict(total=len(records), definitions=sum(r["role"] == "definition" for r in records),
                challenge_theorems=sum(r["role"] == "challenge_theorem" for r in records),
                helper_lemmas=sum(r["role"] == "helper_lemma" for r in records)),
    problems=problems,
    declarations=records,
)
out.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
print(json.dumps(manifest["counts"]), "problems:", problems)
