/**
 * Complexity Analysis:
 * - Time Complexity: O(N) where N is the length of the input DNA strand.
 *   - The lookup table initialization incurs O(1) fixed initialization overhead.
 *   - `input.split('')` performs a linear O(N) pass to construct an array of single-character tokens.
 *   - The `forEach` traversal executes exactly N hash table lookups (O(1) average), N boundary checks,
 *     and N string concatenations, bounded linearly by strand length N.
 * - Auxiliary Space Complexity: O(N) for the intermediate character array and the output string buffer.
 * - Invariant:
 *   - Every character in `input` must be one of the canonical DNA nucleotides ('G', 'C', 'T', 'A').
 *     Any invalid nucleotide immediately triggers an `Error('Invalid input DNA.')`.
 */
export function toRna(input: string): string {
  const dictionary: { [key: string]: string } = {
    G: 'C',
    C: 'G',
    T: 'A',
    A: 'U',
  }
  let temp = ''
  input.split('').forEach((element) => {
    const current = dictionary[element]
    if (current === undefined) {
      throw new Error('Invalid input DNA.')
    }
    temp += current
  })
  return temp
}
