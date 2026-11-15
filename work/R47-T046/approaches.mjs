// Two approaches to crypto-square (R47-T046), compared.
// Run: node work/R47-T046/approaches.mjs
// Exits non-zero if the two implementations disagree on any input.
//
// Approach A ("reference technique") is the maintained reference from
// exercises/practice/crypto-square/.meta/proof.ci.ts with types
// stripped: normalize, split the plaintext into row segments with a
// regex, push every character into a column bucket (an array of
// arrays), join the columns, then re-chunk and pad.
//
// Approach B ("index arithmetic") is written independently for this
// task: it never builds rows or columns. The character at (row, col)
// of the rectangle lives at index row * c + col of the normalized
// string, so the transposed text is produced by walking the indices
// column by column and skipping indices past the end (the ragged
// last row). The final chunking/padding step is shared by the
// contract, not by the approach, so both apply it the same way.

// ---------- Approach A: reference technique ----------
class CryptoA {
  constructor(input) {
    this.input = input
  }

  get plaintext() {
    return this.input.toLowerCase().replace(/[^a-zA-Z0-9]/g, '')
  }

  get ciphertext() {
    const chunkSize = this.size
    if (chunkSize === 0) {
      return ''
    }
    const splitRegex = new RegExp(`.{1,${chunkSize}}`, 'g')
    const segments = this.ciphertextSegments() ?? []
    const chunks = segments.join('').match(splitRegex) ?? []
    return chunks.map((item) => item.padEnd(chunkSize, ' ')).join(' ')
  }

  get size() {
    const realLength = Math.sqrt(this.plaintext.length)
    return Math.ceil(realLength)
  }

  ciphertextSegments() {
    const textSegments = this.plaintextSegments() ?? []
    const columns = []
    let i
    let j
    let currentSegment
    let currentLetter

    for (i = 0; i < this.size; i += 1) {
      columns.push([])
    }

    for (i = 0; i < textSegments.length; i += 1) {
      currentSegment = textSegments[i]
      for (j = 0; j < currentSegment.length; j += 1) {
        currentLetter = currentSegment[j]
        columns[j].push(currentLetter)
      }
    }

    const result = []
    for (i = 0; i < columns.length; i += 1) {
      result[i] = columns[i].join('')
    }
    return result
  }

  plaintextSegments() {
    const plainText = this.plaintext
    const chunkSize = this.size
    const splitRegex = new RegExp(`.{1,${chunkSize}}`, 'g')
    return plainText.match(splitRegex)
  }
}

// ---------- Approach B: index arithmetic ----------
class CryptoB {
  constructor(input) {
    this.input = input
  }

  get ciphertext() {
    const text = this.input.toLowerCase().replace(/[^a-z0-9]/g, '')
    const length = text.length
    if (length === 0) {
      return ''
    }
    const columns = Math.ceil(Math.sqrt(length))
    const rows = Math.ceil(length / columns)

    let transposed = ''
    for (let col = 0; col < columns; col += 1) {
      for (let row = 0; row < rows; row += 1) {
        const index = row * columns + col
        if (index < length) {
          transposed += text[index]
        }
      }
    }

    const chunks = []
    for (let i = 0; i < transposed.length; i += columns) {
      chunks.push(transposed.slice(i, i + columns).padEnd(columns, ' '))
    }
    return chunks.join(' ')
  }
}

// ---------- comparison ----------
const inputs = [
  // every input from crypto-square.test.ts, including the skipped one
  '',
  '... --- ...',
  'A',
  '  b ',
  '@1,%!',
  'This is fun!',
  'Chill out.',
  'If man was meant to stay on the ground, god would have given us roots.',
  // extra shapes: every normalized length 0..40, mixed case + noise
  ...Array.from({ length: 41 }, (_, n) =>
    'Ab3 xY!9zQ'.repeat(Math.ceil(n / 10) + 1).slice(0, n)
  ),
]

let disagreements = 0
for (const input of inputs) {
  const a = new CryptoA(input).ciphertext
  const b = new CryptoB(input).ciphertext
  if (a !== b) {
    disagreements += 1
    console.log(
      `DIFF input=${JSON.stringify(input)}\n  A=${JSON.stringify(a)}\n  B=${JSON.stringify(b)}`
    )
  }
}
console.log(
  `${inputs.length} inputs compared, ${disagreements} disagreement(s)`
)
process.exit(disagreements === 0 ? 0 : 1)
