# Maintenance Guide: rotational-cipher

## Overview
- Exercise: `exercises/practice/rotational-cipher`
- Reference implementation: `exercises/practice/rotational-cipher/.meta/proof.ci.ts`
- Solution starter: `exercises/practice/rotational-cipher/rotational-cipher.ts`
- Test suite: `exercises/practice/rotational-cipher/rotational-cipher.test.ts`
- Canonical case metadata: `exercises/practice/rotational-cipher/.meta/tests.toml`
- Focus tool: `tools/course_checks/r47-t002.py`

## File Role Distinction

| File | Maintenance Role | Generation Source / Notes |
|---|---|---|
| `rotational-cipher.ts` | Maintained by hand | Starter stub (unsolved) throwing an error for learners. |
| `.meta/proof.ci.ts` | Maintained by hand | Reference implementation implementing `rotate(text, shiftBy)`. |
| `.meta/tests.toml` | Track-managed / sync | Synced from Exercism `problem-specifications` canonical cases via `configlet sync`. |
| `rotational-cipher.test.ts` | Maintained / Generated | Jest test cases corresponding 1:1 with canonical cases. Reproducible via `tools/course_checks/r47-t002.py`. |
| `.meta/config.json` | Maintained by hand | Declares solution, test, and reference example files. |

## Anchor Cases & Source Mapping

The canonical case data originates from `problem-specifications/exercises/rotational-cipher/canonical-data.json` and `.meta/tests.toml`:

1. **`rotate a by 1`**
   - **UUID:** `7ee352c6-e6b0-4930-b903-d09943ecb8f5`
   - **Input:** `text = "a"`, `shiftBy = 1`
   - **Expected Result:** `'b'`
   - **Rationale:** Base rotation case verifying simple non-wrapping single-character transposition.

2. **`rotate a by 26, same output as input`**
   - **UUID:** `edf0a733-4231-4594-a5ee-46a4009ad764`
   - **Input:** `text = "a"`, `shiftBy = 26`
   - **Expected Result:** `'a'`
   - **Rationale:** Modular arithmetic identity boundary; shifting by alphabet length $26 \equiv 0 \pmod{26}$.

3. **`rotate a by 0, same output as input`**
   - **UUID:** `74e58a38-e484-43f1-9466-877a7515e10f`
   - **Input:** `text = "a"`, `shiftBy = 0`
   - **Expected Result:** `'a'`
   - **Rationale:** Identity case; shift by 0 returns unmodified string.

## Complete Canonical Case-to-Output Mapping

| UUID | Case Description | Input (`text`, `shiftBy`) | Expected Output | Active / Skipped |
|---|---|---|---|---|
| `7ee352c6-e6b0-4930-b903-d09943ecb8f5` | `rotate a by 1` | `('a', 1)` | `'b'` | `it` (Active) |
| `edf0a733-4231-4594-a5ee-46a4009ad764` | `rotate a by 26, same output as input` | `('a', 26)` | `'a'` | `xit` (Optional) |
| `74e58a38-e484-43f1-9466-877a7515e10f` | `rotate a by 0, same output as input` | `('a', 0)` | `'a'` | `xit` (Optional) |
| `e3e82cb9-2a5b-403f-9931-e43213879300` | `rotate m by 13` | `('m', 13)` | `'z'` | `xit` (Optional) |
| `19f9eb78-e2ad-4da4-8fe3-9291d47c1709` | `rotate n by 13 with wrap around alphabet` | `('n', 13)` | `'a'` | `xit` (Optional) |
| `a116aef4-225b-4da9-884f-e8023ca6408a` | `rotate capital letters` | `('OMG', 5)` | `'TRL'` | `xit` (Optional) |
| `71b541bb-819c-4dc6-a9c3-132ef9bb737b` | `rotate spaces` | `('O M G', 5)` | `'T R L'` | `xit` (Optional) |
| `ef32601d-e9ef-4b29-b2b5-8971392282e6` | `rotate numbers` | `('Testing 1 2 3 testing', 4)` | `'Xiwxmrk 1 2 3 xiwxmrk'` | `xit` (Optional) |
| `32dd74f6-db2b-41a6-b02c-82eb4f93e549` | `rotate punctuation` | `("Let's eat, Grandma!", 21)` | `"Gzo'n zvo, Bmviyhv!"` | `xit` (Optional) |
| `9fb93fe6-42b0-46e6-9ec1-0bf0a062d8c9` | `rotate all letters` | `('The quick brown fox jumps over the lazy dog.', 13)` | `'Gur dhvpx oebja sbk whzcf bire gur ynml qbt.'` | `xit` (Optional) |

## Exact Generation & Validation Commands

1. **Verify Test Generation Reproducibility:**
   ```bash
   python3 tools/course_checks/r47-t002.py
   ```
2. **Sync / Check Canonical Metadata:**
   ```bash
   ./bin/configlet sync --tests --exercise rotational-cipher
   ```
3. **Execute Full Automated Verification:**
   ```bash
   python3 work/R47-T002/check.py
   ```
4. **Execute PR Exercise Test:**
   ```bash
   corepack yarn node scripts/pr.mjs exercises/practice/rotational-cipher
   ```
