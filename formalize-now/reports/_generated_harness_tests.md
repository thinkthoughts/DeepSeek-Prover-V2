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
