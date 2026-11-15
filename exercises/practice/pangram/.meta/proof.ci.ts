// Invariant for this exercise: a sentence is a pangram exactly when
// every letter a-z occurs at least once. The reference therefore keeps
// one counter per letter of the alphabet; after the whole sentence has
// been scanned, a counter that is still 0 settles the answer (false),
// and the actual counts never matter beyond zero vs non-zero.
const aToZ = [...Array<string>(26)].map((_, index) => {
  return String.fromCharCode('A'.charCodeAt(0) + index)
})

export function isPangram(value: string): boolean {
  const letterCounts = new Map<string, number>()
  aToZ.forEach((letter: string) => {
    letterCounts.set(letter.toLowerCase(), 0)
  })

  for (const character of value) {
    const count = letterCounts.get(character) || 0
    letterCounts.set(character.toLowerCase(), count + 1)
  }

  for (const count of letterCounts.values()) {
    if (count === 0) {
      return false
    }
  }
  return true
}
