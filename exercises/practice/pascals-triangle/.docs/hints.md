# Hints

## TypeScript: what `readonly` does and does not protect

The `Triangle` class publishes its results as readonly properties:

```ts
export class Triangle {
  public readonly rows: number[][]
  public readonly lastRow: number[]
  // ...
}
```

That is a deliberate TypeScript construct worth understanding,
because `readonly` is narrower than it looks. It is a **compile-time
only** rule about **reassigning the property** — it is not
immutability, and it does not exist at runtime. This standalone
example shows both halves (it does not solve the exercise):

```ts
class ScoreBoard {
  public readonly scores: number[] = [1, 2]
}

const board = new ScoreBoard()
board.scores.push(3) // allowed: readonly is shallow
console.log(board.scores) // [ 1, 2, 3 ]

const untyped = board as { scores: number[] }
untyped.scores = [9] // bypasses the static check
console.log(board.scores) // [ 9 ]
```

Expected output:

```text
[ 1, 2, 3 ]
[ 9 ]
```

The contrasting expression is the direct assignment without the
detour:

```ts
board.scores = [9]
```

That line does not compile at all — `tsc` rejects it with
`error TS2540: Cannot assign to 'scores' because it is a read-only
property.` The two outcomes differ because TypeScript checks the
*property slot*, not the contents of the array it points to, and
because the check happens only where types are known: once the code
runs as JavaScript, nothing enforces it.

The exercise-relevant pitfall: `triangle.rows` and
`triangle.lastRow` being readonly does **not** freeze the triangle.
Code holding a `Triangle` can still `push` into `triangle.rows` or
into one of its rows, and because `lastRow` is the very same array
object as the last element of `rows`, mutating one is visible through
the other. Treat `readonly` here as "the class will not replace these
arrays, and typed callers may not either" — not as a guarantee that
the contents never change.

Reference: the `readonly` modifier in the TypeScript handbook,
<https://www.typescriptlang.org/docs/handbook/2/classes.html#readonly>
