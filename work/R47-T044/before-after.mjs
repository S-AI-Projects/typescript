// Before/after comparison for the R47-T044 readability refactor of
// exercises/practice/pangram/.meta/proof.ci.ts.
// Run: node work/R47-T044/before-after.mjs
// Exits non-zero if the two implementations disagree on any input.

// ---- BEFORE (original proof.ci.ts, types stripped) ----
const aToZBefore = [...Array(26)].map((_, index) => {
  return String.fromCharCode(index + 65)
})

function isPangramBefore(value) {
  const myMap = new Map()
  aToZBefore.forEach((key) => {
    myMap.set(key.toLowerCase(), 0)
  })

  for (const each of value) {
    const item = myMap.get(each) || 0
    myMap.set(each.toLowerCase(), item + 1)
  }

  for (const each of myMap.values()) {
    if (each === 0) {
      return false
    }
  }
  return true
}

// ---- AFTER (refactored proof.ci.ts, types stripped) ----
const aToZAfter = [...Array(26)].map((_, index) => {
  return String.fromCharCode('A'.charCodeAt(0) + index)
})

function isPangramAfter(value) {
  const letterCounts = new Map()
  aToZAfter.forEach((letter) => {
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

// ---- Inputs: every sentence used by pangram.test.ts, plus edge cases ----
const inputs = [
  '',
  'abcdefghijklmnopqrstuvwxyz',
  'the quick brown fox jumps over the lazy dog',
  'a quick movement of the enemy will jeopardize five gunboats',
  'five boxing wizards jump quickly at it',
  'the_quick_brown_fox_jumps_over_the_lazy_dog',
  'the quick brown fox jumps over the lazy dog 12345',
  '"Five quacking Zephyrs jolt my wax bed."',
  'the 1 quick brown fox jumps over the 2 lazy dogs',
  '7h3 qu1ck brown fox jumps ov3r 7h3 lazy dog',
  'The Quick Brown Fox Jumps Over The Lazy Dog',
  'pack my box with five dozen liquor jugs',
  'how vexingly quick daft zebras jump!',
  'a',
  'abcdefghijklmnopqrstuvwxy',
  'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
  '1234567890 !@#$%',
]

let disagreements = 0
for (const input of inputs) {
  const before = isPangramBefore(input)
  const after = isPangramAfter(input)
  const mark = before === after ? 'OK ' : 'DIFF'
  if (before !== after) disagreements += 1
  console.log(`${mark} before=${before} after=${after} input=${JSON.stringify(input)}`)
}

console.log(
  `\n${inputs.length} inputs compared, ${disagreements} disagreement(s)`
)
process.exit(disagreements === 0 ? 0 : 1)
