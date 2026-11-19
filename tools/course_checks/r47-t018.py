#!/usr/bin/env python3
"""
r47-t018.py — Metadata file declaration check for Diamond (R47-T018)
-------------------------------------------------------------------
This script validates the `files` section of the exercise configuration:
  1. Ensures every declared file exists inside the Diamond exercise folder.
  2. Rejects any file declaration that is missing on disk.
  3. Rejects any file path that attempts to escape the exercise directory.
  4. Tests three synthetic invalid cases:
       - Missing reference file
       - Missing test file
       - Path escaping the exercise folder
  5. Verifies that the real metadata passes cleanly.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "diamond"
CONFIG_FILE = EXERCISE_DIR / ".meta" / "config.json"


def validate_files_declaration(
    exercise_dir: Path, files_obj: Dict[str, List[str]]
) -> Tuple[bool, List[str]]:
    """
    Validates that every file declared in `files_obj`:
      - Resolves to a path strictly inside `exercise_dir` (does not escape).
      - Exists as a regular file on disk.

    Returns (is_valid, list_of_error_messages).
    """
    errors: List[str] = []
    exercise_root = exercise_dir.resolve()

    if not isinstance(files_obj, dict) or not files_obj:
        return False, ["'files' object must be a non-empty dictionary"]

    for category, declared_paths in files_obj.items():
        if not isinstance(declared_paths, list) or not declared_paths:
            errors.append(f"Category '{category}' must be a non-empty list of paths")
            continue

        for rel_path in declared_paths:
            if not isinstance(rel_path, str) or not rel_path.strip():
                errors.append(f"Category '{category}' contains an invalid path: {rel_path!r}")
                continue

            # Resolve the path relative to the exercise folder
            target_path = (exercise_root / rel_path).resolve()

            # Check 1: Does the target path escape the exercise directory?
            try:
                target_path.relative_to(exercise_root)
            except ValueError:
                errors.append(
                    f"Path escapes exercise directory in category '{category}': {rel_path}"
                )
                continue

            # Check 2: Does the declared file exist on disk?
            if not target_path.is_file():
                errors.append(
                    f"Declared file missing on disk in category '{category}': {rel_path}"
                )

    is_valid = len(errors) == 0
    return is_valid, errors


def test_invalid_cases(exercise_dir: Path, real_files: Dict[str, List[str]]) -> bool:
    """
    Runs three negative test cases to ensure the validator correctly rejects:
      1. Missing reference file.
      2. Missing test file.
      3. Outside-exercise path traversal.
    """
    print("\n--- Running Synthetic Negative Test Cases ---")
    all_passed = True

    # Case 1: Missing reference file
    mock_case_1 = {
        "solution": real_files.get("solution", ["diamond.ts"]),
        "test": real_files.get("test", ["diamond.test.ts"]),
        "example": [".meta/non_existent_proof.ci.ts"],
    }
    valid_1, errors_1 = validate_files_declaration(exercise_dir, mock_case_1)
    if not valid_1 and any("non_existent_proof" in e for e in errors_1):
        print("✅ Case 1 Passed: Correctly rejected missing reference file.")
        print(f"   Reason: {errors_1[0]}")
    else:
        print("❌ Case 1 Failed: Should have rejected missing reference file!")
        all_passed = False

    # Case 2: Missing test file
    mock_case_2 = {
        "solution": real_files.get("solution", ["diamond.ts"]),
        "test": ["missing_diamond.test.ts"],
        "example": real_files.get("example", [".meta/proof.ci.ts"]),
    }
    valid_2, errors_2 = validate_files_declaration(exercise_dir, mock_case_2)
    if not valid_2 and any("missing_diamond" in e for e in errors_2):
        print("✅ Case 2 Passed: Correctly rejected missing test file.")
        print(f"   Reason: {errors_2[0]}")
    else:
        print("❌ Case 2 Failed: Should have rejected missing test file!")
        all_passed = False

    # Case 3: Outside-exercise path traversal
    mock_case_3 = {
        "solution": ["../diamond.ts"],
        "test": real_files.get("test", ["diamond.test.ts"]),
        "example": real_files.get("example", [".meta/proof.ci.ts"]),
    }
    valid_3, errors_3 = validate_files_declaration(exercise_dir, mock_case_3)
    if not valid_3 and any("escapes" in e.lower() for e in errors_3):
        print("✅ Case 3 Passed: Correctly rejected outside-exercise path.")
        print(f"   Reason: {errors_3[0]}")
    else:
        print("❌ Case 3 Failed: Should have rejected outside-exercise path!")
        all_passed = False

    return all_passed


def main() -> int:
    print("==================================================")
    print("Diamond Exercise Metadata File Check (R47-T018)")
    print("==================================================")
    print(f"Exercise Directory: {EXERCISE_DIR}")
    print(f"Config File:        {CONFIG_FILE}")

    if not CONFIG_FILE.is_file():
        print(f"[FAIL] Config file not found at: {CONFIG_FILE}", file=sys.stderr)
        return 1

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"[FAIL] Could not read JSON config: {e}", file=sys.stderr)
        return 1

    files_obj = config_data.get("files")
    if not isinstance(files_obj, dict):
        print("[FAIL] 'files' object is missing or invalid in config.json", file=sys.stderr)
        return 1

    print(f"Declared files: {json.dumps(files_obj, indent=2)}")

    # 1. Test invalid cases
    negative_tests_ok = test_invalid_cases(EXERCISE_DIR, files_obj)
    if not negative_tests_ok:
        print("\n[FAIL] One or more negative test cases failed!", file=sys.stderr)
        return 1

    # 2. Test real metadata
    print("\n--- Validating Real Exercise Metadata ---")
    valid, errors = validate_files_declaration(EXERCISE_DIR, files_obj)
    if not valid:
        print("[FAIL] Real metadata validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("✅ Real metadata passed all checks:")
    for category, paths in files_obj.items():
        for path in paths:
            print(f"   - {category}: {path} (exists, within exercise)")

    print("\n==================================================")
    print("RESULT: ALL METADATA CHECKS PASSED SUCCESSFULLY")
    print("==================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
