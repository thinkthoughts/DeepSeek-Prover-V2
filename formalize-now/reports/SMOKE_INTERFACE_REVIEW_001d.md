# RPI-DS-001d — Model-output interface review and smoke-test implementation plan

**Result.** The output-to-certificate path is ready for a 2-output smoke test of
`gdt_periodic` (C0) and, optionally, 2 outputs of `gcd_with_N_iff_gcd_with_R` (C2).

The review found two interface defects, both fixed before any model output existed and
recorded as Amendment A1:

1. `prompts_v1` non-CoT prompts ran past the target's `:= by`.
2. The pre-registered full-code extraction would have rejected correct CoT proofs over
   byte-level drift in the echoed header.

It also found that C2 verification lacked its pre-registered trusted dependency context;
that context is now implemented and tested.

The pre-registered CoT budget (`max_new_tokens` 16384) needs a GPU with ≥ 40 GB, which
corrects the earlier 24 GB estimate. Recommendation: **go** for the smoke test, on
approval of a ≥ 40 GB GPU host. **Hold** the 512-attempt pilot until the theorem-level
C2 assembler exists.

Everything here ran on CPU. No weights were downloaded and no inference was run. Only
`config.json`, file metadata and `tokenizer.json` (sha256 `091b9dad…`) were fetched at
revision `a8d9e144`.

## 1. Output formats and the trust boundary

| Source | Finding |
|---|---|
| DeepSeek-Prover-V1.5 `prover/utils.py` | `non_cot_prompt` = "Complete the following Lean 4 code:\n\n```lean4\n" + header + statement, so the prompt ends inside an open block and the model writes the proof continuation |
| V1.5 `datasets/minif2f.jsonl` | all 488 `formal_statement` fields end in `:= by\n` |
| V2 README CoT prompt | closed block containing `:= by\n  sorry`, then the plan instruction; the model returns plan + a complete code block |
| DeepSeek's 438 released miniF2F proofs | 438/438 begin with the exact V1.5 header; 438/438 contain one declaration; 438/438 use `:= by`. These are prompt + completion as published, so they show the format of assembled files, not CoT echo fidelity |
| Our `prompts_v1` | CoT matches the README. Non-CoT continued with `  sorry` / `end GDT.Challenge` past the `:= by`: **defect** |
| Our §7 extraction rule (001c) | last block, full-code mode, byte-identical prefix check. A CoT output must reproduce the 40-line definitions block exactly, so any whitespace or `maxHeartbeats` drift becomes `prefix_mismatch` and a correct proof is lost: **defect** |

**Fix (Amendment A1).** `prompts_v2` ends every non-CoT prompt at the target's `:= by\n`;
CoT prompts are byte-identical to v1. `harness/extract.py` takes only the target's tactic
proof:

- **CoT:** the text after the top-level `:= by` of the unique `theorem|lemma <target>` in
  the last closed `lean`/`lean4` block, up to the first non-empty column-0 line.
- **non-CoT:** the continuation up to the closing fence.

The extracted proof goes through `verify_strict.assemble(..., "proof")`. Each body line is
indented under the *trusted* header, definitions and statement, and the trusted expected
statement is elaborated before it.

How each trust requirement is met:

| Requirement | How it holds |
|---|---|
| Trusted signature and definitions preserved | always taken from `gdt_items_v2.jsonl`; the model's echo is compared (`statement_echo_matches`, `header_echo_matches`) and never compiled |
| Only the candidate proof extracted | one declaration's tactic block; other declarations are listed in `extra_declarations` and dropped |
| Generated text never replaces the specification | structural: the model text enters only below `:= by`, indented. A command keyword inside it (`#exit`) ends the tactic block, and the trailing trusted check then fails C2 (test X10) |
| Incomplete or invalid output rejected | `no_code_block`, `truncated`, `target_missing`, `ambiguous_target`, `term_mode_proof`, `empty_proof`; then C1–C7 |
| REPL for preliminary screening | `repl_adapter.verify_repl` (≤ `preliminary`) |
| Direct verification and kernel replay before certification | `verify_repl(..., certify=True)`: direct path plus lean4checker; any disagreement between the two paths rejects |
| Whitelist and signature checks unchanged | `ALLOWED` and C4 unchanged; no special case for model output |

Known consequences, recorded and not hidden:

1. **Helper declarations.** A proof that needs a model-written helper lemma before the
   theorem fails (test X4). Helper support would be a separate amendment, and only if the
   smoke test shows such outputs. It would need its own tests.
2. **Term-mode proofs** (`:= term`) are rejected as `term_mode_proof` (test X9). They are
   absent from DeepSeek's released proofs.

