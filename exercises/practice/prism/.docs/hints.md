# Hints

## General

- Step from the starting point and angle by repeatedly finding the **closest** prism strictly ahead along the current laser ray (within the floating-point collinearity tolerance), recording its `id`, updating `(x, y)` to that prism's coordinates, and adding its deflection `angle` modulo `360`.
- Stop and return the collected sequence of `id`s as soon as no prism lies ahead along the ray.

## TypeScript: narrowing `T | undefined`

Under `"strict": true`, TypeScript enables `strictNullChecks`, so a variable that holds either a hit or "not found yet" must include `undefined` in its type — for example, `let nearest: Prism | undefined` (where `Prism` is an intersection type `Point & { id: number }`).

Because `nearest` has the union type `Prism | undefined`, you cannot read `nearest.id` until TypeScript's control-flow analysis **narrows** the union down to `Prism`. Testing `if (!nearest) break` (or `if (nearest === undefined) break`) tells the compiler that execution only continues past the `if` when `nearest` is a `Prism`, making `nearest.id`, `nearest.x`, `nearest.y`, and `nearest.angle` type-safe without type assertions.

Note that the exercise contract uses ordinary mutable types (`(start: Point, prisms: Prism[]): number[]` without `readonly`) and performs **no runtime type validation** — `Point` and `Prism` exist only at compile time and are erased from the emitted JavaScript.

### Micro-example and falsy-zero pitfall

For object unions (`Target | undefined`), `!best` and `best === undefined` behave identically because every object is truthy. For primitive unions like `id: number | undefined` (for instance, if you track `nearestId: number | undefined` instead of the object), `!id` treats `0` as falsy and wrongly reports a miss when `id === 0`:

```ts
type Target = { id: number; distance: number }

function pickNearest(targets: Target[]): Target | undefined {
  let best: Target | undefined
  for (const item of targets) {
    if (best === undefined || item.distance < best.distance) {
      best = item
    }
  }
  return best
}

function summarizeFalsyBug(id: number | undefined): string {
  // Pitfall: 0 is falsy, so `!id` misclassifies id = 0 as missing
  if (!id) {
    return 'none'
  }
  return `hit #${id}`
}

function summarizeStrict(id: number | undefined): string {
  if (id === undefined) {
    return 'none'
  }
  return `hit #${id}`
}

const nearest = pickNearest([
  { id: 2, distance: 25 },
  { id: 1, distance: 10 },
])
if (nearest !== undefined) {
  console.log(`nearest=${nearest.id}`)
}
const missing = pickNearest([])
console.log(missing === undefined ? 'empty=none' : `empty=${missing.id}`)
console.log(`falsy(0)=${summarizeFalsyBug(0)}`)
console.log(`strict(0)=${summarizeStrict(0)}`)
console.log(`strict(undefined)=${summarizeStrict(undefined)}`)
```

Expected output:

```text
nearest=1
empty=none
falsy(0)=none
strict(0)=hit #0
strict(undefined)=none
```

`falsy(0)` returns `'none'` because `!0` is `true` in JavaScript, whereas `strict(0)` checks `id === undefined` (`false` for `0`) and preserves the hit `'hit #0'`.

Further reading: [TypeScript Handbook: Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
