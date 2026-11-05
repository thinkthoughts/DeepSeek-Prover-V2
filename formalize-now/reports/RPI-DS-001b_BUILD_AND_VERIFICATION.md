# Build and verification report — RPI-DS-001b

**Result.** All 39 GDT theorems (7 challenge theorems, 32 helper lemmas) are certified in
Lean 4.9.0-rc1 with Mathlib `d1d1e4b7`. This took 9 proof-body edits; every statement and
definition is unchanged, and every theorem uses only `propext`, `Quot.sound` and
`Classical.choice`. The strict verification wrapper passes all 13 of its tests.

## 1. Environment

| Item | Value |
|---|---|
| Machine | 2 vCPU, 7 GiB RAM, no swap, Linux x86_64 |
| Lean | 4.9.0-rc1 (`be6c4894e0a6`) |
| Mathlib | `leanprover-community/mathlib4@d1d1e4b72c6e009edd97cabe1d661b021fe8eeae`, whose `Mathlib/` sources are identical to DeepSeek's fork `xinhjBrant/mathlib4@2f65ba7f` |
| lean4checker | `leanprover/lean4checker@9da7f4a3` (tag v4.9.0-rc1) |
| GDT source | `thinkthoughts/general-divisor-theorem@ec66260c` (untouched; `git status` clean) |
| Branch base | `31d818a2` (RPI-DS-001a) |

## 2. Proof port (`lean49/GDTBench/SolutionRef.lean`)

Edits were applied with `tools/port_edit.py`, which refuses any fragment that occurs
outside the named declaration's proof body (after its top-level `:=`). All edits are
recorded in `manifest/proof_port_log.json`: original, revised, error, reason and
verification.

| Edit | Declaration | Port line | Error class | Change |
|---|---|---|---|---|
| E01 | `prod_primes_squarefree` | 103 | `Finset.induction` case arity | `\| insert a s ha ih =>` → `\| @insert a s ha ih =>` |
| E02 | `gdt_empty` | 45 | renamed lemma | `Finset.eq_empty_iff_forall_notMem.mpr` → `Finset.eq_empty_iff_forall_not_mem.mpr` |
| E03 | `exists_repr_mod_R` | 459 | `exact_mod_cast` (missing `norm_cast` attribute) | `exact_mod_cast hnm` → `exact Int.natCast_modEq_iff.mpr hnm` |
| E04 | `repr_unique` | 478 | `exact_mod_cast` (missing `norm_cast` attribute) | `exact_mod_cast h` → `exact Int.natCast_modEq_iff.mp h` |
| E05 | `exists_accepted` | 517 | `exact_mod_cast` (missing `norm_cast` attribute) | `exact_mod_cast hk1` → `exact Int.natCast_modEq_iff.mpr hk1` |
| E06 | `exists_coprime_R_neg_t_mod_p` | 664 | `exact_mod_cast` (missing `norm_cast` attribute) | `by exact_mod_cast hr_modeq_rp` → `by exact Int.natCast_modEq_iff.mpr hr_modeq_rp` |
| E07 | `gdt_minimal_period` | 734 | `exact_mod_cast` (missing `norm_cast` attribute) | `exact_mod_cast hn1_modp_nat` → `exact Int.natCast_modEq_iff.mpr hn1_modp_nat` |
| E08 | `S_eq_filter_Ico` | 845 | simp residue | `simp only [Finset.mem_filter, Finset.mem_Icc, Finset.mem_Ico] ⏎   simp` → `simp only [Finset.mem_filter, Finset.mem_Icc, Finset.mem_Ico] ⏎   simp ⏎   intro _ _ ⏎   omega` |
| E09 | `gdt_density` | 864 | `omega` with cast-product atom | `(by omega) (by omega)]` → `(Nat.le_add_left 1 _) (Nat.add_le_add_right (Nat.le_add_right _ _) 1)]` |

All 9 root failures from Stage 0 are repaired. The 11 declarations that inherited
`sorryAx` are now clean with no edits of their own, because their failures came only
from the roots. Each edit changes how a step is justified in Lean 4.9; none changes
what is proved.

| Step | Lean result |
|---|---|
| After E01–E02 | 7 errors left (5 `mod_cast`, simp residue, `omega`) |
| After E03–E07 | 2 errors left |
| After E08–E09 | 0 errors, 0 `sorry` |

## 3. Certification

