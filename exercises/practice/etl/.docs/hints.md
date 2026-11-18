# Hints

## General

- The goal of ETL is to transform legacy Scrabble score data formatted as `{ [score: string]: string[] }` into a new dictionary mapping each individual lowercase letter to its numerical score `{ [letter: string]: number }`.
- Don't assume the letters in the input array should remain uppercase! Check the requirement: the new data store requires all keys to be converted to lowercase letters.
- For example, with an input of `{ 1: ['A'] }`, returning `{ A: 1 }` preserves the input case and fails. The expected output is `{ a: 1 }`.
- Ensure the keys of the new object are lowercase characters (e.g. using `letter.toLowerCase()`) and scores are parsed or stored as numbers.
