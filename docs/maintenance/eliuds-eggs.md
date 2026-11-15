# Eliuds Eggs — test generation path (R47-T042)

Maintainer notes for `exercises/practice/eliuds-eggs`, prepared by Advait
Bodkhe for task R47-T042 (issue #42). This page documents how the exercise's
tests are produced and how to reproduce and verify that route.

## Generated vs maintained files

| File | How it is produced |
| --- | --- |
| `exercises/practice/eliuds-eggs/.meta/tests.toml` | **Generated/synced** by configlet from the canonical data for `eliuds-eggs` in exercism/problem-specifications. It lists each canonical case's UUID and description, plus any `include = false` exclusions. |
| `exercises/practice/eliuds-eggs/eliuds-eggs.test.ts` | **Maintained by hand** in this track. There is no per-exercise template (no Jinja or similar) and no track script that generates this file; maintainers write the Jest tests so that they implement exactly the cases `tests.toml` includes. |
| `exercises/practice/eliuds-eggs/.meta/proof.ci.ts` | Maintained by hand; the reference implementation the tests are verified against in CI. |
| `exercises/practice/eliuds-eggs/eliuds-eggs.ts` | Learner stub; never generated and never edited by this process. |

## Exact generation command (tests.toml)

From the repository root:

```bash
./bin/fetch-configlet
./bin/configlet sync --tests --exercise eliuds-eggs
```

`configlet sync` compares `tests.toml` against the canonical data and
updates the `description` (and any `reimplements`) keys. It does **not**
touch `eliuds-eggs.test.ts`; after a sync, a maintainer updates the test
file by hand if cases were added, removed or renamed, and then runs the
verification below.

Input files for the sync: the exercise's current `.meta/tests.toml` and
the canonical `data.json` for `eliuds-eggs` in problem-specifications
(fetched by configlet). Input files for the hand-maintained test file:
`.meta/tests.toml` (which cases exist) and `.docs/instructions.md`
(what the exercise promises).

## Case-to-output mapping

| UUID | Description | Test input | Expected output |
| --- | --- | --- | --- |
| `559e789d-07d1-4422-9004-3b699f83bca3` | 0 eggs | `eggCount(0)` | `0` |
| `97223282-f71e-490c-92f0-b3ec9e275aba` | 1 egg | `eggCount(16)` | `1` |
| `1f8fd18f-26e9-4144-9a0e-57cdfc4f4ff5` | 4 eggs | `eggCount(89)` | `4` |
| `0c18be92-a498-4ef2-bcbb-28ac4b06cb81` | 13 eggs | `eggCount(2000000000)` | `13` |

Each expected output is the number of 1 bits in the input's binary
representation (0 = `0`, 16 = `10000`, 89 = `1011001`,
2000000000 = `1110111001101011001010000000000`), which is what the
reference implementation counts.

## Reproducible verification

```bash
python3 tools/course_checks/r47-t042.py   # case-table round trip
python3 work/R47-T042/check.py            # full check, incl. the above
```

`tools/course_checks/r47-t042.py` parses `tests.toml` and the test file,
asserts both name exactly the same cases (no case silently dropped),
asserts every expected output equals the popcount of its input, pins the
three anchor cases (0 eggs, 1 egg, 4 eggs), and regenerates the case
table above in two fresh temporary directories — the table contains no
timestamp or other nondeterministic field, and the two generations must
be byte-identical.

Latest results: the round trip passes (4 cases in both sources, anchors
exact, regeneration deterministic), and `work/R47-T042/check.py` runs all
4 enabled cases against the reference — 4 passed, 0 failed. Evidence is
in `work/R47-T042/`.
