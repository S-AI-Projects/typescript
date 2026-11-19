# R47-T016 test evidence

Both implementations ran from separate temporary copies of the tournament exercise. `shutil.copytree` copied the complete exercise, including hidden metadata directories; the configured solution and test paths came from `.meta/config.json`. Only the temporary solution/test files were changed.

The original `xit` cases were enabled in each temporary copy. CI mode disabled Jest watch mode. Three additional contract examples checked empty input, a win, and the same win expressed as the opponent's loss.

## Tool versions

- Python: Python 3.9.6
- Node.js: v26.8.2
- Corepack/Yarn: 4.5.1

## Expected and actual contract results

| Input | Expected result | Actual result |
| --- | --- | --- |
| empty string | Header only | Captured in each Jest probe; compared with header |
| `Allegoric Alaskans;Blithering Badgers;win` | Allegoric: 1 MP, 1 W, 0 L, 3 P; Blithering: 1 MP, 0 W, 1 L, 0 P | Captured in each Jest probe and asserted equal |
| `Blithering Badgers;Allegoric Alaskans;loss` | Same standings as the win above | Captured in each Jest probe and asserted equal |

The exact expected and returned tables are included in the successful Jest probe output below.

## Reference implementation

- Result: PASS
- Expected tests: 15
- Tests passed: 15
- Tests reported: 15
- Failed tests: 0

### Dependency installation

```text
Status: exit code 0
stdout:
➤ YN0000: · Yarn 4.5.1
➤ YN0000: ┌ Resolution step
➤ YN0085: │ + @exercism/babel-preset-typescript@npm:0.6.0, @exercism/eslint-config-typescript@npm:0.8.0, @jest/globals@npm:29.7.0, @types/node@npm:22.7.9, and 578 more.
➤ YN0000: └ Completed in 4s 17ms
➤ YN0000: ┌ Post-resolution validation
➤ YN0002: │ @exercism/typescript-tournament@workspace:. doesn't provide @babel/core (p0d660), requested by babel-jest.
➤ YN0086: │ Some peer dependencies are incorrectly met by your project; run yarn explain peer-requirements <hash> for details, where <hash> is the six-letter p-prefixed code.
➤ YN0086: │ Some peer dependencies are incorrectly met by dependencies; run yarn explain peer-requirements for details.
➤ YN0000: └ Completed
➤ YN0000: ┌ Fetch step
➤ YN0000: └ Completed
➤ YN0000: ┌ Link step
➤ YN0000: │ ESM support for PnP uses the experimental loader API and is therefore experimental
➤ YN0007: │ core-js@npm:3.38.1 must be built because it never has been before or the last one failed
➤ YN0007: │ core-js@npm:3.51.0 must be built because it never has been before or the last one failed
➤ YN0000: └ Completed in 2s 32ms
➤ YN0000: · Done with warnings in 6s 193ms
stderr:
(empty)
```

### Exercise test command (`CI=true corepack yarn test`)

```text
Status: exit code 0
stdout:
[tests] tsc: ✅, tstyche: ❌, jest: ✅, 
[tests] tsc (compile)
[tests] tstyche (implementation tests)
  console.log
    
    empty input returns only the header
    Expected:
    Team                           | MP |  W |  D |  L |  P
    Actual:
    Team                           | MP |  W |  D |  L |  P

      at Object.log (r47-t016.probe.test.ts:29:15)

  console.log
    
    a win earns three points and the other team loses
    Expected:
    Team                           | MP |  W |  D |  L |  P
    Allegoric Alaskans             |  1 |  1 |  0 |  0 |  3
    Blithering Badgers             |  1 |  0 |  0 |  1 |  0
    Actual:
    Team                           | MP |  W |  D |  L |  P
    Allegoric Alaskans             |  1 |  1 |  0 |  0 |  3
    Blithering Badgers             |  1 |  0 |  0 |  1 |  0

      at Object.log (r47-t016.probe.test.ts:29:15)

  console.log
    
    a loss for the first team is a win for the second
    Expected:
    Team                           | MP |  W |  D |  L |  P
    Allegoric Alaskans             |  1 |  1 |  0 |  0 |  3
    Blithering Badgers             |  1 |  0 |  0 |  1 |  0
    Actual:
    Team                           | MP |  W |  D |  L |  P
    Allegoric Alaskans             |  1 |  1 |  0 |  0 |  3
    Blithering Badgers             |  1 |  0 |  0 |  1 |  0

      at Object.log (r47-t016.probe.test.ts:29:15)
stderr:
PASS ./r47-t016.probe.test.ts
  R47-T016 contract examples
    ✓ empty input returns only the header (22 ms)
    ✓ a win earns three points and the other team loses (2 ms)
    ✓ a loss for the first team is a win for the second (1 ms)

PASS ./tournament.test.ts
  Tournament
    ✓ just the header if no input (3 ms)
    ✓ a win is three points, a loss is zero points
    ✓ a win can also be expressed as a loss
    ✓ a different team can win
    ✓ a draw is one point each (10 ms)
    ✓ There can be more than one match
    ✓ There can be more than one winner
    ✓ There can be more than two teams (1 ms)
    ✓ typical input (2 ms)
    ✓ incomplete competition (not all pairs have played)
    ✓ ties broken alphabetically
    ✓ ensure points sorted numerically

Test Suites: 2 passed, 2 total
Tests:       15 passed, 15 total
Snapshots:   0 total
Time:        0.766 s
Ran all test suites.
```

