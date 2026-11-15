# Complex Numbers — file-role map (R47-T048)

Maintainer notes for `exercises/practice/complex-numbers`, prepared by
Advait Bodkhe for task R47-T048 (issue #48). This page explains which
file plays which role in the exercise, how the test runner finds them,
and how to verify the metadata that ties them together.

## The map

All paths are relative to `exercises/practice/complex-numbers/`.

| Path | Role | Source of truth |
| --- | --- | --- |
| `complex-numbers.ts` | **Learner stub** — the file a learner edits and submits. | Declared as `files.solution` in `.meta/config.json`; maintained by hand. |
| `complex-numbers.test.ts` | **Test suite** — the Jest tests the solution is judged by. | Declared as `files.test`; maintained by hand to match `.meta/tests.toml`. |
| `.meta/proof.ci.ts` | **Reference implementation** — the maintained correct solution CI substitutes for the stub. | Declared as `files.example`; maintained by hand. |
| `.meta/config.json` | **Exercise metadata** — authors, blurb, and the `files` object above. | Maintained by hand (configlet can lint it). |
| `.meta/tests.toml` | Canonical case list (UUIDs + descriptions). | **Generated/synced** by configlet from problem-specifications; do not hand-edit descriptions. |
| `.docs/instructions.md` | The exercise brief shown to learners. | Maintained by hand / synced from problem-specifications by configlet. |
| `package.json`, `jest.config.cjs`, `babel.config.cjs`, `tsconfig.json`, `eslint.config.mjs`, `test-runner.mjs` | Per-exercise tooling copies shared by all exercises in the track (install, type-check and test entry points). | Copied from the track's shared exercise template. |
| `node_modules/`, compiled output in a temp run | **Generated artifacts** — produced by installing and running; never committed as exercise content. | Created by Yarn/tsc/Jest at run time. |

This exercise's `files` object declares no `editor` files; when a
config does declare them, the checker below validates them by the
same rules.

## How the runner finds the test file and the reference

Nothing is found by guessing filenames. The runner (the track's
`scripts/test-runner.mjs`, wrapped by each exercise's
`test-runner.mjs`) reads `.meta/config.json`, takes the first entry of
`files.test` (`complex-numbers.test.ts`) and of `files.example`
(`.meta/proof.ci.ts`), copies the exercise to a working directory,
replaces the `files.solution` file (`complex-numbers.ts`) with the
reference in that copy only, enables every test case, and runs the
package's test script. If a declared path were wrong, the run would
fail before any test executed — which is why the paths are worth a
dedicated check.

## Validation

```bash
python3 tools/course_checks/r47-t048.py
python3 work/R47-T048/check.py   # full check, includes the above
```

The checker parses the `files` object (it does not search filenames),
resolves every declared path, rejects any path that escapes the
exercise directory, and requires each file to exist. It also tests
itself against three deliberately broken fixtures — a missing
reference, a missing test file, and an outside-exercise path — and
requires each to be rejected for the intended reason.

Latest results: the real `config.json` passes unchanged (no correction
was needed — every declared path resolves inside the exercise and
exists), all three fixtures are rejected as intended, and the full
check runs the suite against the reference: 30 passed, 0 failed.
Evidence is in `work/R47-T048/`.
