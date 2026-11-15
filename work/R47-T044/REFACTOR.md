# R47-T044 — pangram reference readability refactor

One scoped readability improvement in
`exercises/practice/pangram/.meta/proof.ci.ts`, by Advait Bodkhe:

- The alphabet is no longer built from the unexplained magic number
  `65`: it is now `String.fromCharCode('A'.charCodeAt(0) + index)`, so
  the reader can see the letters run from 'A' without knowing ASCII
  codes by heart.
- The counter map and its loop variables are named for what they hold
  (`myMap` → `letterCounts`, `each`/`item` → `character`/`count`), so
  the scan reads as "count each character, then look for a letter whose
  count stayed zero".
- A comment at the top states the exercise-specific invariant the whole
  function rests on: a sentence is a pangram exactly when every letter
  a–z occurs at least once, so only zero vs non-zero counts matter.

Why it helps this exercise: the pangram rule is a statement about the
alphabet, not about the sentence; naming the alphabet's start and the
per-letter counters makes that rule visible in the code, which is what
a learner reading the reference needs.

No logic, return type, ordering or error behaviour changed, and no new
dependency or public API change was introduced. The learner stub
(`pangram.ts`) is untouched.

Verification:

- `python3 work/R47-T044/check.py` — all 10 enabled cases pass against
  the refactored reference (see `results.json`).
- `node work/R47-T044/before-after.mjs` — the original and refactored
  implementations agree on 17 inputs (every sentence in
  `pangram.test.ts` plus edge cases); output saved in
  `before-after.txt`, 0 disagreements.
