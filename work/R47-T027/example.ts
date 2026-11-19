/**
 * work/R47-T027/example.ts
 *
 * Micro-example demonstrating Union Narrowing with Literal Types in TypeScript,
 * as used in exercises/practice/connect/.meta/proof.ci.ts.
 */

export type Player = 'X' | 'O';

/**
 * Type-safe helper demonstrating equality narrowing on a literal union type.
 * Inside the truthy branch, player is narrowed to 'X'.
 * In the fallback branch, TypeScript exhaustively narrows player to 'O'.
 */
export function getPlayerAxis(player: Player): string {
  if (player === 'X') {
    return `Player ${player}: horizontal (left to right)`;
  }
  return `Player ${player}: vertical (top to bottom)`;
}

/**
 * Common pitfall: using an unconstrained string type.
 * When typed broadly as string, the fallback else branch erroneously
 * treats invalid board tokens (such as '.' or '?') as if they were 'O'.
 */
export function getPlayerAxisPitfall(player: string): string {
  if (player === 'X') {
    return `Player ${player}: horizontal (left to right)`;
  }
  return `Player ${player}: vertical (top to bottom)`;
}

/**
 * Standalone execution runner.
 */
export function runDemo(): {
  narrowed: Record<string, string>;
  pitfall: Record<string, string>;
} {
  const players = ['X', 'O'] as const;
  const narrowed: Record<string, string> = {};
  for (const p of players) {
    narrowed[p] = getPlayerAxis(p);
  }

  const pitfallTokens = ['.', '?'];
  const pitfall: Record<string, string> = {};
  for (const token of pitfallTokens) {
    pitfall[token] = getPlayerAxisPitfall(token);
  }

  return { narrowed, pitfall };
}

// When executed directly, print JSON result
const result = runDemo();
console.log(JSON.stringify(result, null, 2));
