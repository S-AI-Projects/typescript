# Maintenance Notes: `sieve`

## Purpose

This document records a single-token mutation test for `exercises/practice/sieve/.meta/proof.ci.ts`, identifies the minimal spec-valid input and test case that reject the mutant, and documents an independently reproduced duplicate-prime edge case in the current reference solution.

## Mutant and Diff

Scratch mutant stored in `work/R47-T033/mutant.ts`. Compared with `exercises/practice/sieve/.meta/proof.ci.ts`, only the upper-bound comparison in the marking loop changes (`<=` to `<` on line 20):

```diff
--- a/exercises/practice/sieve/.meta/proof.ci.ts
+++ b/work/R47-T033/mutant.ts
@@ -17,7 +17,7 @@
     found.push(candidate)
     let multiple = candidate * candidate
-    while (multiple <= limit) {
+    while (multiple < limit) {
       sieve[multiple - 1] = false
       multiple += candidate
     }
```

This is a semantic change (1 operator token changed: `<=` -> `<`), not whitespace-only.

## Rejecting Test and Outputs

Running both implementations against the full 5-case suite in `exercises/practice/sieve/sieve.test.ts`:

- **Original `.meta/proof.ci.ts`**: `5` passed, `0` failed.
- **Mutant `work/R47-T033/mutant.ts`**: fails on `"find primes up to 10"` (`sieve.test.ts:15-18`, UUID `974945d8-8cd9-4f00-9463-7d813c7f17b7`) and `"find primes up to 1000"` (`sieve.test.ts:25-40`, UUID `92102a05-4c7c-47de-9ed0-b7d5fcd00f21`), while `"no primes under two"`, `"find first prime"`, and `"limit is prime"` pass.

| Input / Case                                | UUID                                   | Expected               | Original (`proof.ci.ts`)      | Mutant (`mutant.ts`)          |
| ------------------------------------------- | -------------------------------------- | ---------------------- | ----------------------------- | ----------------------------- |
| `primes(1)` (`"no primes under two"`)       | `88529125-c4ce-43cc-bb36-1eb4ddd7b44f` | `[]`                   | `[]` (PASS)                   | `[]` (PASS)                   |
| `primes(2)` (`"find first prime"`)          | `4afe9474-c705-4477-9923-840e1024cc2b` | `[2]`                  | `[2]` (PASS)                  | `[2]` (PASS)                  |
| `primes(9)` (minimal distinguishing input)  | —                                      | `[2, 3, 5, 7]`         | `[2, 3, 5, 7]` (OK)           | `[2, 3, 5, 7, 9]` (WRONG)     |
| `primes(10)` (`"find primes up to 10"`)     | `974945d8-8cd9-4f00-9463-7d813c7f17b7` | `[2, 3, 5, 7]`         | `[2, 3, 5, 7]` (PASS)         | `[2, 3, 5, 7, 10]` (FAIL)     |
| `primes(13)` (`"limit is prime"`)           | `2e2417b7-3f3a-452a-8594-b9af08af6d82` | `[2, 3, 5, 7, 11, 13]` | `[2, 3, 5, 7, 11, 13]` (PASS) | `[2, 3, 5, 7, 11, 13]` (PASS) |
| `primes(1000)` (`"find primes up to 1000"`) | `92102a05-4c7c-47de-9ed0-b7d5fcd00f21` | 168 primes (`2..997`)  | 168 primes (PASS)             | Includes `1000` (FAIL)        |

### Minimal Spec-Valid Rejecting Input

The smallest spec-valid input on which the original returns the exact expected primes and the mutant fails is **`limit = 9`**:

- Expected: `[2, 3, 5, 7]`
- Original (`proof.ci.ts`): `[2, 3, 5, 7]`
- Mutant (`mutant.ts`): `[2, 3, 5, 7, 9]` (because `candidate = 3`, `multiple = 3 * 3 = 9`, and `9 < 9` evaluates to `false`, leaving `9` unmarked)

For smaller composite limits `4`, `6`, and `8`, the mutant also includes the composite limit (`[2, 3, 3, 4]`, `[2, 3, 3, 5, 6]`, `[2, 3, 3, 5, 7, 8]`), whereas the original is not correct on those limits because of the duplicate-prime behaviour documented below.

## Expected Behaviour

Per `exercises/practice/sieve/.docs/instructions.md:3-18`, `primes(limit)` must return all prime numbers less than or equal to `limit`, each once, in ascending order (`[]` when `limit < 2`). Multiples of each prime up to **and including** `limit` must be marked composite.

## Observation: Duplicate Primes When `Math.floor(Math.sqrt(limit)) + 1` Is Prime

Running `exercises/practice/sieve/.meta/proof.ci.ts` across integer limits reproduces a defect when `Math.floor(Math.sqrt(limit)) + 1` is prime (for `limit >= 3`):

- `primes(3)` -> `[2, 2, 3]` (expected `[2, 3]`)
- `primes(4)` -> `[2, 3, 3]` (expected `[2, 3]`)
- `primes(5)` -> `[2, 3, 3, 5]` (expected `[2, 3, 5]`)
- `primes(16)` -> `[2, 3, 5, 5, 7, 11, 13]` (expected `[2, 3, 5, 7, 11, 13]`)
- `primes(24)` -> `[2, 3, 5, 5, 7, 11, 13, 17, 19, 23]` (expected `[2, 3, 5, 7, 11, 13, 17, 19, 23]`)
- `primes(36)` -> `[2, 3, 5, 7, 7, 11, 13, 17, 19, 23, 29, 31]` (expected `[2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]`)
- `primes(100)` -> `[2, 3, 5, 7, 11, 11, 13, ..., 97]` (expected 25 primes without duplicate `11`)
- `primes(120)` -> `[2, 3, 5, 7, 11, 11, 13, ..., 113]` (expected 30 primes without duplicate `11`)

Affected integer ranges include `3-8` (`2` for `3`, `3` for `4-8`), `16-24` (`5`), `36-48` (`7`), and `100-120` (`11`).

**Cause in `.meta/proof.ci.ts`**:

- Line 13 runs the candidate loop up to `candidate <= maxCandidate + 1` and pushes unmarked `candidate` values to `found` (line 18).
- Line 26 starts the collection loop at `i = maxCandidate + 1` and pushes unmarked `i` values to `found` (line 28).
- Thus `maxCandidate + 1` is visited by both loops and emitted twice whenever it is prime.

None of the five existing test inputs (`1`, `2`, `10`, `13`, `1000`) triggers this condition (`limit = 2` hits the early return on line 2, and `floor(sqrt(10)) + 1 = 4`, `floor(sqrt(13)) + 1 = 4`, `floor(sqrt(1000)) + 1 = 32` are all composite).

**Proposed new test case** (for instructor / upstream problem-specifications review; `.meta/proof.ci.ts` and `sieve.test.ts` are intentionally left untouched in this task):

- Input: `primes(5)`
- Expected output: `[2, 3, 5]`

## How to Verify

```bash
python3 work/R47-T033/check.py
```

Expected final line:

```text
RESULT: PASS - executed 5 cases
```
