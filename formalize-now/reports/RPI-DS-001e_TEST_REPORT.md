# RPI-DS-001e — Test report (CPU only)

**Result.** Every CPU-side check passes in one consolidated run (`tools/validate_001e.sh`,
13 min 43 s, 2 vCPU / 7 GiB, no GPU):

- 39/39 reference proofs remain certified, with lean4checker replay and `--fresh` replay;
- all 140 harness tests across 7 suites pass;
- `prompts_v1` and `prompts_v2` regenerate byte for byte;
- smoke dry runs complete in both modes.

The patch adds a kernel-level information check (C9), a C2 condition suite over all 39
items, and a GPU execution kit with preflight, launch gate, budget guard, resumable runs,
collection and a shutdown checklist. Recommendation: **GO** for the bounded smoke test when
an A6000 is available, subject to the preflight passing on the instance.

## Commands and outcomes

Environment variables:

```bash
export LEAN4CHECKER=<lean4checker@9da7f4a3>/.lake/build/bin/lean4checker \
       RPI_REPL=<repl@3334a97>/.lake/build/bin/repl TOKENIZER_JSON=<pinned tokenizer.json>
formalize-now/tools/validate_001e.sh      # logs/validate_001e.log
```

| Step | Command | Outcome | Wall |
|---|---|---|---|
| Clean build | `cd lean49 && rm -rf .lake/build && lake build` | exit 0 | 3.8 s |
| Certification | `lake env lean ../tools/SigCheck.lean` → `python3 tools/certify49.py logs/lean49_sigcheck.log` | `certified 39 / 39 \| scan {} \| sigs unchanged True` | 5.6 s |
| Kernel replay | `lake env $LEAN4CHECKER GDTBench.SolutionRef` | exit 0 | 1.0 s |
| Fresh kernel replay | `lake env $LEAN4CHECKER --fresh GDTBench.SolutionRef` | exit 0 | 272.6 s |
| Strict verifier | `harness/tests/run_tests.py` | 18/18 (13 with kernel replay, 3 preliminary-mode, 2 counting guards) | 46.4 s |
| REPL adapter vs direct | `harness/tests/run_repl_tests.py` | 16/16 agree; certify mode 5/5 | 64.6 s |
| Extraction + trusted assembly | `harness/tests/run_extract_tests.py` | 15/15 | 29.6 s |
| C2 verification contexts | `harness/tests/run_context_tests.py` | 42/42 (39 reference proofs certified in context + 3 negatives, incl. transitive-use → C9) | 198.0 s |
| Theorem-level assembler | `harness/tests/run_assembly_tests.py` | 23/23 | 93.3 s |
| C2 condition (graph, prompts) | `harness/tests/run_c2_condition_tests.py` | 9/9 | 50.6 s |
| GPU kit on CPU | `harness/tests/run_infra_tests.py` | 12/12 | 45.7 s |
| Prompt reproducibility | `harness/prompts.py --version 1/2` then `git diff --quiet` | both byte-identical; 0 reference-proof lines in 184 prompts | — |
| Smoke dry runs | `harness/smoke_run.py --dry-run --with-c2 --mode cot` and `--mode noncot` | completed; fixtures rejected as designed | 5 s each |

## Assignment 1 — C2 condition

| Requirement | Implementation | Evidence |
|---|---|---|
| Original statement preserved | trusted statement from the item; the model's echo is never compiled | P1: verbatim, once, last, in all 78 C2 prompts; P5: 92 CoT prompts elaborate with statements alpha-equivalent to the trusted ones |
| Only permitted dependency information | the C2 prompt declares the item's **direct** dependencies (statements, `sorry` bodies); the verification context also holds the transitive closure, needed only so the direct dependencies' reference proofs compile | P2: context = direct deps for all 39 × 2 modes; 179 transitive-only lemma slots never appear in prompts |
| Direct vs transitive distinguished | **C9** (Amendment A3): the GDT lemmas in the candidate's proof term (kernel constants) ⊆ the condition's exposed lemmas | context N3 and assembly V5: transitive use rejected; all 39 reference proofs pass C9 |
| Reference-proof rules | reference proofs only in verification contexts and test fixtures; claim level `c2_success` requires model provenance and no reference-proof line | assembly A1/A3/A4; leak check P3 |
| No target-proof leakage | prompt leak check over all reference proof lines | 0 / 471 lines |
| Deterministic ordering | prompts: alphabetical direct deps (committed `prompts_v2`); assembly: topological over kernel deps, source-line tie-break | P4; assembly O1 |
| Missing / circular / inconsistent deps rejected | assembler: unknown dependency, cycle, unknown target → `error`; missing member → `incomplete` | G4; assembly M1–M3, E1 |
| Reproducible prompt artifacts | `prompts_v2.jsonl` regenerates to the committed sha256 | P4 |

**Discrepancy check.** The direct-dependency graph is identical in three independent
sources:

