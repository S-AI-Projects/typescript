# Hints

## Concept: Runtime vs. Static Validation

When working with TypeScript, it is important to understand the boundary between **static validation** (performed by the TypeScript compiler at build time) and **runtime validation** (checks executed by JavaScript while your code runs).

In this exercise, the function signature:

```typescript
export const colorCode = (color: string): number
```

uses the general type `string` for the `color` argument.

- **Static Validation (Compile Time):** The TypeScript compiler ensures that callers supply a `string` primitive. Passing a number, boolean, object, or undefined will produce a compilation error before the code ever runs.
- **Runtime Validation (Execution Time):** The static type `string` permits *any* string value (e.g. `"black"`, `"white"`, `"orange"`, or even `"purple"`). TypeScript does not inspect or restrict strings to resistor color names at compile time. Instead, finding the corresponding number or checking if a color is valid occurs at runtime using array operations such as `COLORS.indexOf(color)`.

### Standalone Example

Here is a small standalone example using compass directions that demonstrates how static typing and runtime lookup operate together:

```typescript
const DIRECTIONS = ['north', 'east', 'south', 'west']

export function getDirectionCode(direction: string): number {
  return DIRECTIONS.indexOf(direction)
}

// Example 1: Valid input (found in array at runtime)
console.log(getDirectionCode('north'))

// Example 2: Invalid input (passes static string check, but returns -1 at runtime)
console.log(getDirectionCode('up'))
```

### Expected Output

- **Example 1 (`getDirectionCode('north')`):** `0`
- **Example 2 (`getDirectionCode('up')`):** `-1`

### Common Mistake

A frequent misunderstanding for beginners is expecting TypeScript to prevent invalid colors (such as typos like `'balck'` or unsupported colors like `'purple'`) at compile time.

Because `color` is typed as `string`, TypeScript considers every string valid. Since types are erased when compiling to JavaScript, any validation against a list of values must happen at runtime. When `Array.prototype.indexOf()` does not find a match, it returns `-1`.

### Documentation

- [TypeScript Handbook: Static Type Checking](https://www.typescriptlang.org/docs/handbook/2/basic-types.html#static-type-checking)
- [TypeScript Handbook: Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)
