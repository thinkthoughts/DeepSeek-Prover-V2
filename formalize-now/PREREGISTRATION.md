# Pre-registration — GDT-Ladder Stage 1 (RPI-DS-001c)

Fixed on 2026-11-05, before any model output exists. Changes after the first generation
are amendments: they are dated, appended in §12, and reported alongside the results.
The machine-readable form is `preregistration.json`; its sha256 goes in the commit
message of the run that uses it.

## 1. Question

Does providing the established GDT lemma decomposition increase the number of
kernel-verified theorems solved by DeepSeek-Prover-V2-7B under a matched computational
budget?

**Primary unit:** the 7 challenge theorems. **Secondary unit:** the 32 helper lemmas.

## 2. Benchmark items

- `benchmark/gdt_items_v2.jsonl`: 39 items (7 challenge theorems, 32 helper lemmas).
- Statements are verbatim from `thinkthoughts/general-divisor-theorem@ec66260`, translated
  by the logged header rules (RPI-DS-001a).
- Each statement has a certified reference proof (RPI-DS-001b).
- Theorem closures (transitive GDT lemma dependencies): `gdt_empty` 0, `gdt_periodic` 7,
  `gdt_correction_factor` 8, `gdt_minimal_period` 21, `gdt_count_per_period` 22,
  `gdt_density` 25, `general_divisor_theorem` 33.
- Cauto (§4) certifies `coprime_add_mul_right` and `S_eq_filter_Ico`. Results are reported
  both with and without these two lemmas counted.

## 3. Model, prompts, sampling

| Item | Value |
|---|---|
| Model | `deepseek-ai/DeepSeek-Prover-V2-7B`, revision `a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b` (HF metadata, 2025-04-30); weights loaded at that revision only |
| Precision | bf16; a quantized model counts as a different model and is out of scope |
| Inference engine | vLLM; exact version, CUDA version and GPU model recorded in the run manifest |
| Prompts | `benchmark/prompts_v1.jsonl` (184 prompts, sha256 `de8143b2…`, full value in `prompts_v1.manifest.json`), built by `harness/prompts.py` from the V2 README template; superseded for non-CoT by `prompts_v2` (Amendment A1) |
| Primary mode | CoT (V2 README prompt) |
| Secondary mode | non-CoT (`Complete the following Lean 4 code:` + code) |
| Sampling | temperature 1.0, top_p 0.95, max_new_tokens 8192 (non-CoT) / 16384 (CoT) |
| Seeds | sample *i* of prompt *p* uses seed = first 8 hex digits of sha256(`"rpi-ds-001c" + p.id + str(i)`), interpreted as an integer; vLLM per-request seed |
| Sample order | samples are indexed `i = 0, 1, 2, …`; every budget-truncated metric uses the prefix `0..b−1` |

## 4. Conditions

| Id | What the model sees | Items | Attempts per item |
|---|---|---|---|
| C0 | header + definitions + statement | 7 challenge theorems | k_C0(T) = 32 · (1 + \|closure(T)\|) |
| C0h | C0 + the statements of every lemma in closure(T), as Lean comments (not declarations) | 7 challenge theorems | same as C0 |
| C1 | header + definitions + statement (each item alone; Figure 3(a)) | all 39 | 32 |
| C2 | header + definitions + the item's direct dependencies as declarations with `sorry` bodies + statement (Figure 3(b)) | all 39 | 32 |
| Cauto | ten tactic scripts, no model (`baseline/cauto.py`) | all 39 | 1 per script |

Information accounting:

- C0h and C2 receive the same lemma *statements* (C0h for the whole closure, C2 for direct
  dependencies at each step). C0h is the information control: it separates "knowing the
  lemma statements" from "proving along the decomposition".
- Prompt tokens are recorded per attempt and reported for every condition, so the extra
  context of C0h and C2 stays visible in every comparison.
