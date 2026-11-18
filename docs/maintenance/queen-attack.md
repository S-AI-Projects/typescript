# Queen Attack: Complexity Analysis & Maintenance Guide

## Overview

The `queen-attack` exercise models placing two queens on an $8 \times 8$ chessboard and determining whether either queen can attack the other along ranks (rows), files (columns), or diagonals.

Position coordinates are 0-indexed integer tuples `[row, column]` representing positions on the board.

---

## 1. Supported Input Sizes

The chessboard in this exercise has a strictly fixed dimension:
- **Board Width ($W$):** $8$ columns ($0 \le \text{col} \le 7$)
- **Board Height ($H$):** $8$ rows ($0 \le \text{row} \le 7$)

The coordinate domain for any valid piece position is the discrete set $\{0, 1, 2, 3, 4, 5, 6, 7\} \times \{0, 1, 2, 3, 4, 5, 6, 7\}$. Arbitrary $N \times N$ matrix sizing is not part of the problem specification, so no variable input parameter $N$ exists.

---

## 2. Real Implementation & Branch Operation Table

In `.meta/proof.ci.ts`, position validity is evaluated by `invalidPosition`:

```typescript
function invalidPosition({ white, black }: Positions): boolean {
  if (white[0] < 0 || white[0] >= H || white[1] < 0 || white[1] >= W) {
    return true
  }

  if (black[0] < 0 || black[0] >= H || black[1] < 0 || black[1] >= W) {
    return true
  }

  return false
}
```

Due to JavaScript/TypeScript logical OR (`||`) short-circuit evaluation:
- The first sub-condition evaluating to `true` immediately causes the expression to evaluate to `true` without evaluating subsequent operands.
- The second `if` statement is only evaluated if the first `if` statement evaluates to `false` (meaning the white queen's position was valid).

### Branch / Operation Table

The following table details the exact number of relational comparisons executed under short-circuit evaluation for distinct position cases:

| Case / Condition Evaluated | Specific Sub-Condition | Comparisons Executed (White Check) | Comparisons Executed (Black Check) | Total Comparisons | Return Value |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **White: Row below board** | `white[0] < 0` is `true` | 1 | 0 (short-circuited) | **1** | `true` (invalid) |
| **White: Row off board** | `white[0] >= 8` is `true` | 2 (`< 0` is false, `>= 8` is true) | 0 (short-circuited) | **2** | `true` (invalid) |
| **White: Col below board** | `white[1] < 0` is `true` | 3 (`row` checks false, `col < 0` is true) | 0 (short-circuited) | **3** | `true` (invalid) |
| **White: Col off board** | `white[1] >= 8` is `true` | 4 (all 3 prior false, `col >= 8` is true) | 0 (short-circuited) | **4** | `true` (invalid) |
| **White Valid, Black: Row below board** | `white` valid, `black[0] < 0` is `true` | 4 (all white checks false) | 1 (`black[0] < 0` is true) | **5** | `true` (invalid) |
| **White Valid, Black: Row off board** | `white` valid, `black[0] >= 8` is `true` | 4 (all white checks false) | 2 (`< 0` false, `>= 8` true) | **6** | `true` (invalid) |
| **White Valid, Black: Col below board** | `white` valid, `black[1] < 0` is `true` | 4 (all white checks false) | 3 (`row` false, `col < 0` true) | **7** | `true` (invalid) |
| **White Valid, Black: Col off board** | `white` valid, `black[1] >= 8` is `true` | 4 (all white checks false) | 4 (`col >= 8` true) | **8** | `true` (invalid) |
| **Both Positions Valid** | Both `white` and `black` on $[0, 7] \times [0, 7]$ | 4 (all white checks false) | 4 (all black checks false) | **8** | `false` (valid) |

### Minimum and Maximum Bounds
- **Minimum comparisons:** 1 comparison (when `white[0] < 0`).
- **Maximum comparisons:** 8 comparisons (when white is valid and black is checked through to `black[1] >= W`, or both pieces are valid).
- **Time Complexity:** $\mathcal{O}(1)$ worst-case and average-case time.
- **Space Complexity:** $\mathcal{O}(1)$ auxiliary memory (zero allocations).

---

## 3. Cost Statement: Algorithmic Work vs Runtime Overhead

When analyzing runtime execution in this test suite, it is essential to distinguish between actual algorithmic workload and toolchain overhead:

1. **Algorithmic Work:**
   The function `invalidPosition` performs between $1$ and $8$ primitive 64-bit integer comparisons in CPU registers. At modern processor clock speeds (e.g., 3 GHz), 8 comparisons execute in well under **5 nanoseconds** (sub-microsecond CPU time).

2. **Harness & Toolchain Overhead:**
   In contrast, invoking the test suite via `corepack yarn test` requires:
   - Node.js runtime process initialization (~30–50 ms).
   - Corepack & Yarn Berry package manager bootstrap (~100–200 ms).
   - TypeScript AST parsing, type-checking (`tsc --noEmit`), and Babel transpilation (~400–800 ms).
   - Jest framework bootstrap, runner isolation, worker process spawning, and assertion evaluation (~300–600 ms).
   Total test invocation overhead measures $\approx 1.0\text{--}1.5\text{ seconds}$, of which the algorithmic validation accounts for less than $0.0001\%$.

---

## 4. Limit of Conclusion

- **Domain Limitation:** This analysis and its bounds apply exclusively to the fixed $8 \times 8$ board specification defined by Exercism's canonical problem specification.
- **No Speedup Claim:** No optimization or algorithmic speedup is claimed because the existing implementation is already optimal ($\mathcal{O}(1)$ bound, at most 8 comparisons) and nothing is being compared against an alternative algorithm.

