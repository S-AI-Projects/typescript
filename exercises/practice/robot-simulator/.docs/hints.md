# Hints

## General

- A newly created `Robot` starts at `[0, 0]` facing `'north'`.
- On the grid, `x` increases toward `'east'` (`+1`) and decreases toward `'west'` (`-1`); `y` increases toward `'north'` (`+1`) and decreases toward `'south'` (`-1`).
- Validate both bearings in `place(...)` and instruction characters (`'L'`, `'R'`, `'A'`) in `evaluate(...)`, throwing `InvalidInputError` on invalid input.

## Choosing an approach

Two common ways to model robot orientation and movement in TypeScript trade off explicit readability against compact lookup tables:

1. **String-union state with explicit branches**:

   - Store `bearing` as `'north' | 'east' | 'south' | 'west'` and implement `turnLeft`, `turnRight`, and `advance` with `if / else` chains or `switch` statements.
   - **Pros**: Every state transition is spelled out by name and easy to read in isolation without mental indirection.
   - **Cons**: Turning and advancing repeat similar 4-way branches, and adding directions later requires updating multiple conditional blocks. Parsing instructions into an intermediate array via `[...s].map(...)` also allocates `O(n)` temporary elements for a string of length `n`.

2. **Ordered compass index with unit-vector lookup table**:
   - Order the directions clockwise (`['north', 'east', 'south', 'west'] as const`) alongside matching coordinate deltas (`[[0, 1], [1, 0], [0, -1], [-1, 0]]`) and store an integer `dirIndex` (`0..3`).
   - Turning right is `(dirIndex + 1) % 4`; turning left is `(dirIndex + 3) % 4`; advancing adds the `[dx, dy]` delta at `dirIndex`.
   - **Pros**: Eliminates 4-way branching in rotation and movement, validates bearings in `O(1)` via a `Map`, and executes instruction characters in `O(1)` extra memory without allocating an intermediate command array.
   - **Cons**: Correctness relies on keeping the direction array and delta array in matching clockwise order, and `O(1)` lookup maps add a small constant memory setup per robot or module.

### Worked step-by-step trace

Suppose a robot starts at `(0, 0)` facing `'north'` (`dirIndex = 0`) and evaluates `"RA"`:

1. **Initial state**: `coordinates = [0, 0]`, `dirIndex = 0` (`'north'`).
2. **Instruction `'R'`**: `(dirIndex + 1) % 4` -> `(0 + 1) % 4 = 1`, which indexes `'east'`. Coordinates remain `[0, 0]`.
3. **Instruction `'A'`**: Look up unit vector at index `1` (`[1, 0]`) and add to `[0, 0]` -> `coordinates = [1, 0]`, `bearing = 'east'`.
