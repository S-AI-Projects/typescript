# Maintenance Guide: list-ops

## Overview
- Exercise: `exercises/practice/list-ops`
- Reference implementation: `exercises/practice/list-ops/.meta/proof.ci.ts`
- Starter stub: `exercises/practice/list-ops/list-ops.ts`
- Test suite: `exercises/practice/list-ops/list-ops.test.ts`
- Canonical case configuration: `exercises/practice/list-ops/.meta/tests.toml`

The `list-ops` exercise requires implementing fundamental list operations (append, concatenate, filter, length, map, foldl, foldr, reverse) without using built-in JavaScript `Array` prototype methods or array literals.

## Deliberate Mutant: Cons.append Boundary Condition

To verify suite sensitivity, we define a scoped mutant in `Cons.append`:

### Mutant Implementation
```typescript
// Located in Cons class in proof.ci.ts
public append(other: Cons<T>): Cons<T> {
  // Deliberate mutant: incorrectly returns 'other' if other is empty
  if (other.length() === 0) {
    return other
  }
  return other.foldl((result, item) => result.push(item), this)
}
```

### Mistaken Assumption
The mutant mistakenly assumes that appending an empty list returns an empty list, confusing the left/right identity properties of monoidal concatenation ($L + \emptyset = L$, not $\emptyset$).

### Rejecting Test Case
- **Test Suite:** `append entries to a list and return the new list`
- **Test Name:** `empty list to list`
- **Input:**
  ```typescript
  const list1 = List.create(1, 2, 3, 4)
  const list2 = List.create<number>()
  const result = list1.append(list2)
  ```
- **Expected Outcome:** `result` equals `list1` (elements `[1, 2, 3, 4]`).
- **Mutant Actual Outcome:** `result` equals `list2` (empty list `[]`).
- **Assertion:** `expect(list1.append(list2)).toEqual(list1)` fails with mismatched length and values.
- **Minimal Reduced Counterexample:** `List.create(1).append(List.create())` produces `[]` instead of `[1]`.

## Verification & Commands

Run the exercise test suite against the original reference:
```bash
corepack yarn node scripts/pr.mjs exercises/practice/list-ops
```
Run the automated check verifying that the original passes and the mutant is rejected:
```bash
python3 work/R47-T003/check.py
```
