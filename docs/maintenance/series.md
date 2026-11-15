# Series — cost of the reference implementation (R47-T045)

Maintainer notes for `exercises/practice/series`, prepared by Advait
Bodkhe for task R47-T045 (issue #45). This page explains what
`Series.slices()` costs and backs the statement with measurements.

## Input size

For this exercise the input size is **n = the number of digits** in the
series string, and **k = the slice length** passed to `slices()`. Both
are defined by the exercise itself (a series is a string of digits;
`1 ≤ k ≤ n` or the call throws).

## Operation count (exact, from the code)

- Constructor: converts the string to an array of digits once — Θ(n).
- `slices(k)`: the outer loop runs `n − k + 1` times and the inner loop
  copies `k` digits per slice, so it performs exactly
  `(n − k + 1) · k` digit copies — which is also exactly the number of
  elements in the returned array of arrays. The algorithm does no work
  beyond building its output.
- Consequences: for a **fixed k**, the cost is linear in n. When **k
  grows with n** — worst case `k ≈ n / 2` — the cost is quadratic in n
  (≈ n²/4 copies).

The same statement is recorded as a comment on the reference in
`exercises/practice/series/.meta/proof.ci.ts`.

## Measurements

Method: `work/R47-T045/benchmark.mjs` (the reference with types
stripped; algorithm unchanged). Correctness against the exercise's own
cases is asserted before any timing. Each figure is the median of 7
repetitions of a single `slices()` call, measured with
`performance.now()` around the call only — process start-up, module
loading and construction are excluded. Inputs are the repeating digit
pattern `1234567890…` truncated to n digits. Node v24.22.1.

Fixed slice length, k = 5:

| n | slices returned | elements copied | median | min |
| --- | --- | --- | --- | --- |
| 1,000 | 996 | 4,980 | 0.111 ms | 0.054 ms |
| 10,000 | 9,996 | 49,980 | 1.360 ms | 0.851 ms |
| 100,000 | 99,996 | 499,980 | 27.049 ms | 5.511 ms |

Slice length half the series, k = n / 2:

| n | k | slices returned | elements copied | median | min |
| --- | --- | --- | --- | --- | --- |
| 200 | 100 | 101 | 10,100 | 0.072 ms | 0.070 ms |
| 2,000 | 1,000 | 1,001 | 1,001,000 | 7.321 ms | 5.558 ms |
| 8,000 | 4,000 | 4,001 | 16,004,000 | 240.933 ms | 133.876 ms |

## Reading the numbers — and their limits

The element counts are exact and grow precisely as the formula says:
×10 per step at fixed k, and ×~100 then ×16 in the half-length table,
matching the (n − k + 1) · k growth. The wall-clock times grow at
least as fast as the element counts, and at the largest sizes they grow
faster than the counts alone (allocation and garbage-collection
pressure on the shared machine used for the measurement). So the
supported conclusion is the operation-count one: **the work is
Θ((n − k + 1) · k), i.e. linear in n for fixed k and quadratic when k
scales with n**. No constant factor, and no claim about other machines
or runtimes, is made — re-run `benchmark.mjs` to get figures for a
different environment. Raw output of the run above is saved in
`work/R47-T045/benchmark-results.json`.

## Verification

```bash
python3 work/R47-T045/check.py
```

All 11 enabled exercise cases pass against the reference (which now
carries the cost comment), and the check re-runs the benchmark,
including its correctness assertions. Evidence is in `work/R47-T045/`.
