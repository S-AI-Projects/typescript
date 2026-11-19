export class Squares {
  public readonly squareOfSum: number
  public readonly sumOfSquares: number
  public readonly difference: number

  constructor(count: number) {
    this.squareOfSum = this._squareOfSum(count)
    this.sumOfSquares = this._sumOfSquares(count)
    this.difference = this._difference()
  }

  private _squareOfSum(count: number): number {
    // Accumulate the sum of the first N natural numbers: (1 + 2 + ... + N)
    let sumOfNumbers = 0
    let currentNumber = 1

    while (currentNumber <= count) {
      sumOfNumbers += currentNumber
      currentNumber++
    }

    return sumOfNumbers * sumOfNumbers
  }

  private _sumOfSquares(count: number): number {
    // Accumulate the sum of squares of the first N natural numbers: (1² + 2² + ... + N²)
    let totalSumOfSquares = 0
    let currentNumber = 1

    while (currentNumber <= count) {
      totalSumOfSquares += currentNumber * currentNumber
      currentNumber++
    }

    return totalSumOfSquares
  }

  private _difference(): number {
    return this.squareOfSum - this.sumOfSquares
  }
}

