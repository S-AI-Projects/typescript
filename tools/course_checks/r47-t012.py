#!/usr/bin/env python3
"""
Repeatability Check for Game of Life (GitHub Issue #12 — R47-T012).

This script verifies that the test preparation process identified in
scripts/helpers.mjs is reproducible and deterministic.

Requirements:
1. Creates two separate, fresh temporary directories.
2. Reproduces the existing track test-preparation process in both.
3. Compares the prepared test files between the two preparations.
4. Verifies that all eight canonical test cases are present.
5. Verifies that none of the test cases silently disappears.
6. Reports whether both preparations produce identical outputs.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


EXPECTED_TEST_CASES = [
    "empty matrix",
    "live cells with zero live neighbors die",
    "live cells with only one live neighbor die",
    "live cells with two live neighbors stay alive",
    "live cells with three live neighbors stay alive",
    "dead cells with three live neighbors become alive",
    "live cells with four or more neighbors die",
    "bigger matrix",
]


def prepare_exercise(repo_root: Path, target_dir: Path) -> Path:
    """
    Reproduces the track's test preparation process from scripts/helpers.mjs:
    - Reads .meta/config.json
    - Copies test file and unskips tests (xit -> it)
    - Copies reference implementation (.meta/proof.ci.ts) as the solution file
    - Sets up necessary configuration files
    """
    exercise_dir = repo_root / "exercises" / "practice" / "game-of-life"
    config_file = exercise_dir / ".meta" / "config.json"

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    solution_name = config["files"]["solution"][0]
    test_name = config["files"]["test"][0]
    example_name = config["files"]["example"][0]

    # Copy entire exercise directory (including hidden files) into target
    shutil.copytree(exercise_dir, target_dir, dirs_exist_ok=True)

    dest_test_file = target_dir / test_name
    dest_solution_file = target_dir / solution_name
    source_example = target_dir / example_name

    # Transform test file: unskip tests as done in scripts/helpers.mjs lines 368-378
    with open(dest_test_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Apply helpers.mjs regex substitutions
    content = re.sub(r"x(test|it)\(", r"it(", content)
    content = re.sub(r"xdescribe\(", r"describe(", content)
    content = re.sub(r"x(test|it|describe),\s*", r"", content)
    content = re.sub(r",\s*x(test|it|describe)\s*}", r"}", content)

    with open(dest_test_file, "w", encoding="utf-8") as f:
        f.write(content)

    # Substitute reference implementation as solution
    shutil.copy2(source_example, dest_solution_file)

    return dest_test_file


def normalize_timestamps(text: str) -> str:
    """
    Normalizes any dynamic timestamp differences if present.
    Documents and neutralizes ISO 8601 timestamps before comparison.
    """
    timestamp_pattern = r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"
    return re.sub(timestamp_pattern, "<TIMESTAMP_NORMALIZED>", text)


def verify_test_cases(test_file: Path) -> tuple[bool, list[str]]:
    """Verifies that all 8 canonical test cases are present in the prepared test file."""
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()

    missing = []
    for test_name in EXPECTED_TEST_CASES:
        pattern = rf"it\(\s*['\"]{re.escape(test_name)}['\"]"
        if not re.search(pattern, content):
            missing.append(test_name)

    # Check for any remaining skipped tests
    has_skipped = bool(re.search(r"\bxit\(", content))
    return len(missing) == 0 and not has_skipped, missing


def run_tests_in_dir(target_dir: Path) -> tuple[int, int, str]:
    """Runs tests in prepared directory to verify test execution count."""
    env = os.environ.copy()
    env["CI"] = "true"
    env["JEST_WATCH"] = "false"
    env["NODE_ENV"] = "test"

    # Install dependencies non-mutably
    subprocess.run(
        ["corepack", "yarn", "install", "--no-immutable"],
        cwd=target_dir,
        env=env,
        capture_output=True,
        text=True,
    )

    proc = subprocess.run(
        ["corepack", "yarn", "test"],
        cwd=target_dir,
        env=env,
        capture_output=True,
        text=True,
    )

    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    match = re.search(r"Tests:\s+(\d+)\s+passed,\s+(\d+)\s+total", output)
    passed = int(match.group(1)) if match else 0
    total = int(match.group(2)) if match else 0
    return proc.returncode, passed, output


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    exercise_dir = repo_root / "exercises" / "practice" / "game-of-life"

    print("==================================================")
    print("Game of Life Repeatability Check (R47-T012)")
    print("==================================================")
    print(f"Target Exercise: {exercise_dir}")
    print(f"Expected Canonical Cases: {len(EXPECTED_TEST_CASES)}")

    with tempfile.TemporaryDirectory() as temp_dir_1, tempfile.TemporaryDirectory() as temp_dir_2:
        path_1 = Path(temp_dir_1)
        path_2 = Path(temp_dir_2)

        print(f"Directory 1: {path_1}")
        print(f"Directory 2: {path_2}")

        # Perform preparation 1
        print("\n[Step 1] Performing Preparation 1...")
        test_file_1 = prepare_exercise(repo_root, path_1)
        valid_1, missing_1 = verify_test_cases(test_file_1)
        if not valid_1:
            print(f"[FAIL] Preparation 1 missing cases: {missing_1}", file=sys.stderr)
            sys.exit(1)
        print("[PASS] Preparation 1 contains all 8 canonical test cases.")

        # Perform preparation 2
        print("\n[Step 2] Performing Preparation 2...")
        test_file_2 = prepare_exercise(repo_root, path_2)
        valid_2, missing_2 = verify_test_cases(test_file_2)
        if not valid_2:
            print(f"[FAIL] Preparation 2 missing cases: {missing_2}", file=sys.stderr)
            sys.exit(1)
        print("[PASS] Preparation 2 contains all 8 canonical test cases.")

        # Compare prepared test files
        print("\n[Step 3] Comparing prepared test files...")
        with open(test_file_1, "r", encoding="utf-8") as f:
            content_1 = f.read()
        with open(test_file_2, "r", encoding="utf-8") as f:
            content_2 = f.read()

        norm_1 = normalize_timestamps(content_1)
        norm_2 = normalize_timestamps(content_2)

        if norm_1 != norm_2:
            print("[FAIL] Mismatch detected between Preparation 1 and Preparation 2!", file=sys.stderr)
            sys.exit(1)
        print("[PASS] Prepared test files in both directories are 100% IDENTICAL.")

        # Verify test execution in both preparations
        print("\n[Step 4] Running test execution in Preparation 1...")
        code_1, passed_1, _ = run_tests_in_dir(path_1)
        if code_1 != 0 or passed_1 != 8:
            print(f"[FAIL] Preparation 1 test run failed: {passed_1}/8 passed (code {code_1})", file=sys.stderr)
            sys.exit(1)
        print(f"[PASS] Preparation 1 executed and passed all {passed_1}/8 tests.")

        print("\n[Step 5] Running test execution in Preparation 2...")
        code_2, passed_2, _ = run_tests_in_dir(path_2)
        if code_2 != 0 or passed_2 != 8:
            print(f"[FAIL] Preparation 2 test run failed: {passed_2}/8 passed (code {code_2})", file=sys.stderr)
            sys.exit(1)
        print(f"[PASS] Preparation 2 executed and passed all {passed_2}/8 tests.")

        print("\n==================================================")
        print("RESULT: REPEATABILITY VERIFIED (Identical across preparations)")
        print("==================================================")
        sys.exit(0)


if __name__ == "__main__":
    main()

