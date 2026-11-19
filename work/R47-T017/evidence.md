# Evidence — R47-T017 (resistor-color)

## Tool Versions
- Python: Python 3.9.6
- Node.js: v26.8.2
- Yarn: 4.5.1

## Selected TypeScript Concept
**Runtime vs. Static Validation**

The `colorCode(color: string): number` implementation relies on static type checking to ensure callers pass a `string`, while actual validation of colors against the resistor array occurs at runtime via `COLORS.indexOf(color)`. Union narrowing and readonly inputs are not used.

## Expected vs. Actual Results

| Case | Input | Expected Output | Actual Output | Status |
| --- | --- | --- | --- | --- |
| Black | `'black'` | `0` | `0` | PASS |
| White | `'white'` | `9` | `9` | PASS |
| Orange | `'orange'` | `3` | `3` | PASS |
| Hint Example 1 (Valid) | `'north'` | `0` | `0` | PASS |
| Hint Example 2 (Invalid) | `'up'` | `-1` | `-1` | PASS |

## Test Execution Summary
- Exit Code: 0
- Tests Passed: 9
- Tests Total: 9
- Tests Failed: 0
- All Probes Verified: True

## Full Test Runner Output
```text
[tests] tsc: ✅, tstyche: ❌, jest: ✅, 
[tests] tsc (compile)
[tests] tstyche (implementation tests)
  console.log
    [PROBE] Black -> expected: 0, actual: 0

      at Object.log (r47-t017.probe.test.ts:14:15)

  console.log
    [PROBE] White -> expected: 9, actual: 9

      at Object.log (r47-t017.probe.test.ts:20:15)

  console.log
    [PROBE] Orange -> expected: 3, actual: 3

      at Object.log (r47-t017.probe.test.ts:26:15)

  console.log
    [PROBE] Hint Example 1 (north) -> expected: 0, actual: 0

      at Object.log (r47-t017.probe.test.ts:34:15)

  console.log
    [PROBE] Hint Example 2 (up) -> expected: -1, actual: -1

      at Object.log (r47-t017.probe.test.ts:40:15)

PASS ./resistor-color.test.ts
  color code
    ✓ Black (4 ms)
    ✓ White
    ✓ Orange (1 ms)
  Colors
    ✓ returns all colors

PASS ./r47-t017.probe.test.ts
  R47-T017 Verification Probes
    Resistor Color Cases
      ✓ verifies Black case (23 ms)
      ✓ verifies White case (2 ms)
      ✓ verifies Orange case (1 ms)
    Hints Example Cases (Runtime vs Static Validation)
      ✓ verifies hint Example 1 (valid input: north) (1 ms)
      ✓ verifies hint Example 2 (invalid input: up) (1 ms)

Test Suites: 2 passed, 2 total
Tests:       9 passed, 9 total
Snapshots:   0 total
Time:        0.75 s
Ran all test suites.
```
