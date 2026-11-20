# Hints

## Walkthrough: Three Anchor Cases

Base conversion always follows the same two-step pipeline:

1. **Convert input digits → decimal** using positional notation (like evaluating a polynomial)
2. **Convert decimal → output digits** using repeated division by the output base

Working through three canonical test cases shows exactly how both steps work.

---

### Anchor Case 1 — `single bit one to decimal`

```
convert([1], 2, 10)  →  [1]
```

**Step 1 — to decimal:**  
The input `[1]` in base 2 means:  
`1 × 2⁰ = 1`  
Decimal value = **1**

**Step 2 — to output base 10:**  
`1 ÷ 10 = 0 remainder 1`  
Result digits (most-significant first) = `[1]`

---

### Anchor Case 2 — `binary to single decimal`

```
convert([1, 0, 1], 2, 10)  →  [5]
```

**Step 1 — to decimal (Horner's method — scan left to right):**

| Position | Digit | Running total |
|----------|-------|---------------|
| start    | —     | 0             |
| 0        | 1     | 0 × 2 + 1 = 1 |
| 1        | 0     | 1 × 2 + 0 = 2 |
| 2        | 1     | 2 × 2 + 1 = **5** |

Decimal value = **5**

**Step 2 — to output base 10:**  
`5 ÷ 10 = 0 remainder 5`  
Result digits = `[5]`

> [!TIP]
> Horner's method (`acc * base + digit`) avoids computing separate powers of the base.
> `array.reduce((acc, d) => acc * inputBase + d, 0)` implements it in one expression.

---

### Anchor Case 3 — `single decimal to binary`

```
convert([5], 10, 2)  →  [1, 0, 1]
```

**Step 1 — to decimal:**  
`[5]` in base 10 → decimal value = **5**

**Step 2 — to output base 2 (repeated division, collect remainders):**

| Iteration | Value | ÷ 2 | Remainder |
|-----------|-------|-----|-----------|
| 1         | 5     | 2   | **1**     |
| 2         | 2     | 1   | **0**     |
| 3         | 1     | 0   | **1**     |
| done      | 0     | —   | —         |

Remainders collected bottom-up (most-significant first): `[1, 0, 1]` ✅

> [!TIP]
> The `unshift` pattern (or reversing at the end) is the classic way to build the
> output array: `while (num > 0) { digits.unshift(num % outputBase); num = Math.floor(num / outputBase) }`

---

## Special Cases to Handle

| Situation | Expected behaviour |
|-----------|--------------------|
| Input `[0]` | Return `[0]` (single zero is valid) |
| Input `[1]` | Return `[1]` |
| Leading zeros (e.g. `[0, 6, 0]`) | Throw `'Input has wrong format'` |
| Empty input array | Throw `'Input has wrong format'` |
| Input base < 2 | Throw `'Wrong input base'` |
| Output base < 2 | Throw `'Wrong output base'` |

Check both bases **before** validating the input array.
