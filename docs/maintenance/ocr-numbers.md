# OCR Numbers — isolated reference runner (R47-T049)

Maintainer notes for `exercises/practice/ocr-numbers`, prepared by
Advait Bodkhe for task R47-T049 (issue #49). Maintaining this exercise
means re-running its tests against the reference implementation
without ever disturbing a learner's in-progress files. This page
documents the tool that does that.

## The tool

```bash
python3 tools/course_checks/r47-t049.py              # run the reference check
python3 tools/course_checks/r47-t049.py --self-test  # prove the runner itself
python3 work/R47-T049/check.py                       # full task check (both)
```

`tools/course_checks/r47-t049.py` reads the solution, test and
example paths from `exercises/practice/ocr-numbers/.meta/config.json`
(`ocr-numbers.ts`, `ocr-numbers.test.ts`, `.meta/proof.ci.ts`), then:

1. hashes the learner solution file in the working tree;
2. copies the whole exercise, dotfiles included, into a fresh
   temporary directory;
3. substitutes the reference for the solution **in the copy only** and
   enables every test case there;
4. runs the tests (the exercise's Yarn test script as pinned, or the
   equivalent npm/tsc/Jest steps the track runner performs);
5. reports the real executed case count and exits non-zero on any
   assertion failure, any non-zero child exit, or a run that executed
   zero tests;
6. deletes the temporary directory (always, even on failure) and
   re-hashes the learner file — the run fails if the hash changed.

## Self-test results

`--self-test` runs three scenarios and checks the exit status, the
learner-file hash and the cleanup for each:

| Scenario | Tests | Exit | Learner files |
| --- | --- | --- | --- |
| Real reference | 16 passed, 0 failed | 0 | unchanged |
| Deliberately wrong reference (`convert` returns a fixed wrong string) | 0 passed, 16 failed | 1 | unchanged |
| Empty test selection (Jest name filter matches nothing) | 0 executed, 16 skipped | 1 | unchanged |

So success, assertion failure and a zero-test run each produce the
correct exit status, temporary files are cleaned up in all three, and
the learner stub is byte-identical before and after every run —
including the failing ones. Full output is saved in
`work/R47-T049/self-test.json`, and the standard suite check
(16 passed, 0 failed against the reference) is in
`work/R47-T049/results.json`.
