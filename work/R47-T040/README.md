# R47-T040 Check (`roman-numerals`)

## What It Verifies

`work/R47-T040/check.py` verifies:

1. `.meta/config.json` resolves `solution`, `test`, and `example` files inside `exercises/practice/roman-numerals`.
2. Learner files (`roman-numerals.ts`, `roman-numerals.test.ts`, `.meta/proof.ci.ts`, and `.docs/instructions.md`) remain untouched vs `org/main`.
3. Regex-parses the decision table rows for `n = 1, 2, 3` from `exercises/practice/roman-numerals/.docs/hints.md` and the three named cases (`"converts 1"`, `"converts 2"`, `"converts 3"`) from `roman-numerals.test.ts`, asserting exact agreement (`1 -> 'I'`, `2 -> 'II'`, `3 -> 'III'`) and the presence of the `"Unspecified behaviour"` section.
4. In an isolated temporary copy, compiles `.meta/proof.ci.ts` and runs all 27 Jest cases (`corepack yarn test` + `test:implementation --json`), and executes `toRoman(1)`, `toRoman(2)`, `toRoman(3)` directly against the compiled reference.
5. Negative controls confirm `evaluate()` catches assertion failures, zero-test runs, and non-zero child exit codes.

## How to Run

From the repository root:

```bash
python3 work/R47-T040/check.py
```

## Last Run Result

```text
RESULT: PASS - executed 27 cases
```

## Evidence Index

- `work/R47-T040/notes.md` — inspection notes covering `.docs/instructions.md`, `.docs/introduction.md`, `.meta/proof.ci.ts`, and `roman-numerals.test.ts`
- `work/R47-T040/named-cases-verification.json` — compiled reference outputs for `1, 2, 3` and unspecified inputs (`0, -1, 1.5, NaN`)
- `work/R47-T040/tool-versions.json`, `inputs.json`, `counts.json`, `expected-vs-actual.json`, `jest-results.json`, `negative-controls.json`, and `*.log`
