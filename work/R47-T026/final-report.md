# Final Report: Assignment R47-T026 (Bowling Approach Comparison)

## 1. Assignment Summary
- **Student:** Surya Paladugu
- **Assignment:** R47-T026 (Task 6 of 10)
- **Repository:** `https://github.com/S-AI-Projects/typescript`
- **Branch:** `student/e26b07f0754/R47-T026`
- **Exercise:** `exercises/practice/bowling`

---

## 2. Technical Comparison Summary

We compared the maintained reference technique in `.meta/proof.ci.ts` with an independently designed alternative in `work/R47-T026/alternative.ts`.

### Approach A: Incremental State Machine (`proof.ci.ts`)
- **Data representation:** Frame tracking array (`frames: Frame[]`), current frame counter, and an accumulating score array (`frameScores: number[]`).
- **Processing model:** Eager evaluation during `roll(pins)`. Applies strike and spare bonuses retroactively to prior frames (`currentFrame - 2` and `currentFrame - 3`) as new rolls arrive.
- **Trade-off:** Allows tracking frame progress incrementally, but introduces complex backward pointer coordination and state transitions.

### Approach B: Flat Event Log with Forward Lookahead (`alternative.ts`)
- **Data representation:** Flat integer sequence (`rolls: number[]`).
- **Processing model:** Lazy evaluation on `score()`. Validates pin counts and game completion using frame boundaries, then executes a 10-iteration loop with forward lookahead index offsets (`+1`, `+2`) for strike and spare bonuses.
- **Trade-off:** Eliminates retroactive mutation of historical frames. Very easy to reason about and aligns with traditional scorekeeping rules. Requires validating game completion before evaluation.

---

## 3. Worked Example: Spare Followed by Zeros

For rolls `[7, 3, 0, 0, ...]`:
1. Frame 1: Roll 1 is 7, Roll 2 is 3. Total is 10 $\rightarrow$ Spare.
2. Under bowling rules, a spare earns 10 pins plus the pins knocked down in the immediately following roll.
3. The next roll is 0.
4. Frame 1 score is $10 + 0 = 10$.
5. Frame 2: Rolls are 0 and 0. Frame 2 score is $0 + 0 = 0$.
6. Why does frame 1 score 10 rather than 20? The spare bonus only counts the single next roll, not the entire next frame.

---

## 4. Verification & Automated Checker Results

The automated checker (`work/R47-T026/check.py`) tested both implementations in isolated environments against all 31 canonical test cases:
- **Reference Implementation:** Executed: 31, Passed: 31, Failed: 0
- **Alternative Implementation:** Executed: 31, Passed: 31, Failed: 0
- **Agreement:** 100% agreement on all 31 test cases.
- **Three Named Cases:**
  - `should be able to score a game with all zeros`: PASSED (both)
  - `should be able to score a game with no strikes or spares`: PASSED (both)
  - `a spare followed by zeros is worth ten points`: PASSED (both)

---

## 5. Integrity & Safety
- **Learner Stub:** `exercises/practice/bowling/bowling.ts` remains unsolved with `throw new Error(...)`.
- **Working Tree:** Canonical test suite and exercise files were not modified during testing.
- **Isolation:** No files or commits from assignments R47-T021 through R47-T025 were touched or included.
