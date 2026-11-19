# Final Report: Assignment R47-T027 — Connect Language-Specific Hint

## 1. Selected TypeScript Construct and Why It Is Used in Connect

### Selected Construct
**Union Narrowing with Literal Types (Equality Narrowing)**

### Rationale & Concrete Code Evidence
In Connect (Hex), cells on the board may contain spaces (`'.'`), player `'X'`, or player `'O'`, but game completion and winner checking involves only two active players: `'X'` and `'O'`.

The maintained reference implementation (`exercises/practice/connect/.meta/proof.ci.ts`) explicitly leverages union narrowing in several key areas:
1. **Return and Parameter Type Modeling**:
   - Line 12: `public winner(): '' | 'X' | 'O'` guarantees only valid game outcomes can be returned.
   - Line 22: `private checkWin(player: 'X' | 'O'): boolean`
   - Line 34: `XorO: 'X' | 'O'`
2. **Const Assertions to Preserve Literal Unions**:
   - Line 13: `const players = ['X', 'O'] as const` infers a readonly tuple of literal types `readonly ['X', 'O']` rather than widening to `string[]`.
3. **Equality Narrowing**:
   - Lines 73–77 (`startPositions`):
     ```typescript
     private startPositions(XorO: 'X' | 'O'): Array<{ x: number; y: number }> {
       return XorO === 'X'
         ? this.board.map((_, i) => ({ x: i, y: i }))
         : this.board[0].map((_, i) => ({ x: 0, y: i }))
     }
     ```
   - Lines 79–83 (`winningSpot`):
     ```typescript
     private winningSpot(pos: { x: number; y: number }, XorO: 'X' | 'O'): boolean {
       return XorO === 'X'
         ? pos.y === this.board[0].length - 1 + pos.x
         : pos.x === this.board.length - 1
     }
     ```

In both methods, the equality check `XorO === 'X'` narrows the union type `'X' | 'O'` to `'X'` in the truthy expression. In the ternary fallback branch, TypeScript's control flow analysis exhaustively narrows `XorO` to `'O'`.

### Why Alternatives Were Ruled Out
- **Readonly Inputs**: The constructor in `proof.ci.ts` takes `board: string[]`, not `readonly string[]` or `ReadonlyArray<string>`.
- **Runtime vs Static Validation**: The reference implementation performs no runtime board dimensions or stone character validation assertions, relying instead on static typing and coordinate bounds.

---

## 2. Files Changed and Created

### Exercise Hint
- `exercises/practice/connect/.docs/hints.md`: Added comprehensive guide on Union Narrowing with Literal Types, including reference code links, standalone executable micro-example, expected outputs, pitfall demonstration, and official TypeScript documentation links.

### Verification Evidence (`work/R47-T027/`)
- `check.py`: Automated Python 3 verification checker.
- `example.ts`: Standalone executable TypeScript micro-example.
- `inputs.json`: Test inputs for narrowed and pitfall cases.
- `expected-results.json`: Documented expected outcomes.
- `actual-results.json`: Captured runtime results from executing `example.ts`.
- `test-results.md`: Complete markdown breakdown of canonical test outcomes.
- `tool-versions.txt`: Recorded environment tool versions.
- `output.txt`: Checker execution output log.
- `final-report.md`: This comprehensive assignment summary.

---

## 3. Actual Canonical Test Count
- Total canonical test cases in `tests.toml`: **10**
- Executed by Jest: **10**
- Passed: **10**
- Failed: **0**

### Mandatory Cases
1. `an empty board has no winner`: **PASS**
2. `X can win on a 1x1 board`: **PASS**
3. `O can win on a 1x1 board`: **PASS**

---

## 4. Micro-Example Expected vs Actual Outputs

### Narrowed Inputs (`['X', 'O']`)
- `getPlayerAxis('X')`:
  - Expected: `"Player X: horizontal (left to right)"`
  - Actual:   `"Player X: horizontal (left to right)"`
