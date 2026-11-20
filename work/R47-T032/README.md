# R47-T032 Check (`accumulate`)

## What It Verifies

`work/R47-T032/check.py` verifies:

1. `.meta/config.json` resolves `solution`, `test`, and `example` files inside `exercises/practice/accumulate`.
2. Learner files (`accumulate.ts` stub and `accumulate.test.ts`) are unsolved and unmodified relative to `org/main`, and remain byte-identical before and after the check.
3. `tools/course_checks/r47-t032.py --exercise practice/accumulate` archives `org/main` into two fresh temporary directories, runs `corepack yarn install --immutable` and `scripts/helpers.mjs` `prepareAndRun()` in each, compares `tmp_exercises/accumulate.test.ts` and `tmp_exercises/accumulate.ts` byte-for-byte via SHA-256, verifies equality with `enable_all()`, and confirms all 5 test cases are present in both generations.
4. In an isolated temporary copy of the exercise, substituting `.meta/proof.ci.ts` and applying `enable_all()` enables all 5 cases, runs `corepack yarn test` (`tsc` + `jest`), and runs `corepack yarn test:implementation --json`.
5. `evaluate()` validates exit code `0`, non-zero total tests, exact count (`5`), `0` failed/pending tests, and `"passed"` status for all 3 named cases (`"accumulation empty"`, `"accumulate squares"`, `"accumulate upcases"`).
6. Negative controls confirm `evaluate()` catches an assertion failure, a zero-test run, and a non-zero child exit code.

## How to Run

From the repository root:

```bash
python3 work/R47-T032/check.py
```

Or run the reusable reproducibility tool directly:

```bash
python3 tools/course_checks/r47-t032.py --exercise practice/accumulate
```

## Last Run Result

```text
RESULT: PASS - executed 5 cases
```

## Evidence Index

- `work/R47-T032/notes.md` — inspection notes covering scripts, workflows, `config.json`, and `configlet`
- `work/R47-T032/reproducibility.json` — SHA-256 hashes, byte lengths, diffs, `enable_all` checks, and normalisation statement
- `work/R47-T032/reproducibility-tool.log` — normalized output from `tools/course_checks/r47-t032.py`
- `work/R47-T032/generated-copy1-accumulate.test.ts.txt` / `generated-copy2-accumulate.test.ts.txt` — generated test files from both temp archives
- `work/R47-T032/generated-copy1-accumulate.ts.txt` / `generated-copy2-accumulate.ts.txt` — generated reference solution files from both temp archives
- `work/R47-T032/tool-versions.json` — Python, Node, Corepack, Yarn, TypeScript, Jest, OS, and Git SHAs
- `work/R47-T032/inputs.json` — `config.json` files map, expected case count, named cases, and learner file SHA-256 hashes
- `work/R47-T032/counts.json` — static case count and Jest counts
- `work/R47-T032/expected-vs-actual.json` — per-case expected vs actual Jest status
- `work/R47-T032/jest-results.json` — normalized Jest JSON output
- `work/R47-T032/negative-controls.json` — outcomes for assertion failure, zero-test, and child-failure controls
- `work/R47-T032/yarn-install.log` — normalized `corepack yarn install` log
- `work/R47-T032/yarn-test.log` — normalized `corepack yarn test` log
- `work/R47-T032/jest-implementation.log` — normalized `corepack yarn test:implementation` log
