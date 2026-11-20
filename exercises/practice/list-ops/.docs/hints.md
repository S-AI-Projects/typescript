# Hints

## General

- Remember that you must not use JavaScript's built-in `Array` methods (`push`, `map`, `filter`, `reduce`, etc.) or array literals in your core list implementation.
- Consider treating an empty list as a base/terminal case or distinct structure (often called `Nil` or `Null`) and non-empty elements as nodes linking head elements to tail lists.

## Appending Lists

### Identity Element Pitfall
When appending one list to another (`list1.append(list2)`):
- Appending an empty list to any non-empty list must preserve the original elements ($L + \emptyset = L$).
- A common mistaken assumption is prematurely returning the second list argument `list2` whenever it is empty. If your implementation checks whether `list2` has length 0 and returns `list2`, it will discard all existing elements in `list1`.

### Diagnostic Check
If tests fail on cases like `empty list to list`, trace the behavior on a minimal input:
```typescript
const list1 = List.create(1)
const list2 = List.create()
const result = list1.append(list2)
// Expected: result has elements [1]
// Buggy outcome: result has elements []
```
Ensure that when `list2` has no items to add, the original `list1` is returned intact rather than returning the empty target.
