# Hints

## Walkthrough of Core Cases

The goal of this exercise is to take an array of arbitrary nesting depth and return a single, fully flattened array containing all values except `null` and `undefined`.

Here is a walkthrough of three fundamental test cases from the test suite:

### 1. Empty Array: `[]` → `[]`
- **Input:** `[]`
- **Output:** `[]`
- **Why this is correct:** The input contains zero elements. Flattening an empty list yields an empty list with no values to extract or filter out.

### 2. Array With No Nesting: `[0, 1, 2]` → `[0, 1, 2]`
- **Input:** `[0, 1, 2]`
- **Output:** `[0, 1, 2]`
- **Why this is correct:** The array is already one-dimensional (completely flat) and all elements (`0`, `1`, `2`) are defined, non-null values. Because there are no inner arrays to unwrap and no null-like values to exclude, the elements are preserved in their original order.

### 3. Nested Empty Array: `[[[]]]` → `[]`
- **Input:** `[[[]]]`
- **Output:** `[]`
- **Why this is correct:** The input consists of nested boxes within boxes, but none of the inner arrays contain any values. When recursively unwrapping each layer of nesting, there are no scalar values present, resulting in a flat empty array `[]`.

---

## Key Approaches

- **Recursion / Reduction:** You can iterate through each item in the array. If an item is an array (`Array.isArray(item)`), recursively flatten it and combine it with your accumulator. If it is an individual value, append it directly.
- **Filtering:** Ensure any `null` or `undefined` values are omitted from the final flattened array.
