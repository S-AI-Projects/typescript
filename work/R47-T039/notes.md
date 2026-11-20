# Notes for R47-T039 (`isbn-verifier`)

## Inspected Files

- `exercises/practice/isbn-verifier/.docs/instructions.md` (lines 1-42): ISBN-10 validation formula `(d1*10 + ... + d10*1) mod 11 == 0`, optional separating hyphens, `'X'`/`'x'` check character representing `10`.
- `exercises/practice/isbn-verifier/.meta/config.json` (lines 1-31): `files.solution = ["isbn-verifier.ts"]`, `files.test = ["isbn-verifier.test.ts"]`, `files.example = [".meta/proof.ci.ts"]`. Jest enabled, TStyche disabled.
- `exercises/practice/isbn-verifier/.meta/tests.toml` (lines 1-73): 21 canonical entries (`21/21/0`).
- `exercises/practice/isbn-verifier/isbn-verifier.test.ts` (lines 1-92): 22 test cases (`1` `it`, `21` `xit`). Extra track case beyond `tests.toml`: `"too long isbn"` (`lines 53-55`, `isValid('3-598-21507-XX')`).
- `exercises/practice/isbn-verifier/isbn-verifier.ts` (lines 1-3): learner stub throwing `'Remove this line and implement the function'`.
- `exercises/practice/isbn-verifier/.meta/proof.ci.ts` (lines 1-18): strips hyphens, validates `/^(\d{9}[\dxX])$/`, converts check digit `X`/`x` to `'10'`, checks weighted sum `% 11 === 0`.

## Safety Requirements for Isolated Runner

- `tools/course_checks/r47-t039.py` never writes inside `exercises/practice/isbn-verifier`, never invokes `corepack yarn` inside the working tree, hashes all exercise files before and in `finally:`, creates a `r47-t039-` temp dir, prints `TEMP_DIR: <path>`, and cleans up on normal exit, test failure, zero-test guard failure, and `SIGINT`/`SIGBREAK` interruption.
