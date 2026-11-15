// Scaling measurement for the series reference (R47-T045).
// Run: node work/R47-T045/benchmark.mjs
//
// The Series class below is exercises/practice/series/.meta/proof.ci.ts
// with TypeScript types stripped; the algorithm is unchanged.
// Correctness is asserted BEFORE any timing. Timings measure only the
// slices() call (medians of 7 repetitions, after one warm-up call), so
// process start-up and module loading are excluded.

export class Series {
  constructor(numberString) {
    if (!numberString) {
      throw new Error('series cannot be empty')
    }
    this.numberString = numberString
    this.digits = this.getDigits()
  }

  getDigits() {
    return [...this.numberString].map((digit) => parseInt(digit, 10))
  }

  slices(sliceSize) {
    const result = []
    let slice = []

    if (sliceSize < 0) {
      throw new Error('slice length cannot be negative')
    }
    if (sliceSize === 0) {
      throw new Error('slice length cannot be zero')
    }
    if (sliceSize > this.digits.length) {
      throw new Error('slice length cannot be greater than series length')
    }

    for (let i = 0; i < this.digits.length - sliceSize + 1; i += 1) {
      for (let j = 0; j < sliceSize; j += 1) {
        slice.push(this.digits[i + j])
      }
      result.push(slice)
      slice = []
    }

    return result
  }
}

// ---- correctness first (cases taken from series.test.ts) ----
const assert = (cond, msg) => {
  if (!cond) {
    console.error(`CORRECTNESS FAILURE: ${msg}`)
    process.exit(1)
  }
}
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b)

assert(eq(new Series('1').slices(1), [[1]]), 'slices of one from one')
assert(eq(new Series('12').slices(1), [[1], [2]]), 'slices of one from two')
assert(eq(new Series('35').slices(2), [[3, 5]]), 'slices of two')
assert(
  eq(new Series('9142').slices(2), [
    [9, 1],
    [1, 4],
    [4, 2],
  ]),
  'slices of two overlap'
)

// ---- timing ----
const digits = (n) => '1234567890'.repeat(Math.ceil(n / 10)).slice(0, n)

function measure(n, k, reps = 7) {
  const series = new Series(digits(n))
  series.slices(k) // warm-up, also proves the measured call is valid
  const times = []
  let sliceCount = 0
  for (let r = 0; r < reps; r += 1) {
    const start = performance.now()
    const out = series.slices(k)
    times.push(performance.now() - start)
    sliceCount = out.length
  }
  times.sort((a, b) => a - b)
  return {
    n,
    k,
    slices: sliceCount,
    elementsCopied: sliceCount * k,
    medianMs: Number(times[Math.floor(times.length / 2)].toFixed(3)),
    minMs: Number(times[0].toFixed(3)),
    reps,
  }
}

const results = {
  node: process.version,
  fixedSliceLength: [1000, 10000, 100000].map((n) => measure(n, 5)),
  halfLengthSlice: [200, 2000, 8000].map((n) => measure(n, n / 2)),
}

console.log(JSON.stringify(results, null, 2))
