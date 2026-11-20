# Maintenance Guide: square-root

## Overview
- Exercise: `exercises/practice/square-root`
- Reference implementation: `exercises/practice/square-root/.meta/proof.ci.ts`
- Test suite: `exercises/practice/square-root/square-root.test.ts`
- Canonical case configuration: `exercises/practice/square-root/.meta/tests.toml`

The `square-root` exercise requires calculating the integer square root of a natural radicand without using built-in math square-root functions (`Math.sqrt`).

## Canonical Cases Mapping Table

All 6 canonical cases from problem-specifications are included (`include = true` implied, 0 exclusions).

| UUID | Test Name | Input (`radicand`) | Expected Output | Status | Rationale / TypeScript Operation |
|---|---|---|---|---|---|
| `9b748478-7b0a-490c-b87a-609dacf631fd` | `root of 1` | `1` | `1` | Included | Base case; identity check `radicand === 1` guards against zero division when computing initial guess `Math.floor(radicand / 2)` where `Math.floor(1 / 2) === 0`. |
| `7d3aa9ba-9ac6-4e93-a18b-2e8b477139bb` | `root of 4` | `4` | `2` | Included | Smallest non-trivial even square; initial estimate `Math.floor(4 / 2) = 2` yields exact integer root immediately without successive approximation error. |
| `6624aabf-3659-4ae0-a1c8-25ae7f33c6ef` | `root of 25` | `25` | `5` | Included | Non-even odd square root; tests iterative convergence of Newton's method `Math.floor((guess + radicand / guess) / 2)` in double-precision floating-point arithmetic. |
| `93beac69-265e-4429-abb1-94506b431f81` | `root of 81` | `81` | `9` | Included | Two-digit square test case verifying stability of integer convergence. |
| `fbddfeda-8c4f-4bc4-87ca-6991af35360e` | `root of 196` | `196` | `14` | Included | Three-digit radicand; confirms 10 iteration loop bound in `proof.ci.ts` is sufficient. |
| `c03d0532-8368-4734-a8e0-f96a9eb7fc1d` | `root of 65025` | `65025` | `255` | Included | 16-bit boundary value ($255^2$); confirms convergence without integer overflow. |

## Verification & Test Execution

Run the exercise test suite against the reference implementation:
```bash
corepack yarn node scripts/pr.mjs exercises/practice/square-root
```
Or run the dedicated automated check:
```bash
python3 work/R47-T001/check.py
```
