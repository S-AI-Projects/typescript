export class InvalidInputError extends Error {
  constructor(message: string) {
    super()
    this.message = message || 'Invalid Input'
  }
}

type Direction = 'north' | 'east' | 'south' | 'west'
type Coordinates = [number, number]

const COMPASS: readonly Direction[] = ['north', 'east', 'south', 'west']

const STEP_VECTORS: readonly Coordinates[] = [
  [0, 1],
  [1, 0],
  [0, -1],
  [-1, 0],
]

const DIRECTION_INDEX = new Map<string, number>(
  COMPASS.map((name, index) => [name, index])
)

export class Robot {
  private static readonly COMMANDS = new Map<string, (robot: Robot) => void>([
    [
      'R',
      (robot: Robot): void => {
        robot.dirIndex = (robot.dirIndex + 1) % COMPASS.length
      },
    ],
    [
      'L',
      (robot: Robot): void => {
        robot.dirIndex = (robot.dirIndex + COMPASS.length - 1) % COMPASS.length
      },
    ],
    [
      'A',
      (robot: Robot): void => {
        const [dx, dy] = STEP_VECTORS[robot.dirIndex]
        robot.posX += dx
        robot.posY += dy
      },
    ],
  ])

  private dirIndex = 0
  private posX = 0
  private posY = 0

  public get bearing(): Direction {
    return COMPASS[this.dirIndex]
  }

  public get coordinates(): Coordinates {
    return [this.posX, this.posY]
  }

  public place({
    x,
    y,
    direction,
  }: {
    x: number
    y: number
    direction: string
  }): void {
    const resolvedIndex = DIRECTION_INDEX.get(direction)
    if (resolvedIndex === undefined) {
      throw new InvalidInputError('Invalid Robot Bearing')
    }
    this.posX = x
    this.posY = y
    this.dirIndex = resolvedIndex
  }

  public evaluate(instructions: string): void {
    for (const ch of instructions) {
      if (!Robot.COMMANDS.has(ch)) {
        throw new InvalidInputError(
          `${ch} is not a valid instruction character.`
        )
      }
    }
    for (const ch of instructions) {
      Robot.COMMANDS.get(ch)?.(this)
    }
  }
}
