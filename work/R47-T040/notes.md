# Notes for R47-T040 (`roman-numerals`)

## Inspected Files

- `exercises/practice/roman-numerals/.docs/instructions.md` (lines 1-12): convert Arabic numerals to traditional Roman numerals, largest `MMMCMXCIX` (`3,999`).
- `exercises/practice/roman-numerals/.docs/introduction.md` (lines 1-59): defines symbol values (`M..I`), rule that the same letter cannot appear more than three times in succession (`4 = IV` instead of `IIII`), subtractive pairs (`4, 9, 40, 90, 400, 900`), and decreasing-order rule.
- `exercises/practice/roman-numerals/.meta/config.json` (lines 1-31): `files.solution = ["roman-numerals.ts"]`, `files.test = ["roman-numerals.test.ts"]`, `files.example = [".meta/proof.ci.ts"]`. Jest enabled, TStyche disabled.
- `exercises/practice/roman-numerals/.meta/tests.toml` (lines 1-91): 27 canonical entries (`27/27/0`).
- `exercises/practice/roman-numerals/roman-numerals.test.ts` (lines 1-32): 27 cases (`1` `it`, `26` `xit`). Named cases:
  - Line 5: `it('converts 1', () => expect(toRoman(1)).toEqual('I'))`
  - Line 6: `xit('converts 2', () => expect(toRoman(2)).toEqual('II'))`
  - Line 7: `xit('converts 3', () => expect(toRoman(3)).toEqual('III'))`
- `exercises/practice/roman-numerals/roman-numerals.ts` (lines 1-3): learner stub throwing `'Remove this line and implement the function'`.
- `exercises/practice/roman-numerals/.meta/proof.ci.ts` (lines 1-29): greedy descending `mappings` table (`1000 'M'` down to `1 'I'`), no runtime validation; returns `''` for inputs `< 1` (like `0` or negatives).
