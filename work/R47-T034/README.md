# R47-T034 Check (`collatz-conjecture`)

## Concrete Readability Improvement & Why It Helps

In `exercises/practice/collatz-conjecture/.meta/proof.ci.ts`, `calculateStepsRecursively` previously mutated its `count` parameter in-place inside both recursive call arguments (`++count`) and duplicated the recursive return branches. The refactor:

1. Replaces `++count` parameter mutation with pure `stepsSoFar + 1` and renames `(n, count)` to `(current, stepsSoFar)`, separating the current Collatz term from the accumulated step count so callers and readers do not have to track prefix-increment side effects inside argument lists.
2. Computes `const next = current % 2 === 0 ? current / 2 : current * 3 + 1` once before a single recursive `return`, making the Collatz transition and step-count increment immediately clear, alongside a one-line invariant comment.

The exported signature `steps(n: number): number`, validation, error type (`Error`), and error message (`'Only positive integers are allowed'`) are unchanged.

## What It Verifies

`work/R47-T034/check.py` verifies:

1. `.meta/config.json` resolves `solution`, `test`, and `example` files inside `exercises/practice/collatz-conjecture`.
2. Learner stub (`collatz-conjecture.ts`) and test (`collatz-conjecture.test.ts`) remain unsolved and identical to `org/main`, and all exercise files remain unchanged during the check.
3. Both the BEFORE (`org/main`) and AFTER versions of `.meta/proof.ci.ts` pass all 7 Jest cases (`tsc` + `jest`) in separate isolated temporary copies.
4. Exercise ESLint (`corepack yarn lint:ci`) passes on the refactored `.meta/proof.ci.ts`.
5. Single-file `tsc` compilation (`--target es2020 --module nodenext --strict`) followed by an equivalence sweep across `n = 1..100000` plus error inputs `0`, `-15`, `1.5`, `NaN` (`100,004` total checks) produces `0` mismatches.
6. Negative controls confirm `evaluate()` catches assertion failures, zero-test runs, and non-zero child exit codes.

## How to Run

From the repository root:

```bash
python3 work/R47-T034/check.py
```

## Last Run Result

```text
RESULT: PASS - executed 7 cases
```

## Evidence Index

- `work/R47-T034/notes.md` — inspection notes and step-by-step state trace for inputs `1`, `16`, and `12`
- `work/R47-T034/before.proof.ci.ts` / `after.proof.ci.ts` — BEFORE (`org/main`) and AFTER reference implementations
- `work/R47-T034/equivalence-sweep.json` — `100,004`-input equivalence sweep summary (`1..100000` and error cases)
- `work/R47-T034/before-jest-results.json` / `jest-results.json` — BEFORE and AFTER Jest JSON outputs
- `work/R47-T034/counts.json`, `expected-vs-actual.json`, `inputs.json`, `tool-versions.json`, `negative-controls.json`, and `*.log`
