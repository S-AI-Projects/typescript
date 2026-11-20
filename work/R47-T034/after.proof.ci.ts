export function steps(n: number): number {
  if (n <= 0 || !Number.isInteger(n)) {
    throw new Error('Only positive integers are allowed')
  }
  return calculateStepsRecursively(n, 0)
}

// Invariant: each step applies the Collatz map once; the result counts applications until current === 1.
function calculateStepsRecursively(
  current: number,
  stepsSoFar: number
): number {
  if (current === 1) {
    return stepsSoFar
  }

  const next = current % 2 === 0 ? current / 2 : current * 3 + 1
  return calculateStepsRecursively(next, stepsSoFar + 1)
}
