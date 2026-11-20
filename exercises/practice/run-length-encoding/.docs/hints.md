# Hints

## Two Approaches to Run-Length Encoding

There are two common strategies for implementing `encode` and `decode`. Both are correct — choose whichever you find easier to reason about.

---

### Approach 1 — Regex Replace (Concise)

JavaScript's `String.prototype.replace` with a capturing group and a callback can handle the entire scan in one pass.

**Key idea for `encode`:**
- Match a character followed by zero or more of the same character: `/(\w|\s)\1*/g`
- In the callback, prepend the run-length only when the run is longer than 1

**Partial sketch (not a full implementation):**
```
// match a run of identical characters, then format it
plaintext.replace(/(X)\1*/g, (match) => /* use match.length and match[0] */)
```

**Key idea for `decode`:**
- Match a leading digit group followed by a single character: `/(\d+)(\w|\s)/g`
- Repeat that character the specified number of times

**Partial sketch:**
```
// expand a count-char pair
cypher.replace(/(\d+)(X)/g, (_match, repeats, char) => char.repeat(Number(repeats)))
```

**Trade-offs:**
- ✅ Very concise — each function is a single expression
- ⚠️ The character class matters: `\w` covers `[A-Za-z0-9_]`; include `\s` to handle spaces
- ⚠️ Back-references (`\1`) only work in the *pattern* string, not inside character classes

---

### Approach 2 — Imperative Loop (Explicit State)

Scan the string character by character with a counter variable. This makes the state machine explicit and can be easier to debug.

**Key idea for `encode`:**
- Walk from left to right, incrementing a `count` while the next character equals the current one
- When the character changes (or the string ends), flush `(count > 1 ? count : '') + currentChar`

**Worked example — encoding `'AABBBCCCC'`:**

| Step | Current char | Count | Output so far |
|------|-------------|-------|---------------|
| 0    | A           | 1     | ``            |
| 1    | A           | 2     | ``            |
| 2    | B (change!) | flush | `2A`          |
| 3    | B           | 2     | `2A`          |
| 4    | B           | 3     | `2A`          |
| 5    | C (change!) | flush | `2A3B`        |
| 6    | C           | 2     | `2A3B`        |
| 7    | C           | 3     | `2A3B`        |
| 8    | C           | 4     | `2A3B`        |
| end  | —           | flush | `2A3B4C`      |

**Trade-offs:**
- ✅ Every decision is explicit — easy to add logging or assertions
- ✅ No regex syntax to debug
- ⚠️ More code; remember to flush the final run after the loop exits

---

### Edge Cases Both Approaches Must Handle

| Input | Expected `encode` output |
|-------|--------------------------|
| `''` (empty) | `''` |
| `'XYZ'` | `'XYZ'` (no counts for single chars) |
| `'AABBBCCCC'` | `'2A3B4C'` |
| `'  hsqq qww  '` | `'2 hs2q q2w2 '` (spaces are valid characters) |

And the round-trip property must hold:  
`decode(encode(s)) === s` for any valid string `s`.
