# Maintenance Notes — two-bucket (R47-T015)

## What the exercise is about

Given two buckets of different sizes and a starting bucket, find the minimum
number of moves to reach an exact water level in one of them.  
Each move is one action: fill a bucket, empty a bucket, or pour one into the other.

---

## The `Bucket` class — O(1) per operation

The `Bucket` class stores two numbers: `size` (capacity) and `amount` (current
water level). Every method just reads or sets those numbers:

| Operation | What it does | Cost |
|-----------|--------------|------|
| `fill()`  | Sets `amount = size` | **O(1)** |
| `empty()` | Sets `amount = 0` | **O(1)** |
| `pourInto(other)` | Computes `Math.min`, updates two numbers | **O(1)** |
| `isFull`, `isEmpty`, `available` | Arithmetic on two numbers | **O(1)** |

There are no loops, no arrays, and no recursion inside `Bucket`. Each call
takes the same tiny amount of time regardless of the bucket size.

---

## `TwoBucket.moves()` — bounded by bucket sizes

The algorithm is a greedy (not BFS) simulation that follows a fixed decision
tree each step:

1. If `first` is empty → fill it.
2. Else if `second` is full → empty it.
3. Else → pour `first` into `second`.

Each move produces a new unique `(first.amount, second.amount)` state.  
Because `first.amount` can be `0..cap1` and `second.amount` can be `0..cap2`,
there are at most `(cap1 + 1) × (cap2 + 1)` possible states.  
The algorithm never revisits a state, so it always terminates within that bound.

**Worst-case moves ≤ (cap1 + 1) × (cap2 + 1)**

In practice the algorithm finds the goal well before that limit.

---

## Operation-count table (canonical test cases)

These inputs come directly from `two-bucket.test.ts`.

| cap1 | cap2 | goal | start | Expected moves | States bound |
|------|------|------|-------|---------------|--------------|
| 3    | 5    | 1    | one   | 4             | (3+1)×(5+1) = 24 |
| 3    | 5    | 1    | two   | 8             | (3+1)×(5+1) = 24 |
| 7    | 11   | 2    | one   | 14            | (7+1)×(11+1) = 96 |
| 7    | 11   | 2    | two   | 18            | (7+1)×(11+1) = 96 |
| 1    | 3    | 3    | two   | 1             | (1+1)×(3+1) = 8  |
| 2    | 3    | 3    | one   | 2             | (2+1)×(3+1) = 12 |
| 5    | 1    | 2    | one   | 6             | (5+1)×(1+1) = 12 |
| 3    | 15   | 9    | one   | 6             | (3+1)×(15+1) = 64 |
| 6    | 15   | 9    | one   | 10            | (6+1)×(15+1) = 112 |

> The actual moves are always much smaller than the states bound —
> the greedy strategy avoids wasted steps.

---

## Valid input constraints

The exercise defines two hard validity rules (enforced in `validate()`):

1. **Goal must be reachable in size:** `goal ≤ max(cap1, cap2)`  
   → If the goal is bigger than both buckets, it can never be held in one bucket.

2. **GCD divisibility:** `goal % gcd(cap1, cap2) === 0`  
   → Water-pouring can only produce amounts that are multiples of the GCD of
   the two sizes. If the goal is not a multiple of that GCD, it is impossible.

Both violations throw an `Error`.

---

## Why we count moves instead of timing wall-clock time

The two-bucket inputs are tiny (bucket sizes are single or double digits).
Running the algorithm takes under a millisecond. The majority of elapsed time
in any benchmark would be **Node.js startup + TypeScript compilation**, not the
algorithm itself. Timing results would therefore reflect the runtime overhead,
not the algorithm's complexity.

Counting `moves` is an honest, repeatable measure of algorithm work that is
independent of machine speed or startup time.

---

## Limitations

- The exercise inputs are small by design; the algorithm is not intended for
  bucket sizes in the millions.
- The greedy strategy works because the water-pouring state space is small
  and acyclic (given the problem constraints). It is not BFS/Dijkstra, so it
  may not generalise to variations of the problem.
- The `validate()` check catches the two mathematically impossible cases;
  other invalid inputs (e.g., negative sizes) are not explicitly handled.

---

## Verification

Run the automated check to confirm all tests pass with the reference solution:

```bash
python3 work/R47-T015/check.py
```
