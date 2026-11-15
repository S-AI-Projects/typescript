# Raindrops — canonical case rationale (R47-T041)

Maintainer notes for `exercises/practice/raindrops`, prepared by Advait Bodkhe
for task R47-T041 (issue #41). This document records why the three selected
canonical cases in `.meta/tests.toml` are included, and how each one maps to
the TypeScript test file and the reference implementation
(`.meta/proof.ci.ts`).

## Selected cases

| tests.toml UUID | Canonical description | Test in `raindrops.test.ts` | Input → expected | Rationale |
| --- | --- | --- | --- | --- |
| `1575d549-e502-46d4-a8e1-6b7bec6123d8` | the sound for 1 is 1 | `converts 1` | `convert(1)` → `"1"` | 1 is divisible by none of 3, 5 or 7, so no sound is appended and the reference falls back to `drops.toString()`. This is the selected case that covers the no-factor fallback branch, where the number itself is stringified. |
| `1f51a9f9-4895-4539-b182-d7b0a5ab2913` | the sound for 3 is Pling | `converts 3` | `convert(3)` → `"Pling"` | 3 is the smallest input with a factor of 3, so it covers the first conditional (`drops % 3 === 0` appends `'Pling'`) in isolation, with no concatenation from the 5 or 7 branches. |
| `2d9bfae5-2b21-4bcd-9629-c8c0e388f3e0` | the sound for 5 is Plang | `converts 5` | `convert(5)` → `"Plang"` | 5 is the smallest input with a factor of 5 and no factor of 3 (`5 % 3 !== 0`), so it covers the second conditional (`drops % 5 === 0` appends `'Plang'`) independently and proves `'Plang'` is not a side effect of the 3 branch. |

The same rationales are stored as `comment` keys beside the three UUIDs in
`exercises/practice/raindrops/.meta/tests.toml`, so they survive
regeneration of that file. No `include` value was changed.

## Inclusion counts

| | Before | After |
| --- | --- | --- |
| Canonical entries in `tests.toml` | 18 | 18 |
| Included | 18 | 18 |
| Excluded (`include = false`) | 0 | 0 |

## Verification

Run:

```bash
python3 work/R47-T041/check.py
```

The check copies the exercise to a temporary directory, substitutes the
reference (`.meta/proof.ci.ts`) for the learner stub in that copy only,
enables every case, and runs the tests. Latest result: 16 passed, 0 failed,
16 total — the three named cases (`converts 1`, `converts 3`, `converts 5`)
and all other enabled cases pass against the reference, and the learner stub
in the working tree is unchanged. Full evidence is in `work/R47-T041/`
(`results.json`, `RESULTS.md`, `test-output.txt`).

## Observation (recorded, not changed)

Three canonical entries in `tests.toml` — the cases for inputs 8
("2 to the power 3…"), 27 and 3125 — have no corresponding test in this
track's `raindrops.test.ts`, and the test file has one extra test
(`converts 12121`) with no `tests.toml` entry. This task does not change any
inclusion to address that; it is recorded here so a maintainer can decide
whether the generated test file should be regenerated.
