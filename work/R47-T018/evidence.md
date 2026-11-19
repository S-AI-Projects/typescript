# Evidence — R47-T018 (Diamond)

## Tool Versions
- Python: Python 3.9.6
- Node.js: v26.8.2
- Yarn: 4.5.1

## 1. Metadata Verification (tools/course_checks/r47-t018.py)

The check script validates that every file declared in `.meta/config.json` exists within the exercise directory and does not escape it.

| Check Case | Description | Expected Result | Actual Result | Status |
| --- | --- | --- | --- | --- |
| Case 1: Missing Reference | `.meta/non_existent_proof.ci.ts` | Rejected (file missing) | Rejected with error | PASS |
| Case 2: Missing Test | `missing_diamond.test.ts` | Rejected (file missing) | Rejected with error | PASS |
| Case 3: Outside Exercise | `../diamond.ts` | Rejected (escapes folder) | Rejected with error | PASS |
| Real Metadata | Declared `diamond.ts`, `diamond.test.ts`, `.meta/proof.ci.ts` | Pass | All files exist within folder | PASS |

### Course Check Output
```text
==================================================
Diamond Exercise Metadata File Check (R47-T018)
==================================================
Exercise Directory: /Users/sparsh/Desktop/Project S&Ai/typescript/exercises/practice/diamond
Config File:        /Users/sparsh/Desktop/Project S&Ai/typescript/exercises/practice/diamond/.meta/config.json
Declared files: {
  "solution": [
    "diamond.ts"
  ],
  "test": [
    "diamond.test.ts"
  ],
  "example": [
    ".meta/proof.ci.ts"
  ]
}

--- Running Synthetic Negative Test Cases ---
✅ Case 1 Passed: Correctly rejected missing reference file.
   Reason: Declared file missing on disk in category 'example': .meta/non_existent_proof.ci.ts
✅ Case 2 Passed: Correctly rejected missing test file.
   Reason: Declared file missing on disk in category 'test': missing_diamond.test.ts
✅ Case 3 Passed: Correctly rejected outside-exercise path.
   Reason: Path escapes exercise directory in category 'solution': ../diamond.ts

--- Validating Real Exercise Metadata ---
✅ Real metadata passed all checks:
   - solution: diamond.ts (exists, within exercise)
   - test: diamond.test.ts (exists, within exercise)
   - example: .meta/proof.ci.ts (exists, within exercise)

==================================================
RESULT: ALL METADATA CHECKS PASSED SUCCESSFULLY
==================================================
```

## 2. Test Execution with Reference Implementation

- Exit Status: 0
- Tests Passed: 3
- Tests Total: 3
- Tests Failed: 0
- At Least One Test Ran: True

### Canonical Test Cases Verified

| Letter | Expected Shape Description | Result |
| --- | --- | --- |
| `'A'` | Single letter `'A\n'` | PASS |
| `'C'` | 5x5 diamond (A, B, C, B, A) with padding | PASS |
| `'E'` | 9x9 diamond (A, B, C, D, E, D, C, B, A) with padding | PASS |

### Full Test Runner Output
```text
[tests] tsc: ✅, tstyche: ❌, jest: ✅, 
[tests] tsc (compile)
[tests] tstyche (implementation tests)
PASS ./diamond.test.ts
  Make diamond function
    ✓ test letter A (1 ms)
    ✓ test letter C
    ✓ test letter E

Test Suites: 1 passed, 1 total
Tests:       3 passed, 3 total
Snapshots:   0 total
Time:        0.427 s
Ran all test suites.
```
