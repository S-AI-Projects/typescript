# Maintenance Notes: `darts`

## Purpose

This document analyses the time and space cost of `score(x, y)` in `exercises/practice/darts/.meta/proof.ci.ts`. Because the input is a fixed pair of scalar coordinates `(x, y)` rather than a variable-length collection, there is no scaling curve in `N`; instead, cost is bounded by an exact `O(1)` operation count per call.

## Supported Input Domain

- Per `exercises/practice/darts/.docs/instructions.md:19`, `x` and `y` are real Cartesian coordinates, typed as `number` in `score(x: number, y: number): number` (`proof.ci.ts:3`).
- `number` in TypeScript/JavaScript is an IEEE-754 double-precision float (`Infinity`, `-Infinity`, `NaN` are statically permitted by `number`; `NaN` makes every `>` comparison `false` and falls through to `return 10`).

## Branch and Operation Table

Every path executes `Math.sqrt(x * x + y * y)` (`proof.ci.ts:5`) once before branching on strict `>` comparisons (`proof.ci.ts:8,12,16`):

| Region (points) | Representative case                       | Multiplications | Additions | `Math.sqrt` calls | Comparisons executed | Return statement               |
| --------------- | ----------------------------------------- | --------------- | --------- | ----------------- | -------------------- | ------------------------------ |
| `0`             | `"Missed target"` (`score(-9, 9)`)        | `2`             | `1`       | `1`               | `1`                  | `return 0` (`proof.ci.ts:9`)   |
| `1`             | `"On the outer circle"` (`score(0, 10)`)  | `2`             | `1`       | `1`               | `2`                  | `return 1` (`proof.ci.ts:13`)  |
| `5`             | `"On the middle circle"` (`score(-5, 0)`) | `2`             | `1`       | `1`               | `3`                  | `return 5` (`proof.ci.ts:17`)  |
| `10`            | `"On the inner circle"` (`score(0, -1)`)  | `2`             | `1`       | `1`               | `3`                  | `return 10` (`proof.ci.ts:19`) |

- **Time complexity**: `O(1)` — `2` multiplications, `1` addition, `1` `Math.sqrt`, and `1`–`3` strict `>` comparisons.
- **Space complexity**: `O(1)` — scalar locals only (`distanceToDart`).

## Timing Measurements (Separated from Startup and Compilation)

**Method** (constant environment: `Node v24.22.1`, `TypeScript 5.6.3`, `Darwin 27.2.0 arm64`):

1. Assert correctness on all four representative inputs (`(-9, 9) -> 0`, `(0, 10) -> 1`, `(-5, 0) -> 5`, `(0, -1) -> 10`) before timing.
2. Measure TypeScript single-file compilation (`tsc --target es2020 --module nodenext --strict`) and cold Node startup (`node -e 0`) separately from the algorithm loop.
3. Inside a single Node process, warm up `100,000` calls per input, then time `N = 1,000,000` calls across `7` repetitions per input using `process.hrtime.bigint()`, accumulating return values into `sink` to prevent dead-code elimination, and report the median `ns/call`.

**Recorded sample measurement** (live run metrics from each check invocation are written to `work/R47-T035/operation-counts-and-timing.json`):

- `tsc` single-file compile time (separate): `1128.548 ms`
- Cold Node process startup time (separate): `20.662 ms`
- Algorithm loop medians (`7` reps × `1,000,000` calls inside one Node process):

| Region (points)                | Input     | Median (`ns/call`) |
| ------------------------------ | --------- | ------------------ |
| `0` (`"Missed target"`)        | `(-9, 9)` | `0.577`            |
| `1` (`"On the outer circle"`)  | `(0, 10)` | `0.705`            |
| `5` (`"On the middle circle"`) | `(-5, 0)` | `0.705`            |
| `10` (`"On the inner circle"`) | `(0, -1)` | `0.693`            |

All four branches execute in sub-nanosecond constant time once V8 JIT-compiles `score`; process startup and TypeScript compilation dominate single-invocation latency by orders of magnitude. No speedup claims are made.

## Limits of the Conclusion

- **No scaling curve exists**: Input size is constant (2 numbers), so runtime does not grow with any problem-size parameter `N`.
- **Floating-point boundaries**: Exact integer boundaries such as `(0, 10)`, `(-5, 0)`, `(0, -1)` satisfy `Math.sqrt(x * x + y * y) === r` exactly, so strict `>` assigns boundary points to the inner region (`1`, `5`, `10` points respectively). Non-axis points near radii `1`, `5`, `10` can incur IEEE-754 rounding in `x * x + y * y` or `Math.sqrt(...)`, and `x * x + y * y` can overflow to `Infinity` for `|x|, |y| > ~9.48e153` even though `Math.hypot` is not used.
- **Non-finite `NaN`**: `distanceToDart = NaN` evaluates `NaN > 10`, `NaN > 5`, `NaN > 1` all as `false` and returns `10`.

## How to Verify

```bash
python3 work/R47-T035/check.py
```

Expected final line:

```text
RESULT: PASS - executed 13 cases
```
