# Evidence — R47-T020 (Flatten Array Validation)

## Tool Versions
- Python: Python 3.9.6
- Node.js: v26.8.2
- Yarn: 4.5.1

## Core Walkthrough Cases (.docs/hints.md)

1. **Empty Array:** `[]` $\to$ `[]` (no elements to flatten or filter)
2. **No Nesting:** `[0, 1, 2]` $\to$ `[0, 1, 2]` (already flat, defined scalar values preserved)
3. **Nested Empty Array:** `[[[]]]` $\to$ `[]` (nested empty levels unwrap to an empty array)

## Test Cases Summary

| Case | Input | Expected Output | Actual Output | Status |
| --- | --- | --- | --- | --- |
| empty | `[]` | `[]` | `[]` | PASS |
| no nesting | `[0, 1, 2]` | `[0, 1, 2]` | `[0, 1, 2]` | PASS |
| flattens a nested array | `[[[]]]` | `[]` | `[]` | PASS |
| flattens array with just integers present | `[1, [2, 3, 4, 5, 6, 7], 8]` | `[1, 2, 3, 4, 5, 6, 7, 8]` | `[1, 2, 3, 4, 5, 6, 7, 8]` | PASS |
| 5 level nesting | `[0, 2, [[2, 3], 8, 100, 4, [[[50]]]], -2]` | `[0, 2, 2, 3, 8, 100, 4, 50, -2]` | `[0, 2, 2, 3, 8, 100, 4, 50, -2]` | PASS |
| 6 level nesting | `[1, [2, [[3]], [4, [[5]]], 6, 7], 8]` | `[1, 2, 3, 4, 5, 6, 7, 8]` | `[1, 2, 3, 4, 5, 6, 7, 8]` | PASS |
| consecutive null values at the front | `[undefined, undefined, 3]` | `[3]` | `[3]` | PASS |
| consecutive null values in the middle | `[1, undefined, undefined, 4]` | `[1, 4]` | `[1, 4]` | PASS |
| 6 level nest array with null values | `[0, 2, [[2, 3], 8, [[100]], undefined, [[undefined]]], -2]` | `[0, 2, 2, 3, 8, 100, -2]` | `[0, 2, 2, 3, 8, 100, -2]` | PASS |
| all values in nested array are null | `[undefined, [[[undefined]]], undefined, undefined, [[undefined, undefined], undefined], undefined]` | `[]` | `[]` | PASS |

## Test Run Summary
- Process Exit Code: 0
- Tests Reported Total: 10
- Tests Passed: 10
- Tests Failed: 0
- Zero Tests Failure Check: PASSED (ran > 0 tests)
- Overall Validation: SUCCESS

## Full Test Runner Output
```text
[tests] tsc: ✅, tstyche: ❌, jest: ✅, 
[tests] tsc (compile)
[tests] tstyche (implementation tests)

PASS ./flatten-array.test.ts
  Flatten Array
    ✓ empty (2 ms)
    ✓ no nesting
    ✓ flattens a nested array
    ✓ flattens array with just integers present (1 ms)
    ✓ 5 level nesting
    ✓ 6 level nesting
    ✓ consecutive null values at the front of the array are omitted from the final result
    ✓ consecutive null values in the middle of the array are omitted from the final result
    ✓ 6 level nest array with null values (1 ms)
    ✓ all values in nested array are null

Test Suites: 1 passed, 1 total
Tests:       10 passed, 10 total
Snapshots:   0 total
Time:        0.397 s
Ran all test suites.
```
