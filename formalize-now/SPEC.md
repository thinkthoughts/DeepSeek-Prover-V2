# SPEC — RPI-DS-001a (GDT-Ladder Stage 0) and the benchmark it prepares

## 1. Benchmark objective

Measure whether a specification-derived decomposition improves verified theorem proving
by DeepSeek-Prover-V2-7B on number theory built from definitions absent from its
training data.

- **Unit of success:** a GDT theorem whose statement is unchanged, whose proof is
  accepted by the Lean kernel in the benchmark environment, and whose axioms are a subset
  of {`propext`, `Quot.sound`, `Classical.choice`}.
- **Items:** 7 challenge theorems and 32 helper lemmas (`benchmark/gdt_items.jsonl`).
- **Conditions (Stage 1, defined here and run later):** C0 direct; C0h direct with lemma
  statements as comments; C1 ladder form (a); C2 ladder form (b), earlier lemmas as
  premises; Cauto tactics only, without a model.
- **Stage 0 objective (this patch):** a verified inventory, a dependency manifest that
  separates kernel facts from text matches, and a Lean 4.9 compatibility assessment.

## 2. Preservation conditions

P1. **Original source untouched.** GDT files are read and copied; they are never edited.
    Recorded sha256 (commit `ec66260`):
    - `GeneralDivisorTheorem/Basic.lean` and `Challenge/GeneralDivisorTheorem.lean`: see `manifest/gdt_manifest.json → file_sha256`
    - `Solution/GeneralDivisorTheorem.lean`: `419c1670799f6cdbddcffa5fb532b5b8c0608d1aadfc0ce2a3fb50f1ea0dba8f`

P2. **Statements verbatim.** A translated statement or definition differs from its source
    only by the rules in `manifest/translation_log.json`:
    - T1: delete `module`
    - T2: `public import` → `import`
    - T3: delete `@[expose] public section`
    - T4: rename the local import path
    - L1: replace a ladder proof with `sorry`

    These rules touch only headers and imports. A new rule is a change to this SPEC.

P3. **Signatures fixed.** A translated statement that fails to elaborate is reported as
    incompatible; its signature is kept as it is.

P4. **Separate attribution.** Original declarations live in the GDT repository.
    Translated declarations live under `formalize-now/lean49/` with source path and sha256
    headers. Benchmark items live in `formalize-now/benchmark/`.

P5. **Proof claims.** A declaration is "proved" only if it compiles without error and
    `#print axioms` shows no `sorryAx` and no axiom beyond the whitelist. `SolutionPort.lean`
    is a compatibility probe. Its kernel-clean results are reported as such and are
    never presented as benchmark solutions.

P6. **Equivalence claims.** Elaboration success, equal pretty-printing and equal constant
    names are evidence of preserved meaning. Kernel equality of Lean 4.34 and Lean 4.9
    terms is unavailable across versions. Any claim beyond name-level agreement needs a
    separate argument (see the compatibility report, §4).

P7. **Dependencies.** "Kernel dependency" means a GDT constant occurring in the
    elaborated type or proof term, with compiler-generated auxiliaries expanded.
    "Syntactic reference" means a name match in comment-stripped source. The manifest
    stores both and their differences, so neither is passed off as the other.

## 3. Environments

| Name | Lean | Mathlib | Role |
|---|---|---|---|
| Original | 4.34.0-rc2 | `85e3a25` (tag v4.34.0-rc2) | Ground truth, kernel inventory |
| Benchmark | 4.9.0-rc1 | upstream `d1d1e4b7` (sources = DeepSeek fork `2f65ba7f`) | Model-matched elaboration |

Batteries differs between the benchmark build (`f96a344`) and the DeepSeek fork
(`42b5ddd`); see the compatibility report.

## 4. Out of scope for Stage 0

Model downloads, inference, sampling, GPU use, retraining, upstream edits, pull requests,
pushing the branch.
