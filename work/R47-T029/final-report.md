# Final Report: Assignment R47-T029 — Nucleotide Count Isolated Test Runner

## 1. Branch Name
- **Assigned Branch:** `student/e26b07f0754`
- **Task Working Branch:** `student/e26b07f0754/R47-T029` (branched cleanly from `upstream/main`)

---

## 2. Commit Hash & Git Push Status
- **Commit Message:** `R47-T029: Add isolated nucleotide-count test runner`
- **Pushed To:** `origin/student/e26b07f0754/R47-T029`
- **Initial Commit Hash:** `71a255f5ddcfd485f52445cbf92b323145465bb6`


---

## 3. Changed and Created Files
- **Isolated Test Runner:**
  - `tools/course_checks/r47-t029.py`
- **Maintenance Documentation:**
  - `docs/maintenance/nucleotide-count.md`
- **Checker & Evidence Artifacts (`work/R47-T029/`):**
  - `check.py`
  - `inputs.json`
  - `expected-results.json`
  - `actual-results.json`
  - `test-results.md`
  - `hash-integrity.json`
  - `tool-versions.txt`
  - `output.txt`
  - `final-report.md`

---

## 4. Actual Canonical Test Count
- **Total Canonical Cases in `tests.toml`:** 5
- **Executed by Jest in Sandbox:** 5
- **Named Cases Verified:**
  1. `empty strand`: **PASS**
  2. `can count one nucleotide in single-character input`: **PASS**
  3. `strand with repeated nucleotide`: **PASS**

---

## 5. Passed and Failed Test Counts
- **Total:** 5
- **Passed:** 5
- **Failed:** 0
- **Duration:** 0.207 s

---

## 6. Successful-Reference Scenario (Scenario A)
- **Configuration:** Real maintained reference (`.meta/proof.ci.ts`) substituted into temporary sandbox copy.
- **Exit Code:** `0`
- **Executed Cases:** 5/5 passed.
- **Zero-test Protection:** Verified non-zero test execution.
- **Result:** **PASS**.

---

## 7. Failing-Reference Scenario (Scenario B)
- **Configuration:** Deliberately failing reference implementation returning invalid counts (`{ A: -1, C: -1, G: -1, T: -1 }`).
- **Exit Code:** `1` (non-zero).
- **Diagnostics:** Runner caught assertion failures (`5 failed, 0 passed`) and propagated error status.
- **Result:** **PASS**.

---

## 8. Zero-Test Scenario (Scenario C)
- **Configuration:** Test selection pattern matching non-existent test (`-t NONEXISTENT_TEST_NAME_XYZ`).
- **Exit Code:** `1` (non-zero).
- **Diagnostics:** Runner detected zero executed tests and refused to report false success.
- **Result:** **PASS**.

---

## 9. SHA-256 File Hash Integrity Results
Cryptographic SHA-256 hashes calculated before and after every scenario:
- `exercises/practice/nucleotide-count/nucleotide-count.ts`:
  - `774c2697bd0e0f7a133525521500da3e1ecc165542fd223e66b1e8649b32f382`
- `exercises/practice/nucleotide-count/nucleotide-count.test.ts`:
  - `6b19a46d7d7b4767b4b19d0f5936e1a6e820dbefccd961f6f2f9361d4cc2ff97`
- `exercises/practice/nucleotide-count/.meta/proof.ci.ts`:
  - `dcef80826c7d94c570885e884742d62f2fd51d612218449db22ce85048929fcb`

All hashes matched initial values across all scenarios.

---

## 10. Temporary Directory Cleanup Result
- Managed via Python's `tempfile.TemporaryDirectory()` context managers.
- Verified that all sandbox directories were completely removed following test completion and exception paths.

---

## 11. Learner-Stub Preservation Confirmation
- File: `exercises/practice/nucleotide-count/nucleotide-count.ts`
- Status: **Unsolved and untouched**.
- Content: `throw new Error('Remove this line and implement the function')`.
- Working tree diff: 0 modifications.

---

## 12. Separate Pull Request Details
- **Base Repository:** `S-AI-Projects/typescript` (branch: `main`)
- **Head Branch:** `student/e26b07f0754/R47-T029`
- **PR Number:** #70
- **PR URL:** https://github.com/S-AI-Projects/typescript/pull/70
- **Title:** `R47-T029: Add isolated nucleotide-count test runner`
- **Isolation:** Standalone PR completely isolated from R47-T021 through R47-T028.
- **State:** Open

