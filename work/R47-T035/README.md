# R47-T035 Check (`darts`)

## What It Verifies

`work/R47-T035/check.py` verifies:

1. `.meta/config.json` resolves `solution`, `test`, and `example` files inside `exercises/practice/darts`.
2. Learner stub (`darts.ts`) and test (`darts.test.ts`) remain unsolved and identical to `org/main`.
3. Only comment lines changed in `exercises/practice/darts/.meta/proof.ci.ts` compared with `org/main` (code tokens after stripping comments are identical).
4. In an isolated temporary copy, all 13 cases pass `corepack yarn test` (`tsc` + `jest`) and `corepack yarn test:implementation --json`, and `corepack yarn lint:ci` passes.
5. An instrumented copy of `score` runs in Node after asserting correctness on `(-9, 9)`, `(0, 10)`, `(-5, 0)`, and `(0, -1)` and confirms exact agreement with the operation table in `docs/maintenance/darts.md`, while separately measuring `tsc` compile time, Node process startup, and median `ns/call` across 7 repetitions of 1,000,000 calls per region.
6. Negative controls confirm `evaluate()` catches assertion failures, zero-test runs, and non-zero child exit codes.

## How to Run

From the repository root:

```bash
python3 work/R47-T035/check.py
```

## Last Run Result

```text
RESULT: PASS - executed 13 cases
```

## Evidence Index

- `work/R47-T035/notes.md` — inspection notes and constant-bound analysis
- `work/R47-T035/operation-counts-and-timing.json` — instrumented operation counts and separated `tsc`/startup/algorithm timings
- `work/R47-T035/tool-versions.json`, `inputs.json`, `counts.json`, `expected-vs-actual.json`, `jest-results.json`, `negative-controls.json`, and `*.log`