## Alternative implementation

- Result: PASS
- Expected tests: 15
- Tests passed: 15
- Tests reported: 15
- Failed tests: 0

### Dependency installation

```text
Status: exit code 0
stdout:
➤ YN0000: · Yarn 4.5.1
➤ YN0000: ┌ Resolution step
➤ YN0085: │ + @exercism/babel-preset-typescript@npm:0.6.0, @exercism/eslint-config-typescript@npm:0.8.0, @jest/globals@npm:29.7.0, @types/node@npm:22.7.9, and 578 more.
➤ YN0000: └ Completed in 5s 655ms
➤ YN0000: ┌ Post-resolution validation
➤ YN0002: │ @exercism/typescript-tournament@workspace:. doesn't provide @babel/core (p0d660), requested by babel-jest.
➤ YN0086: │ Some peer dependencies are incorrectly met by your project; run yarn explain peer-requirements <hash> for details, where <hash> is the six-letter p-prefixed code.
➤ YN0086: │ Some peer dependencies are incorrectly met by dependencies; run yarn explain peer-requirements for details.
➤ YN0000: └ Completed
➤ YN0000: ┌ Fetch step
➤ YN0000: └ Completed
➤ YN0000: ┌ Link step
➤ YN0000: │ ESM support for PnP uses the experimental loader API and is therefore experimental
➤ YN0007: │ core-js@npm:3.38.1 must be built because it never has been before or the last one failed
➤ YN0007: │ core-js@npm:3.51.0 must be built because it never has been before or the last one failed
➤ YN0000: └ Completed in 1s 750ms
➤ YN0000: · Done with warnings in 7s 554ms
stderr:
(empty)
```

### Exercise test command (`CI=true corepack yarn test`)

```text
Status: exit code 0
stdout:
[tests] tsc: ✅, tstyche: ❌, jest: ✅, 
[tests] tsc (compile)
[tests] tstyche (implementation tests)
  console.log
    
    empty input returns only the header
    Expected:
    Team                           | MP |  W |  D |  L |  P
    Actual:
    Team                           | MP |  W |  D |  L |  P

      at Object.log (r47-t016.probe.test.ts:29:15)

  console.log
    
    a win earns three points and the other team loses
    Expected:
    Team                           | MP |  W |  D |  L |  P
    Allegoric Alaskans             |  1 |  1 |  0 |  0 |  3
    Blithering Badgers             |  1 |  0 |  0 |  1 |  0
    Actual:
    Team                           | MP |  W |  D |  L |  P
    Allegoric Alaskans             |  1 |  1 |  0 |  0 |  3
    Blithering Badgers             |  1 |  0 |  0 |  1 |  0

      at Object.log (r47-t016.probe.test.ts:29:15)

  console.log
    
    a loss for the first team is a win for the second
    Expected:
    Team                           | MP |  W |  D |  L |  P
    Allegoric Alaskans             |  1 |  1 |  0 |  0 |  3
    Blithering Badgers             |  1 |  0 |  0 |  1 |  0
    Actual:
    Team                           | MP |  W |  D |  L |  P
    Allegoric Alaskans             |  1 |  1 |  0 |  0 |  3
    Blithering Badgers             |  1 |  0 |  0 |  1 |  0

      at Object.log (r47-t016.probe.test.ts:29:15)
stderr:
PASS ./tournament.test.ts
  Tournament
    ✓ just the header if no input (4 ms)
    ✓ a win is three points, a loss is zero points
    ✓ a win can also be expressed as a loss (1 ms)
    ✓ a different team can win
    ✓ a draw is one point each (10 ms)
    ✓ There can be more than one match
    ✓ There can be more than one winner
    ✓ There can be more than two teams
    ✓ typical input (1 ms)
    ✓ incomplete competition (not all pairs have played)
    ✓ ties broken alphabetically
    ✓ ensure points sorted numerically

PASS ./r47-t016.probe.test.ts
  R47-T016 contract examples
    ✓ empty input returns only the header (24 ms)
    ✓ a win earns three points and the other team loses (2 ms)
    ✓ a loss for the first team is a win for the second (1 ms)

Test Suites: 2 passed, 2 total
Tests:       15 passed, 15 total
Snapshots:   0 total
Time:        0.842 s
Ran all test suites.
```
