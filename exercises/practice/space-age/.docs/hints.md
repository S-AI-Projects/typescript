# Hints

## TypeScript-Specific Guidance for Space Age

This exercise is a great opportunity to practise two TypeScript features that are
commonly used together: **`const` object lookup tables** and **literal-union narrowing**.

---

### 1. Defining the Planet Lookup Table

A plain JavaScript object with numeric values works fine, but TypeScript lets you
lock down the shape at compile time so the compiler catches typos at the call site:

```typescript
// The `as const` modifier makes all values readonly literals (0.2408467, not number)
const ORBITAL_PERIODS = {
  mercury: 0.2408467,
  venus:   0.61519726,
  earth:   1,
  // ...
} as const
```

The type of `ORBITAL_PERIODS` is then:
```
{ readonly mercury: 0.2408467; readonly venus: 0.61519726; readonly earth: 1; ... }
```

---

### 2. Deriving the Planet Union Type

Instead of writing `type Planet = 'mercury' | 'venus' | 'earth' | ...` by hand, derive
it from the object so the two can never go out of sync:

```typescript
type Planet = keyof typeof ORBITAL_PERIODS
// equivalent to: 'mercury' | 'venus' | 'earth' | 'mars' | 'jupiter' | 'saturn' | 'uranus' | 'neptune'
```

**Why `keyof typeof` and not just `keyof`?**  
`typeof ORBITAL_PERIODS` turns the *value* into a *type*; `keyof` then extracts its
string-literal key union. You need both steps because `ORBITAL_PERIODS` is a value, not
a type.

---

### 3. Using the Derived Type in the Function Signature

```typescript
export const age = (planet: Planet, seconds: number): number => {
  // TypeScript guarantees `planet` is a valid key of ORBITAL_PERIODS here
  // — no runtime guard needed
}
```

**Common pitfall:** if you write `planet: string` instead, TypeScript will not let you
index `ORBITAL_PERIODS[planet]` without a type assertion, because `string` is wider
than the key union.

---

### 4. Static vs. Runtime Validation

| Concern | Static (compile-time) | Runtime |
|---------|----------------------|---------|
| Invalid planet name | ✅ Caught by TypeScript if caller is also typed | ❌ Not checked at runtime |
| Negative seconds | ❌ Not checked by types (`number` is wide) | ✅ Needs explicit guard |

The reference solution only uses static validation — the type system guarantees the
planet is valid, but it does not guard against `seconds < 0`. That is intentional for
this exercise.

---

### 5. Putting It Together — Partial Sketch

```typescript
// Step 1: build the lookup table
const PERIODS = { mercury: 0.2408467, /* … */ } as const

// Step 2: derive Planet type from the table
type Planet = keyof typeof PERIODS

// Step 3: write the function — TypeScript infers the index is safe
export const age = (planet: Planet, seconds: number): number => {
  const EARTH_YEAR_SECONDS = 31_557_600
  const earthYears = seconds / EARTH_YEAR_SECONDS
  // divide by orbital period ratio, then round to 2 decimal places
  return Number((earthYears / PERIODS[planet]).toFixed(2))
}
```

The `31_557_600` literal uses TypeScript's (and ES2021's) numeric separator for
readability — `365.25 * 24 * 60 * 60 = 31,557,600`.