1. the Stage 0 Lean 4.34 kernel record (G1);
2. the manifest used by the assembler;
3. a fresh Lean 4.9 recomputation from the certified `SolutionRef` proof terms
   (`tools/UsedLemmas49.lean`, G3).

The graph is acyclic and every dependency precedes its user in source order (G2). **No
discrepancy** exists between the assembler and the kernel-derived graph.

The one test expectation that failed during development was mine: it expected source
order where the committed prompts use alphabetical order. It was corrected to assert the
committed convention, and the prompts were left unchanged.

## Assignment 2 — C2 verification

Each C2 verification context (39 items) was checked for:

- elaboration;
- statement preservation;
- axioms ⊆ {propext, Quot.sound, Classical.choice};
- C9;
- lean4checker replay.

All certify. Invalid candidates are rejected:

- citing a lemma outside the closure (C1/C5);
- citing a dependency without the context (C1/C5);
- using a transitive non-direct dependency (C9).

Successful elaboration is never counted as certification: `certified` requires C1–C9
including kernel replay, and `count_certified` rejects records that claim otherwise.

## Assignments 3–4 — GPU kit and safeguards (`formalize-now/gpu/`)

| Item | File | Tested on CPU |
|---|---|---|
| Pins (model revision and file hashes, vLLM 0.32.0, torch 2.13.0, driver ≥ 580, Lean/checker/REPL commits, inference settings, budget) | `pins.json` | used by every test below |
| Preparation, separated from execution | `setup_gpu.sh` (phases 0–5; budget gate between phases; stops at $1.50 of setup spend) | I12: syntax check, `DRY_RUN=1` run |
| Model verification | `verify_model.py` (sha256 for shards, git-blob sha1 for small files) | I1–I3: pinned tokenizer passes, corrupted copy fails, absent weights fail |
| Preflight | `preflight.py` (GPU, driver, vLLM/torch, CUDA, NVML, model hashes, binaries, 39/39 certification, lean4checker, budget) | I7: CPU mode writes the report, GPU checks `unavailable`, report fails |
| Launch approval gate | `smoke_run.py --live`: `RPI_SMOKE_APPROVED=1` + full preflight passed < 60 min, same HEAD and pins + budget | I8: 6 refusal cases |
| Time budget warning / stop | `budget.py` (`status`, `gate`, `guard` with SIGTERM/SIGKILL and a STOP file); re-checked between outputs | I4–I6 (guard stops a process with an accelerated clock); reports `provider_side_cap: false` |
| Incremental saving and recovery | completions, generation metadata and records fsync'd per output; `--resume` skips recorded samples | I9: crash after 1 of 4 outputs, then resume → 4 unique records, 4 completions |
| Measurements | tokens, finish reason, GPU time, NVML energy, peak GPU memory, mean power, verification time and RSS; nulls carry an `unavailable` reason | I10: every row valid, every null documented |
| Transfer off the instance | `collect_results.sh` (tarball + sha256 + inner MANIFEST) | I11: archive and inner manifest verify |
| Shutdown | `reports/GPU_EXECUTION_CHECKLIST_001e.md` §F | — |

## Preserved

These are unchanged since `e9a2080`:

- upstream files;
- the GDT reference proofs (`lean49/GDTBench/*`);
- manifests and items;
- `prompts_v1`, and `prompts_v2` with its manifest.

The pre-registration gains Amendments A2 and A3, both appended with no line removed and
recorded before any model output.

## Untestable without a GPU

The list is in `GPU_EXECUTION_CHECKLIST_001e.md`:

- driver and CUDA compatibility of vLLM 0.32.0 / torch 2.13.0;
- model loading at `max_model_len` 20480 on 48 GB;
- real completion formats;
- vLLM seeding;
- NVML readings;
- throughput, actual setup time and cost;
- the real `setup_gpu.sh` run, including the weight-shard hash checks.

## Recommended first live command

On the instance, after the setup and a passing preflight (checklist steps B–C):

```bash
export RPI_SMOKE_APPROVED=1 LAUNCH_TIME=<launch time UTC> MODEL_DIR=~/models/DeepSeek-Prover-V2-7B \
       LEAN4CHECKER=~/rpi-tools/lean4checker/.lake/build/bin/lean4checker RPI_REPL=~/rpi-tools/repl/.lake/build/bin/repl
~/rpi-venv/bin/python formalize-now/harness/smoke_run.py --live --mode cot --max-outputs 2 &
python3 formalize-now/gpu/budget.py guard --launch-time $LAUNCH_TIME --pid $! --interval 15 --out-dir ~/rpi_state
```

## GO / HOLD

**GO** for the bounded smoke test (≤ 2 C0 outputs, then optionally ≤ 2 C2 outputs) when an
A6000 is available. Two conditions apply on the instance:

- `preflight.py` prints `PASSED`;
- setup finishes within $1.50.

If either fails, **HOLD**: collect, terminate, and revise without substituting versions.

The 512-attempt pilot stays on **HOLD** until the smoke test has exercised the live path.
