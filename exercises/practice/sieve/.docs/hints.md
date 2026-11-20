# Hints

## General

- Return an array of all prime numbers from `2` up to and **including** `limit`, with each prime appearing **exactly once** in ascending order.
- If `limit < 2`, there are no prime numbers, so return `[]`.

## Debugging boundary and loop-overlap issues

- **Inclusive upper bound (`<= limit`)**: When marking multiples of a prime `p` (for example starting at `p * p` and stepping by `p`), make sure the loop condition includes `limit` itself (`multiple <= limit`, not `multiple < limit`). An off-by-one `< limit` leaves composite numbers equal to `limit` unmarked.
  - **Diagnostic check**: Try `primes(9)`. Because `9 = 3 * 3`, an exclusive upper bound fails to cross out `9` and returns `[2, 3, 5, 7, 9]` instead of `[2, 3, 5, 7]`.
- **No overlapping candidate and collection ranges**: If you stop marking multiples once `candidate * candidate > limit` (i.e., `candidate > Math.floor(Math.sqrt(limit))`) and then collect remaining unmarked numbers in a second loop, start the second loop _after_ the last candidate checked in the first loop so the boundary value is not collected twice.
  - **Diagnostic check**: Try `primes(5)`. `Math.floor(Math.sqrt(5)) + 1` is `3` (which is prime), so overlapping loops emit `3` twice (`[2, 3, 3, 5]`) instead of the expected `[2, 3, 5]`.