- `getPlayerAxis('O')`:
  - Expected: `"Player O: vertical (top to bottom)"`
  - Actual:   `"Player O: vertical (top to bottom)"`

### Contrasting Pitfall Inputs (`['.', '?']`)
- `getPlayerAxisPitfall('.')`:
  - Expected: `"Player .: vertical (top to bottom)"`
  - Actual:   `"Player .: vertical (top to bottom)"`
- `getPlayerAxisPitfall('?')`:
  - Expected: `"Player ?: vertical (top to bottom)"`
  - Actual:   `"Player ?: vertical (top to bottom)"`

Documented outputs in `.docs/hints.md` match actual runtime outputs verbatim.

---

## 5. Checker Execution Result
All assertions passed cleanly:
```text
=== Connect R47-T027 Automated Verification Checker ===
Tool versions: {'Python': '3.14.5', 'Node': 'v24.22.1', 'Yarn': '4.5.1', 'Corepack': '0.36.0'}
Resolved paths: solution=connect.ts, test=connect.test.ts, example=.meta/proof.ci.ts
Canonical test cases in tests.toml: 10
PASS  canonical test count > 0 in tests.toml
PASS  learner stub is unsolved in working tree
PASS  connect.ts unchanged in working tree
PASS  connect.test.ts unchanged in working tree
PASS  .meta/proof.ci.ts unchanged in working tree

--- Verifying Micro-Example (work/R47-T027/example.ts) ---
PASS  example.ts executed with return code 0 (got 0)
PASS  actual-results.json matches expected-results.json exactly
PASS  Micro-example asserts player 'X' horizontal
PASS  Micro-example asserts player 'O' vertical
PASS  Contrasting pitfall asserts '.' falls into 'O'
PASS  Contrasting pitfall asserts '?' falls into 'O'
PASS  hints.md documents Player X output
PASS  hints.md documents Player O output
PASS  hints.md documents contrasting pitfall '.' output
PASS  hints.md documents contrasting pitfall '?' output
PASS  hints.md links official TypeScript equality narrowing documentation

--- Running Reference Implementation Tests in Isolated Temp Dir ---
PASS  yarn install succeeded (exit 0)
PASS  package.json test script exit code is 0 (got 0)
PASS  jest exit code is 0 (got 0)

Test Execution Summary: total=10, passed=10, failed=0
PASS  Executed test count > 0 (got 10)
PASS  All canonical tests executed (10/10)
PASS  All executed tests passed (10/10)
PASS  No tests failed (failed=0)
PASS  Mandatory case 'an empty board has no winner' passed (status: passed)
PASS  Mandatory case 'X can win on a 1x1 board' passed (status: passed)
PASS  Mandatory case 'O can win on a 1x1 board' passed (status: passed)
PASS  Learner stub remained completely unmodified throughout checker execution

=== Final Verification Summary ===
All verification checks PASSED successfully!
```

---

## 6. Confirmation of Learner Stub & Canonical Test Immutability
- `exercises/practice/connect/connect.ts` retains `throw new Error('Remove this line and implement the function')`.
- `git diff --quiet HEAD -- exercises/practice/connect/connect.ts` confirmed 0 diffs.
- `git diff --quiet HEAD -- exercises/practice/connect/connect.test.ts` confirmed 0 diffs.
- No public API changes were introduced.

---

## 7. Commit and Pull Request Details
- **Commit Hash:** `127df0e53f02863fae2a03b9cbf1bc4171334359`
- **Pull Request:** #68
- **Pull Request URL:** https://github.com/S-AI-Projects/typescript/pull/68
- **Base Repository:** `S-AI-Projects/typescript` (branch: `main`)
- **Head Branch:** `student/e26b07f0754/R47-T027`

---

## 8. Isolation Confirmation
No files or commits from assignments R47-T021 through R47-T026 or any other assignment are present.

