# Strain Contract Decision Table

This decision table documents the input conditions, predicate behaviors, expected outputs, and specification rationale for the three fundamental boundary cases in `exercises/practice/strain`.

---

## Canonical Cases Decision Table

| Case | Canonical Description | Input Array | Predicate Behavior | Return Output | Specification Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Case 1** | `keeps on empty array returns empty array` | `[]` | `(_: number): boolean => true` | `[]` | When the input collection contains zero elements, there are no items to evaluate or retain. The result is an empty array. |
| **Case 2** | `keeps everything` | `[1, 3, 5]` | `(_: number): boolean => true` | `[1, 3, 5]` | When the predicate accepts every element, every element is retained in original sequential order. |
| **Case 3** | `keeps nothing` | `[1, 3, 5]` | `(_: number): boolean => false` | `[]` | When the predicate rejects every element, zero elements are retained, producing an empty array. |

---

## Contract Guarantees and Invariants

1. **Pure Function Contract:** Neither `keep` nor `discard` mutates the input array. A new array instance is returned in every invocation.
2. **Order Preservation:** Retained elements appear in the output array in the exact relative order of their original indices.
3. **Generics Preservation:** The generic type parameter `T` is preserved across inputs and outputs without type coercion.
4. **Boundary Invariant:** An empty array input always produces an empty array output regardless of predicate logic.
