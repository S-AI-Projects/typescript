# Hints

## General

- Traditional Roman numerals represent positive integers from `1` (`I`) up to `3,999` (`MMMCMXCIX`).
- Build the numeral from largest to smallest symbol values, including the six subtractive forms (`IV = 4`, `IX = 9`, `XL = 40`, `XC = 90`, `CD = 400`, `CM = 900`), while never repeating the same additive symbol more than three times in a row.

## Walkthrough and decision table (`1`, `2`, and `3`)

For inputs `1`, `2`, and `3`, no subtractive rule applies yet (`4 = IV` lies outside this subset): `I` (`1`) is the largest symbol less than or equal to `n`, so the numeral is built by repeating `I` up to the three-repetition limit:

| Input condition | Rule from the spec                                                                                                                                                 | Required output |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- |
| `n = 1`         | `I` (`1`) is the largest symbol `<= 1`; emit `I` once                                                                                                              | `'I'`           |
| `n = 2`         | `I` (`1`) is the largest symbol `<= 2`; repeat `I` twice (`1 + 1`)                                                                                                 | `'II'`          |
| `n = 3`         | `I` (`1`) is the largest symbol `<= 3`; repeat `I` three times (`3` is the maximum repetitions before subtractive `4 = IV`, which is outside these selected cases) | `'III'`         |

## TypeScript representation

The test suite calls `toRoman(number: number): string`: a JavaScript/TypeScript `number` input and a `string` output. Because `number` is an IEEE-754 floating-point type with no integer-range refinement, `number` statically admits `0`, negative values, fractions (such as `1.5`), `Infinity`, and `NaN` in addition to integers `1`–`3999`.

## Unspecified behaviour

Inputs outside the integer range `1`–`3999` and non-integers (such as `0`, negative numbers, fractions, `Infinity`, or `NaN`) are **unspecified** by this exercise's instructions (`instructions.md` states only traditional Roman numerals up to `MMMCMXCIX` / `3,999`) and by `roman-numerals.test.ts` (all 27 tests pass integers in `1..3999`). Accordingly, the contract imposes no exception, clamping, rounding/coercion, or ordering requirement for out-of-domain inputs.
