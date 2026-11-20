# Notes for R47-T035 (`darts`)

## Inspected Files

- `exercises/practice/darts/.docs/instructions.md` (lines 1-31): score a single dart throw at Cartesian `(x, y)` (real numbers) against concentric circles centered at `(0, 0)`: outside target (`> 10`) -> `0`, outer (`<= 10`, `> 5`) -> `1`, middle (`<= 5`, `> 1`) -> `5`, inner (`<= 1`) -> `10`.
- `exercises/practice/darts/.meta/config.json` (lines 1-29): `files.solution = ["darts.ts"]`, `files.test = ["darts.test.ts"]`, `files.example = [".meta/proof.ci.ts"]`. Jest enabled, TStyche disabled.
- `exercises/practice/darts/.meta/tests.toml` (lines 1-49): 13 entries, all 13 included (`13/13/0`).
- `exercises/practice/darts/darts.test.ts` (lines 1-56): 13 cases (`1` `it`, `12` `xit`). Named cases:
  - `"Missed target"` (`lines 5-7`): `score(-9, 9)` -> `0`
  - `"On the outer circle"` (`lines 9-11`): `score(0, 10)` -> `1`
  - `"On the middle circle"` (`lines 13-15`): `score(-5, 0)` -> `5`
  - Inner-circle case `"On the inner circle"` (`lines 17-19`): `score(0, -1)` -> `10`
- `exercises/practice/darts/darts.ts` (lines 1-3): learner stub throwing `'Remove this line and implement the function'`.
- `exercises/practice/darts/.meta/proof.ci.ts`: computes `const distanceToDart = Math.sqrt(x * x + y * y)` (`2` multiplications, `1` addition, `1` `Math.sqrt`), then executes up to `3` strict `>` comparisons (`> 10`, `> 5`, `> 1`).

## Fixed Input Size & Constant Bounds

- Input size is fixed at two IEEE-754 `number` coordinates `(x, y)`. There is no collection or scaling parameter `N`, so no scaling curve exists.
- Worst-case cost is `O(1)` time and `O(1)` auxiliary space: `2` multiplications, `1` addition, `1` `Math.sqrt`, and `1`–`3` strict `>` comparisons.
