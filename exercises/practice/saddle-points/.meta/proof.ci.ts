export function saddlePoints(
  matrix: number[][]
): Array<{ row: number; column: number }> {
  // A saddle point is an entry that is greater than or equal to every element in its row
  // (row maximum) and less than or equal to every element in its column (column minimum).
  // Coordinates in the returned result are 1-based: { row: 1..M, column: 1..N }.
  if (matrix.length === 0 || matrix[0].length === 0) {
    return []
  }

  const maximumRowValues: number[] = matrix.map((row) => Math.max(...row))
  const numColumns = matrix[0].length

  const minimumColumnValues: number[] = Array.from(
    { length: numColumns },
    (_, colIndex) => Math.min(...matrix.map((row) => row[colIndex]))
  )

  const resultPoints: Array<{ row: number; column: number }> = []

  for (let rowIndex = 0; rowIndex < maximumRowValues.length; rowIndex++) {
    for (let colIndex = 0; colIndex < minimumColumnValues.length; colIndex++) {
      if (maximumRowValues[rowIndex] === minimumColumnValues[colIndex]) {
        resultPoints.push({ row: rowIndex + 1, column: colIndex + 1 })
      }
    }
  }

  return resultPoints
}
