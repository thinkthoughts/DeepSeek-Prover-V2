#!/usr/bin/env python3
"""RPI-DS-001c: deterministic prompt construction for the pre-registered conditions,
with an automated reference-proof leakage check. CPU only; no tokenizer is loaded
(token counts are measured at inference time with the model's own tokenizer).

Prompt template: DeepSeek-Prover-V2 README (CoT), verbatim, with `{}` = the Lean code.
Sources used: benchmark/gdt_items_v2.jsonl (header, definitions, statements) and the
ladder statements; SolutionRef.lean is read ONLY to check that none of its proof
lines appears in any prompt.

usage: prompts.py  -> benchmark/prompts_v1.jsonl, benchmark/prompts_v1.manifest.json
"""
import hashlib, json, re
from pathlib import Path
F = Path(__file__).resolve().parent.parent
TEMPLATE_COT = ("Complete the following Lean 4 code:\n\n```lean4\n{}\n```\n\n"
                "Before producing the Lean 4 code to formally prove the given theorem, provide a detailed proof plan outlining the main proof steps and strategies.\n"
                "The plan should highlight key ideas, intermediate lemmas, and proof structures that will guide the construction of the final formal proof.")
TEMPLATE_NONCOT = "Complete the following Lean 4 code:\n\n```lean4\n{}"
items = {json.loads(l)["id"]: json.loads(l) for l in (F / "benchmark/gdt_items_v2.jsonl").read_text().splitlines()}
man = json.loads((F / "manifest/gdt_manifest_v2.json").read_text())
deps = {d["short"]: sorted(x.split(".")[-1] for x in d["kernel_deps"] if x.startswith("GDT.Challenge."))
        for d in man["declarations"] if d["kind"] == "theorem"}
order = [d["short"] for d in sorted((d for d in man["declarations"] if d["kind"] == "theorem"), key=lambda d: d["source_line"])]

def closure(n):
    seen, todo = set(), list(deps[n])
    while todo:
        x = todo.pop()
        if x not in seen: seen.add(x); todo += deps[x]
    return [x for x in order if x in seen]           # source order = a valid dependency order

def stmt_only(short):
    st = items[f"gdt/{short}"]["formal_statement"]
    return st.split("namespace GDT.Challenge\nopen GDT\n\n", 1)[1].rsplit(":= by\n  sorry", 1)[0].rstrip()

def code(short, cond):
    it = items[f"gdt/{short}"]
    pre = it["header"] + it["definitions"] + "\n"
    if cond in ("C0", "C1"):
        return pre + it["formal_statement"]
    if cond == "C0h":
        hint = "\n".join("-- " + l for s in closure(short) for l in (stmt_only(s) + "\n").split("\n"))
        return pre + "-- Statements of facts that may help (not available as Lean declarations):\n" + hint + "\n" + it["formal_statement"]
    if cond == "C2":
        ctx = "".join(f"namespace GDT.Challenge\nopen GDT\n\n{stmt_only(d)} := by\n  sorry\n\nend GDT.Challenge\n\n" for d in deps[short])
        return pre + ctx + it["formal_statement"]
    raise ValueError(cond)

def main():
    challenge = [d["short"] for d in man["declarations"] if d["role"] == "challenge_theorem"]
    plan = [(c, s) for c in ("C0", "C0h") for s in challenge] + [(c, s) for c in ("C1", "C2") for s in order]
    ref = (F / "lean49/GDTBench/SolutionRef.lean").read_text()
    # proof-body lines of the reference: every line after a declaration's `:= by` that is not a statement line
    proof_lines = set()
    for m in re.finditer(r":= by\n(.*?)(?=\n(?:theorem|lemma|def|/--|end )|\Z)", ref, flags=re.S):
        for l in m.group(1).split("\n"):
            t = " ".join(l.split())
            if len(t) >= 20: proof_lines.add(t)
    # lines that belong to public statement/definition text are not proof content
    public = set()
    for it in items.values():
        for fld in ("header", "definitions", "formal_statement"):
            public |= {" ".join(l.split()) for l in it[fld].split("\n")}
    proof_lines -= public
    out, leaks = [], []
    for cond, short in plan:
        c = code(short, cond)
        for mode, tpl in (("cot", TEMPLATE_COT), ("noncot", TEMPLATE_NONCOT)):
            p = tpl.format(c)
            norm = {" ".join(l.split()) for l in p.split("\n")}
            hit = sorted(norm & proof_lines)
            if hit: leaks.append(dict(condition=cond, item=short, mode=mode, lines=hit[:3]))
            out.append(dict(id=f"{cond}/{mode}/{short}", condition=cond, mode=mode, item=f"gdt/{short}",
                            context_lemmas=(closure(short) if cond == "C0h" else deps[short] if cond == "C2" else []),
                            prompt_chars=len(p), prompt_sha256=hashlib.sha256(p.encode()).hexdigest(), prompt=p))
    with open(F / "benchmark/prompts_v1.jsonl", "w") as f:
        for o in out: f.write(json.dumps(o, ensure_ascii=False) + "\n")
    blob = (F / "benchmark/prompts_v1.jsonl").read_bytes()
    (F / "benchmark/prompts_v1.manifest.json").write_text(json.dumps(dict(
        prompts=len(out), sha256=hashlib.sha256(blob).hexdigest(), reference_proof_lines_checked=len(proof_lines),
        leaks=leaks, closure_sizes={s: len(closure(s)) for s in challenge}), indent=1) + "\n")
    print(len(out), "prompts; reference lines checked:", len(proof_lines), "; leaks:", len(leaks))
    if leaks: raise SystemExit("reference-proof leakage detected")

if __name__ == "__main__":
    main()
