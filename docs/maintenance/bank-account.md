# Maintenance Notes — bank-account

## Exercise Metadata

| Field | Value |
|-------|-------|
| Slug | `bank-account` |
| Difficulty | Medium |
| Blurb | Simulate a bank account supporting opening/closing, withdraws, and deposits of money. |

---

## Maintained Files

All paths are relative to `exercises/practice/bank-account/`.

| File | Role | Maintained by |
|------|------|---------------|
| `bank-account.ts` | Learner stub — skeleton with `throw new Error(...)` placeholders | Exercise author / configlet |
| `bank-account.test.ts` | Test suite (Jest) — first case enabled, rest use `xit` | Exercise author / configlet |
| `.meta/proof.ci.ts` | Reference implementation used by CI | Exercise maintainer |
| `.meta/config.json` | Exercise metadata, file paths, feature flags | configlet |
| `.meta/tests.toml` | Canonical test-case UUID registry | configlet sync |

### `.meta/config.json` Path Verification

The `files` block declares:

```json
"files": {
  "solution": ["bank-account.ts"],
  "test":     ["bank-account.test.ts"],
  "example":  [".meta/proof.ci.ts"]
}
```

All three paths exist on disk and are non-empty — verified by `tools/course_checks/r47-t008.py`.

---

## Class Structure (proof.ci.ts)

```
ValueError (extends Error)
  constructor()

BankAccount
  private _isOpen: boolean
  private _balance: number
  constructor()
  open(): void
  close(): void
  deposit(amount: number): void
  withdraw(amount: number): void
  get balance(): number   ← read-only getter; throws ValueError if closed
```

### Key invariants

| State | Allowed operations |
|-------|--------------------|
| Closed (initial) | `open()` |
| Open | `deposit()`, `withdraw()`, `balance` (get), `close()` |
| Re-opened | Balance resets to 0 |

Operations called in an invalid state throw `ValueError`.

---

## Test Suite Summary

| # | Test description | Status in test file |
|---|-----------------|---------------------|
| 1 | newly opened account has zero balance | `it` (enabled) |
| 2 | can deposit money | `xit` |
| 3 | can deposit money sequentially | `xit` |
| 4 | can withdraw money | `xit` |
| 5 | can withdraw money sequentially | `xit` |
| 6 | checking balance of closed account throws error | `xit` |
| 7 | deposit into closed account throws error | `xit` |
| 8 | withdraw from closed account throws error | `xit` |
| 9 | close already closed account throws error | `xit` |
| 10 | open already opened account throws error | `xit` |
| 11 | reopened account does not retain balance | `xit` |
| 12 | cannot withdraw more than deposited | `xit` |
| 13 | cannot withdraw negative amount | `xit` |
| 14 | cannot deposit negative amount | `xit` |
| 15 | changing balance directly throws error | `xit` |

Total: **15 test cases** (1 enabled by default, 14 behind `xit`).

The PR script (`scripts/pr.mjs`) converts all `xit` → `it` before running CI, so the
reference must pass all 15.

---

## Regeneration / Sync Commands

```bash
# Re-sync tests.toml from problem-specifications
./bin/configlet sync --tests --exercise bank-account

# Lint the exercise metadata
./bin/configlet lint --exercise bank-account
```
