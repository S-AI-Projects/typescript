# Evidence — R47-T015 two-bucket

## Tool versions
- Python : Python 3.9.6
- Node.js : v26.8.2
- Yarn    : 4.5.1

## Test run summary
- Tests passed : 11
- Tests total  : 11
- Exit code    : 0

## Complexity summary
Each `Bucket` operation (fill, empty, pourInto) is **O(1)** — it updates
a single numeric field with no loops.

`TwoBucket.moves()` terminates in at most **(cap1+1) × (cap2+1)** moves.
Actual move counts for canonical cases:

| cap1 | cap2 | goal | start | moves |
|------|------|------|-------|-------|
| 3    | 5    | 1    | one   | 4     |
| 3    | 5    | 1    | two   | 8     |
| 7    | 11   | 2    | one   | 14    |
| 7    | 11   | 2    | two   | 18    |
| 1    | 3    | 3    | two   | 1     |
| 2    | 3    | 3    | one   | 2     |
| 5    | 1    | 2    | one   | 6     |
| 3    | 15   | 9    | one   | 6     |
| 6    | 15   | 9    | one   | 10    |

## Full test output
```
[tests] tsc: ✅, tstyche: ❌, jest: ✅, 
[tests] tsc (compile)
[tests] tstyche (implementation tests)
PASS ./two-bucket.test.ts
  TwoBucket
    Measure using bucket one of size 3 and bucket two of size 5
      ✓ start with bucket one (2 ms)
      ✓ start with bucket two (1 ms)
    Measure using bucket one of size 7 and bucket two of size 11
      ✓ start with bucket one
      ✓ start with bucket two
    Measure one step using bucket one of size 1 and bucket two of size 3
      ✓ start with bucket two (1 ms)
    Measure using bucket one of size 2 and bucket two of size 3
      ✓ start with bucket one and end with bucket two
    Very different sizes
      ✓ measure using bucket one much bigger than bucket two
      ✓ measure using bucket one much smaller than bucket two
    Reachability
      ✓ Not possible to reach the goal (5 ms)
      ✓ With the same buckets but a different goal, then it is possible (1 ms)
    Goal larger than both buckets
      ✓ Is impossible

Test Suites: 1 passed, 1 total
Tests:       11 passed, 11 total
Snapshots:   0 total
Time:        0.408 s
Ran all test suites.
```
