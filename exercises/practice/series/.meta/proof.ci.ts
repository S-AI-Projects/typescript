// Cost, with n = the number of digits in the series and k = the slice
// length passed to slices(): the constructor converts the string to
// digits once, in Θ(n). slices(k) builds (n − k + 1) slices of length
// k, copying Θ((n − k + 1) · k) digit values — exactly the size of the
// output it returns. For a fixed k that is linear in n; when k grows
// with n (worst case k ≈ n / 2) it is quadratic in n. Measured timings
// that back this statement are recorded in docs/maintenance/series.md.
export class Series {
  private readonly numberString: string
  private readonly digits: number[]

  constructor(numberString: string) {
    if (!numberString) {
      throw new Error('series cannot be empty')
    }

    this.numberString = numberString
    this.digits = this.getDigits()
  }

  private getDigits(): number[] {
    return [...this.numberString].map((digit) => parseInt(digit, 10))
  }

  public slices(sliceSize: number): number[][] {
    const result: number[][] = []
    let slice: number[] = []

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
