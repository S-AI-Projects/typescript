# Notes for R47-T037 (`prism`)

## Inspected Files

- `exercises/practice/prism/.docs/introduction.md` (lines 1-5): PRISM laser calibration framing.
- `exercises/practice/prism/.docs/instructions.md` (lines 1-38): predict the sequence of crystal `id`s hit by a laser starting at `(x, y, angle)` and refracting by each struck prism's `angle`.
- `exercises/practice/prism/.meta/config.json` (lines 1-27): `files.solution = ["prism.ts"]`, `files.test = ["prism.test.ts"]`, `files.example = [".meta/proof.ci.ts"]`. Jest enabled, TStyche disabled.
- `exercises/practice/prism/.meta/tests.toml` (lines 1-52): 14 canonical entries (`14/14/0`).
- `exercises/practice/prism/prism.test.ts` (lines 1-270): 14 cases (`1` `it`, `13` `xit`). Named cases: `"zero prisms"`, `"one prism one hit"`, `"one prism zero hits"`.
- `exercises/practice/prism/prism.ts` (lines 1-3): learner stub throwing `'Remove this line and implement the function'`.
- `exercises/practice/prism/tsconfig.json` (lines 1-38): `"strict": true`, `"target": "ES2020"`, `"module": "Node16"`, `"noEmit": true`, `"allowImportingTsExtensions": true`.
- `exercises/practice/prism/.meta/proof.ci.ts` (lines 1-51):
  - `Point = { x: number; y: number; angle: number }` (lines 1-5)
  - `Prism = Point & { id: number }` (lines 7-9, intersection type)
  - `export const findSequence = (start: Point, prisms: Prism[]): number[] =>` (line 11; non-readonly inputs, no runtime type validation)
  - `let nearest: Prism | undefined` (line 20) narrowed by control-flow analysis at `if (!nearest) break` (line 42) before reading `nearest.id`, `nearest.x`, `nearest.y`, `nearest.angle` (lines 44-47).
