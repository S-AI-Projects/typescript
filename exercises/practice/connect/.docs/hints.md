# Hints

## TypeScript: Union Narrowing with Literal Types

In Connect (Hex), players place stones on a hexagonal board. While a cell on the board can be empty (`'.'`) or occupied by player `'X'` or player `'O'`, only two players compete in the game: `'X'` and `'O'`.

Instead of modeling player parameters as an open-ended `string`, TypeScript allows you to define a **literal union type**:

```typescript
type Player = 'X' | 'O';
```

When a function takes a union type, TypeScript's compiler employs **control flow analysis** and **equality narrowing**. Inside an `if (player === 'X')` check (or a conditional ternary expression), TypeScript narrows the type of `player` to the single literal type `'X'` in the truthy branch. In the alternative (`else` or `:`) branch, the compiler exhaustively narrows `player` to `'O'`.

### Where This Appears in the Connect Reference Implementation

In the maintained reference implementation (`.meta/proof.ci.ts`):
1. **Union Return and Parameter Types**:
   - `winner(): '' | 'X' | 'O'` specifies that the game result is either empty or won by `'X'` or `'O'`.
   - `checkWin(player: 'X' | 'O')` and `search(pos, XorO: 'X' | 'O', checked)` restrict search routines to valid players.
2. **Const Assertions**:
   - `const players = ['X', 'O'] as const` infers a readonly tuple of literal types `readonly ['X', 'O']` rather than widening to `string[]`.
3. **Equality Narrowing**:
   - In helper methods such as `startPositions(XorO: 'X' | 'O')` and `winningSpot(pos, XorO: 'X' | 'O')`, the reference uses ternary operators:
     ```typescript
     return XorO === 'X'
       ? this.board.map((_, i) => ({ x: i, y: i }))
       : this.board[0].map((_, i) => ({ x: 0, y: i }))
     ```
     Because `XorO` is typed `'X' | 'O'`, checking `XorO === 'X'` narrows the first branch to `'X'` and the fallback branch to `'O'`.

### Standalone Executable Example

Consider determining the connection axis for a player:

```typescript
type Player = 'X' | 'O';

export function getPlayerAxis(player: Player): string {
  // Equality narrowing: inside the truthy branch, player is narrowed to 'X'
  if (player === 'X') {
    return `Player ${player}: horizontal (left to right)`;
  }
  // In the fallback branch, TypeScript exhaustively narrows player to 'O'
  return `Player ${player}: vertical (top to bottom)`;
}
```

#### Expected Output

```text
Player X: horizontal (left to right)
Player O: vertical (top to bottom)
```

### Common Pitfall: Unconstrained `string`

A common mistake is typing player parameters or cell contents as a broad `string`:

```typescript
export function getPlayerAxisPitfall(player: string): string {
  if (player === 'X') {
    return `Player ${player}: horizontal (left to right)`;
  }
  // Common pitfall: any unvalidated string falls through as if it were 'O'!
  return `Player ${player}: vertical (top to bottom)`;
}
```

#### Contrasting Output

When passing unvalidated board characters or invalid inputs:

```text
Player .: vertical (top to bottom)
Player ?: vertical (top to bottom)
```

### Why the Outcomes Differ

- **Type Safety and Exhaustiveness**: With `Player = 'X' | 'O'`, the compiler prevents invalid strings like `'.'`, `' '`, or `'?'` from ever being passed to the function at compile time. Inside the branch, checking `player === 'X'` safely narrows the remaining possibility to `'O'`.
- **Silent Logic Bugs**: With an unconstrained `string`, the negation of `player === 'X'` matches *every* other string. An empty cell `'.'` or unrelated character will silently execute the `'O'` path, leading to erroneous path traversals and false win detections.

### Connecting to the Board Implementation

In Connect, Player `'X'` wins by connecting left to right, whereas Player `'O'` wins by connecting top to bottom. Modeling player tokens as a literal union (`'X' | 'O'`) ensures that:
- Starting coordinates can branch safely between left-edge cells and top-edge cells.
- Boundary checks know whether to test for reaching the right edge or the bottom edge.
- Code remains concise without needing defensive `else if (player === 'O') else throw new Error(...)` blocks.

### Official Documentation

- [TypeScript Handbook: Equality Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#equality-narrowing)
- [TypeScript Handbook: Literal Types & Unions](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#union-types)
