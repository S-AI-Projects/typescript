# Notes for R47-T031 (`rational-numbers`)

## Inspected Files

- `exercises/practice/rational-numbers/.docs/instructions.md` (lines 1-42): defines rational numbers `a/b` (`b != 0`), arithmetic operations, reduction via `gcd(a, b)`, and standard form (positive denominator). Line 42 notes the assumption that the language has no built-in rational number implementation.
- `exercises/practice/rational-numbers/.meta/config.json` (lines 1-32): `files.solution = ["rational-numbers.ts"]`, `files.test = ["rational-numbers.test.ts"]`, `files.example = [".meta/proof.ci.ts"]`. No `editor` key. Jest enabled, TStyche disabled.
- `exercises/practice/rational-numbers/.meta/tests.toml` (lines 1-139): 43 UUID entries, 43 included (no `include = false`), 0 excluded, 0 `reimplements`. Header lines 9-10 state `#` comments are removed by `configlet sync` and `comment = "..."` keys are preserved.
- `exercises/practice/rational-numbers/rational-numbers.test.ts` (lines 1-244): 43 test cases total (`it` / `xit`).
- `exercises/practice/rational-numbers/.meta/proof.ci.ts` (lines 1-99): `Rational` class with `add` (lines 17-23), `reduce` (lines 72-80), `gcd` (lines 82-91), and `ensureSignInNumerator` (lines 93-98).

## Named Cases Traced

1. `0ba4d988-044c-4ed5-9215-4d0bb8d0ae9f`
   - `tests.toml` line 12-13: `"Arithmetic -> Addition -> Add two positive rational numbers"`
   - `rational-numbers.test.ts` lines 16-19: `"Add two positive rational numbers"`, `new Rational(1, 2).add(new Rational(2, 3))` -> `(7, 6)`
   - `proof.ci.ts`: `add` (lines 17-23) computes `(1*3 + 2*2, 2*3) = (7, 6)`; `constructor` (lines 5-15) calls `reduce` (lines 72-80) with `gcd(7, 6) = 1` (lines 82-91) and `ensureSignInNumerator` (lines 93-98).
2. `88ebc342-a2ac-4812-a656-7b664f718b6a`
   - `tests.toml` line 15-16: `"Arithmetic -> Addition -> Add a positive rational number and a negative rational number"`
   - `rational-numbers.test.ts` lines 21-24: `"Add a positive rational number and a negative rational number"`, `new Rational(1, 2).add(new Rational(-2, 3))` -> `(-1, 6)`
   - `proof.ci.ts`: `add` computes `(1*3 + (-2)*2, 2*3) = (-1, 6)`; `gcd(-1, 6)` uses JS `%` (`-1 % 6 === -1`), returning `-1`, so `reduce` divides to `(1, -6)` and `ensureSignInNumerator` negates both to `(-1, 6)`.
3. `92ed09c2-991e-4082-a602-13557080205c`
   - `tests.toml` line 18-19: `"Arithmetic -> Addition -> Add two negative rational numbers"`
   - `rational-numbers.test.ts` lines 26-29: `"Add two negative rational numbers"`, `new Rational(-1, 2).add(new Rational(-2, 3))` -> `(-7, 6)`
   - `proof.ci.ts`: `add` computes `((-1)*3 + (-2)*2, 2*3) = (-7, 6)`; `gcd(-7, 6)` returns `-1`, `reduce` gives `(7, -6)`, and `ensureSignInNumerator` normalizes to `(-7, 6)`.
