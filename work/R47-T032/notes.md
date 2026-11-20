# Notes for R47-T032 (`accumulate`)

## Inspected Files

- `scripts/test.mjs` (lines 1-31): sets `PREPARE=true`, `CLEANUP=true`, calls `helpers.prepareAndRun('corepack yarn tstyche tmp_exercises --failFast && corepack yarn jest --bail tmp_exercises', ...)`.
- `scripts/helpers.mjs` (lines 117-145, 166-244, 338-413):
  - `fileConfiguration(assignment)` reads `exercises/<assignment>/.meta/config.json` (lines 118-132), falling back to root `config.json` `files` template (line 134).
  - `prepareAndRun(command, infoStr, failureStr)` checks `shouldPrepare()` (`PREPARE`), creates `tmp_exercises/`, copies `COMMON_FILES` from `common/`, calls `prepare(assignment)` for one assignment or all, runs `command`, and cleans up if `shouldCleanup()` (`CLEANUP`).
  - `prepare(assignment)` copies each test file to `tmp_exercises/<test>` and applies four `shell.sed` rules in order (lines 367-378) to enable `xit`/`xtest`/`xdescribe` while preserving `it.skip`/`describe.skip`. It then copies `exampleFiles` (`.meta/proof.ci.ts`) to `tmp_exercises/<solution>` replacing `"from '../"` with `"from './"` (lines 383-388).
  - `cleanUp()` removes `tmp_exercises`, `exercise-package.json`, `exercise-package.json.sha` (lines 240-244).
- `scripts/ci.mjs` (lines 1-53) and `scripts/pr.mjs` (lines 1-89): call `prepare` directly with `PREPARE=false`/`CLEANUP=false`, run `corepack yarn jest --bail tmp_exercises`, then call `cleanUp()`.
- `.github/workflows/ci.js.yml` (lines 1-89) & `.github/workflows/pr.ci.js.yml` (lines 1-112): use `corepack yarn install --immutable` at repo root, then `corepack yarn ci:check` / `corepack yarn ci` / `scripts/pr-check.mjs` / `scripts/pr.mjs`.
- `config.json` (lines 1397-1410): `accumulate` has `"status": "deprecated"`.
- `exercises/practice/accumulate/`:
  - No `.meta/tests.toml` and no `.docs/introduction.md`.
  - `.docs/instructions.md` (lines 1-26): implement `accumulate` without using standard library `map`.
  - `.meta/config.json` (lines 1-34): `files.solution = ["accumulate.ts"]`, `files.test = ["accumulate.test.ts"]`, `files.example = [".meta/proof.ci.ts"]`.
  - `accumulate.ts` (lines 1-3): learner stub throwing `'Remove this line and implement the function'`.
  - `accumulate.test.ts` (lines 1-43): 5 test cases (`1` active `it`, `4` skipped `xit`), hand-maintained.
  - `.meta/proof.ci.ts` (lines 1-11): generic `accumulate<T, O>(list: T[], accumulator: (arg: T) => O): O[]` implementation.
- `configlet` check: `./bin/configlet sync -e accumulate` exited `1` reporting `` `accumulate` is not an slug in the track config `` because `accumulate` is deprecated in `config.json`.

## Generated vs. Hand-Maintained Files

- **Hand-maintained**:
  - `exercises/practice/accumulate/accumulate.test.ts`
  - `exercises/practice/accumulate/accumulate.ts`
  - `exercises/practice/accumulate/.meta/proof.ci.ts`
  - `exercises/practice/accumulate/.meta/config.json`
  - `exercises/practice/accumulate/.docs/instructions.md`
  - `common/*` (`package.json`, `tsconfig.json`, `jest.config.cjs`, `babel.config.cjs`, `eslint.config.mjs`, `test-runner.mjs`, `.yarnrc.yml`, `.vscode/*`)
- **Generated at test/lint time in `tmp_exercises/`**:
  - `tmp_exercises/accumulate.test.ts` (from `accumulate.test.ts` via `prepare()` `shell.sed` un-skipping)
  - `tmp_exercises/accumulate.ts` (from `.meta/proof.ci.ts` via `prepare()` with `"from '../"` -> `"from './"`)
  - `tmp_exercises/<COMMON_FILES>` (copied from `common/`)
  - `tmp_exercises/lib/`, `tmp_exercises/data/` (created empty when no `lib/` or `data/` dir exists in exercise)