| # | Check | Command | Result | Log |
|---|---|---|---|---|
| 1 | Clean build | `cd lean49 && rm -rf .lake/build && ../tools/peak_rss.sh … lake build` | exit 0, 0 errors; `sorry` only in Challenge (7), Ladder (32), Expected (39), all by design; wall 5.9 s, peak tree RSS 2.80 GB | `logs/lean49_lake_build_001b.log` |
| 2 | Signatures, statement equality, axioms | `lake env lean ../tools/SigCheck.lean` → `python3 tools/certify49.py logs/lean49_sigcheck.log` | 39/39 certified; 0 unexpected extra theorems; wall 8.8 s, 1.57 GB | `logs/lean49_sigcheck.log`, `manifest/certification_lean49.json` |
| 2a | Expected statement | `Expr.eqv` against `GDTBench.Expected` (Challenge + Ladder statements, namespace renamed), loaded in the same environment | 39/39 alpha-equivalent | same |
| 2b | Strict `Expr.equal` | same | 29/39 equal; the other 10 differ only in binder names: 6 hygienic notation binders (`a._@.<module>._hyg.n`), 4 underscore hypothesis names (`_hN` vs `hN`) that the original GDT Solution already uses relative to its Challenge | same |
| 2c | Signature text | byte comparison of every declaration's text up to `:=`, SolutionPort vs SolutionRef | identical for all 39 theorems; `Defs.lean` (the 9 definitions) unchanged since `31d818a` (`git diff` empty) | same |
| 2d | Axioms | Lean 4.9 `CollectAxioms` (the `#print axioms` collector) | 38 × {propext, Quot.sound, Classical.choice}, 1 × {propext} (`gcd_mod_eq`, which uses {propext, Quot.sound} in Lean 4.34); 0 `sorryAx`; 0 other | same |
| 2e | Placeholder scan (additional signal) | `certify49.py` | 0 occurrences of sorry, admit, apply?, exact?, native_decide, implemented_by, extern, axiom, unsafe, opaque, debug.skipKernelTC | same |
| 3 | Kernel replay | `lake env lean4checker GDTBench.SolutionRef` | exit 0, 1.6 s | `logs/lean4checker_GDTBench.SolutionRef.log` |
| 4 | Kernel replay, fresh environment (all imported Mathlib constants plus SolutionRef) | `lake env lean4checker --fresh GDTBench.SolutionRef` | exit 0, 5 min 26 s | `logs/lean4checker_fresh_GDTBench.SolutionRef.log` |
| 5 | Definitions module replay | `lake env lean4checker GDTBench.Defs` | exit 0 | `logs/lean4checker_GDTBench.Defs.log` |
| 6 | Wrapper tests | `python3 harness/tests/run_tests.py --lean4checker` | 13/13 as expected | `harness/tests/results.json` |

The 39 certified declarations carry the original GDT proofs with 9 local repairs. They are
reference proofs and stay out of every model prompt.

## 4. Verification wrapper (`harness/verify_strict.py`)

The upstream verifier (`DeepSeek-Prover-V1.5/prover/lean/verifier.py`, unchanged) accepts
when the REPL reports no error, no `sorries`, and no warning containing
`declaration uses 'sorry'` or `failed`. The wrapper requires eight checks, C1–C8:

| Check | Requirement |
|---|---|
| C1 | Compile without error |
| C2 | The trusted trailing check actually ran |
| C3 | The expected constant exists and is a theorem |
| C4 | Its type is alpha-equivalent to the trusted statement, which is elaborated before any candidate text |
| C5 | Its axioms stay within the whitelist |
| C6 | The file declares no axioms of its own |
| C7 | No weakening options |
| C8 | lean4checker replay passes |

A token scan is recorded as an extra signal and plays no part in the decision. In
`full-code` mode the candidate must begin with the item's header and definitions
byte for byte.

| Case | Expected | Strict wrapper | Failed checks | V1.5 `complete` rule on same compile |
|---|---|---|---|---|
| V1_valid_proof_gdt_empty | accept | accept | — | accept |
| V2_valid_proof_coprime_add_mul_right | accept | accept | — | accept |
| V3_valid_full_code_gdt_empty | accept | accept | — | accept |
| I1_sorry | reject | reject | C5_axioms | reject |
| I2_admit | reject | reject | C5_axioms | reject |
| I3_compile_error | reject | reject | C1_compile, C5_axioms | reject |
| I4_weakened_statement_full_code | reject | reject | C4_statement | accept |
| I5_local_axiom_full_code | reject | reject | C5_axioms, C6_no_local_axioms | accept |
| I6_exit_after_partial_proof | reject | reject | C1_compile, C2_check_ran, C3_present_theorem, C4_statement, C5_axioms, C6_no_local_axioms | reject |
| I7_native_decide_dependency | reject | reject | C5_axioms, C8_lean4checker | accept |
| I8_renamed_theorem_full_code | reject | reject | C3_present_theorem, C4_statement, C5_axioms | accept |
| I9_prefix_tampering_full_code | reject | reject | full-code candidate does not start with the trusted header and definitions | n/a (rejected before compile) |
| I10_skipKernelTC_option | reject | reject | C7_options, C1_compile | reject |

On the same compiles, the V1.5 decision rule would accept 4 of the 10 invalid cases:

- I4: weakened statement;
- I5: injected axiom;
- I7: `native_decide` dependency;
- I8: renamed theorem.

The strict wrapper rejects all four, through C4, C5/C6, C5/C8 and C3/C4 respectively.
The V1.5 column applies the rule from `verifier.py:53` to the `lean` command-line
messages; it is a stand-in for the REPL's own message stream.

Implementation note: Lean 4.9's code generator registers specialisations such as
`Finset.filter._at.GDT.S._spec_2` as axiom-kind declarations in the current file. C6
excludes names of that exact shape and records them. Soundness rests on C5, which rejects
any reachable non-whitelisted axiom whatever its name.

## 5. Remaining compatibility issues

1. The exact DeepSeek environment (fork `2f65ba7f` with Batteries `42b5ddd` and the
   `xinhjBrant/repl` REPL) is still unbuilt. The wrapper calls `lean` directly; a REPL
   adapter remains for Stage 1 (RPI-DS-001c).
2. Cross-version definitional correspondence is established at the printed and lemma
   level (`reports/LEAN49_DEFINITIONS.md`).
3. `import Mathlib` checks peak at about 3.5 GB per process. With 7 GiB, at most one
   wrapper run at a time fits.
