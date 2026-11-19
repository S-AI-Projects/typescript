# Final Report: Assignment R47-T028 — Validate Stopwatch Exercise Metadata

## 1. Assignment Overview
- **Student:** Surya Paladugu
- **Assignment:** R47-T028 (8 of 10)
- **Repository:** `https://github.com/S-AI-Projects/typescript`
- **Assigned Working Branch:** `student/e26b07f0754`
- **Task Working Branch:** `student/e26b07f0754/R47-T028`
- **Target Exercise:** `exercises/practice/split-second-stopwatch`
- **Objective:** Validate exercise metadata paths in `config.json`, prevent path escaping/traversal vulnerabilities, verify negative metadata fixtures, validate reference implementation test execution in an isolated sandbox, and document maintenance procedures.

---

## 2. Files Inspected
The following files were inspected:
- `exercises/practice/split-second-stopwatch/.docs/instructions.md`
- `exercises/practice/split-second-stopwatch/split-second-stopwatch.test.ts`
- `exercises/practice/split-second-stopwatch/.meta/tests.toml`
- `exercises/practice/split-second-stopwatch/.meta/proof.ci.ts`
- `exercises/practice/split-second-stopwatch/.meta/config.json`
- `exercises/practice/split-second-stopwatch/package.json`

---

## 3. Metadata Structure and Path Resolution Explanation
In `exercises/practice/split-second-stopwatch/.meta/config.json`, the `files` object declares paths for exercise roles:
```json
{
  "files": {
    "solution": [
      "split-second-stopwatch.ts"
    ],
    "test": [
      "split-second-stopwatch.test.ts"
    ],
    "example": [
      ".meta/proof.ci.ts"
    ]
  }
}
```

### Path Resolution Mechanism
1. **Base Directory:** The root of the exercise (`exercises/practice/split-second-stopwatch/`) is the base path against which all relative paths are resolved.
2. **Path Normalization:** Relative paths (`split-second-stopwatch.ts`, `.meta/proof.ci.ts`) resolve strictly inside the exercise root.
3. **Traversal Prevention:** Any path containing `..` components or absolute paths pointing outside the exercise root is rejected with a fatal error.
4. **Existence Verification:** All declared files must exist as actual regular files on disk.

---

## 4. Real Configuration Validation Result
Executing `tools/course_checks/r47-t028.py` against `exercises/practice/split-second-stopwatch/.meta/config.json`:
- **Exit Code:** `0`
- **Status:** `[SUCCESS]`
- **Result:** All declared file paths (`split-second-stopwatch.ts`, `split-second-stopwatch.test.ts`, `.meta/proof.ci.ts`) exist on disk and resolve safely inside the exercise directory.

---

## 5. Three Invalid Fixture Results
The validator was tested against three negative configurations:

| Fixture | Scenario | Expected Exit Code | Actual Exit Code | Diagnostic Message |
| :--- | :--- | :---: | :---: | :--- |
| **Fixture A** | Missing reference implementation (`.meta/proof.ci.missing.ts`) | `1` | `1` | `Role 'example': Declared file '.meta/proof.ci.missing.ts' does not exist on disk` |
| **Fixture B** | Missing test suite file (`split-second-stopwatch.test.missing.ts`) | `1` | `1` | `Role 'test': Declared file 'split-second-stopwatch.test.missing.ts' does not exist on disk` |
| **Fixture C** | Directory traversal escaping exercise (`../outside.ts`) | `1` | `1` | `Role 'solution': Path '../outside.ts' contains forbidden parent-directory traversal ('..')` |

All fixtures failed with non-zero exit codes for the exact expected reasons.

---

## 6. Reference Test Execution Count
- **Total Canonical Cases in `tests.toml`:** 29
- **Executed by Jest in Sandbox:** 29
- **Passed:** 29
- **Failed:** 0

### Named Test Cases Verified:
1. `new stopwatch starts in ready state`: **PASS**
2. `new stopwatch's current lap has no elapsed time`: **PASS**
3. `new stopwatch's total has no elapsed time`: **PASS**
4. `new stopwatch does not have previous laps`: **PASS**

---

## 7. Expected versus Actual Outcomes
All expected validation and test execution outcomes matched actual runtime results:
- Metadata validator passed real config and caught all 3 invalid fixtures.
- Test runner in sandbox completed with exit code 0 and 29/29 tests passed.
- No assertions failed.

---

## 8. Learner Stub Preservation Confirmation
- File: `exercises/practice/split-second-stopwatch/split-second-stopwatch.ts`
- Status: **Unsolved and untouched**.
- Contains starter stub throwing: `throw new Error('Remove this line and implement the function')`.
- Working tree diff: 0 modifications.

---

## 9. Test File Preservation Confirmation
- File: `exercises/practice/split-second-stopwatch/split-second-stopwatch.test.ts`
- Status: **Unchanged in repository working tree**.
- Working tree diff: 0 modifications.

---

## 10. Tool Versions
Recorded from the execution environment:
- **Python:** 3.14.5
- **Node:** v24.22.1
- **Corepack:** 0.36.0
- **Yarn:** 4.5.1

---

## 11. Git Commit Details
- **Branch:** `student/e26b07f0754/R47-T028`
- **Commit Hash:** `9971fc0724bf2003c462377b21dc8f066b57117d`
- **Commit Message:** `R47-T028: Validate stopwatch exercise metadata`
- **Files Included:**
  - `tools/course_checks/r47-t028.py`
  - `docs/maintenance/split-second-stopwatch.md`
  - `work/R47-T028/*`

---

## 12. Pull Request Details
- **Base Repository:** `S-AI-Projects/typescript` (branch: `main`)
- **Head Branch:** `student/e26b07f0754/R47-T028`
- **PR Number:** #69
- **PR URL:** https://github.com/S-AI-Projects/typescript/pull/69
- **Title:** `R47-T028: Validate split-second-stopwatch metadata and document file resolution`
- **Isolation:** Standalone PR completely isolated from R47-T021 through R47-T027.

