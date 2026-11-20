# Maintenance Notes: `rational-numbers`

## Purpose

This document records the canonical-test inclusion decisions and implementation trace for the three `Addition` canonical test cases in `exercises/practice/rational-numbers`.

## Canonical Case Mapping

All 43 canonical entries in `exercises/practice/rational-numbers/.meta/tests.toml` are included (`43` total, `43` included, `0` excluded, `0` `reimplements`).

| UUID                                   | `tests.toml` description                                                                  | Test name                                                       | Test line                        | Input                                          | Expected  | Reference operation & line                                                                                                  | Rationale                                                                                                                                                                 | Included?                                |
| -------------------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------- | ---------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `0ba4d988-044c-4ed5-9215-4d0bb8d0ae9f` | `Arithmetic -> Addition -> Add two positive rational numbers`                             | `Add two positive rational numbers`                             | `rational-numbers.test.ts:16-19` | `new Rational(1, 2).add(new Rational(2, 3))`   | `(7, 6)`  | `add` (`proof.ci.ts:17-23`), `constructor` (`5-15`), `reduce` (`72-80`), `gcd` (`82-91`), `ensureSignInNumerator` (`93-98`) | Baseline positive-operand addition: verifies cross-multiplication `(1*3 + 2*2) / (2*3)`, `gcd(7, 6) = 1`, and standard form.                                              | Yes (no `include` key; default included) |
| `88ebc342-a2ac-4812-a656-7b664f718b6a` | `Arithmetic -> Addition -> Add a positive rational number and a negative rational number` | `Add a positive rational number and a negative rational number` | `rational-numbers.test.ts:21-24` | `new Rational(1, 2).add(new Rational(-2, 3))`  | `(-1, 6)` | `add` (`proof.ci.ts:17-23`), `gcd` (`82-91`), `reduce` (`72-80`), `ensureSignInNumerator` (`93-98`)                         | Mixed-sign addition producing a negative sum (`-1/6`): exercises negative-dividend `%` in `gcd(-1, 6) = -1` and sign normalization to keep the denominator positive.      | Yes (no `include` key; default included) |
| `92ed09c2-991e-4082-a602-13557080205c` | `Arithmetic -> Addition -> Add two negative rational numbers`                             | `Add two negative rational numbers`                             | `rational-numbers.test.ts:26-29` | `new Rational(-1, 2).add(new Rational(-2, 3))` | `(-7, 6)` | `add` (`proof.ci.ts:17-23`), `gcd` (`82-91`), `reduce` (`72-80`), `ensureSignInNumerator` (`93-98`)                         | Both-negative addition (`-7/6`): verifies signed cross-multiplication `(-1*3 + (-2)*2)` and that negative numerator signs are preserved on the numerator after reduction. | Yes (no `include` key; default included) |

## TypeScript / JavaScript Operations Involved

- `number` in TypeScript/JavaScript is an IEEE-754 double-precision floating-point value. Integer arithmetic (`*`, `+`, `/`, `%`) is exact up to `Number.MAX_SAFE_INTEGER` ($2^{53} - 1$), so all small integers in these cases are exact.
- The remainder operator `%` in JavaScript/TypeScript preserves the sign of the dividend (left operand). In `proof.ci.ts:82-91`, `gcd(a, b)` does not take `Math.abs`, so `gcd(-1, 6)` and `gcd(-7, 6)` return `-1`. Dividing by `-1` in `reduce()` (`proof.ci.ts:75-76`) temporarily makes the denominator `-6`, which `ensureSignInNumerator()` (`proof.ci.ts:93-98`) then normalizes back to `denominator = 6` and a negative `numerator`.

## Excluded vs. Replacement Cases

**N/A**: All 43 canonical cases in `exercises/practice/rational-numbers/.meta/tests.toml` are included, and none use `reimplements`. Inclusion of all three addition cases is appropriate for TypeScript because the language has no built-in rational number type (see `exercises/practice/rational-numbers/.docs/instructions.md:42`), so the user-defined `Rational` class must be verified across all sign combinations.

## Why `comment` Keys Are Used in `tests.toml`

Per the header of `exercises/practice/rational-numbers/.meta/tests.toml:9-10`, `configlet sync` removes `#`-prefixed comments when regenerating the file, whereas `comment = "..."` key/value pairs inside each `[uuid]` table are preserved.

## Counts Before and After

- Before (`org/main`): `43` entries, `43` included, `0` excluded
- After: `43` entries, `43` included, `0` excluded

## How to Verify

Run from the repository root (requires Python 3.11+ for `tomllib`):

```bash
python3 work/R47-T031/check.py
```

Expected final line:

```text
RESULT: PASS - executed 43 cases
```
