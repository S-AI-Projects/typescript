# Automated Execution & Mutation Regression Report (R47-T023)

- **Date:** 2026-11-18
- **Exercise:** `exercises/practice/etl`
- **Branch:** `student/e26b07f0754/R47-T023`
- **Checker:** `work/R47-T023/check.py`

---

## 1. Summary of Execution

The automated verification checker (`work/R47-T023/check.py`) was executed to perform a mutation-driven regression test on the `etl` exercise in isolated temporary environments.

### Overall Outcome: **ALL CHECKS PASSED**

---

## 2. Tool Versions

| Tool | Version | Source File |
| :--- | :--- | :--- |
| Python | `3.14.5` | `work/R47-T023/tool-versions.json` |
| Node.js | `v24.22.1` | `work/R47-T023/version-node.log` |
| Yarn (Berry) | `4.5.1` | `work/R47-T023/version-yarn.log` |

---

## 3. Reference Implementation Verification (Original)

In an isolated temporary environment with all 4 canonical test cases enabled:
- **Total Tests Executed:** 4
- **Passed:** 4
- **Failed:** 0
- **Exit Code:** 0

All 4 canonical test cases cleanly pass against the reference implementation (`.meta/proof.ci.ts`).

---

## 4. Mutation Experiment

### Deliberate Mutation
In `.meta/proof.ci.ts`:
```typescript
// Original
phase1[each.toLowerCase()] = Number.parseInt(key, 10)

// Mutated
phase1[each] = Number.parseInt(key, 10)
```
The mutation deliberately omits `.toLowerCase()`, directly using uppercase letter strings as dictionary keys.

### Minimal Rejecting Case
- **Canonical Test ID (UUID):** `78a7a9f9-4490-4a47-8ee9-5a38bb47d28f`
- **Test Title:** `"transforms one value"`
- **Minimal Input:**
  ```json
  { "1": ["A"] }
  ```
- **Expected Result:**
  ```json
  { "a": 1 }
  ```
- **Actual Mutated Result:**
  ```json
  { "A": 1 }
  ```

### Mutant Test Suite Results
- **Total Tests Executed:** 4
- **Passed:** 0
- **Failed:** 4
- **Exit Code:** 1 (Non-zero exit caught and verified)

---

## 5. Integrity & Verification Checks

1. **Learner Stub:** `exercises/practice/etl/etl.ts` remains unsolved with `throw new Error('Remove this line and implement the function')`.
2. **Repository Working Tree:** Neither `etl.ts`, `etl.test.ts`, nor `.meta/proof.ci.ts` were modified by the verification scripts.
3. **Isolation:** Neither R47-T021 nor R47-T022 files were touched.
