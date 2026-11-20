# R47-T038 Check (`dnd-character`)

## What It Verifies

`work/R47-T038/check.py` verifies:

1. `.meta/config.json` resolves `solution`, `test`, and `example` files inside `exercises/practice/dnd-character`, and `dnd-character.ts`, `dnd-character.test.ts`, and `.meta/config.json` match `org/main`.
2. `tools/course_checks/r47-t038.py` validates `exercises/practice/dnd-character` (`exit 0`) and fails for the intended reasons on three temporary fixtures:
   - `missing_example` (`ERR_MISSING_FILE:example`)
   - `missing_test` (`ERR_MISSING_FILE:test`)
   - `outside_escape` (`../two-fer/two-fer.ts` -> `ERR_PARENT_TRAVERSAL:solution`)
3. In an isolated temporary copy, `.meta/proof.ci.ts` compiles and passes all 25 Jest cases (`19` canonical entries in `.meta/tests.toml` plus `6` extra track cases splitting `"Random character is valid"`).
4. Negative controls confirm `evaluate()` catches assertion failures, zero-test runs, and non-zero child exit codes.

## How to Run

From the repository root:

```bash
python3 work/R47-T038/check.py
```

Or run the validator directly:

```bash
python3 tools/course_checks/r47-t038.py exercises/practice/dnd-character
```

## Last Run Result

```text
RESULT: PASS - executed 25 cases
```

## Evidence Index

- `work/R47-T038/notes.md` — inspection notes covering `.meta/config.json`, runners, and 25 vs 19 test cases
- `work/R47-T038/validator-real.log` — role -> path -> exists output on `exercises/practice/dnd-character`
- `work/R47-T038/validator-fixtures.json` — outputs and expected error codes for the real config and 3 negative fixtures
- `work/R47-T038/tool-versions.json`, `inputs.json`, `counts.json`, `expected-vs-actual.json`, `jest-results.json`, `negative-controls.json`, and `*.log`
