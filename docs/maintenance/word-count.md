# Maintenance Guide: Word Count (R47-T019)

This document describes the isolated test runner and verification architecture for the `word-count` practice exercise.

---

## 1. Overview & Architecture

The Word Count exercise requires students to parse a phrase and return a `Map<string, number>` with the counts of each word.

The test verification runner (`tools/course_checks/r47-t019.py`) tests the reference solution (`.meta/proof.ci.ts`) in an isolated temporary environment. This ensures that:
- The exercise test suite is healthy and fully solvable.
- The learner starter stub (`word-count.ts`) is **never modified or solved**.
- All temporary artifacts are completely cleaned up.

---

## 2. Runner Requirements & Guarantees

The isolated runner adheres to the following contract:

1. **Metadata Discovery:** Reads `.meta/config.json` to dynamically resolve paths for:
   - Solution file (`word-count.ts`)
   - Test suite (`word-count.test.ts`)
   - Reference implementation (`.meta/proof.ci.ts`)

2. **Isolated Environment:**
   - Copies the entire exercise directory (including hidden files like `.meta/` and `.yarnrc.yml`) to a fresh temporary directory using `shutil.copytree`.
   - The learner stub is replaced with the reference implementation **only inside the temporary directory**.

3. **Full Test Execution:**
   - Unskips all skipped tests (`xit` $\to$ `it`) in the temporary test file.
   - All 14 canonical test cases are executed.

4. **Non-Interactive Execution:**
   - Sets environment variable `CI=true` to disable Jest watch mode.
   - Runs the package test script via `corepack yarn test`.

5. **Failure Detection & Safeguards:**
   - **Zero Test Failure:** Fails if zero tests run (e.g. if the test suite is empty).
   - **Process Exit Code:** Fails if `yarn install` or `yarn test` exits with a non-zero status.
   - **Assertion Failure:** Fails if any test case fails.

6. **Guaranteed Cleanup:**
   - Uses `tempfile.TemporaryDirectory` with a `try...finally` block to ensure all temporary folders are removed upon completion, error, or interruption.

---

## 3. Runner Commands

### Main Course Check Runner
Runs the isolated test runner on the canonical reference implementation:

```bash
python3 tools/course_checks/r47-t019.py
```

Optional CLI flags:
- `--reference <path>`: Test a custom reference implementation file.
- `--empty-tests`: Test failure handling when no tests are selected.
- `--json`: Format the output as JSON.

### Verification Script
Runs full scenario testing (real reference, failing reference, empty test selection) and verifies file hash immutability:

```bash
python3 work/R47-T019/check.py
```
