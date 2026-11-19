#!/usr/bin/env python3
"""
r47-t019.py — Isolated test runner for Word Count (R47-T019)
------------------------------------------------------------
Runs the word-count exercise test suite in an isolated temporary directory
using the reference implementation (.meta/proof.ci.ts), without modifying
the learner solution or any repository files.

Requirements:
  1. Reads .meta/config.json to discover solution, test, and reference paths.
  2. Copies the entire exercise into a temporary directory (including hidden files).
  3. Replaces the solution with the reference implementation inside the temp copy.
  4. Unskips all exercise tests (xit -> it) so all 14 tests execute.
  5. Runs package test script (yarn test) with watch mode disabled (CI=true).
  6. Fails if zero tests run, any assertion fails, or any child process exits non-zero.
  7. Guarantees complete cleanup of temporary directories under all exit paths.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "word-count"
EXPECTED_TEST_COUNT = 14


def configured_file(config: Dict[str, object], kind: str) -> str:
    """Extracts a declared file path from the config.json 'files' object."""
    files = config.get("files", {})
    if not isinstance(files, dict):
        raise ValueError("config.json must contain a 'files' object")
    values = files.get(kind)
    if not isinstance(values, list) or not values or not isinstance(values[0], str):
        raise ValueError(f"config.json must contain a '{kind}' file path")
    return values[0]


def run_command(
    command: List[str], cwd: Path, env: Dict[str, str]
) -> Tuple[Optional[int], str, str]:
    """Executes a command and returns (exit_code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except OSError as err:
        return None, "", str(err)


def run_isolated_tests(
    exercise_dir: Path,
    reference_path: Optional[Path] = None,
    empty_tests: bool = False,
    verbose: bool = True,
) -> Dict[str, object]:
    """
    Executes the isolated test run in a temporary directory.
    Guarantees cleanup of temporary directory via try...finally block.
    """
    config_file = exercise_dir / ".meta" / "config.json"
    if not config_file.is_file():
        raise FileNotFoundError(f"Missing config file at {config_file}")

    with config_file.open("r", encoding="utf-8") as f:
        config = json.load(f)

    solution_name = configured_file(config, "solution")
    test_name = configured_file(config, "test")
    default_example = configured_file(config, "example")

    ref_to_use = (
        reference_path.resolve()
        if reference_path is not None
        else (exercise_dir / default_example).resolve()
    )

    if not ref_to_use.is_file():
        raise FileNotFoundError(f"Reference file not found: {ref_to_use}")

    env = os.environ.copy()
    env["CI"] = "true"
    env["FORCE_COLOR"] = "0"

    temp_dir_obj = tempfile.TemporaryDirectory(prefix="r47-t019-")
    try:
        temp_root = Path(temp_dir_obj.name)
        temp_exercise = temp_root / "word-count"

        # 1. Copy exercise including all hidden files/directories
        shutil.copytree(exercise_dir, temp_exercise)
        if verbose:
            print(f"[runner] Copied exercise to temporary directory: {temp_exercise}")

        # 2. Replace learner solution with the chosen reference implementation
        temp_solution = temp_exercise / solution_name
        shutil.copy2(ref_to_use, temp_solution)
        if verbose:
            print(f"[runner] Replaced {solution_name} with reference {ref_to_use.name}")

        # 3. Configure test suite
        temp_test = temp_exercise / test_name
        test_content = temp_test.read_text(encoding="utf-8")

        if empty_tests:
            # Empties the test suite so zero tests execute
            test_content = re.sub(r"\b(?:x?it|x?test)\s*\(", "// it(", test_content)
            temp_test.write_text(test_content, encoding="utf-8")
            if verbose:
                print("[runner] Configured empty test selection (all tests commented out)")
        else:
            # Unskip all tests
            test_content = re.sub(r"\bxdescribe\s*\(", "describe(", test_content)
            test_content = re.sub(r"\bxit\s*\(", "it(", test_content)
            temp_test.write_text(test_content, encoding="utf-8")
            if verbose:
                print(f"[runner] Unskipped all tests in {test_name}")

        # 4. Install dependencies
        if verbose:
            print("[runner] Installing dependencies: corepack yarn install --no-immutable ...")
        install_rc, install_out, install_err = run_command(
            ["corepack", "yarn", "install", "--no-immutable"], temp_exercise, env
        )
        if install_rc != 0:
            if verbose:
                print("[runner] ERROR: yarn install failed!", file=sys.stderr)
                print(install_out, file=sys.stderr)
                print(install_err, file=sys.stderr)
            return {
                "success": False,
                "stage": "install",
                "exit_code": install_rc,
                "stdout": install_out,
                "stderr": install_err,
                "passed": 0,
                "total": 0,
                "failed": 0,
                "error": "yarn install failed",
            }

        # 5. Run exercise test script
        if verbose:
            print("[runner] Running test suite: corepack yarn test ...")
        test_rc, test_out, test_err = run_command(
            ["corepack", "yarn", "test"], temp_exercise, env
        )
        combined_output = (test_out or "") + "\n" + (test_err or "")

        # 6. Parse test summary
        summary = re.search(r"^Tests:\s*(.*)$", combined_output, re.MULTILINE)
        passed_match = re.search(r"(\d+)\s+passed", summary.group(1)) if summary else None
        total_match = re.search(r"(\d+)\s+total", summary.group(1)) if summary else None
        failed_match = re.search(r"(\d+)\s+failed", summary.group(1)) if summary else None

        passed = int(passed_match.group(1)) if passed_match else 0
        total = int(total_match.group(1)) if total_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0

        # 7. Verification criteria:
        # - Process exited with 0
        # - More than 0 tests ran
        # - All executed tests passed
        # - Zero failed tests
        has_tests = total > 0
        passed_all = has_tests and (passed == total) and (failed == 0)
        proc_ok = (test_rc == 0)
        success = proc_ok and passed_all

        error_message = ""
        if not proc_ok:
            error_message = f"Test process exited with non-zero code {test_rc}"
        elif not has_tests:
            error_message = "Zero tests were executed (expected at least 1 test)"
        elif not passed_all:
            error_message = f"Tests failed: {failed} failed out of {total} total"

        result = {
            "success": success,
            "stage": "test",
            "exit_code": test_rc,
            "stdout": test_out,
            "stderr": test_err,
            "combined_output": combined_output,
            "passed": passed,
            "total": total,
            "failed": failed,
            "error": error_message,
        }
        return result

    finally:
        # Guaranteed cleanup of temporary directory
        temp_dir_obj.cleanup()
        if verbose:
            print("[runner] Cleaned up temporary directory.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Isolated test runner for Word Count (R47-T019)"
    )
    parser.add_argument(
        "--exercise-dir",
        type=Path,
        default=DEFAULT_EXERCISE_DIR,
        help="Path to word-count exercise directory",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=None,
        help="Custom reference solution file to test",
    )
    parser.add_argument(
        "--empty-tests",
        action="store_true",
        help="Simulate an empty test selection (0 tests executed)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result in JSON format",
    )
    args = parser.parse_args()

    verbose = not args.json
    try:
        result = run_isolated_tests(
            exercise_dir=args.exercise_dir,
            reference_path=args.reference,
            empty_tests=args.empty_tests,
            verbose=verbose,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"success": False, "error": str(exc)}))
        else:
            print(f"[runner] Fatal error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        # Strip long outputs in JSON if needed, or include summary
        summary = {
            "success": result["success"],
            "exit_code": result["exit_code"],
            "passed": result["passed"],
            "total": result["total"],
            "failed": result["failed"],
            "error": result["error"],
        }
        print(json.dumps(summary, indent=2))
    else:
        print("\n==================================================")
        print("RUNNER SUMMARY")
        print("==================================================")
        print(f"Success:      {result['success']}")
        print(f"Exit Code:    {result['exit_code']}")
        print(f"Tests Passed: {result['passed']}/{result['total']}")
        print(f"Tests Failed: {result['failed']}")
        if result["error"]:
            print(f"Error:        {result['error']}")
        print("==================================================")

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
