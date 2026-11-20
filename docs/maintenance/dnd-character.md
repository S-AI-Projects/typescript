# Maintenance Notes: `dnd-character`

## File-Role Map

The `"files"` map in `exercises/practice/dnd-character/.meta/config.json:6-16` declares three roles (`solution`, `test`, `example`) and omits `"editor"` (no editor file exists for this exercise):

| Role       | Path (relative to exercise)            | Maintained by        | Purpose                                                                                                      |
| ---------- | -------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------ |
| `solution` | `dnd-character.ts`                     | Track stub / Learner | Starter stub (`throw new Error('Remove this line and implement the function')`) replaced by learner solution |
| `test`     | `dnd-character.test.ts`                | Track maintainers    | 25 Jest test cases (`1` active `it`, `24` skipped `xit`); imports `./dnd-character.ts`                       |
| `example`  | `.meta/proof.ci.ts`                    | Track maintainers    | Reference solution verified in CI (`DnDCharacter`)                                                           |
| `editor`   | _(not present in `.meta/config.json`)_ | N/A                  | No `"editor"` key is declared; do not infer or invent one                                                    |

Supporting maintained files inside `exercises/practice/dnd-character/`:

- `.meta/config.json`: exercise metadata, `"files"` role map, and runner flags (`flag.tests.jest = true`, `flag.tests.tstyche = false`).
- `.meta/tests.toml`: 19 canonical test-case UUID entries (19/19 included). `dnd-character.test.ts` has 25 Jest cases (6 extra track cases because `"Random character is valid"` is split into 7 tests: hitpoints plus 6 abilities).
- `.docs/instructions.md` and `.docs/introduction.md`: exercise statement and backstory.
- `package.json`, `test-runner.mjs`, `jest.config.cjs`, `babel.config.cjs`, `tsconfig.json`, `eslint.config.mjs`, `.yarnrc.yml`, `.vscode/*`, and tracked empty `yarn.lock`.

## How Runners Find and Wire the Files

1. **Track CI / test preparation (`scripts/helpers.mjs`)**:
   - `fileConfiguration('practice/dnd-character')` (`scripts/helpers.mjs:117-145`) reads `exercises/practice/dnd-character/.meta/config.json` (falling back to the root `config.json:21-31` `%{kebab_slug}` template if `.meta/config.json` lacks `files.test`).
   - `prepare()` (`scripts/helpers.mjs:338-413`) copies `dnd-character.test.ts` into `tmp_exercises/`, un-skips `xit`/`xtest`/`xdescribe`, and copies `.meta/proof.ci.ts` over `tmp_exercises/dnd-character.ts` (rewriting `"from '../"` to `"from './"`).
2. **Standalone exercise runner (`test-runner.mjs`)**:
   - Looks for `.meta/config.json` (or `.exercism/config.json` when downloaded via Exercism CLI) (`test-runner.mjs:37-58`) to read `custom['flag.tests.jest']` and `custom['flag.tests.tstyche']`, then runs `corepack yarn lint:types` (`tsc --noEmit -p .`) and `corepack yarn test:implementation` (`jest`).
3. **Jest test discovery & import resolution**:
   - `jest.config.cjs:4-8` sets `testMatch` to `['**/__tests__/**/*.[jt]s?(x)', '**/test/**/*.[jt]s?(x)', '**/?(*.)+(spec|test).[jt]s?(x)']`, which discovers `dnd-character.test.ts`.
   - `dnd-character.test.ts:2` imports `{ DnDCharacter }` from `'./dnd-character.ts'`.

## Maintained Source Files vs. Generated Artifacts

| Category              | Paths                                                                                                                                                                                                                            | Notes                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Maintained in Git     | `dnd-character.ts`, `dnd-character.test.ts`, `.meta/*`, `.docs/*`, `test-runner.mjs`, `jest.config.cjs`, `tsconfig.json`, `babel.config.cjs`, `eslint.config.mjs`, `package.json`, `.yarnrc.yml`, `.vscode/*`, empty `yarn.lock` | Tracked in repository; `yarn.lock` in exercise dirs is intentionally empty (`0` bytes) |
| Generated / Ephemeral | `tmp_exercises/`, `.pnp.cjs`, `.pnp.loader.mjs`, `.yarn/`, `node_modules/`, populated exercise `yarn.lock`                                                                                                                       | Produced only by Yarn PnP / `scripts/helpers.mjs` in isolated runs; never committed    |

## Reproducible Validation Commands

Validate `.meta/config.json` file roles and path safety:

```bash
python3 tools/course_checks/r47-t038.py exercises/practice/dnd-character
```

Run the full isolated verification (including 3 negative fixtures and 25 Jest cases):

```bash
python3 work/R47-T038/check.py
```

Expected final line:

```text
RESULT: PASS - executed 25 cases
```
