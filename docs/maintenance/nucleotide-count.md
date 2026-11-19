# Nucleotide Count: Isolated Test Runner & Maintenance Guide

This document describes the design, operation, and maintenance procedures for the isolated nucleotide-count test runner on the Exercism TypeScript track.

---

## 1. Purpose of the Isolated Runner

The isolated test runner executes TypeScript exercise tests in a secure, ephemeral sandbox environment. Its primary objectives are:
- Validating the maintained reference implementation without modifying the working tree.
- Protecting the learner starter stub (`nucleotide-count.ts`) from accidental overwrites or solution leaks.
- Ensuring canonical tests run to completion with full failure propagation and zero-test detection.
- Providing reproducible verification for maintainers and automated CI pipelines.

---

## 2. Location of the Runner

- **Runner Script:** `tools/course_checks/r47-t029.py`
- **Checker Harness:** `work/R47-T029/check.py`
- **Target Exercise:** `exercises/practice/nucleotide-count/`

---

## 3. Configuration Loading & Path Resolution

The runner inspects `exercises/practice/nucleotide-count/.meta/config.json` at runtime:
```json
{
  "files": {
    "solution": [
      "nucleotide-count.ts"
    ],
    "test": [
      "nucleotide-count.test.ts"
    ],
    "example": [
      ".meta/proof.ci.ts"
    ]
  }
}
```

The runner:
1. Loads and parses the JSON configuration dynamically.
2. Extracts relative paths for `solution`, `test`, and `example` roles.
3. Normalizes each path relative to `exercises/practice/nucleotide-count/`.
4. Strictly forbids path traversal segments (`..`) and absolute paths escaping the exercise directory.
5. Asserts that all declared files physically exist on disk before proceeding.

---

## 4. Temporary Reference Substitution

To execute tests against the reference solution without dirtying Git working trees:
1. A temporary directory is provisioned using Python's `tempfile.TemporaryDirectory()`.
2. The complete exercise directory (including hidden configuration files like `.yarnrc.yml`, `.meta/`, and `babel.config.cjs`) is copied into the temporary sandbox.
3. The maintained reference (`.meta/proof.ci.ts`) is copied over `nucleotide-count.ts` **only inside the temporary copy**.
4. The real learner file in the workspace is never modified or touched.

---

## 5. Test Execution & Watch Mode Disabling

Inside the temporary sandbox:
1. All canonical tests are enabled by transforming `\bxit\(` into `it(`.
2. Dependencies are prepared with `corepack yarn install --no-immutable`.
3. Jest implementation tests execute non-interactively with:
   ```bash
   corepack yarn test:implementation --ci --watchAll=false --json --outputFile=<path>
   ```
   - `--ci` and `--watchAll=false` ensure test execution terminates immediately without waiting for terminal input.
   - `--json --outputFile=...` captures machine-readable assertion results.

---

## 6. Test Count Detection & Assertion Handling

The runner parses the generated Jest JSON report:
- **Executed Tests:** Calculated as $\text{numPassedTests} + \text{numFailedTests}$.
- **Passed Tests:** Checked against expected canonical cases.
- **Failed Tests:** Any non-zero count triggers an immediate `RunnerError` and exit code `1`.

### Zero-Test Protection
If Jest executes 0 tests (e.g., all tests disabled or filtered out by a non-matching pattern), the runner detects `executed == 0`, prints an explicit error, and exits with code `1`. An empty test run is never treated as a success.

---

## 7. Sandbox Cleanup & Resource Safety

The runner utilizes Python context managers (`with tempfile.TemporaryDirectory() as tmp_dir:`). Regardless of whether test runs succeed, fail with assertion errors, or terminate via unexpected exceptions, the operating system cleans up all temporary directory contents upon block exit.

---

## 8. SHA-256 Learner File Integrity Verification

To guarantee that no runner execution pollutes the repository working tree, the automated verification checker computes SHA-256 cryptographic hashes for key exercise files before and after every scenario:
- `exercises/practice/nucleotide-count/nucleotide-count.ts`
- `exercises/practice/nucleotide-count/nucleotide-count.test.ts`
- `exercises/practice/nucleotide-count/.meta/proof.ci.ts`

Any divergence between before and after hashes causes the checker to fail immediately. Furthermore, the starter stub is confirmed to retain `throw new Error('Remove this line and implement the function')`.

---

## 9. Environment Requirements

The following toolchain versions are verified in the execution environment:
- **Python:** `>= 3.11` (Python 3.14.5 verified)
- **Node.js:** `v24.22.1`
- **Corepack:** `0.36.0`
- **Yarn:** `4.5.1`

---

## 10. Execution Commands

### Run the Isolated Runner Directly
```bash
python3 tools/course_checks/r47-t029.py
```

### Run the Complete Automated Verification Harness
```bash
python3 work/R47-T029/check.py
```
