# Notes for R47-T033 (`sieve`)

## Inspected Files

- `exercises/practice/sieve/.docs/introduction.md` (lines 1-7): narrative framing for Sieve of Eratosthenes benchmarking.
- `exercises/practice/sieve/.docs/instructions.md` (lines 1-101): find all prime numbers less than or equal to a given number using the Sieve of Eratosthenes (write `2..limit`, repeatedly take next unmarked number and mark its multiples).
- `exercises/practice/sieve/.meta/config.json` (lines 1-31): `files.solution = ["sieve.ts"]`, `files.test = ["sieve.test.ts"]`, `files.example = [".meta/proof.ci.ts"]`; `flag.tests.may-run-long = true`, `flag.tests.jest = true`, `flag.tests.tstyche = false`.
- `exercises/practice/sieve/.meta/tests.toml` (lines 1-18): 5 entries, all 5 included (`5/5/0`):
  - `88529125-c4ce-43cc-bb36-1eb4ddd7b44f`: `"no primes under two"`
  - `4afe9474-c705-4477-9923-840e1024cc2b`: `"find first prime"`
  - `974945d8-8cd9-4f00-9463-7d813c7f17b7`: `"find primes up to 10"`
  - `2e2417b7-3f3a-452a-8594-b9af08af6d82`: `"limit is prime"`
  - `92102a05-4c7c-47de-9ed0-b7d5fcd00f21`: `"find primes up to 1000"`
- `exercises/practice/sieve/sieve.test.ts` (lines 1-41): 5 cases (`1` `it`, `4` `xit`), testing inputs `1`, `2`, `10`, `13`, `1000`.
- `exercises/practice/sieve/.meta/proof.ci.ts` (lines 1-33):
  - Line 2-4: special-cases `limit === 2`.
  - Line 12: `const maxCandidate = Math.floor(Math.sqrt(limit))`
  - Line 13: `for (let candidate = 2; candidate <= maxCandidate + 1; candidate++)`
  - Line 18: pushes `candidate` into `found`
  - Line 20: `while (multiple <= limit)` marks `sieve[multiple - 1] = false`
  - Lines 26-30: `for (let i = maxCandidate + 1; i <= limit; i++)` pushes unmarked `i` into `found`
- `exercises/practice/sieve/sieve.ts` (lines 1-3): learner stub throwing `'Remove this line and implement the function'`.

## Mutant and Minimal Rejecting Input

- Mutant in `work/R47-T033/mutant.ts` (line 20): `while (multiple <= limit)` -> `while (multiple < limit)`.
- Rejecting named test: `"find primes up to 10"` (`sieve.test.ts:15-18`, UUID `974945d8-8cd9-4f00-9463-7d813c7f17b7`), where `primes(10)` returns `[2, 3, 5, 7, 10]` instead of `[2, 3, 5, 7]`.
- Smallest spec-valid input where original is correct and mutant fails: `limit = 9` (original returns `[2, 3, 5, 7]`; mutant returns `[2, 3, 5, 7, 9]`).

## Duplicate-Prime Observation Reproduced

Because `proof.ci.ts:13` loops `candidate <= maxCandidate + 1` and `proof.ci.ts:26` loops `i = maxCandidate + 1` to `limit`, the value `maxCandidate + 1 = Math.floor(Math.sqrt(limit)) + 1` is added to `found` in both loops whenever it is prime (for `limit >= 3`).
Reproduced examples:

- `primes(3)` -> `[2, 2, 3]` (expected `[2, 3]`)
- `primes(5)` -> `[2, 3, 3, 5]` (expected `[2, 3, 5]`)
- `primes(24)` -> `[2, 3, 5, 5, 7, 11, 13, 17, 19, 23]` (expected `[2, 3, 5, 7, 11, 13, 17, 19, 23]`)
- `primes(36)` -> `[2, 3, 5, 7, 7, 11, 13, 17, 19, 23, 29, 31]`
- `primes(100)` -> `[2, 3, 5, 7, 11, 11, 13, ..., 97]`
