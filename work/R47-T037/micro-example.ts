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
