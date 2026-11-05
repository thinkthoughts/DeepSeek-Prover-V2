# Build and verification record — RPI-DS-001a

Machine: 2 vCPU, 7 GiB RAM, no swap, Linux x86_64, elan 4.2.4. Date: 2026-11-05.
Absolute paths inside the logs refer to that working machine.

## Checked

| # | Check | Command (abridged) | Result | Log |
|---|---|---|---|---|
| 1 | Mathlib cache, GDT pin | `lake exe cache get` (GDT repo) | 8,747 files, 111 s | `logs/gdt_cache_get.log` |
| 2 | Original GDT build, unchanged source | `lake build && lake build Challenge && lake build Solution` | exit 0, 1319 jobs, 0 errors; 7 `sorry` warnings, all in Challenge (expected); Solution warnings are style linters only (empty lines, `show` → `change`) | `logs/gdt_lean434_build.log` |
| 3 | GDT working tree after all steps | `git status --short` | clean | — |
| 4 | Kernel inventory, Solution | `tools/run_extract.sh … Solution` (cmp-guarded copy) | 48 declarations, values present for all | `logs/deps_solution.json` |
| 5 | Kernel inventory, Challenge | `tools/run_extract.sh … Challenge` | 16 declarations; 7 theorems with `sorryAx` (expected) | `logs/deps_challenge.json` |
| 6 | Challenge/Solution statement agreement | type-hash and pp comparison | 7/7 theorems and 9/9 definitions agree | `manifest/gdt_manifest.json` |
| 7 | Lean 4.9 cache, DeepSeek fork `2f65ba7f` | `lake exe cache get` | 0 files in the first ~1,900 requests; stopped | `logs/lean49_fork_cache_get_aborted.log` |
| 8 | Lean 4.9 cache, upstream `d1d1e4b7` | `lake exe cache get` | 4,650 files, 61 s | `logs/lean49_upstream_cache_get.log` |
| 9 | Fork vs upstream Mathlib sources | `git diff d1d1e4b7 2f65ba7f -- Mathlib Mathlib.lean` | empty | — |
| 10 | Translated Defs, Challenge, Ladder | `tools/lean49_check.sh` | 0 errors; 7 + 32 `sorry` (expected) | `logs/lean49_{Defs,Challenge,Ladder}.log` |
| 11 | Standalone Lean 4.9 project | `lake update; lake exe cache get; lake build` | exit 0, 0 errors, 39 `sorry` (expected) | `logs/lean49_lake_build*.log` |
| 12 | Items under V1.5 header + `import Mathlib` | `tools/lean49_check.sh … AllItemsCheck.lean` | 0 errors, 39 `sorry`, peak RSS 3.55 GB | `logs/lean49_items_full_mathlib.log` |
| 13 | Unchanged proofs under Lean 4.9 | `tools/lean49_check.sh … SolutionPort.lean` | 14 errors in 9 declarations | `logs/lean49_SolutionPort.log` |
| 14 | Axioms under Lean 4.9 | `tools/axiom_probe49.sh` | 19 kernel-clean, 20 with `sorryAx` | `logs/lean49_axiom_probe.log` |
| 15 | Statement surface 4.34 vs 4.9 vs header | `StatementSurface.append.lean` in each | non-instance constants equal 48/48; header changes notation only | `logs/surface_*.json` |
| 16 | Upstream files unchanged | `git diff --stat main -- ':!formalize-now'` | empty | — |

## Pending (outside this patch)

- **GDT Comparator** (`verify.sh`): its `landrun` sandbox and `lean4export` binaries were
  unavailable on this machine, so it stayed unrun. Check 6 is a partial substitute
  (type agreement and axioms). Comparator additionally compares definitions through
  export and runs sandboxed. You run it on the VPS as usual.
- **lean4checker** on any Lean 4.9 artifact: no Stage 0 file claims a 4.9 proof, so it was
  unnecessary here. It becomes required in Stage 1 assembly.
- **Exact DeepSeek environment** (fork `2f65ba7f` with Batteries `42b5ddd` and REPL):
  building it needs a Mathlib build from source, estimated at several CPU-hours on 2 cores.
  Deferred; the one-commit Batteries difference is documented in the compatibility report.

## Statement-surface procedure (check 15)

1. Lean 4.34: `cat Solution/GeneralDivisorTheorem.lean tools/StatementSurface.append.lean
   > GDT/.lake/rpi_surface.lean`; `lake env lean` it; then delete the file.
2. Lean 4.9: `cat lean49/GDTBench/SolutionPort.lean tools/StatementSurface.append.lean`;
   elaborate with `tools/lean49_check.sh`; delete the file.
3. Items: `cat benchmark/AllItemsCheck.lean tools/StatementSurface.append.lean`; elaborate
   likewise.
4. `tools/make_reports.py` compares the three JSON outputs.

Statements elaborate independently of their proofs, so failing proofs in step 2 leave
the statement data intact.
