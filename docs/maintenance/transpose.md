# Maintenance: Transpose Mutation-Driven Regression

This document records the deliberate logic mutation of the `transpose` reference implementation, the canonical test case that rejects it, and the minimal diagnostic example.

## 1. The Transpose Contract

According to `exercises/practice/transpose/.docs/instructions.md`:
- Input lines become columns, and input columns become rows.
- If input rows have different lengths:
  - **Pad to the left with spaces** (to preserve column alignment).
  - **Do not pad to the right** (no trailing padding spaces).

## 2. Reference Implementation

In `.meta/proof.ci.ts`:

```typescript
const fillColumn: (t: string[], l: string, r: number) => void = (
  transposed,
  fromSource,
  toColumn
) => {
  for (let row = 0; row < fromSource.length; row++) {
    transposed[row] =
      (row in transposed ? transposed[row] : '').padEnd(toColumn) +
      fromSource.charAt(row)
  }
}

export function transpose(lines: string[]): string[] {
  const transposed: string[] = []
  for (let toColumn = 0; toColumn < lines.length; toColumn++)
    fillColumn(transposed, lines[toColumn], toColumn)

  return transposed
}
```

The key operation is `.padEnd(toColumn)`. When line `toColumn` has a character at row index `row`, but an earlier line was shorter and had no character at that row, `.padEnd(toColumn)` fills the intermediate positions with spaces up to index `toColumn`.

## 3. The Deliberate Logic Mutation

The mutant simulates a common learner mistake: directly concatenating characters to `transposed[row]` without left-padding.

```typescript
// Mutated fillColumn (omits .padEnd(toColumn))
const fillColumn: (t: string[], l: string, r: number) => void = (
  transposed,
  fromSource,
  toColumn
) => {
  for (let row = 0; row < fromSource.length; row++) {
    transposed[row] =
      (row in transposed ? transposed[row] : '') +
      fromSource.charAt(row)
  }
}
```

### Why this mutant is subtle:
- It passes `empty string`, `two characters in a row`, and `two characters in a column`.
- It passes `simple`, `single line`, `square`, and `rectangle`.
- It even passes `first line longer than second line` because earlier rows already exist when the second line is processed.

## 4. Rejecting Canonical Test Case

The mutant is rejected by the test suite when a later line is longer than an earlier line:

- **Test Name**: `second line longer than first line`
- **Canonical UUID / Test ID**: `984e2ec3-b3d3-4b53-8bd6-96f5ef404102`
- **Input**:
  ```typescript
  [
    'The first line.',   // length 15 (indices 0..14)
    'The second line.'   // length 16 (indices 0..15)
  ]
  ```
- **Expected Behavior**:
  At row index 15, Line 0 has no character while Line 1 has `'.'`. The output row must be padded with a space at column 0:
  ```typescript
  expected[15] === ' .'  // length 2
  ```
- **Mutant Behavior**:
  The mutant does not apply left-padding and produces:
  ```typescript
  received[15] === '.'   // length 1 (missing leading space)
  ```
- **Result**: Jest assertion fails with deep equality mismatch on `expected[15]`.

## 5. Minimal Diagnostic Test Case

The smallest test case that distinguishes the correct implementation from the mutant is:

- **Input**:
  ```typescript
  ['A', 'BC']
  ```
- **Expected Output**:
  ```typescript
  ['AB', ' C']
  ```
- **Mutant Output**:
  ```typescript
  ['AB', 'C']
  ```

## 6. Automated Verification

Run the automated verification script:

```bash
python3 work/R47-T013/check.py
```

This script:
1. Runs all 12 test cases against the original reference implementation (all 12 pass).
2. Runs all 12 test cases against the mutated reference implementation (verifying that `second line longer than first line` fails).
3. Verifies that the original learner stub (`transpose.ts`) remains unsolved.
4. Records evidence in `work/R47-T013/evidence.md`.
