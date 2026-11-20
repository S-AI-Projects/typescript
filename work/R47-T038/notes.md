# Notes for R47-T038 (`dnd-character`)

## Inspected Files

- `exercises/practice/dnd-character/.docs/instructions.md` (lines 1-32): generate 6 ability scores (roll 4d6, drop lowest -> range `3..18`), compute constitution modifier `Math.floor((constitution - 10) / 2)`, set hitpoints `10 + modifier`.
- `exercises/practice/dnd-character/.docs/introduction.md` (lines 1-10): D&D character generation narrative framing.
- `exercises/practice/dnd-character/.meta/config.json` (lines 1-28):
  - `files.solution = ["dnd-character.ts"]`
  - `files.test = ["dnd-character.test.ts"]`
  - `files.example = [".meta/proof.ci.ts"]`
  - No `"editor"` key and no `"exemplar"` key.
  - `custom.flag.tests.jest = true`, `custom.flag.tests.tstyche = false`.
- `exercises/practice/dnd-character/.meta/tests.toml` (lines 1-76): 19 canonical entries (`19/19/0`).
- `exercises/practice/dnd-character/dnd-character.test.ts` (lines 1-134): 25 test cases (`1` `it`, `24` `xit`). Imports `{ DnDCharacter } from './dnd-character.ts'`. The 6 extra cases beyond `tests.toml` (19 entries) come from expanding `"Random character is valid"` into 7 tests (`hitpoints`, `strength`, `dexterity`, `constitution`, `intelligence`, `wisdom`, `charisma`).
- `exercises/practice/dnd-character/dnd-character.ts` (lines 1-9): learner stub throwing `'Remove this line and implement the function'`.
- `exercises/practice/dnd-character/.meta/proof.ci.ts` (lines 1-40): `DnDCharacter` class with `generateAbilityScore`, `getModifierFor`, and 7 readonly instance properties.
- `exercises/practice/dnd-character/jest.config.cjs` (lines 1-22): `testMatch` matches `'**/?(*.)+(spec|test).[jt]s?(x)'`.
- `exercises/practice/dnd-character/test-runner.mjs` (`common/test-runner.mjs:37-64`): reads `.meta/config.json` (or `.exercism/config.json`) for `flag.tests.jest` / `flag.tests.tstyche`, then runs `tsc` (`lint:types`) and `jest` (`test:implementation`).
- `config.json` (lines 21-31): root fallback `files` template (`"%{kebab_slug}.ts"`, `"%{kebab_slug}.test.ts"`, `".meta/proof.ci.ts"`, `".meta/exemplar.ts"`).
- `scripts/helpers.mjs` (`fileConfiguration` lines 117-145, `prepare` lines 338-413): resolves `.meta/config.json` `files` and copies `.meta/proof.ci.ts` over `<solution>` inside `tmp_exercises/`.

## Config Validation Finding

- All configured files in `exercises/practice/dnd-character/.meta/config.json` exist inside the exercise directory and match reality (`dnd-character.ts`, `dnd-character.test.ts`, `.meta/proof.ci.ts`). No `.meta/config.json` edit is needed.
