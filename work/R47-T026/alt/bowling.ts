export class Bowling {
  private readonly rolls: number[] = []

  public roll(pins: number): void {
    if (pins < 0) {
      throw new Error('Negative roll is invalid')
    }
    if (pins > 10) {
      throw new Error('Pin count exceeds pins on the lane')
    }
    if (this.isGameOver()) {
      throw new Error('Cannot roll after game is over')
    }

    // Validate the roll in the context of the current frame
    this.validateRoll(pins)
    this.rolls.push(pins)
  }

  public score(): number {
    if (!this.isGameOver()) {
      throw new Error('Score cannot be taken until the end of the game')
    }

    let totalScore = 0
    let rollIndex = 0

    for (let frame = 0; frame < 10; frame++) {
      if (this.isStrike(rollIndex)) {
        totalScore += 10 + this.rolls[rollIndex + 1] + this.rolls[rollIndex + 2]
        rollIndex += 1
      } else if (this.isSpare(rollIndex)) {
        totalScore += 10 + this.rolls[rollIndex + 2]
        rollIndex += 2
      } else {
        totalScore += this.rolls[rollIndex] + this.rolls[rollIndex + 1]
        rollIndex += 2
      }
    }

    return totalScore
  }

  private isStrike(index: number): boolean {
    return this.rolls[index] === 10
  }

  private isSpare(index: number): boolean {
    return this.rolls[index] + this.rolls[index + 1] === 10
  }

  private isGameOver(): boolean {
    let rollIndex = 0
    for (let frame = 0; frame < 9; frame++) {
      if (rollIndex >= this.rolls.length) {
        return false
      }
      if (this.rolls[rollIndex] === 10) {
        rollIndex += 1
      } else {
        rollIndex += 2
        if (rollIndex > this.rolls.length) {
          return false
        }
      }
    }

    // Now at 10th frame (index 9)
    if (rollIndex >= this.rolls.length) {
      return false
    }

    const firstRollInTenth = this.rolls[rollIndex]
    if (firstRollInTenth === 10) {
      // Strike in 10th frame requires 2 bonus rolls (total 3 rolls in 10th frame)
      return this.rolls.length >= rollIndex + 3
    }

    if (rollIndex + 1 >= this.rolls.length) {
      return false
    }

    const secondRollInTenth = this.rolls[rollIndex + 1]
    if (firstRollInTenth + secondRollInTenth === 10) {
      // Spare in 10th frame requires 1 bonus roll (total 3 rolls in 10th frame)
      return this.rolls.length >= rollIndex + 3
    }

    // Open frame in 10th frame ends game after 2 rolls
    return this.rolls.length >= rollIndex + 2
  }

  private validateRoll(pins: number): void {
    let rollIndex = 0
    for (let frame = 0; frame < 9; frame++) {
      if (rollIndex === this.rolls.length) {
        // First roll of frame (0..8) - single roll pin limit already checked (<= 10)
        return
      }
      if (this.rolls[rollIndex] === 10) {
        rollIndex += 1
      } else {
        if (rollIndex + 1 === this.rolls.length) {
          // Second roll of frame (0..8)
          if (this.rolls[rollIndex] + pins > 10) {
            throw new Error('Pin count exceeds pins on the lane')
          }
          return
        }
        rollIndex += 2
      }
    }

    // We are at the 10th frame
    const rollsInTenth = this.rolls.length - rollIndex
    if (rollsInTenth === 0) {
      // First roll of 10th frame
      return
    }

    if (rollsInTenth === 1) {
      const first = this.rolls[rollIndex]
      if (first < 10 && first + pins > 10) {
        throw new Error('Pin count exceeds pins on the lane')
      }
      return
    }

    if (rollsInTenth === 2) {
      const first = this.rolls[rollIndex]
      const second = this.rolls[rollIndex + 1]
      if (first === 10) {
        // First was strike
        if (second < 10 && second + pins > 10) {
          throw new Error('Pin count exceeds pins on the lane')
        }
      }
      return
    }
  }
}