**Tests** (`harness/tests/run_extract_tests.py`, 15/15, synthetic completions, no model):

| Case | Expected outcome |
|---|---|
| correct full-file echo | certified |
| `maxHeartbeats 400000` header drift | certified; this was the old rule's false rejection |
| weakened statement in the echo | rejected |
| helper lemma before the target | rejected |
| no code block | `no_code_block` |
| truncated open block | `truncated` |
| renamed target | `target_missing` |
| duplicate target | `ambiguous_target` |
| term-mode proof | `term_mode_proof` |
| `#exit` inside the proof | rejected |
| `sorry` body | rejected |
| non-CoT continuation, with and without trailing commentary | certified |
| non-CoT truncated | `truncated` |
| `gdt_periodic`'s reference proof under C0 | rejected: it needs lemmas the C0 context lacks, which shows the C0 boundary works |

## 2. C2 verification context (pre-registration §5, now implemented)

`verify_strict.verify(..., reference_deps=True)` inserts the certified reference
declarations of the item's full dependency closure, in source order, between the trusted
expected statement and the candidate. This happens only in verification, never in
prompts.

Test (`harness/tests/run_context_tests.py`): each of the 39 items with its own reference
proof body under the V1.5 header and its closure in context, plus two negatives. This
shows two things. The context mechanism works for every closure size, from 0 to 33
lemmas. And all 39 reference proofs elaborate under the prompt header (`import Mathlib`,
`open BigOperators Real Nat Topology Rat`). 

## 3. Smoke-test implementation (`harness/smoke_run.py`)

| Step | Implementation |
|---|---|
| Targets | C0 `gdt_periodic`, ≤ 2 outputs; optional C2 `gcd_with_N_iff_gcd_with_R` (5 lemmas in its closure), ≤ 2 outputs; hard cap enforced |
| Prompts | `benchmark/prompts_v2.jsonl` (CoT primary; non-CoT available) |
| Seeds | `int(sha256("rpi-ds-001d-smoke" + prompt_id + i)[:8], 16)`, disjoint from confirmatory seeds |
| Run manifest | host, platform, `nvidia-smi` (GPU, memory, driver), `pip freeze`, model and revision, dtype, sampling, prompt-file sha256, pre-registration sha256, amendments, git HEAD, Lean toolchain; `excluded_from_confirmatory: true` |
| Generation (live) | vLLM `LLM(model, revision, tokenizer_revision, dtype=bfloat16, max_model_len, gpu_memory_utilization=0.90)`, `SamplingParams(temperature=1.0, top_p=0.95, max_tokens, seed)`; NVML energy read around each call |
| Per output | raw completion saved → extract → REPL screen → certify (direct + lean4checker) → `instrument.Recorder` row |
| Guards | `--live` refuses without `RPI_SMOKE_APPROVED=1`, without a CUDA GPU of ≥ 40 GB, or with more than 2 outputs |
| Dry run (executed) | `--dry-run --with-c2` in both modes on CPU fixtures: extraction, screening, certification and recording all exercised; manifests carry `excluded_from_confirmatory` |

The live path's code is untested: no GPU was available or authorised.

Commands on an approved host, after `git clone` and the Lean 4.9 setup in the README:

```bash
python3 -m venv ~/smoke && . ~/smoke/bin/activate
pip install "vllm==<pinned>" pynvml            # record the exact version in the manifest
huggingface-cli download deepseek-ai/DeepSeek-Prover-V2-7B --revision a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b
export RPI_SMOKE_APPROVED=1 RPI_REPL=… LEAN4CHECKER=…
python3 formalize-now/harness/smoke_run.py --live --mode cot              # 2 × C0 gdt_periodic
python3 formalize-now/harness/smoke_run.py --live --mode cot --with-c2    # only if the C0 path behaved
```

## 4. Computational requirements

Model facts from `config.json` at the pinned revision:

- `LlamaForCausalLM`: 30 layers, 32 KV heads (no grouped-query attention), head dim 128,
  YaRN RoPE ×16, 65,536 max positions, bf16.
- Weights: 13.83 GB.

