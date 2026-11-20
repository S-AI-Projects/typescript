# Notes for R47-T034 (`collatz-conjecture`)

## Inspected Files

- `exercises/practice/collatz-conjecture/.docs/instructions.md` (lines 1-3): given a positive integer, return the number of steps to reach 1 according to the Collatz Conjecture rules.
- `exercises/practice/collatz-conjecture/.docs/introduction.md` (lines 1-28): defines even (`n / 2`) and odd (`3 * n + 1`) transitions and walks through `12 -> 6 -> 3 -> 10 -> 5 -> 16 -> 8 -> 4 -> 2 -> 1` (9 steps).
- `exercises/practice/collatz-conjecture/.meta/config.json` (lines 1-31): `files.solution = ["collatz-conjecture.ts"]`, `files.test = ["collatz-conjecture.test.ts"]`, `files.example = [".meta/proof.ci.ts"]`. Jest enabled, TStyche disabled.
- `exercises/practice/collatz-conjecture/.meta/tests.toml` (lines 1-38): 8 UUID entries (`6` included, `2` excluded with `reimplements` pairs for `zero is an error` and `negative value is an error`).
- `exercises/practice/collatz-conjecture/collatz-conjecture.test.ts` (lines 1-45): 7 test cases (`1` `it`, `6` `xit`), including `non-integer value is an error` (`steps(3.1415)`), which is track-specific beyond the 6 included canonical entries.
- `exercises/practice/collatz-conjecture/collatz-conjecture.ts` (lines 1-3): learner stub throwing `'Remove this line and implement the function'`.
- `exercises/practice/collatz-conjecture/.meta/proof.ci.ts` (before refactor, lines 1-16): validates `n <= 0 || !Number.isInteger(n)` -> `throw new Error('Only positive integers are allowed')`, then calls `calculateStepsRecursively(n, 0)` which passes `++count` inside recursive call arguments.

## Trace of Named Cases (Local State Determining Each Result)

1. **`"zero steps for one"` (`steps(1)` -> `0`)** (`collatz-conjecture.test.ts:5-8`)

   - `steps(1)` passes validation (`1 > 0` and `Number.isInteger(1)` is `true`).
   - Calls `calculateStepsRecursively(current=1, stepsSoFar=0)`.
   - Base case `current === 1` triggers immediately; `stepsSoFar` (`0`) determines the return value `0`.

2. **`"divide if even"` (`steps(16)` -> `4`)** (`collatz-conjecture.test.ts:10-13`)

   - Validation passes; calls `calculateStepsRecursively(current=16, stepsSoFar=0)`.
   - Step transitions driven by `(current, stepsSoFar)`:
     - `(16, 0)` -> `16 % 2 === 0` -> `next = 8`, recurse `(8, 1)`
     - `(8, 1)` -> `8 % 2 === 0` -> `next = 4`, recurse `(4, 2)`
     - `(4, 2)` -> `4 % 2 === 0` -> `next = 2`, recurse `(2, 3)`
     - `(2, 3)` -> `2 % 2 === 0` -> `next = 1`, recurse `(1, 4)`
     - `(1, 4)` -> `current === 1` -> returns `stepsSoFar = 4`.

3. **`"even and odd steps"` (`steps(12)` -> `9`)** (`collatz-conjecture.test.ts:15-18`)
   - Validation passes; calls `calculateStepsRecursively(current=12, stepsSoFar=0)`.
   - Step transitions driven by `(current, stepsSoFar)`:
     - `(12, 0)` -> even -> `next = 6`, recurse `(6, 1)`
     - `(6, 1)` -> even -> `next = 3`, recurse `(3, 2)`
     - `(3, 2)` -> odd -> `next = 10`, recurse `(10, 3)`
     - `(10, 3)` -> even -> `next = 5`, recurse `(5, 4)`
     - `(5, 4)` -> odd -> `next = 16`, recurse `(16, 5)`
     - `(16, 5)` -> even -> `next = 8`, recurse `(8, 6)`
     - `(8, 6)` -> even -> `next = 4`, recurse `(4, 7)`
     - `(4, 7)` -> even -> `next = 2`, recurse `(2, 8)`
     - `(2, 8)` -> even -> `next = 1`, recurse `(1, 9)`
     - `(1, 9)` -> `current === 1` -> returns `stepsSoFar = 9`.

## Readability Refactor

- Replaced in-place `++count` mutation inside recursive call arguments with pure `stepsSoFar + 1`, renamed `(n, count)` in `calculateStepsRecursively` to `(current, stepsSoFar)`, computed `const next = current % 2 === 0 ? current / 2 : current * 3 + 1` once instead of duplicating recursive return statements, and added a single invariant comment.
- Public API (`export function steps(n: number): number`), error type (`Error`), and error message (`'Only positive integers are allowed'`) are unchanged.
