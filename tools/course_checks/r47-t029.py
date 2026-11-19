#!/usr/bin/env python3
"""
tools/course_checks/r47-t029.py

Isolated test runner for exercises/practice/nucleotide-count.

Requirements:
1. Parse exercises/practice/nucleotide-count/.meta/config.json to resolve solution, test, and example paths.
2. Validate paths resolve strictly inside the exercise directory (no parent traversal '..').
3. Verify all declared files exist.
4. Create an isolated temporary directory, copy the exercise (including dotfiles), and preserve structure.
5. Substitute reference implementation into the solution path ONLY inside the temporary copy.
6. Enable all test cases (xit( -> it()) in the temporary copy.
7. Execute tests using package.json scripts with watch mode disabled (--ci, --watchAll=false).
8. Parse executed, passed, and failed test counts.
9. Return non-zero exit status if:
   - Configuration is invalid or path escapes exercise.
   - Any child process fails.
   - Any test assertion fails.
   - Zero tests execute.
10. Ensure temporary directory is always cleaned up and original working tree files remain pristine.
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

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXERCISE_DIR = (
    DEFAULT_REPO_ROOT / "exercises" / "practice" / "nucleotide-count"
)
DEFAULT_CONFIG_PATH = DEFAULT_EXERCISE_DIR / ".meta" / "config.json"


class RunnerError(Exception):
    """Raised when an error occurs during test runner execution."""


def validate_and_resolve_paths(
    config_path: Path, exercise_dir: Path
) -> dict[str, str]:
    """Validate config.json and resolve file paths strictly inside exercise_dir."""
    if not config_path.is_file():
        raise RunnerError(f"Configuration file not found: {config_path}")

    if not exercise_dir.is_dir():
        raise RunnerError(f"Exercise directory not found: {exercise_dir}")

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RunnerError(f"Malformed JSON in config file {config_path}: {exc}")

    files_obj = data.get("files")
    if not isinstance(files_obj, dict):
        raise RunnerError("Missing or invalid 'files' object in config.json")

    for role in ("solution", "test", "example"):
        if role not in files_obj or not isinstance(files_obj[role], list) or not files_obj[role]:
            raise RunnerError(f"Missing or empty required role '{role}' in config.json files object")

    resolved = {}
    ex_resolved = exercise_dir.resolve()

    for role, path_list in files_obj.items():
        if not isinstance(path_list, list):
            continue
        for p in path_list:
            if not isinstance(p, str) or not p.strip():
                raise RunnerError(f"Role '{role}' contains empty or non-string path")

            if ".." in Path(p).parts:
                raise RunnerError(
                    f"Role '{role}': Path '{p}' contains forbidden parent traversal ('..')"
                )

            entry_path = Path(p)
            target = (
                entry_path.resolve()
                if entry_path.is_absolute()
                else (exercise_dir / entry_path).resolve()
            )

            try:
                target.relative_to(ex_resolved)
            except ValueError:
                raise RunnerError(
                    f"Role '{role}': Path '{p}' escapes exercise directory: {target}"
                )

            if not target.is_file():
                raise RunnerError(
                    f"Role '{role}': Declared file '{p}' does not exist on disk: {target}"
                )

            if role not in resolved:
                resolved[role] = p

    return resolved


def run_isolated_test(
    exercise_dir: Path,
    config_path: Path,
    reference_path: Path | None = None,
    test_pattern: str | None = None,
) -> dict:
    """Run tests in an isolated temporary directory.

    Always cleans up the temporary directory. Returns summary dict or raises RunnerError.
    """
    paths = validate_and_resolve_paths(config_path, exercise_dir)
    solution_rel = paths["solution"]
    test_rel = paths["test"]
    example_rel = paths["example"]

    ref_to_substitute = (
        reference_path.resolve()
        if reference_path
        else (exercise_dir / example_rel).resolve()
    )

    if not ref_to_substitute.is_file():
        raise RunnerError(f"Reference implementation file does not exist: {ref_to_substitute}")

    # Temporary directory isolation with context manager
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_exercise = Path(tmp_dir) / "nucleotide-count"
        shutil.copytree(exercise_dir, tmp_exercise, symlinks=True)

        # Substitute reference into solution path ONLY in the temporary copy
        shutil.copyfile(ref_to_substitute, tmp_exercise / solution_rel)

        # Enable all tests (xit( -> it()) in the temporary copy
        test_file = tmp_exercise / test_rel
        enabled_test_content = re.sub(r"\bxit\(", "it(", test_file.read_text(encoding="utf-8"))
        test_file.write_text(enabled_test_content, encoding="utf-8")

        env = dict(os.environ, CI="1")

        # 1. Install dependencies
        inst = subprocess.run(
            ["corepack", "yarn", "install", "--no-immutable"],
            cwd=tmp_exercise,
            capture_output=True,
            text=True,
            env=env,
        )
        if inst.returncode != 0:
            raise RunnerError(
                f"corepack yarn install failed with code {inst.returncode}:\n{inst.stderr}"
            )

        # 2. Run Jest with JSON reporting
        res_file = tmp_exercise / "jest-results.json"
        cmd = [
            "corepack",
            "yarn",
            "test:implementation",
            "--ci",
            "--watchAll=false",
            "--json",
            f"--outputFile={res_file}",
        ]
        if test_pattern:
            cmd.extend(["-t", test_pattern])

        jest_proc = subprocess.run(
            cmd,
            cwd=tmp_exercise,
            capture_output=True,
            text=True,
            env=env,
        )

        if not res_file.is_file():
            raise RunnerError(
                f"Jest failed to produce results JSON (exit {jest_proc.returncode}):\n{jest_proc.stderr}"
            )

        try:
            data = json.loads(res_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RunnerError(f"Failed to parse Jest results JSON: {exc}")

        total_tests = data.get("numTotalTests", 0)
        passed_tests = data.get("numPassedTests", 0)
        failed_tests = data.get("numFailedTests", 0)
        pending_tests = data.get("numPendingTests", 0)
        executed_tests = passed_tests + failed_tests

        assertions = {
            a["title"]: a["status"]
            for suite in data.get("testResults", [])
            for a in suite.get("assertionResults", [])
        }

        # Check zero-test condition
        if executed_tests == 0:
            raise RunnerError(
                f"Zero tests were executed (total={total_tests}, pending={pending_tests}, passed={passed_tests}, failed={failed_tests}). Test selection yielded no executed tests."
            )

        # Check child process and test failure
        if jest_proc.returncode != 0 or failed_tests > 0:
            raise RunnerError(
                f"Test suite execution failed (exit code {jest_proc.returncode}): {failed_tests} failed, {passed_tests} passed."
            )

        return {
            "success": True,
            "total": total_tests,
            "executed": executed_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "assertions": assertions,
            "stdout": jest_proc.stdout,
            "stderr": jest_proc.stderr,
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Isolated test runner for nucleotide-count"
    )
    parser.add_argument(
        "config_path",
        nargs="?",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to config.json (default: exercises/practice/nucleotide-count/.meta/config.json)",
    )
    parser.add_argument(
        "--exercise-dir",
        default=str(DEFAULT_EXERCISE_DIR),
        help="Path to nucleotide-count exercise directory",
    )
    parser.add_argument(
        "--reference",
        default=None,
        help="Path to alternative reference implementation",
    )
    parser.add_argument(
        "--test-pattern",
        "-t",
        default=None,
        help="Pattern to filter tests (passed to jest -t)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON to stdout",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config_path).resolve()
    ex_dir = Path(args.exercise_dir).resolve()
    ref_path = Path(args.reference).resolve() if args.reference else None

    try:
        result = run_isolated_test(
            exercise_dir=ex_dir,
            config_path=cfg_path,
            reference_path=ref_path,
            test_pattern=args.test_pattern,
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("[SUCCESS] All tests executed and passed in isolated sandbox.")
            print(f"Executed: {result['executed']}, Passed: {result['passed']}, Failed: {result['failed']}")
            for title, status in result["assertions"].items():
                print(f"  - {title}: {status}")
        return 0
    except RunnerError as err:
        if args.json:
            print(json.dumps({"success": False, "error": str(err)}, indent=2))
        else:
            print(f"[ERROR] {err}", file=sys.stderr)
        return 1
    except Exception as exc:
        if args.json:
            print(json.dumps({"success": False, "error": f"Unexpected error: {exc}"}, indent=2))
        else:
            print(f"[UNEXPECTED ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
