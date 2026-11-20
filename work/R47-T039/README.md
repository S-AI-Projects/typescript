# R47-T039 Check (`isbn-verifier`)

## What It Verifies

`work/R47-T039/check.py` verifies `tools/course_checks/r47-t039.py` across four scenarios (hashing all files under `exercises/practice/isbn-verifier` before and after every scenario) and runs the shared contract A–K checks:

1. **Real reference**: exits `0`, executes all 22 Jest cases (`"valid isbn"`, `"invalid isbn check digit"`, `"valid isbn with a check digit of 10"`, plus 19 others), removes `r47-t039-*` temp dir, preserves learner hashes.
2. **Failing reference**: exits non-zero, removes temp dir, preserves learner hashes.
3. **Empty test selection** (`--test-name-pattern __no_matching_test_case__`): exits non-zero via the zero-test guard, removes temp dir, preserves learner hashes.
4. **Interrupted run** (`SIGINT` sent mid-run): exits non-zero, removes `r47-t039-*` temp dir, preserves learner hashes.
5. Isolated shared-contract run and negative controls (`assertion_failure`, `zero_tests`, `child_failure`).

## How to Run

From the repository root:

```bash
python3 work/R47-T039/check.py
```

Or run the isolated runner directly:

```bash
python3 tools/course_checks/r47-t039.py --exercise practice/isbn-verifier
```

## Last Run Result

```text
RESULT: PASS - executed 22 cases
```

## Evidence Index

- `work/R47-T039/notes.md` — inspection notes
- `work/R47-T039/scenarios.json` — pass/fail, exit code, temp-dir cleanup, and learner hash checks for all 4 scenarios
- `work/R47-T039/scenario-1-real.log`, `scenario-2-failing-ref.log`, `scenario-3-empty-selection.log`, `scenario-4-interrupted.log`
- `work/R47-T039/tool-versions.json`, `inputs.json`, `counts.json`, `expected-vs-actual.json`, `jest-results.json`, `negative-controls.json`, and `*.log`