- The C1 prompt for a challenge theorem equals its C0 prompt. At theorem level C1 is
  therefore C0, and C1 is reported only per lemma, to avoid counting one condition twice.

## 5. Theorem-level outcome under C2 (assembly)

A challenge theorem T is **C2-solved** at budget b when:

1. T and every lemma in closure(T) has at least one certified C2 proof among its first b
   samples;
2. the assembled file is certified by `harness/verify_strict.py` with kernel replay; that
   file contains the definitions and, in dependency order, every lemma in closure(T) and T,
   each with its first certified model proof replacing the `sorry` context;
3. the assembled file holds no reference-proof text.

**Per-item C2 verification.** Lemma i is first checked with its dependencies supplied by
the certified reference proofs. These are present in the verification context only and
never in the prompt. This gives a per-item status. The theorem-level claim rests solely on
the assembled, fully model-written file.

## 6. Budget matching

Cost attribution is conservative toward C2: every attempt on a lemma in closure(T) counts
toward T, also when the lemma is shared with other theorems.

- **Equal attempts:** C0 and C0h on T receive Σ over closure(T) ∪ {T} of the C2 attempts:
  32 · (1 + \|closure(T)\|).
- **Equal generated tokens:** C0 and C0h on T are truncated at the smallest prefix whose
  cumulative generated tokens reach C2's total generated tokens over closure(T) ∪ {T}.
  The C0 sampling cap is 2 · k_C0(T); a theorem whose match needs more than the cap is
  reported as `budget_cap_reached`.
- **Equal total tokens** (prompt + generated) is reported as a secondary comparison.
- **Lean verification time** (CPU-seconds) is reported per condition, separately from
  generation.

## 7. Invalid or unsuccessful generations

Every generation is an attempt: it is counted, its tokens are recorded, and it goes
through the strict verifier. This includes outputs that are empty, missing a code block,
truncated at `max_new_tokens`, ill-formed, or that change the statement. Extraction takes
the last `lean4` code block and uses full-code mode, whose prefix check requires the
trusted header and definitions byte for byte.

Each failure is recorded as one category: `no_code_block`, `truncated`, `prefix_mismatch`,
or the verifier's failed checks (C1–C8). Only `certified` results count; `preliminary`
results never do (`count_certified` enforces this).

## 8. Verification

`harness/verify_strict.py`: C1–C8, with C8 (lean4checker replay) mandatory for
`certified`. Screening may use `harness/repl_adapter.py`, which yields at most
`preliminary`; every success is then re-verified through the direct path with C8.

Environment: Lean 4.9.0-rc1, Mathlib `d1d1e4b7`, lean4checker `9da7f4a3`, REPL
`xinhjBrant/repl@3334a97`.

## 9. Metrics (per theorem; no aggregate threshold)

- C0 / C0h / C2: solved or unsolved at the equal-attempt budget and at the equal-token
  budget, plus the smallest solving budget b\*.
- Per lemma (C1, C2): unbiased pass@k for k ∈ {1, 4, 16, 32}; first-success index.
- Cost per certified theorem and per attempt: generated tokens, prompt tokens, attempts,
  GPU-seconds, Lean verification CPU-seconds, peak memory, and device energy where a
  hardware counter exists (`harness/instrument.py`). Missing counters are recorded as
  missing.
- **Robustness:** each theorem-level comparison is recomputed over 200 random reorderings
  of the sample sequence (seed `rpi-ds-001c-bootstrap`), and the fraction of reorderings
  in which it holds is reported.

## 10. Interpretation (stated before results)

- **Positive.** For at least one theorem, C2 certifies it and C0 does not, under both
  equal-attempt and equal-token matching, and C0h also does not. No theorem shows the
  reverse. Positive findings are reported per theorem, with the reordering fraction.
- **Negative.** Every theorem C2 certifies is also certified by C0 or C0h at matched
  budget, and at least one theorem is certified by C0 or C0h and not by C2.
