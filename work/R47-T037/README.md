# R47-T037 Check (`prism`)

## What It Verifies

`work/R47-T037/check.py` verifies:

1. `.meta/config.json` resolves `solution`, `test`, and `example` files inside `exercises/practice/prism`.
2. Learner files (`prism.ts`, `prism.test.ts`, `.meta/proof.ci.ts`) remain unsolved and identical to `org/main`.
3. In an isolated temporary copy, `.meta/proof.ci.ts` passes `corepack yarn test` (`tsc` + `jest`) and all 14 Jest cases (`"zero prisms"`, `"one prism one hit"`, `"one prism zero hits"`, plus the remaining 11 cases).
4. Extracts the TypeScript micro-example (`ts` code block) and expected output (`text` code block) directly from `exercises/practice/prism/.docs/hints.md`, compiles the snippet under `tsc --strict` (`--target es2020 --module nodenext --moduleResolution nodenext`), runs it in Node, and asserts exact stdout equality with the published output block.
5. Negative controls confirm `evaluate()` catches assertion failures, zero-test runs, and non-zero child exit codes.

## How to Run

From the repository root:

```bash
python3 work/R47-T037/check.py
```

## Last Run Result

```text
RESULT: PASS - executed 14 cases
```

## Evidence Index

- `work/R47-T037/notes.md` — inspection notes covering `.meta/proof.ci.ts` types and narrowing
- `work/R47-T037/micro-example.ts` — extracted TypeScript micro-example from `hints.md`
- `work/R47-T037/micro-example-expected.txt` / `micro-example-actual.txt` — published vs executed output
- `work/R47-T037/micro-example-tsc.log` — strict `tsc` output
- `work/R47-T037/tool-versions.json`, `inputs.json`, `counts.json`, `expected-vs-actual.json`, `jest-results.json`, `negative-controls.json`, and `*.log`
