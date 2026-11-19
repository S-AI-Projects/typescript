# Split-Second Stopwatch: Exercise Maintenance & Path Resolution Guide

This document describes the structure, path resolution mechanisms, and maintenance procedures for the `split-second-stopwatch` TypeScript practice exercise on Exercism.

---

## 1. Exercise Architecture and File Roles

The exercise configuration resides at `exercises/practice/split-second-stopwatch/.meta/config.json`. Exercism's test runners, automated tooling (`configlet`), and CI workflows rely on this file to locate all operational files for the exercise.

### A. Learner Solution
- **Path:** `exercises/practice/split-second-stopwatch/split-second-stopwatch.ts`
- **Config Key:** `files.solution` (`["split-second-stopwatch.ts"]`)
- **Role:** This is the starter stub provided to learners. It exports the `SplitSecondStopwatch` class with method and getter stubs throwing placeholder errors (`throw new Error('Remove this line and implement the function')`). In the repository working tree, this file must remain unsolved so students receive a pristine template upon downloading the exercise.

### B. Canonical Test Suite
- **Path:** `exercises/practice/split-second-stopwatch/split-second-stopwatch.test.ts`
- **Config Key:** `files.test` (`["split-second-stopwatch.test.ts"]`)
- **Role:** The test suite asserting behavioral requirements for the stopwatch. It imports `SplitSecondStopwatch` from `./split-second-stopwatch.ts`. In the committed starter repository, the initial test (`'new stopwatch starts in ready state'`) is enabled (`it(...)`), while subsequent tests are disabled with `xit(...)` to enable test-driven progression. CI checkers enable all tests (`xit(` -> `it(`) only within isolated temporary execution sandboxes.

### C. Maintained Reference Implementation
- **Path:** `exercises/practice/split-second-stopwatch/.meta/proof.ci.ts`
- **Config Key:** `files.example` (`[".meta/proof.ci.ts"]`)
- **Role:** The complete, maintainer-verified reference implementation. When running CI pipelines, test runners copy or substitute `proof.ci.ts` in place of `split-second-stopwatch.ts` inside a temporary execution sandbox to guarantee that the canonical test suite passes completely.

### D. Exercise Configuration
- **Path:** `exercises/practice/split-second-stopwatch/.meta/config.json`
- **Role:** Declares author attribution, blurb, source metadata, and the critical `files` object mapping roles (`solution`, `test`, `example`, and optional editor configurations) to relative file paths.

### E. Test Metadata
- **Path:** `exercises/practice/split-second-stopwatch/.meta/tests.toml`
- **Role:** Tracks test case UUIDs synchronized with Exercism's canonical problem-specifications repository. Each test UUID corresponds to a standardized test case description.

---

## 2. Comparing File Categories

Understanding the repository requires distinguishing between four distinct file categories:

| Category | Typical Paths | Purpose & Mutability Rules |
| :--- | :--- | :--- |
| **Learner-Authored Files** | `split-second-stopwatch.ts` | Starter code downloaded by students. Must remain completely unsolved in version control. |
| **Maintained Reference Files** | `.meta/proof.ci.ts` | Ground-truth solution used to validate tests and CI. Maintained by track maintainers; never modified by learners. |
| **Canonical / Generated Test Artifacts** | `split-second-stopwatch.test.ts`, `.meta/tests.toml` | Tests and UUID mappings aligned with Exercism's canonical specifications. Not to be manually altered outside synchronization tasks. |
| **Metadata & Editor Configuration** | `.meta/config.json`, `.vscode/`, `package.json`, `tsconfig.json` | Tooling contracts, dependencies, and editor workspaces ensuring reproducible developer and CI environments. |

---

## 3. Metadata Path Resolution & Security Verification

When an automated runner or CI harness processes `config.json`, it resolves declared file paths relative to the exercise root directory (`exercises/practice/split-second-stopwatch/`):

1. **Root Definition:** The exercise directory is defined as the base path:
   $$\text{BaseDir} = \texttt{exercises/practice/split-second-stopwatch}$$
2. **Relative Resolution:** Each path entry $p$ in `files[role]` is resolved as:
   $$\text{ResolvedPath} = \text{normalize}(\text{BaseDir} / p)$$
3. **Containment Invariant:** To prevent directory traversal vulnerabilities or broken builds, the runner enforces:
   $$\text{ResolvedPath} \subseteq \text{BaseDir}$$
   Paths containing traversal segments (`..`), absolute paths, or paths pointing outside the exercise directory are strictly rejected.
4. **Existence Check:** Every resolved file must exist on disk as a readable file.

---

## 4. Reproducible Validation Commands

### Metadata Path Validator
To validate that all paths declared in `config.json` exist and do not escape the exercise directory, run:

```bash
python3 tools/course_checks/r47-t028.py
```

Expected output for valid configuration:
```text
Validating exercise metadata: .../exercises/practice/split-second-stopwatch/.meta/config.json
[SUCCESS] All declared file paths are valid and exist on disk.
```

### Full Automated Verification Checker
To run the automated test suite against the reference implementation in an isolated temporary directory and verify negative metadata fixtures, execute:

```bash
python3 work/R47-T028/check.py
```

This command:
1. Validates real exercise metadata and runs negative fixture tests (missing reference, missing test, escaping paths).
2. Sets up an isolated sandbox with the reference implementation and all tests enabled.
3. Runs package tests with Jest and verifies that all 29 canonical test cases pass.
4. Confirms that the learner stub and working tree remain completely unchanged.
