# Hints

## General

- Bowling is scored over 10 frames.
- A frame typically consists of up to two rolls (unless it is the 10th frame, where bonus fill balls may be awarded for strikes or spares).
- A strike knocks down all 10 pins on the first roll of a frame. The frame score is 10 plus the sum of pins knocked down in the next two rolls.
- A spare knocks down all 10 pins across two rolls within a frame. The frame score is 10 plus the pins knocked down on the immediately following roll.
- An open frame knocks down fewer than 10 pins across two rolls; its score is simply the sum of those two rolls.

## Choosing a scoring approach

When implementing bowling scoring, two primary architectural patterns emerge:

### 1. Incremental Frame-State Scoring (The Reference Technique)
- **Data representation:** Maintains an explicit frame counter (`currentFrame`), a tracking array for frame classifications (`'X'`, `'S'`, or pin count), and an accumulating array of 10 frame scores (`frameScores`).
- **Processing model:** Rolls are processed sequentially as they happen. When a new roll occurs, the implementation checks past frames (e.g. 1 or 2 frames prior) to apply retroactive strike or spare bonus points to earlier frame score totals while simultaneously accumulating the current frame's score.
- **Trade-off:**
  - *Advantage:* Frame-based state machines can track game status and frame transitions in real-time as each roll is made.
  - *Disadvantage:* Retroactive bonus distribution across past frames introduces complex state coordination (e.g., inspecting 1-frame-back vs. 2-frames-back, handling multiple consecutive strikes, and special branching for 10th frame bonus rolls).

### 2. Event-Log with Deferred Frame-Indexed Scoring (The Alternative Technique)
- **Data representation:** Stores all rolls in a single flat array (`rolls: number[]`) as an append-only event log.
- **Processing model:** During the game, rolls are validated and appended. When `score()` is requested, a loop iterates through exactly 10 frames using a forward-pointing roll index (`rollIndex`):
  - If `rolls[rollIndex] === 10` (Strike): Frame score is `10 + rolls[rollIndex + 1] + rolls[rollIndex + 2]`; advance `rollIndex` by 1.
  - If `rolls[rollIndex] + rolls[rollIndex + 1] === 10` (Spare): Frame score is `10 + rolls[rollIndex + 2]`; advance `rollIndex` by 2.
  - Otherwise (Open frame): Frame score is `rolls[rollIndex] + rolls[rollIndex + 1]`; advance `rollIndex` by 2.
- **Trade-off:**
  - *Advantage:* Forward lookahead arithmetic is straightforward and mirrors the official rules directly without backward pointers or mutable multi-frame accumulators. Frame boundary calculations in the 10th frame become natural lookaheads.
  - *Disadvantage:* Scoring is deferred until all rolls are recorded, requiring game-completion verification prior to evaluation.

### Worked Example: Spare Followed by Zeros

Consider a game where the player throws `5` and `5` in frame 1, followed by `0` and `0` in frame 2, and `0` for all remaining rolls:
- **Rolls:** `[5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`
- **Frame 1 Calculation:**
  - Rolls: `5` and `5` $\rightarrow$ Frame 1 is a spare ($5 + 5 = 10$).
  - Spare bonus rule: Add the next single roll immediately following the spare.
  - Next roll: `rolls[2]` = `0`.
  - Frame 1 total: $10 + \text{bonus} = 10 + 0 = 10$.
- **Frame 2 Calculation:**
  - Rolls: `0` and `0` $\rightarrow$ Open frame ($0 + 0 = 0$).
  - Frame 2 total: $0$.
- **Remaining frames (3 to 10):** All open frames of zeros ($0$).
- **Total Game Score:** $10 + 0 + 0 + \dots = 10$.

Why does frame 1 score 10 instead of 20? A spare awards only the pins from the *single* next roll as a bonus, not the entire next frame. Since the next roll knocked down 0 pins, the bonus is 0, giving $10 + 0 = 10$.

### When to choose explicit frame indexing

Explicit forward frame indexing using a flat rolls array is often easier to understand and reason about because:
1. It eliminates the need to mutate past frame totals retroactively.
2. The rules for strikes (look ahead 2 rolls) and spares (look ahead 1 roll) are expressed as clean, local array index offsets (`+1`, `+2`).
3. Memory overhead is minimal: storing 12 to 21 scalar integers in a flat array requires $\mathcal{O}(1)$ space for any standard 10-frame game.
