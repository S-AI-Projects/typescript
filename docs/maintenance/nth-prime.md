# Maintenance: nth-prime

This document summarizes the canonical test case decisions for the `nth-prime` exercise in the TypeScript track.

## Canonical Test Cases

All 5 canonical test cases from `problem-specifications` are supported by the TypeScript reference implementation (`.meta/proof.ci.ts`) and are included in `.meta/tests.toml`.

| Test | Canonical UUID | Input | Expected behavior | Reference Implementation Support |
|---|---|---|---|---|
| First prime | `75c65189-8aef-471a-81de-0a90c728160c` | 1 | Returns 2 | Generates primes and accesses index `[1 - 1]` (`[0]`), returning `2`. |
| Second prime | `2c38804c-295f-4701-b728-56dea34fd1a0` | 2 | Returns 3 | Generates primes and accesses index `[2 - 1]` (`[1]`), returning `3`. |
| Sixth prime | `56692534-781e-4e8c-b1f9-3e82c1640259` | 6 | Returns 13 | Generates primes and accesses index `[6 - 1]` (`[5]`), returning `13`. |
| Big prime | `fce1e979-0edb-412d-93aa-2c744e8f50ff` | 10001 | Returns 104743 | Generates primes up to 2,000,000 and accesses index `[10001 - 1]` (`[10000]`), returning `104743`. |
| Zeroth prime | `bd0a9eae-6df7-485b-a144-80e13c7d55b2` | 0 | Throws "Prime is not possible" | Explicit guard `if (nthPrime === 0)` throws `Error('Prime is not possible')`. |

## Reference Implementation Details

In `.meta/proof.ci.ts`:
- An input of `0` throws an `Error('Prime is not possible')`.
- Positive inputs filter primes from a range starting at `2` and retrieve the prime using zero-indexed array access `[nthPrime - 1]`.

Because all 5 canonical test cases match this behavior, all 5 cases are included with 0 exclusions.

## Difference Between `xit` and `include = false`

It is common to wonder why tests in `nth-prime.test.ts` use `xit` when all 5 tests are included:

- **Skipped Jest test (`xit`)**: In Exercism practice exercises, tests following the first test are intentionally marked with `xit(...)` instead of `it(...)`. This allows students to follow test-driven development (TDD), enabling one test at a time as they implement their solution. The track's CI and maintenance test runners automatically enable all tests by replacing `xit` with `it` when validating the reference implementation.
- **Excluded canonical test (`include = false`)**: This setting is placed in `.meta/tests.toml` only when a language track cannot or deliberately chooses not to implement a canonical test (for example, due to language limitations, 64-bit integer overflow, or incompatible track-specific paradigms).

Therefore, a test being skipped via `xit` does **not** mean it should be excluded with `include = false`.

