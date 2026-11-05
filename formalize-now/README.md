# formalize-now / RPI-DS-001a — GDT-Ladder Stage 0

This directory holds an independent, CPU-only preparation step for a theorem-proving
experiment with DeepSeek-Prover-V2. It belongs to formalize.now (thinkthoughts) and sits on
the branch `formalize-now/gdt-ladder-stage0` of the fork
`thinkthoughts/DeepSeek-Prover-V2`. The upstream files at the repository root stay
byte-identical to `deepseek-ai/DeepSeek-Prover-V2@e598a57`.

Background: *DeepSeek-Prover-V2: Independent Technical Review and Initial Experiment*
(formalize.now). Stage 0 implements its §D "Stage 0" items.

## The experiment in one paragraph

GDT-Ladder asks whether giving DeepSeek-Prover-V2-7B the human lemma graph of the
General Divisor Theorem (GDT), in the paper's own lemma format, changes how many GDT
theorems it proves at a fixed compute budget. GDT is a good test because its eight
definitions are absent from the model's training data and its Solution file holds a
complete, kernel-checked lemma graph. Stage 0 builds the inputs and runs no model:
an inventory of every theorem and lemma, the dependencies Lean actually verified, a
mechanical translation to the model's Lean 4.9 environment, and a test of how much
of it survives.

## What Stage 0 established (checked on 2026-11-05)

| Check | Result |
|---|---|
| Original GDT (`general-divisor-theorem@ec66260`, Lean 4.34.0-rc2) builds unchanged | Pass: 1319 jobs, 0 errors |
| Inventory | 48 declarations: 9 definitions, 7 challenge theorems, 32 helper lemmas |
| Solution proofs, axioms (kernel) | All 39 theorems use only `propext`, `Quot.sound`, `Classical.choice` (`gcd_mod_eq`: `propext`, `Quot.sound`) |
| Challenge vs Solution statements | All 7 elaborated types have identical structural hashes and pretty-printed forms |
| Translation to Lean 4.9.0-rc1 | 4 mechanical rules, 14 line edits, all logged; statements and definitions verbatim |
| Definitions, 7 challenge statements, 32 ladder statements under Lean 4.9 | All elaborate, 0 errors |
| The same 39 statements under the DeepSeek V1.5 prompt header and `import Mathlib` | All elaborate, 0 errors; elaborated constants identical to the header-free build |
| Unchanged human proofs under Lean 4.9 | 19 kernel-clean, 9 fail directly, 11 inherit `sorryAx` from those 9 |

Details: [`reports/DEPENDENCIES.md`](reports/DEPENDENCIES.md),
[`reports/LEAN49_COMPATIBILITY.md`](reports/LEAN49_COMPATIBILITY.md),
[`reports/BUILD_AND_VERIFICATION.md`](reports/BUILD_AND_VERIFICATION.md),
[`reports/RECOMMENDATION_RPI-DS-001b.md`](reports/RECOMMENDATION_RPI-DS-001b.md).
The benchmark objective and preservation conditions are in [`SPEC.md`](SPEC.md).

## Layout

```text
formalize-now/
  README.md, SPEC.md
  manifest/
    gdt_manifest.json          theorem/lemma manifest with kernel and syntactic dependencies
    translation_log.json       every Lean 4.34 -> 4.9 edit (file, line, rule, before, after)
    lean49_port_status.json    per-theorem result of the unchanged proofs under Lean 4.9
  lean49/                      Lean 4.9 project (translated, separately attributable)
    lean-toolchain, lakefile.lean
    GDTBench/Defs.lean         translated definitions
    GDTBench/Challenge.lean    translated 7 challenge statements (sorry)
    GDTBench/Ladder.lean       32 helper-lemma statements, verbatim signatures (sorry)
    GDTBench/SolutionPort.lean unchanged human proofs: a compatibility probe, NOT a proof artifact
  benchmark/
    gdt_items.jsonl            39 items in DeepSeek V1.5/V2 prompt shape (no proofs)
    AllItemsCheck.lean         all items under the V1.5 header, for the elaboration check
  tools/                       extractors, translator, generators, check scripts
  reports/                     human-readable reports (+ _generated_* tables)
  logs/                        build, elaboration, axiom and extraction logs
```

## Reproduce

Requirements: `elan`, `git`, `python3`, network access to GitHub and the Mathlib cache.
Machine used: 2 vCPU, 7 GiB RAM, no swap. Peak RSS stayed below 1.4 GB for the GDT
modules and reached 3.55 GB for the `import Mathlib` item check.

```bash
# 1. original GDT, unchanged (Lean 4.34.0-rc2)
git clone https://github.com/thinkthoughts/general-divisor-theorem && cd general-divisor-theorem
lake exe cache get && lake build && lake build Challenge && lake build Solution && cd ..

# 2. kernel inventory (temporary copy inside GDT/.lake; source files untouched)
formalize-now/tools/run_extract.sh general-divisor-theorem formalize-now/logs/deps_solution.json Solution
formalize-now/tools/run_extract.sh general-divisor-theorem formalize-now/logs/deps_challenge.json Challenge
python3 formalize-now/tools/build_manifest.py general-divisor-theorem \
  formalize-now/logs/deps_solution.json formalize-now/logs/deps_challenge.json formalize-now/manifest/gdt_manifest.json

# 3. Lean 4.9 environment: upstream Mathlib at the fork's parent commit (cache available)
git clone https://github.com/leanprover-community/mathlib4 mathlib-d1d1e4b && cd mathlib-d1d1e4b
git checkout d1d1e4b72c6e009edd97cabe1d661b021fe8eeae && lake exe cache get && cd ..

# 4. translate, then elaborate under Lean 4.9
python3 formalize-now/tools/backport49.py general-divisor-theorem formalize-now/lean49 formalize-now/manifest
B=$PWD/build49; mkdir -p $B/GDTBench; T=formalize-now/tools; L=$PWD/formalize-now/lean49
$T/lean49_check.sh mathlib-d1d1e4b $B Defs --root=$L -o $B/GDTBench/Defs.olean -i $B/GDTBench/Defs.ilean $L/GDTBench/Defs.lean
for n in Challenge Ladder SolutionPort; do $T/lean49_check.sh mathlib-d1d1e4b $B $n --root=$L $L/GDTBench/$n.lean; done
$T/axiom_probe49.sh mathlib-d1d1e4b $B

# 5. benchmark items and reports
python3 $T/build_items.py $PWD/formalize-now
$T/lean49_check.sh mathlib-d1d1e4b $B items_full_mathlib --root=$PWD/formalize-now/benchmark \
  $PWD/formalize-now/benchmark/AllItemsCheck.lean
python3 $T/make_reports.py
```

The statement-surface comparison (`tools/StatementSurface.append.lean`) is described in
`reports/BUILD_AND_VERIFICATION.md`.

## Scope boundaries

Stage 0 used CPU only: no model downloads, no inference, no retraining, no upstream file
changes, no pull request. Nothing here claims a proof under Lean 4.9: the only files
presented as proofs are the original GDT files, verified in their own toolchain.

## Attribution

- GDT mathematics and Lean source: thinkthoughts / Dan Hawkley, Apache-2.0,
  `github.com/thinkthoughts/general-divisor-theorem@ec66260`. Translated files carry the
  source path and sha256 in their headers.
- DeepSeek-Prover-V2 and V1.5: DeepSeek-AI; upstream licences apply to upstream files.
- Stage 0 tooling and reports: formalize.now, prepared with Claude (Anthropic).
