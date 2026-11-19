# Hints

## Understanding the strain contract through examples

The `strain` exercise asks you to implement `keep` and `discard` operations on collections without using built-in array filtering methods (such as `Array.prototype.filter`).

In TypeScript, both functions operate over generic collections:
- **Input Array:** `array: T[]` (an array of elements of any type `T`).
- **Predicate Function:** `predicate: (element: T) => boolean` (a callback invoked for each element returning `true` or `false`).
- **Return Value:** `T[]` (a newly constructed array containing the retained elements).

### The Three Fundamental Canonical Examples

The behavior of `keep` is defined by three foundational boundary cases in the test suite:

#### Example 1: Empty Array (`keeps on empty array returns empty array`)
- **Input Array:** `[]` (empty array of numbers)
- **Predicate:** `(_: number): boolean => true` (returns `true` unconditionally)
- **Invocation:** `keep<number>([], predicate)`
- **Expected Output:** `[]`
- **Explanation:** When the input collection contains zero elements, there are no items to evaluate or retain. The function must return a new, empty array without attempting to access nonexistent elements.

#### Example 2: Retaining Everything (`keeps everything`)
- **Input Array:** `[1, 3, 5]`
- **Predicate:** `(_: number): boolean => true` (returns `true` for all elements)
- **Invocation:** `keep<number>([1, 3, 5], predicate)`
- **Expected Output:** `[1, 3, 5]`
- **Explanation:** The predicate evaluates to `true` for each element in sequence (`1`, `3`, and `5`). Every element satisfies the retention condition, so all elements are included in the output in their original iteration order.

#### Example 3: Retaining Nothing (`keeps nothing`)
- **Input Array:** `[1, 3, 5]`
- **Predicate:** `(_: number): boolean => false` (returns `false` for all elements)
- **Invocation:** `keep<number>([1, 3, 5], predicate)`
- **Expected Output:** `[]`
- **Explanation:** The predicate evaluates to `false` for every element (`1`, `3`, and `5`). Zero elements satisfy the retention condition, so the resulting array is empty.

---

### Decision Table

The relationship between the input collection, predicate evaluation, and output contract is summarized below:

| Case | Input Condition | Predicate Evaluation | Output | Specification Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Empty Input** | `[]` (empty collection) | Any predicate (`_ => true`) | `[]` | With 0 input elements, no predicate invocations produce items to retain; returns a fresh empty array. |
| **Keeps Everything** | `[1, 3, 5]` (non-empty) | Accepts every item (`_ => true`) | `[1, 3, 5]` | Every element produces `true`; all elements are retained, preserving original sequence order. |
| **Keeps Nothing** | `[1, 3, 5]` (non-empty) | Rejects every item (`_ => false`) | `[]` | Every element produces `false`; no elements qualify for retention, yielding an empty array. |

---

### Specified vs. Unspecified Behavior

When implementing `strain`, keep the contract strictly aligned with the canonical specifications:

- **Specified Behavior:**
  - `keep` includes an element if and only if `predicate(element) === true`.
  - `discard` includes an element if and only if `predicate(element) === false` (or `!predicate(element)`).
  - The relative order of retained elements in the output array matches their original sequence in the input array.
  - The function must return a *new* collection rather than mutating the input array in place.
- **Unspecified Behavior (Do Not Assume):**
  - No error handling or exception throwing is required for empty arrays.
  - No type coercion of elements is specified; generic types `T` are preserved without alteration.
  - Behavior on mutated arrays or asynchronous predicates is outside the exercise contract.
