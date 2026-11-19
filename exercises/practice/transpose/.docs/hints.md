# Hints

## Handling Uneven Line Lengths and Left Padding

### The Mistaken Assumption
When transposing rows of text into columns, a common mistake is assuming you can directly append each character at `line[row]` to the output string `transposed[row]` without accounting for missing characters from earlier lines.

This naive concatenation works when all lines have the same length, or when earlier lines are longer than later lines. However, if a later line is longer than an earlier line, the character from the later line must align at its correct column index. Any positions corresponding to shorter earlier lines must be padded to the left with spaces.

### Diagnostic Example
Consider this small two-line input:

```typescript
['A', 'BC']
```

- **Line 0**: `'A'` has length 1 (only row index 0).
- **Line 1**: `'BC'` has length 2 (row indices 0 and 1).

**Expected transposed output**:
```typescript
['AB', ' C']
```

**Common incorrect output** (missing left-padding):
```typescript
['AB', 'C']
```

In the second output row (`' C'`), character `'C'` comes from Line 1 (column 1). Because Line 0 only had length 1, there was no character at column 0 for that row. Therefore, `'C'` must be padded with a space on its left so it sits at column index 1.

### Debugging Tip
Before appending a character to an output row, ensure the string has been padded with spaces up to the current column index (for example, using JavaScript's `.padEnd()` method). Remember: pad with spaces to the left to preserve column positions, but do not add trailing spaces to the right.
