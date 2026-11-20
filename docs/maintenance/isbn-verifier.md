# Maintenance Notes: `isbn-verifier`

## Purpose

This document describes the isolated test runner `tools/course_checks/r47-t039.py`, which runs `exercises/practice/isbn-verifier` (22 Jest cases vs. 21 entries in `.meta/tests.toml`; `"too long isbn"` is an extra track test case) without modifying learner files or the empty tracked `yarn.lock` in the working tree.

## Command

Run the isolated runner from the repository root:

```bash
python3 tools/course_checks/r47-t039.py --exercise practice/isbn-verifier
```

Optional control flags:

- `--reference <path>`: substitute a custom TypeScript file inside the temporary copy only.
- `--test-name-pattern <regex>`: forward `--testNamePattern=<regex>` to Jest.
- `--json-out <path>`: save the Jest JSON output file.

Run the full scenario verification suite (real reference, failing reference, empty selection, interrupted run, and negative controls):

```bash
python3 work/R47-T039/check.py
```

## Tool Requirements

Verified working versions (`work/R47-T039/tool-versions.json`):

- **Python**: `3.11+` (verified on `3.12.16`)
- **Node.js**: `^18.16.0 || >=20.0.0` (verified on `v24.22.1`)
- **Corepack**: `0.36.0`
- **Yarn**: `4.5.1` (installed inside the isolated temporary copy with `YARN_ENABLE_IMMUTABLE_INSTALLS=false` so the empty exercise `yarn.lock` can resolve without touching the working tree)

## Scenarios and Exit Codes

| Scenario             | Invocation / Action                                          | Expected Exit Code        | Outcome                                                                                        |
| -------------------- | ------------------------------------------------------------ | ------------------------- | ---------------------------------------------------------------------------------------------- |
| Real reference       | `r47-t039.py --exercise practice/isbn-verifier`              | `0`                       | Enables all 22 tests, runs `tsc` + Jest, verifies `22/22` passed                               |
| Failing reference    | `--reference <negated isValid>`                              | Non-zero (`1`)            | Jest fails assertions; runner propagates non-zero exit                                         |
| Empty test selection | `--test-name-pattern __no_matching_test_case__`              | Non-zero (`1`)            | Jest exits `0` via `--passWithNoTests` (`22` pending, `0` executed), caught by zero-test guard |
| Interrupted run      | Send `SIGINT` (POSIX) / `CTRL_BREAK_EVENT` (Windows) mid-run | Non-zero (`130` on POSIX) | Child process terminated, `r47-t039-*` temp dir deleted, learner hashes unchanged              |

## Safety Guarantees

1. **Zero working-tree mutations**: All Yarn installs, `.meta/proof.ci.ts` substitution, and `enable_all()` test edits happen strictly inside a `tempfile.mkdtemp(prefix="r47-t039-")` directory.
2. **Pre- and post-execution SHA-256 verification**: `r47-t039.py` hashes every file under `exercises/practice/isbn-verifier` before starting and re-verifies in a `finally:` block (even on failure or interruption).
3. **Guaranteed temp-directory cleanup**: `TEMP_DIR: <path>` is printed immediately upon creation, and `finally:` removes it with retry logic (`remove_tree_with_retry`) on success, failure, and `KeyboardInterrupt` / `SIGINT` / `SIGBREAK`.
4. **Zero-test guard**: Because `package.json` `test:implementation` includes `--passWithNoTests`, Jest exits `0` when 0 tests run (including when `--testNamePattern` skips every test as pending); `evaluate()` explicitly fails whenever `numTotalTests == 0` or `numTotalTests - numPendingTests == 0`.
