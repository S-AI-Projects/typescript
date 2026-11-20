// O(1) time and space: at most 1 Math.sqrt, 2 multiplications, 1 addition, and 3 comparisons;
// boundary points belong to the inner region because the comparisons are strict (>).
export function score(x: number, y: number): number {
  // Use euclidean distance
  const distanceToDart = Math.sqrt(x * x + y * y)

  // Define points for each section of the target
  if (distanceToDart > 10) {
    return 0
  }

  if (distanceToDart > 5) {
    return 1
  }

  if (distanceToDart > 1) {
    return 5
  }
  return 10
}
