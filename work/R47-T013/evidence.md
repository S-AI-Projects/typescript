# Verification Evidence: Transpose (Issue #13 — R47-T013)

## Environment
- **Python Version**: 3.9.6 (default, May 22 2026, 11:13:45)  [Clang 21.0.0 (clang-2100.1.1.101)]
- **Node.js Version**: v26.8.2
- **Yarn Version**: 4.5.1

## Test Execution Comparison

| Metric | Original Reference | Mutated Reference |
|---|---|---|
| Exit Code | `0` (Success) | `253` (Failed as expected) |
| Tests Passed | 12 / 12 | 8 / 12 |
| 'empty string' | PASSED | PASSED |
| 'two characters in a row' | PASSED | PASSED |
| 'two characters in a column' | PASSED | PASSED |
| 'second line longer than first line' | PASSED | **FAILED** (Caught mutation) |
| 'triangle' | PASSED | FAILED |
| 'jagged triangle' | PASSED | FAILED |
| 'test many lines' | PASSED | FAILED |

## Rejecting Test Case Details
- **Test Name**: `second line longer than first line`
- **Canonical UUID**: `984e2ec3-b3d3-4b53-8bd6-96f5ef404102`
- **Input**:
  ```typescript
  ['The first line.', 'The second line.']
  ```
- **Expected Output at row 15**: `' .'` (space + dot)
- **Mutant Output at row 15**: `'.'` (missing leading space)

## Minimal Diagnostic Input
- **Input**: `['A', 'BC']`
- **Expected**: `['AB', ' C']`
- **Mutant**: `['AB', 'C']`

## Output Logs (Mutant Run Excerpt)
```text
FAIL ./transpose.test.ts
  Transpose
    ✓ empty string
    ✓ two characters in a row
    ✓ two characters in a column
    ✓ simple
    ✓ single line
    ✓ first line longer than second line
    ✕ second line longer than first line
    ✓ square
    ✓ rectangle
    ✕ triangle
    ✕ jagged triangle
    ✕ test many lines
```
