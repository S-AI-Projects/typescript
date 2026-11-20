# Notes for R47-T036 (`robot-simulator`)

## Inspected Files

- `exercises/practice/robot-simulator/.docs/instructions.md` (lines 1-25): grid coordinates `(x, y)` increasing to north (`+y`) and east (`+x`), three movements (`R` turn right, `L` turn left, `A` advance), example `(7, 3)` facing north + `"RAALAL"` -> `(9, 4)` facing west.
- `exercises/practice/robot-simulator/.meta/config.json` (lines 1-30): `files.solution = ["robot-simulator.ts"]`, `files.test = ["robot-simulator.test.ts"]`, `files.example = [".meta/proof.ci.ts"]`. Jest enabled, TStyche disabled.
- `exercises/practice/robot-simulator/.meta/tests.toml` (lines 1-57): 18 canonical entries (`18/18/0`).
- `exercises/practice/robot-simulator/robot-simulator.test.ts` (lines 1-237): 22 test cases across 5 `describe`/`xdescribe` blocks (`Create robot`: 5, `Rotating clockwise`: 4, `Rotating counter-clockwise`: 4, `Moving forward one`: 4, `Follow series of instructions`: 5). Track adds 4 cases beyond `tests.toml` (`facing east`, `facing west, at origin`, `invalid robot bearing`, `instruct many robots`).
- `exercises/practice/robot-simulator/robot-simulator.ts` (lines 1-27): exports `InvalidInputError` and stub `Robot` with `bearing`, `coordinates`, `place({ x, y, direction })`, `evaluate(instructions)`.
- `exercises/practice/robot-simulator/.meta/proof.ci.ts` (lines 1-96):
  - `Bearing = 'north' | 'south' | 'east' | 'west'`
  - `validDirections.includes(...)` linear scan for bearing validation (`lines 11-15`)
  - `Robot.instructions(s)` splits `[...s].map(...)` with `switch` (`lines 20-35`) into an intermediate `Instruction[]` array
  - `advance()`, `turnLeft()`, `turnRight()` use 4-way `if / else if` chains (`lines 50-84`)

## Comparison: Reference vs. Direction-Index Alternative

- **Reference (`.meta/proof.ci.ts`)**:
  - Stores `bearing` as a string union and updates orientation/coordinates via explicit `if / else if` chains; converts instruction strings to an intermediate `Instruction[]` array of length `|s|`.
  - Extra memory: `O(|s|)` intermediate `Instruction[]` array in `evaluate(s)` plus `[number, number]` coordinates.
- **Alternative (`work/R47-T036/alternative.ts`)**:
  - Stores orientation as an integer `dirIndex` (`0..3`) indexing `COMPASS = ['north', 'east', 'south', 'west']` and `STEP_VECTORS = [[0, 1], [1, 0], [0, -1], [-1, 0]]`.
  - Turning uses modulo arithmetic (`(dirIndex + 1) % 4` and `(dirIndex + 3) % 4`); advancing adds `STEP_VECTORS[dirIndex]` without direction branches.
  - Validation uses `Map<string, number>` for bearings (`O(1)` lookup without prototype collisions) and validates/dispatches instructions via `Map` in `O(1)` extra heap space.
  - Trade-off: avoids duplicated 4-branch `if/else` chains and intermediate array allocation, at the cost of keeping `COMPASS` and `STEP_VECTORS` index-aligned.