- **Inconclusive.** Any other pattern, including:
  - identical solved sets;
  - outcomes that differ between equal-attempt and equal-token matching;
  - an effect that disappears when the two Cauto-solvable lemmas are excluded;
  - `budget_cap_reached` for the deciding theorem.

  Per-lemma C1 versus C2 rates are reported in every case. They are descriptive, not
  decisive.
- A C0h advantage over C0 is reported as an effect of lemma-statement *information*. It is
  not credited to decomposition.
- Lower token or time cost is reported as cost. An environmental-impact statement needs
  PUE and grid carbon data, which this design leaves out.

## 11. Exclusion of reference proofs

- Prompts are built only from item headers, definitions and statement texts.
- `harness/prompts.py` checks every prompt line against the 471 proof-body lines of
  `SolutionRef.lean` (lines of public statement text excluded) and refuses to write
  prompts if any match. The current result is 0 matches.
- Reference proofs appear only in per-item verification contexts (§5), never in prompts,
  and never in an assembled theorem-level artifact.

## 12. Amendments

### A1 — 2026-11-05, recorded before any model output (RPI-DS-001d interface review)

Found by inspecting the prompt and verifier interfaces against DeepSeek-Prover-V1.5's
`prover/utils.py` and datasets; no generation had been run.

1. **Non-CoT prompt format.** V1.5's non-CoT prompt ends inside an open code block,
   right after the statement's `:= by\n`: all 488 miniF2F `formal_statement` fields end
   that way. `prompts_v1` non-CoT prompts continued with `  sorry` and
   `end GDT.Challenge`. `benchmark/prompts_v2.jsonl` (sha256 `b7d12b04…`, full value in
   `prompts_v2.manifest.json`) ends every non-CoT prompt at the target's `:= by\n`. All
   92 CoT prompts are byte-identical to v1, and the 0-leak check is unchanged.
   `prompts_v1` stays in the repository, reproducible byte for byte.
2. **Extraction (replaces §7's "last `lean4` block, full-code mode" rule).**
   `harness/extract.py` takes only the target theorem's tactic proof from the completion.
   - CoT: the proof after the unique `theorem|lemma <target>`'s top-level `:= by` in the
     last closed `lean`/`lean4` block.
   - non-CoT: the continuation up to the closing fence.

   `verify_strict.assemble(..., "proof")` then places that proof under the trusted
   header, definitions and statement. Generated headers, definitions, statements and
   helper declarations are never compiled. They are recorded as diagnostics
   (`header_echo_matches`, `statement_echo_matches`, `extra_declarations`).

   Categories: `no_code_block`, `truncated`, `target_missing`, `ambiguous_target`,
   `term_mode_proof`, `empty_proof`, `extracted`; `prefix_mismatch` is retired.

   Reason: under the old rule a correct CoT proof was rejected whenever the model's echo
   of the 40-line definitions block drifted by one byte (whitespace, a changed
   `maxHeartbeats`). That counts output formatting as proof failure. The trust property
   the prefix check protected is now enforced structurally, because the specification
   text always comes from the item.
3. **Unchanged:** verification C1–C8 (kernel replay mandatory), axiom whitelist,
   statement alpha-equivalence, model revision, sampling parameters, seeds, conditions,
   budgets, metrics and interpretation rules.
4. **Smoke test exclusion.** RPI-DS-001d smoke samples are engineering runs. They are
   excluded from every confirmatory count, budget and statistic. Their seeds use the
   prefix `"rpi-ds-001d-smoke"` in place of `"rpi-ds-001c"`, so no smoke seed coincides
   with a confirmatory seed.
5. **Hardware consequence (no design change):** `max_new_tokens` 16384 (CoT) plus the
   prompt needs a GPU with ≥ 40 GB. See `reports/SMOKE_INTERFACE_REVIEW_001d.md`.

Tests: `harness/tests/run_extract_tests.py`, 15/15 synthetic completions
(`harness/tests/extract_results.json`).
