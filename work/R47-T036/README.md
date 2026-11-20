# R47-T036 Check (`robot-simulator`)

## What It Verifies

`work/R47-T036/check.py` verifies:

1. `.meta/config.json` resolves `solution`, `test`, and `example` files inside `exercises/practice/robot-simulator`.
2. Learner files (`robot-simulator.ts`, `robot-simulator.test.ts`, `.meta/proof.ci.ts`) remain unsolved and identical to `org/main`.
3. `work/R47-T036/alternative.ts` implements an independent direction-index + unit-vector lookup table approach (`COMPASS`, `STEP_VECTORS`, `%`, `Map`, no `switch`) whose token stream differs substantially from `.meta/proof.ci.ts`.
4. In separate isolated temporary copies, BOTH `.meta/proof.ci.ts` and `work/R47-T036/alternative.ts` compile with `tsc`, enable all `xdescribe`/`xit` blocks to run the exact same 22 Jest cases (including `"facing north by default"`, `"facing east"`, `"facing west, at origin"`), and `alternative.ts` passes `corepack yarn lint:ci`.
5. Negative controls confirm `evaluate()` catches assertion failures, zero-test runs, and non-zero child exit codes.

## How to Run

From the repository root:

```bash
python3 work/R47-T036/check.py
```

## Last Run Result

```text
RESULT: PASS - executed 22 cases
```

## Evidence Index

- `work/R47-T036/notes.md` — inspection notes and approach comparison
- `work/R47-T036/alternative.ts` — direction-index + unit-vector implementation
- `work/R47-T036/approach-comparison.json` — token similarity ratio and case counts for both implementations
- `work/R47-T036/reference-*` / `alternative-*` logs and `alternative-jest-results.json`
- `work/R47-T036/tool-versions.json`, `inputs.json`, `counts.json`, `expected-vs-actual.json`, `jest-results.json`, `negative-controls.json`
