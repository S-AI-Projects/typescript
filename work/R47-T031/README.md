# R47-T031 Check (`rational-numbers`)

## What It Verifies

`work/R47-T031/check.py` verifies:

1. `.meta/config.json` resolves `solution`, `test`, and `example` files inside `exercises/practice/rational-numbers`.
2. Learner files (`rational-numbers.ts` stub and `rational-numbers.test.ts`) are unsolved and unmodified relative to `org/main`, and remain byte-identical before and after the check.
3. `exercises/practice/rational-numbers/.meta/tests.toml` parses with `tomllib`, preserves all 43 UUIDs and `include` statuses (`43/43/0` before and after), and includes a `comment` key naming each of the 3 target `Addition` test cases.
4. In an isolated temporary copy, substituting `.meta/proof.ci.ts` and applying the track's `enable_all` transform enables all 43 cases, installs dependencies, runs `corepack yarn test` (`tsc` + `jest`), and runs `corepack yarn test:implementation --json`.
5. `evaluate()` validates exit code 0, non-zero total tests, exact count (`43`), 0 failed/pending tests, and `"passed"` status for all 3 named cases.
6. Negative controls confirm `evaluate()` catches an assertion failure, a zero-test run, and a non-zero child exit code.

## How to Run

From the repository root (Python 3.11+):

```bash
python3 work/R47-T031/check.py
```

## Last Run Result

```text
RESULT: PASS - executed 43 cases
```

## Evidence Index

- `work/R47-T031/notes.md` — inspection notes and line-level trace of the 3 named cases
- `work/R47-T031/tool-versions.json` — Python, Node, Corepack, Yarn, TypeScript, Jest, OS, and Git SHAs
- `work/R47-T031/inputs.json` — `config.json` files map, expected case count, named cases, and learner file SHA-256 hashes
- `work/R47-T031/tests.before.toml` — `tests.toml` from `org/main`
- `work/R47-T031/tests.after.toml` — updated `tests.toml` with `comment` keys
- `work/R47-T031/counts.json` — static case count, Jest counts, and `tests.toml` counts before/after
- `work/R47-T031/expected-vs-actual.json` — per-case expected vs actual Jest status
- `work/R47-T031/jest-results.json` — normalized Jest JSON output
- `work/R47-T031/negative-controls.json` — outcomes for assertion failure, zero-test, and child-failure controls
- `work/R47-T031/yarn-install.log` — normalized `corepack yarn install` log
- `work/R47-T031/yarn-test.log` — normalized `corepack yarn test` log
- `work/R47-T031/jest-implementation.log` — normalized `corepack yarn test:implementation` log
