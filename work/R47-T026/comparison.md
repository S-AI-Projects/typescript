# Technical Comparison: Bowling Scoring Implementations

## 1. Overview

The `bowling` exercise in Exercism's TypeScript track requires maintaining the state of a ten-pin bowling game, recording pin falls via `roll(pins: number)`, and evaluating the final score via `score(): number`.

This document provides an in-depth technical comparison between:
1. **The Maintained Reference Implementation** (`.meta/proof.ci.ts`): Stateful, incremental frame-by-frame scoring with retroactive bonus application.
2. **The Alternative Implementation** (`work/R47-T026/alternative.ts`): Append-only event-log representation with deferred, forward-indexed frame scoring.

---

## 2. Approach Architectures

### Approach A: Incremental Frame-State Machine (Reference)
- **Data Representation:**
  - `currentFrame: number` (1-based frame index)
  - `frames: Frame[]` (array tracking `'X'`, `'S'`, or frame pin counts)
  - `frameScores: number[]` (length 10 array accumulating point totals per frame)
  - `frameRoll: number` (1 or 2, tracking throw within current frame)
  - `remainingPins: number` (pins standing on current lane, initialized to 10)
- **Control Flow:**
  - On each `roll(pins)`:
    - Increments the score for `currentFrame`.
    - If previous frames were strikes or spares, retroactively credits `pins` to `frameScores[currentFrame - 2]` or `frameScores[currentFrame - 3]`.
    - Checks frame transition: if strike or 2nd roll, initializes a new frame.
  - On `score()`:
    - Verifies `isGameOver()` by inspecting 10th-frame marker and bonus roll counters.
    - Sums `frameScores` using `.reduce()`.

### Approach B: Flat Event Log with Forward Lookahead (Alternative)
- **Data Representation:**
  - `rolls: number[]` (single flat array recording all pin falls in chronological order)
- **Control Flow:**
  - On each `roll(pins)`:
    - Validates pin bounds ($0 \le \text{pins} \le 10$).
    - Validates game completion status via `isGameOver()`.
    - Validates frame-level pin sum consistency (e.g. roll 1 + roll 2 $\le 10$ in non-strike frames).
    - Appends `pins` to `this.rolls`.
  - On `score()`:
    - Verifies `isGameOver()`.
    - Iterates through exactly 10 frames ($0 \le \text{frame} < 10$) with a pointer `rollIndex`:
      - **Strike (`rolls[rollIndex] === 10`):** Adds $10 + \text{rolls}[rollIndex + 1] + \text{rolls}[rollIndex + 2]$; advances `rollIndex += 1`.
      - **Spare (`rolls[rollIndex] + rolls[rollIndex + 1] === 10`):** Adds $10 + \text{rolls}[rollIndex + 2]$; advances `rollIndex += 2`.
      - **Open Frame:** Adds $\text{rolls}[rollIndex] + \text{rolls}[rollIndex + 1]$; advances `rollIndex += 2`.

---

## 3. Comparison Matrix

| Attribute | Reference Implementation (`proof.ci.ts`) | Alternative Implementation (`alternative.ts`) |
| :--- | :--- | :--- |
| **Primary Data Structure** | Multiple stateful arrays (`frames`, `frameScores`) + tracking scalars | Single flat integer array (`rolls: number[]`) |
| **Scoring Point in Time** | Incremental / Eager during `roll()` | Deferred / Lazy on demand during `score()` |
| **Bonus Handling** | Retroactive back-propagation (`currentFrame - 2`, `currentFrame - 3`) | Forward lookahead index offsets (`+1`, `+2`) |
| **10th Frame Handling** | Virtual frames beyond 10 with special termination branching | Standard roll count lookahead; loop terminates after 10 frames |
| **Memory Allocation** | Multiple objects & fixed arrays ($\mathcal{O}(1)$ space, $\approx 3$ arrays) | Single array ($\mathcal{O}(1)$ space, $12 \le \text{len} \le 21$) |
| **Complexity & Readability** | Moderate: complex back-pointer arithmetic & multi-variable sync | High: directly mirrors traditional bowling scorebook rules |

---

## 4. Worked Example: Spare Followed by Zeros

Consider a frame where the bowler throws 7 pins, then 3 pins, followed by two zero rolls:
- **Rolls:** `[7, 3, 0, 0, ...]`
- **Calculation:**
  1. Frame 1 throws: $7$ and $3$. $7 + 3 = 10 \rightarrow$ Spare.
  2. Spare bonus: Under bowling rules, a spare earns 10 pins plus the pins knocked down in the immediately following roll.
  3. The next roll is $0$.
  4. Frame 1 score: $10 + 0 = 10$.
  5. Frame 2 throws: $0$ and $0$. Open frame score: $0 + 0 = 0$.
- **Why does Frame 1 score 10 rather than 20?**
  A common misconception is that a spare counts the entire next frame twice. In reality, a spare only awards the single next ball thrown as a bonus. Since the next roll was $0$, the bonus was $0$.

---

## 5. Verification Summary

Both implementations were subjected to all 31 canonical test cases in the Exercism test suite:
- **Reference Implementation:** 31 passed / 31 total (0 failed)
- **Alternative Implementation:** 31 passed / 31 total (0 failed)
- Both implementations cleanly enforce invalid pin counts, invalid negative rolls, game-over restrictions, and unstarted/incomplete game errors.
