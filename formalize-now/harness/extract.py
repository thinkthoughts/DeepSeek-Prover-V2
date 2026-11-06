#!/usr/bin/env python3
"""RPI-DS-001d: extract a candidate proof body from a DeepSeek-Prover-V2 completion.

Trust boundary. The model's text is used for ONE thing: the tactic proof of the target
theorem. The header, definitions, theorem name and signature always come from the
trusted item (benchmark/gdt_items_v2.jsonl) and are assembled by
`verify_strict.assemble(..., mode="proof")`. Anything else the model writes (its echo of
the header, definitions, the statement, helper declarations, commentary) is recorded as
diagnostics and never compiled.

Formats
  cot     : the completion contains a plan and a fenced ```lean4 block holding a whole
            file (V2 README prompt). The LAST closed lean/lean4 block is used; inside it,
            the unique declaration `theorem|lemma <target>` is located and the text after
            its top-level `:= by` is taken up to the first non-empty column-0 line.
  noncot  : the prompt ends inside an open code block right after `:= by\\n` (V1.5
            `non_cot_prompt` convention); the completion IS the proof continuation, taken
            up to the closing ``` or the first non-empty column-0 line.

Categories (first match wins; only `extracted` proceeds to verification)
  no_code_block, truncated, target_missing, ambiguous_target, term_mode_proof,
  empty_proof, extracted
"""
import re

FENCE = re.compile(r"```(?:lean4|lean)[ \t]*\n(.*?)\n?```", re.S)
OPEN_FENCE = re.compile(r"```(?:lean4|lean)[ \t]*\n")
DECL_KW = r"(?:theorem|lemma)"
ANY_DECL = re.compile(r"^(?:@\[[^\]]*\]\s*)?(?:private |protected |noncomputable )*(theorem|lemma|def|abbrev|instance|axiom|example)\s*(\S*)", re.M)

def _norm(s):
    return " ".join(s.split())

def _top_level_assign(text, start):
    depth = 0
    for j in range(start, len(text)):
        c = text[j]
        if c in "([{⦃⟨": depth += 1
        elif c in ")]}⦄⟩": depth -= 1
        elif text.startswith(":=", j) and depth == 0:
            return j
    return None

def _body_until_col0(lines):
    out = []
    for l in lines:
        if l.strip() and not l[0].isspace():
            break
        out.append(l)
    while out and not out[-1].strip():
        out.pop()
    ind = min((len(l) - len(l.lstrip(" ")) for l in out if l.strip()), default=0)
    return "\n".join(l[ind:] if len(l) >= ind else l.lstrip(" ") for l in out)

def trusted_signature(item):
    st = item["formal_statement"]
    return st.split("namespace GDT.Challenge\nopen GDT\n\n", 1)[1].rsplit(":= by\n  sorry", 1)[0]

def extract(completion, item, fmt, finish_reason=None):
    short = item["id"].split("/")[-1]
    diag = dict(format=fmt, finish_reason=finish_reason, completion_chars=len(completion))
    if fmt == "noncot":
        cut = completion.split("```", 1)
        closed = len(cut) == 2
        lines = cut[0].split("\n")
        body = _body_until_col0(lines)
        stopped_at_col0 = any(l.strip() and not l[0].isspace() for l in lines)
        if not closed and not stopped_at_col0 and finish_reason == "length":
            return dict(category="truncated", proof=None, diagnostics=diag)
        if body.strip().startswith(":="):
            return dict(category="term_mode_proof", proof=None, diagnostics=diag)
        if not body.strip():
            return dict(category="empty_proof", proof=None, diagnostics=diag)
        diag["trailing_text_after_proof_chars"] = len(completion) - len(cut[0])
        return dict(category="extracted", proof=body, diagnostics=diag)

    blocks = FENCE.findall(completion)
    if not blocks:
        opened = OPEN_FENCE.search(completion)
        cat = "truncated" if (opened or finish_reason == "length") else "no_code_block"
        return dict(category=cat, proof=None, diagnostics=diag)
    block = blocks[-1]
    diag["code_blocks"] = len(blocks)
    hits = [m for m in re.finditer(rf"^{DECL_KW}\s+{re.escape(short)}(?=[\s:({{\[]|$)", block, re.M)]
    decls = [(m.group(1), m.group(2)) for m in ANY_DECL.finditer(block)]
    diag["declarations_in_block"] = [f"{k} {n}" for k, n in decls]
    trusted = {n for _, n in ANY_DECL.findall(item["definitions"])}
    diag["echoed_trusted_declarations"] = sorted(n for _, n in decls if n in trusted)
    diag["extra_declarations"] = [f"{k} {n}" for k, n in decls if n != short and n not in trusted]
    diag["header_echo_matches"] = block.startswith((item["header"] + item["definitions"]).rstrip("\n")[:200])
    if not hits:
        return dict(category="target_missing", proof=None, diagnostics=diag)
    if len(hits) > 1:
        return dict(category="ambiguous_target", proof=None, diagnostics=diag)
    m = hits[0]
    a = _top_level_assign(block, m.end())
    if a is None:
        return dict(category="target_missing", proof=None, diagnostics=diag)
    sig = block[m.start():a]
    diag["statement_echo_matches"] = _norm(sig) == _norm(trusted_signature(item))
    rest = block[a + 2:]
    stripped = rest.lstrip()
    if not re.match(r"by(\s|$)", stripped):
        return dict(category="term_mode_proof", proof=None, diagnostics=diag)
    after_by = stripped[2:]
    first, _, tail = after_by.partition("\n")
    lines = ([("  " + first.strip())] if first.strip() else []) + tail.split("\n")
    body = _body_until_col0(lines)
    if not body.strip():
        return dict(category="empty_proof", proof=None, diagnostics=diag)
    return dict(category="extracted", proof=body, diagnostics=diag)
