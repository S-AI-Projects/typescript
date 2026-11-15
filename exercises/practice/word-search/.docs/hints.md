# Hints

## Debugging: every position is off by one

The locations you return are counted the way a player counts rows and
columns on the printed puzzle: the first row is row 1 and the first
letter of a row is column 1. Array indices inside your code start at 0,
reported positions start at 1.

If a word is being found in the right place but the reported `start`
and `end` are each exactly one less than expected in both coordinates,
your search is probably correct and the conversion is not: check the
single place where internal 0-based coordinates become the reported
result, for both the start and the end of the word.

Small diagnostic: with the grid `['ab']`, searching for `'ab'` must
report `start: [1, 1]` and `end: [1, 2]`. If you get `[0, 0]` and
`[0, 1]` instead, the off-by-one is in the reporting step, not in the
search itself.
