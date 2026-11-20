// Alternative implementation using imperative loops (instead of regex)
// This is an equivalent approach to the regex-based proof.ci.ts

export function encode(plaintext: string): string {
  if (plaintext.length === 0) return ''
  let result = ''
  let count = 1
  for (let i = 1; i <= plaintext.length; i++) {
    if (i < plaintext.length && plaintext[i] === plaintext[i - 1]) {
      count++
    } else {
      result += (count > 1 ? String(count) : '') + plaintext[i - 1]
      count = 1
    }
  }
  return result
}

export function decode(cypher: string): string {
  if (cypher.length === 0) return ''
  let result = ''
  let numStr = ''
  for (const ch of cypher) {
    if (ch >= '0' && ch <= '9') {
      numStr += ch
    } else {
      const times = numStr.length > 0 ? Number(numStr) : 1
      result += ch.repeat(times)
      numStr = ''
    }
  }
  return result
}
