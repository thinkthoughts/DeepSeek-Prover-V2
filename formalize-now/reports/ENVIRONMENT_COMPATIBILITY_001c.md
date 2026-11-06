# Environment compatibility — RPI-DS-001c

**Result.** The verified Lean 4.9 environment is sufficient for Stage 1. It uses DeepSeek's
exact Lean toolchain and REPL, plus Mathlib sources byte-identical to DeepSeek's fork. One
Batteries commit differs, and it touches a linter file that none of the 8,170 constants
behind the 39 certified proofs comes from. The exact fork build (Mathlib from source) stays
deferred on cost grounds.

## 1. Component comparison

| Component | DeepSeek (as released) | GDT-Ladder environment | Status |
|---|---|---|---|
| Lean | `leanprover/lean4:v4.9.0-rc1` (fork `lean-toolchain`, REPL `lean-toolchain`) | v4.9.0-rc1 | identical |
| Stated versions | V1.5 paper: "Lean 4.9.0"; V2 paper §3: "Lean 4.9.0-rc2, using the same testing environment as DeepSeek-Prover-V1.5" | — | three descriptions; the pinned files say rc1 |
| Mathlib | `xinhjBrant/mathlib4@2f65ba7f` ("align", 2024-08-07) | `leanprover-community/mathlib4@d1d1e4b7` (2024-06-12, the fork's parent) | `Mathlib/` and `Mathlib.lean` identical (`git diff` empty) |
| Fork-only lakefile changes | adds REPL; `pp.proofs.withType false`; CI-only `warningAsError`; `MathlibExtras` lib; `supportInterpreter` for `cache` | absent | none of these alters declarations: a pretty-printer option, build options and an extra library |
| Batteries | `42b5ddd` | `f96a344` | one commit: `Batteries/Tactic/Lint/Frontend.lean` (+4/−2, linter message fix #838) |
| Cli | `2cf1030` | `a1156602` | build tooling, unused by proofs |
| REPL | `xinhjBrant/repl@3334a97` (branch `deepseek`) | the same commit, built in 12 s | identical |
| Verifier | `DeepSeek-Prover-V1.5/prover/lean/verifier.py`, `complete` at line 53 | unchanged; strict wrapper and REPL adapter added alongside | see §3 |

## 2. Why the Batteries difference leaves the certified results unaffected

`tools/EnvClosure.lean` computes the transitive closure (types and values) of all 39
certified theorems in `GDTBench.SolutionRef`: 8,170 constants from 273 modules
(`logs/env_closure.log`).

- No constant in the closure comes from `Batteries.Tactic.Lint.Frontend`.
- The 9 Batteries modules in the closure (`Data.List.*`, `Data.Nat.*`, `Logic`) are
  byte-identical between the two Batteries commits, because the commits differ in one
  file only.

The kernel-checked content of the reference proofs is therefore the same in both
environments. A candidate proof could in principle use a Batteries linter declaration; the
strict verifier would then still check it in this environment, and the difference would
show up only as a name the DeepSeek environment also provides.

## 3. REPL pathway

- DeepSeek's V1.5 verifier starts `lake exe repl` once per check, with the command on
  stdin. The GDT adapter keeps one REPL per worker: it sends `import Mathlib` / `import
  Aesop` once, and each candidate as a command on that snapshot (env 0).
- Measured: import 2.2 s once, then about 0.3 s per candidate, against about 2.5 s per
  candidate on the direct `lean` path.
- Interactive use needs `stdbuf -oL`. The REPL prints through C stdio, which
  block-buffers when piped, and without line buffering a long-lived process stalls.
  DeepSeek's one-shot invocation reads from a file and never meets this.
- The fork's REPL returns an extra `ast` field (used by V1.5's `ast_parser.py`). The
  adapter leaves it unread.

## 4. Exact environment build: deferred

Building the fork exactly means compiling Mathlib from source against Batteries
`42b5ddd`. The changed Batteries file sits under Mathlib's tactic layer, so nearly all of
Mathlib's 4,650 modules would rebuild. That is on the order of ten or more CPU-hours on
this 2-vCPU machine, against a 60–90 minute session. §2 shows the difference cannot reach
the certified proofs. The build stays a one-time task for a larger CPU host (≥ 16 cores) or
for the GPU host before Stage 1, followed by `tools/validate_001c.sh` there.

## 5. Open differences

1. The rc1/rc2/4.9.0 wording in the papers: unresolvable from public artifacts. Ask
   upstream if it matters.
2. Batteries `42b5ddd` vs `f96a344`: kernel-irrelevant for the reference proofs (§2).
   Re-check model candidates in the exact build if one is made.
3. The V1.5 `verifier.py` path itself (`lake exe repl` inside the fork workspace) was left
   unrun. The adapter reproduces its message stream with the same REPL binary in an
   equivalent workspace.
