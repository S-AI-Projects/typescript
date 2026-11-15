# Hints

## Choosing an approach

Two genuinely different ways to build the transposition both work.
Pick by what you find easier to reason about — and handle the short
last row carefully in either one; it is where the trailing-space
padding in the output comes from.

Worked example, using `Chill out.` — the normalized text is
`chillout` (8 characters), so the rectangle is 3 columns wide
(⌈√8⌉ = 3) and 3 rows tall, with the last row short:

```text
c h i
l l o
u t
```

Reading down the columns gives `clu`, `hlt`, `io`, and the output is
those chunks padded to the chunk length and joined with spaces:
`clu hlt io ` — note the trailing space after `io`.

**Approach A — build the rectangle.** Split the normalized text into
rows, then collect each column into its own list and join the lists.
The intermediate grid mirrors the picture above, which makes it easy
to trace and debug by printing it. The cost is the extra memory for
the row/column structure (a second copy of the text, plus per-column
lists) and the bookkeeping of two passes over the characters.

**Approach B — index arithmetic, no rectangle.** The character at
(row, column) of the rectangle sits at index `row * columns + column`
of the normalized string, so you can walk column by column and read
characters straight out of the string, skipping any index that falls
past the end of the text (those are exactly the missing cells of the
short last row). This uses no intermediate grid — just the output
string being built — but the index formula is easier to get wrong
than the picture, especially at the ragged edge; test it against the
example above before trusting it.

Trade-off in one line: A spends memory to make the geometry visible;
B spends care on arithmetic to avoid the extra structure. For the
short inputs this exercise uses, either is fast enough — choose the
one you can verify.