| Quantity | Value | Basis |
|---|---|---|
| KV cache | 0.469 MiB per token (2 × 30 × 32 × 128 × 2 B) | config |
| Longest prompt | 3,134 tokens (C0h, `general_divisor_theorem`); smoke C0 prompt 547 tokens | pinned tokenizer, `benchmark/prompts_v2.token_counts.json` |
| Longest sequence (CoT) | 3,134 + 16,384 = 19,518 tokens → 8.9 GiB KV; `max_model_len` 20,480 | pre-registration |
| 24 GB GPU (L4, A10G, RTX 4090) | about 5.5–7 GiB left for KV after 12.9 GiB of weights and runtime overhead at 0.90–0.95 utilisation, i.e. ≈ 12–15K tokens | too small for the pre-registered CoT budget; fits non-CoT (≤ 8.7K tokens) |
| 40 GB (A100-40GB) | ≈ 19 GiB KV ≈ 40K tokens: 2 full CoT sequences concurrently | minimum for the pre-registered settings |
| 48 GB (L40S, A6000) / 80 GB | ≈ 24 / 52 GiB KV | comfortable |
| Quantization | changes the weights, so it is a different model under pre-registration §3 | at most a labelled engineering run; never confirmatory |
| Disk | 13.8 GB weights + ~10–15 GB Python/CUDA wheels + ~6 GB Lean toolchain and Mathlib cache | ≥ 60 GB |
| System RAM | weight loading plus Lean (REPL ≈ 3.5 GB plus a direct check ≈ 3.9 GB at once) | ≥ 32 GB |
| vLLM / CUDA | any vLLM release supporting `LlamaForCausalLM` with YaRN, with the CUDA build its wheel requires and an NVIDIA driver that build supports | pin the exact version; record `pip freeze`, `torch.version.cuda` and the driver in the run manifest |

**Smoke-test time (estimate).** Single-stream bf16 decode of a 7B model on an A100 is
memory-bandwidth-bound, at roughly 50–90 tokens/s. A maximum-length 16K-token CoT output
takes about 3–6 minutes; the two outputs run concurrently.

| Phase | Estimate |
|---|---|
| Setup (wheels, 13.8 GB weights, Lean cache, REPL and lean4checker builds) | 20–40 min |
| Generation | ≤ 6 min for 2 × C0; ≤ 12 min with C2 |
| Verification | about 1 min |
| **Total** | **≤ 1 GPU-hour** |

**Cost.** One GPU-hour of a 40–80 GB instance at the provider's on-demand rate,
typically a few US dollars (unverified here; confirm before approval).

**Energy.**

- GPU: NVML `nvmlDeviceGetTotalEnergyConsumption` read around each generation call. This
  is whole-device energy, idle draw included.
- CPU: RAPL where exposed; cloud VMs and this host usually lack it, and it is recorded as
  unavailable.
- Environmental impact: stated only with facility PUE and grid carbon intensity, which
  this setup leaves unmeasured.

**Available environments.**

| Environment | Suitable? |
|---|---|
| This sandbox | no GPU |
| `srv838187` | 3.8 GiB RAM: far below requirements |
| An Apple-silicon MacBook with ≥ 32 GB unified memory | could run a transformers/MPS engineering check at no cost, but with a different runtime from the pre-registered vLLM/CUDA stack; label the results as such |

No paid infrastructure has been provisioned.

## 5. Open items and blockers

| Item | Blocks |
|---|---|
| Theorem-level C2 assembler (pre-registration §5: compose each lemma's first certified model proof into one file and certify it) | 512-attempt pilot and full run; the smoke test is unaffected |
| Live path untested | will be exercised by the smoke test |
| Helper-lemma outputs | rejected by design; revisit only via a new amendment if observed |
| vLLM sampling determinism across GPUs/versions | is out of our control; seeds and versions are recorded, and reproducibility is stated as "same stack" |
| Exact DeepSeek fork build (Batteries) | deferred (`ENVIRONMENT_COMPATIBILITY_001c.md`); build on the GPU host if time allows |
| REPL needs `stdbuf -oL` for long-lived use | handled in the adapter |

## 6. Go / no-go

- **Smoke test: GO**, on approval of a ≥ 40 GB GPU host for about one hour. The other
  conditions hold: the interface fixes are recorded before outputs, extraction and
  context tests pass, guards are in place, and smoke results stay outside confirmatory
  statistics.
- **512-attempt pilot: HOLD** until the C2 assembler is implemented and tested (next
  patch), and until the smoke test has exercised the live path.
- **Performance claims: none.** The smoke test is an engineering validation.

## 7. Test record

| Suite | Result | Log |
|---|---|---|
| Extraction + trusted assembly (synthetic) | 15/15 | `logs/extract_tests.log`, `harness/tests/extract_results.json` |
| C2 reference context (39 items + 2 negatives) | 41/41 (3 min 53 s) | `harness/tests/context_results.json` |
| Smoke dry runs (CoT, non-CoT; C0 + C2) | pipeline completed; all fixtures rejected as designed (`sorry`, no code block, compile error) | `runs/` (not committed; regenerate with `--dry-run`) |
