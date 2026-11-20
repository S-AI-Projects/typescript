# R47-T033 Check (`sieve`)

## What It Verifies

`work/R47-T033/check.py` verifies:

1. `.meta/config.json` resolves `solution`, `test`, and `example` files inside `exercises/practice/sieve`.
2. Learner files (`sieve.ts`, `sieve.test.ts`, `.meta/proof.ci.ts`) are unsolved and unmodified relative to `org/main`, and all files under `exercises/practice/sieve` remain unchanged during the check.
3. `work/R47-T033/mutant.ts` differs from `.meta/proof.ci.ts` by a non-whitespace token change (`<=` -> `<` in `while (multiple <= limit)`).
4. In separate isolated temporary copies:
   - Original `.meta/proof.ci.ts` passes all 5 cases (`tsc` + `jest`).
   - Mutant `work/R47-T033/mutant.ts` fails specifically on `"find primes up to 10"` (`974945d8-8cd9-4f00-9463-7d813c7f17b7`).
5. A direct Node probe confirms `limit = 9` is the smallest spec-valid input where original returns `[2, 3, 5, 7]` and mutant fails (`[2, 3, 5, 7, 9]`), and reproduces the duplicate-prime defect on `primes(5)` (`[2, 3, 3, 5]`).
6. Negative controls confirm `evaluate()` catches assertion failures, zero-test runs, and non-zero child exit codes.

## How to Run

From the repository root:

```bash
python3 work/R47-T033/check.py
```

## Last Run Result

```text
RESULT: PASS - executed 5 cases
```

## Evidence Index

- `work/R47-T033/notes.md` — inspection notes
- `work/R47-T033/mutant.ts` — deliberate mutant (`while (multiple < limit)`)
- `work/R47-T033/mutant-diff.patch` — unified diff vs `.meta/proof.ci.ts`
- `work/R47-T033/mutant-comparison.json` — per-case comparison of original vs mutant
- `work/R47-T033/probe-outputs.json` — original vs mutant vs exact reference across inputs `1..120`
- `work/R47-T033/tool-versions.json`, `inputs.json`, `counts.json`, `expected-vs-actual.json`, `jest-results.json`, `mutant-jest-results.json`, `negative-controls.json`, and `*.log`
