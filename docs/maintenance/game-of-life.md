# Maintenance: Game of Life

This document explains the test management and preparation process for the `game-of-life` exercise in the Exercism TypeScript track.

## 1. Source of Canonical Test Data

Canonical test data for `game-of-life` originates from the cross-track Exercism repository:
- **Repository**: [`exercism/problem-specifications`](https://github.com/exercism/problem-specifications)
- **Path**: `exercises/game-of-life/canonical-data.json`

This JSON specification defines the standardized test cases, inputs, and expected outcomes shared across all Exercism language tracks.

## 2. Purpose of `.meta/tests.toml`

The file `exercises/practice/game-of-life/.meta/tests.toml` tracks which canonical test cases are included or excluded in this track:
- Each test case is identified by its canonical **UUID**.
- An entry without `include = false` is included by default.
- **Important**: `.meta/tests.toml` is a **metadata file** used for tracking canonical compliance. It is **not** a code generator and does not automatically generate TypeScript test files. There is no Jinja template for `game-of-life`.

## 3. Correspondence Between Canonical UUIDs and TypeScript Tests

The TypeScript test suite (`game-of-life.test.ts`) is hand-maintained TypeScript code. The Jest test names in `game-of-life.test.ts` correspond directly to the `description` fields in `canonical-data.json` and `.meta/tests.toml`:

| Canonical UUID | Canonical Description | TypeScript Test Name |
|---|---|---|
| `ae86ea7d-bd07-4357-90b3-ac7d256bd5c5` | empty matrix | `it('empty matrix', ...)` |
| `4ea5ccb7-7b73-4281-954a-bed1b0f139a5` | live cells with zero live neighbors die | `xit('live cells with zero live neighbors die', ...)` |
| `df245adc-14ff-4f9c-b2ae-f465ef5321b2` | live cells with only one live neighbor die | `xit('live cells with only one live neighbor die', ...)` |
| `2a713b56-283c-48c8-adae-1d21306c80ae` | live cells with two live neighbors stay alive | `xit('live cells with two live neighbors stay alive', ...)` |
| `86d5c5a5-ab7b-41a1-8907-c9b3fc5e9dae` | live cells with three live neighbors stay alive | `xit('live cells with three live neighbors stay alive', ...)` |
| `015f60ac-39d8-4c6c-8328-57f334fc9f89` | dead cells with three live neighbors become alive | `xit('dead cells with three live neighbors become alive', ...)` |
| `2ee69c00-9d41-4b8b-89da-5832e735ccf1` | live cells with four or more neighbors die | `xit('live cells with four or more neighbors die', ...)` |
| `a79b42be-ed6c-4e27-9206-43da08697ef6` | bigger matrix | `xit('bigger matrix', ...)` |

All 8 canonical cases are supported by the reference implementation (`.meta/proof.ci.ts`) and are included. In the student test file, tests after the first use `xit` so students can solve the exercise test-by-test (TDD).

## 4. The Three Selected Canonical Cases

Here is the detailed mapping for the three key cases highlighted in Issue #12:

### Case 1: Empty matrix
- **UUID**: `ae86ea7d-bd07-4357-90b3-ac7d256bd5c5`
- **Input**:
  ```typescript
  []
  ```
- **Expected Output**:
  ```typescript
  []
  ```
- **Reference Behavior**: In `.meta/proof.ci.ts`, `if (this.matrix.length === 0) return;` immediately handles an empty matrix, and `state()` returns `[]`.

### Case 2: Live cells with zero live neighbors die
- **UUID**: `4ea5ccb7-7b73-4281-954a-bed1b0f139a5`
- **Input**:
  ```typescript
  [
    [0, 0, 0],
    [0, 1, 0],
    [0, 0, 0]
  ]
  ```
- **Expected Output**:
  ```typescript
  [
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0]
  ]
  ```
- **Reference Behavior**: The center live cell has 0 neighbors. Since `liveNeighbors < 2`, the cell transitions to dead (`0`).

### Case 3: Live cells with only one live neighbor die
- **UUID**: `df245adc-14ff-4f9c-b2ae-f465ef5321b2`
- **Input**:
  ```typescript
  [
    [0, 0, 0],
    [0, 1, 0],
    [0, 1, 0]
  ]
  ```
- **Expected Output**:
  ```typescript
  [
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0]
  ]
  ```
- **Reference Behavior**: The two live cells are adjacent, each having exactly 1 live neighbor. Since `liveNeighbors < 2`, both die (`0`).

## 5. How the Track Helper Prepares Tests

In the TypeScript track, tests are prepared dynamically by `scripts/helpers.mjs` (`prepare()` function) during CI or testing:
1. **Reads configuration**: Loads `.meta/config.json` to locate the test file (`game-of-life.test.ts`), solution stub (`game-of-life.ts`), and reference example (`.meta/proof.ci.ts`).
2. **Creates temporary workspace**: Prepares a clean directory (`tmp_exercises`).
3. **Unskips tests**: Copies `game-of-life.test.ts` into `tmp_exercises` and automatically unskips all cases (`xit(` -> `it(`).
4. **Substitutes reference**: Copies `.meta/proof.ci.ts` to `tmp_exercises/game-of-life.ts` so the full test suite runs against the verified reference solution.

## 6. Exact Reproduction Commands

It is important to clearly distinguish between **metadata synchronization** and **test execution**:

### A. Metadata Synchronization (configlet)
To check or update `.meta/tests.toml` against canonical data from `problem-specifications`:
```bash
./bin/configlet sync --tests --exercise game-of-life
```
*What this does*: Compares `.meta/tests.toml` with `problem-specifications/exercises/game-of-life/canonical-data.json`.
*What this does NOT do*: It does not touch or generate any TypeScript `.ts` test files.

### B. Track CI Test Preparation and Execution
To prepare the temporary test files and run Jest against the reference implementation:
```bash
ASSIGNMENT=practice/game-of-life corepack yarn ci
```
*What this does*: Calls `scripts/ci.mjs`, which runs `prepare('practice/game-of-life')` to copy and unskip tests in `tmp_exercises`, substitutes `proof.ci.ts`, and runs Jest.

## 7. How to Verify Results

1. **Exercise Checker**:
   ```bash
   python3 work/R47-T012/check.py
   ```
   Verifies that all 8 canonical test cases execute and pass against the reference implementation in an isolated temporary environment.

2. **Preparation Repeatability Check**:
   ```bash
   python3 tools/course_checks/r47-t012.py
   ```
   Prepares the tests in two separate temporary directories and verifies that both preparations produce identical test files with all 8 cases present.

