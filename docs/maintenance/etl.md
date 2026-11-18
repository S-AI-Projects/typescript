# ETL: Mutation-Driven Regression & Maintenance Guide

## Overview

The `etl` (Extract-Transform-Load) exercise requires transforming a legacy scoring format mapping point values (as keys) to arrays of uppercase letters into a modern format mapping individual lowercase letters to their integer point values:
- **Legacy input**: `{ "1": ["A", "E"], "2": ["D", "G"] }`
- **Modern output**: `{ "a": 1, "d": 2, "e": 1, "g": 2 }`

All 4 canonical test cases are included and verified against the reference implementation (`.meta/proof.ci.ts`).

---

## Mutation Experiment

To verify that the test suite is sensitive to logical regressions in output construction and case normalization, we performed a mutation-driven regression test.

### 1. Deliberate Mutation
In `.meta/proof.ci.ts`, key normalization is implemented via:
```typescript
phase1[each.toLowerCase()] = Number.parseInt(key, 10)
```
The mutant deliberately omits `.toLowerCase()`, directly using the raw letter key from the legacy input array:
```typescript
phase1[each] = Number.parseInt(key, 10)
```
This simulates a common learner mistake: extracting and transposing the keys without normalizing letters to lowercase.

### 2. Rejecting Canonical Test Case
- **Test ID (UUID)**: `78a7a9f9-4490-4a47-8ee9-5a38bb47d28f`
- **Canonical Description**: `"single letter"`
- **Test Name in `etl.test.ts`**: `"transforms one value"`

### 3. Minimal Input
- **Input**:
  ```json
  { "1": ["A"] }
  ```

### 4. Expected vs Mutated Behavior
- **Expected Output**:
  ```json
  { "a": 1 }
  ```
- **Actual Mutated Output**:
  ```json
  { "A": 1 }
  ```
- **Failure Message**:
  ```text
  expect(received).toEqual(expected) // deep equality

  - Expected  - 1
  + Received  + 1

    Object {
  -   "a": 1,
  +   "A": 1,
    }
  ```

### 5. Suite-wide Rejection
In addition to the minimal test case, all 4 test cases in `etl.test.ts` fail against this mutant because all uppercase characters in test fixtures remain unconverted.

---

## Canonical Test Suite Mapping (4 Cases)

| UUID | Canonical Description | Test Name in `etl.test.ts` | Status |
| :--- | :--- | :--- | :---: |
| `78a7a9f9-4490-4a47-8ee9-5a38bb47d28f` | single letter | transforms one value | Included |
| `60dbd000-451d-44c7-bdbb-97c73ac1f497` | single score with multiple letters | transforms more values | Included |
| `f5c5de0c-301f-4fdd-a0e5-df97d4214f54` | multiple scores with multiple letters | transforms more keys | Included |
| `5db8ea89-ecb4-4dcd-902f-2b418cc87b9d` | multiple scores with differing numbers of letters | transforms a full dataset | Included |

---

## Conclusion
The test suite immediately and strictly rejects mutations that fail to lowercase the letters, starting from the single-element boundary case. The reference implementation correctly passes all tests.
