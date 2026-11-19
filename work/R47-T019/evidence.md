# Evidence — R47-T019 (Word Count Isolated Test Runner)

## Tool Versions
- Python: Python 3.9.6
- Node.js: v26.8.2
- Yarn: 4.5.1

## Learner Solution Immutability
- File: `exercises/practice/word-count/word-count.ts`
- Initial SHA-256: `03161c44aeefe4c9514de054ae2bd0a3496b005c1f3b10cdae53d4bd61087314`
- Final SHA-256:   `03161c44aeefe4c9514de054ae2bd0a3496b005c1f3b10cdae53d4bd61087314`
- Immutability Verified: **True** (file was never modified or solved)

## Scenario Verification Results

| Scenario | Description | Expected Result | Actual Result | File Hash Unchanged | Status |
| --- | --- | --- | --- | --- | --- |
| Scenario 1: Real Reference Implementation | Runs r47-t019.py with canonical .meta/proof.ci.ts | Exit code 0 (success=True) | Exit code 0 | Yes | PASS |
| Scenario 2: Deliberately Failing Reference | Runs r47-t019.py with a reference returning an empty Map | Exit code 1 (success=False) | Exit code 1 | Yes | PASS |
| Scenario 3: Empty Test Selection | Runs r47-t019.py with --empty-tests (0 tests executed) | Exit code 1 (success=False) | Exit code 1 | Yes | PASS |

## Scenario Execution Logs

### Scenario 1: Real Reference Implementation
```text
[runner] Copied exercise to temporary directory: /var/folders/1m/z27s7x0d5lv4wbcnbmdwpz4h0000gn/T/r47-t019-qgwq2hdo/word-count
[runner] Replaced word-count.ts with reference proof.ci.ts
[runner] Unskipped all tests in word-count.test.ts
[runner] Installing dependencies: corepack yarn install --no-immutable ...
[runner] Running test suite: corepack yarn test ...
[runner] Cleaned up temporary directory.

==================================================
RUNNER SUMMARY
==================================================
Success:      True
Exit Code:    0
Tests Passed: 14/14
Tests Failed: 0
==================================================
```

### Scenario 2: Deliberately Failing Reference
```text
[runner] Copied exercise to temporary directory: /var/folders/1m/z27s7x0d5lv4wbcnbmdwpz4h0000gn/T/r47-t019-88b9b8gr/word-count
[runner] Replaced word-count.ts with reference failing_reference.ts
[runner] Unskipped all tests in word-count.test.ts
[runner] Installing dependencies: corepack yarn install --no-immutable ...
[runner] Running test suite: corepack yarn test ...
[runner] Cleaned up temporary directory.

==================================================
RUNNER SUMMARY
==================================================
Success:      False
Exit Code:    253
Tests Passed: 0/14
Tests Failed: 14
Error:        Test process exited with non-zero code 253
==================================================
```

### Scenario 3: Empty Test Selection
```text
[runner] Copied exercise to temporary directory: /var/folders/1m/z27s7x0d5lv4wbcnbmdwpz4h0000gn/T/r47-t019-1w8xzisx/word-count
[runner] Replaced word-count.ts with reference proof.ci.ts
[runner] Configured empty test selection (all tests commented out)
[runner] Installing dependencies: corepack yarn install --no-immutable ...
[runner] Running test suite: corepack yarn test ...
[runner] Cleaned up temporary directory.

==================================================
RUNNER SUMMARY
==================================================
Success:      False
Exit Code:    255
Tests Passed: 0/0
Tests Failed: 0
Error:        Test process exited with non-zero code 255
==================================================
```
