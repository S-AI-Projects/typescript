# Word Search — mutation record (R47-T043)

Maintainer notes for `exercises/practice/word-search`, prepared by Advait
Bodkhe for task R47-T043 (issue #43). A deliberate mutant of the reference
implementation was used to find an existing test that distinguishes a
wrong implementation from a correct one.

## The mutant

Base: the maintained reference, `exercises/practice/word-search/.meta/proof.ci.ts`.

One change only, in the output construction of `findOne` — the reference
converts each internal 0-based path coordinate to the reported position
with `+ 1`; the mutant drops that conversion:

```diff
- start: path[0].map((c) => c + 1),
- end: path[path.length - 1].map((c) => c + 1),
+ start: path[0].map((c) => c),
+ end: path[path.length - 1].map((c) => c),
```

Mistaken assumption exposed: that puzzle positions are reported 0-based,
like array indices. The exercise contract reports positions 1-based —
the first row and the first column are 1, as every locating test in the
suite expects.

## Rejecting test

- Test: `should locate a word written left to right`
  (`word-search.test.ts`, describe block "single line grids")
- tests.toml UUID: `6b22bcc5-6cbf-4674-931b-d2edbff73132`
  ("Should locate one word written left to right")
- Input: grid `['clojurermt']`, words `['clojure']`
- Expected behaviour: `{ clojure: { start: [1, 1], end: [1, 7] } }`
- Mutant behaviour: `{ clojure: { start: [0, 0], end: [0, 6] } }` — the
  word is found in the right place, but every reported coordinate is one
  less, so the assertion fails.

Smallest diagnostic input (same failure, minimal size): grid `['ab']`,
word `'ab'` — expected `start: [1, 1], end: [1, 2]`; the mutant reports
`[0, 0]` and `[0, 1]`.

## Verification

```bash
python3 work/R47-T043/check.py
```

The check runs the full suite twice in a temporary copy, against the
reference and against the mutant. Latest results: the reference passes
all 26 enabled cases; the mutant fails 20 of 26 (the 6 it still passes
are the cases that expect `undefined` or only construct the class, which
never inspect coordinates), and the rejecting test above is among the
failures. Evidence is in `work/R47-T043/`. The learner stub in the
working tree is unchanged, and no claim is made that the current
reference is buggy — it passes the whole suite.
