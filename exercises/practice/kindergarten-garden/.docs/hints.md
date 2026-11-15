# Hints

## Working out who owns which plants

The whole exercise follows from three rules in the instructions:

1. The diagram is **two rows** of plant codes, separated by `\n`.
   Each letter is one plant: `G` grass, `V` violets, `R` radishes,
   `C` clover.
2. Students are ordered **alphabetically** (the default class list
   already is). Each student owns a **2×2 block**: the two adjacent
   columns starting at column `2 × (student's position)`, in both
   rows.
3. `plants(student)` returns that block in reading order: the two
   plants from the first row, then the two from the second row.

Walkthrough of the three smallest cases from the test suite:

**Garden with single student** — diagram `"RC\nGG"`, `plants('Alice')`.
Alice is student 0, so her columns are 0 and 1. First row gives
`R, C` → radishes, clover; second row gives `G, G` → grass, grass.
Result: `['radishes', 'clover', 'grass', 'grass']`.

**Different garden with single student** — diagram `"VC\nRC"`,
`plants('Alice')`. Same columns, different letters: `V, C` →
violets, clover; then `R, C` → radishes, clover.
Result: `['violets', 'clover', 'radishes', 'clover']`.
Nothing about the method changes — only the codes in the diagram do.

**Garden with two students** — diagram `"VVCG\nVVRC"`,
`plants('Bob')`. Bob is student 1, so his columns are 2 and 3, not 0
and 1: first row `C, G` → clover, grass; second row `R, C` →
radishes, clover.
Result: `['clover', 'grass', 'radishes', 'clover']`.
The only new idea is the offset: student *n* starts at column *2n*.

### Decision table

| Condition | Required result |
| --- | --- |
| Student's alphabetical position is *i* | Their plants are at columns *2i* and *2i + 1* of each row |
| Diagram row pair for those columns is `XY` / `ZW` | `plants()` returns `[name(X), name(Y), name(Z), name(W)]`, first row first |
| Code is `G` / `V` / `R` / `C` | `grass` / `violets` / `radishes` / `clover` |
| A custom student list is passed | The list is sorted alphabetically before positions are assigned; a student's plants depend on their sorted position, not the order the list was written in |

### What the exercise leaves unspecified

The instructions and tests say nothing about: asking for a student
who is not in the list, a diagram with other than two rows, rows of
unequal or odd length, letters other than `G`, `V`, `R`, `C`, or an
empty diagram. Those inputs are outside the exercise contract — the
tests never exercise them, and a solution is not required to throw a
particular error, coerce them into valid input, or return a
particular value for them. Don't invent rules for them; implement
exactly the specified behaviour above.
