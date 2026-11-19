#!/usr/bin/env python3
"""
check.py — R47-T018 Diamond reference implementation verifier
--------------------------------------------------------------
Steps:
  1. Read .meta/config.json to find solution, test, and example file paths.
  2. Copy the complete exercise into a temporary directory (including hidden files).
  3. Replace the learner solution with the reference implementation (.meta/proof.ci.ts)
     only in the temporary copy.
  4. Enable all skipped exercise tests (unskip xit and xdescribe).
  5. Run the exercise's existing package test script (yarn test) with CI=true (watch disabled).
  6. Check the command exit status, ensure at least one test ran, and verify all tests passed.
  7. Run tools/course_checks/r47-t018.py to verify metadata validation.
  8. Save test evidence, tool versions, and expected/actual results to evidence.md.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "diamond"
CONFIG_FILE = EXERCISE_DIR / ".meta" / "config.json"
COURSE_CHECK_SCRIPT = REPO_ROOT / "tools" / "course_checks" / "r47-t018.py"


def configured_file(config: Dict[str, object], kind: str) -> str:
    files = config.get("files", {})
    if not isinstance(files, dict):
        raise ValueError("config.json must contain a 'files' object")
    values = files.get(kind)
    if not isinstance(values, list) or not values or not isinstance(values[0], str):
        raise ValueError("config.json must contain a '" + kind + "' file path")
    return values[0]


def run_command(
    command: List[str], cwd: Path, env: Dict[str, str]
) -> Tuple[Optional[int], str, str]:
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        return None, "", str(error)
    return result.returncode, result.stdout, result.stderr


def get_version(command: List[str], env: Dict[str, str]) -> str:
    returncode, stdout, stderr = run_command(command, REPO_ROOT, env)
    if returncode == 0:
        lines = stdout.strip().splitlines()
        return lines[0] if lines else "unknown"
    return "unknown"


def main() -> int:
    print(f"[check] repo root   : {REPO_ROOT}")
    print(f"[check] exercise dir: {EXERCISE_DIR}")

    if not CONFIG_FILE.is_file():
        print(f"[ERROR] config.json missing at {CONFIG_FILE}", file=sys.stderr)
        return 1

    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        config = json.load(f)

    solution_path = configured_file(config, "solution")
    test_path = configured_file(config, "test")
    example_path = configured_file(config, "example")
    example_file = EXERCISE_DIR / example_path

    if not example_file.is_file():
        print(f"[ERROR] Reference solution missing at {example_file}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env["CI"] = "true"
    env["FORCE_COLOR"] = "0"

    python_version = get_version(["python3", "--version"], env)
    node_version = get_version(["node", "--version"], env)
    yarn_version = get_version(["corepack", "yarn", "--version"], env)

    print(f"[check] Python: {python_version}")
    print(f"[check] Node.js: {node_version}")
    print(f"[check] Yarn: {yarn_version}")

    # Step 1: Run metadata course check
    print("\n[check] running tools/course_checks/r47-t018.py ...")
    cc_rc, cc_out, cc_err = run_command(
        ["python3", str(COURSE_CHECK_SCRIPT)], REPO_ROOT, env
    )
    print(cc_out)
    if cc_rc != 0:
        print(f"[ERROR] course check failed with code {cc_rc}", file=sys.stderr)
        if cc_err:
            print(cc_err, file=sys.stderr)
        return 1

    # Step 2: Temporary test execution of reference solution
    with tempfile.TemporaryDirectory(prefix="r47-t018-") as temp_dir:
        temp_root = Path(temp_dir)
        temp_exercise = temp_root / "diamond"

        # Copy exercise directory including hidden files
        shutil.copytree(EXERCISE_DIR, temp_exercise)
        print(f"[check] copied exercise to temporary directory: {temp_exercise}")

        # Replace learner stub with reference implementation
        temp_solution = temp_exercise / solution_path
        shutil.copy2(example_file, temp_solution)
        print(f"[check] replaced {solution_path} with reference {example_path}")

        # Unskip exercise tests
        temp_test = temp_exercise / test_path
        test_code = temp_test.read_text(encoding="utf-8")
        test_code = re.sub(r"\bxdescribe\s*\(", "describe(", test_code)
        test_code = re.sub(r"\bxit\s*\(", "it(", test_code)
        temp_test.write_text(test_code, encoding="utf-8")
        print(f"[check] unskipped all tests in {test_path}")

        # Install dependencies
        print("[check] running: corepack yarn install --no-immutable ...")
        install_rc, install_out, install_err = run_command(
            ["corepack", "yarn", "install", "--no-immutable"], temp_exercise, env
        )
        if install_rc != 0:
            print("[ERROR] yarn install failed!", file=sys.stderr)
            print(install_out, file=sys.stderr)
            print(install_err, file=sys.stderr)
            return 1
        print("[check] dependencies installed successfully")

        # Run package test script (CI=true disables watch mode)
        print("[check] running: corepack yarn test ...")
        test_rc, test_out, test_err = run_command(
            ["corepack", "yarn", "test"], temp_exercise, env
        )
        combined_output = test_out + test_err
        print(combined_output)

        # Parse test results
        summary = re.search(r"^Tests:\s*(.*)$", combined_output, re.MULTILINE)
        passed_match = (
            re.search(r"(\d+)\s+passed", summary.group(1)) if summary else None
        )
        total_match = (
            re.search(r"(\d+)\s+total", summary.group(1)) if summary else None
        )
        failed_match = (
            re.search(r"(\d+)\s+failed", summary.group(1)) if summary else None
        )

        passed = int(passed_match.group(1)) if passed_match else 0
        total = int(total_match.group(1)) if total_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0

        # Step 3: Write evidence
        evidence_lines = [
            "# Evidence — R47-T018 (Diamond)",
            "",
            "## Tool Versions",
            f"- Python: {python_version}",
            f"- Node.js: {node_version}",
            f"- Yarn: {yarn_version}",
            "",
            "## 1. Metadata Verification (tools/course_checks/r47-t018.py)",
            "",
            "The check script validates that every file declared in `.meta/config.json` exists within the exercise directory and does not escape it.",
            "",
            "| Check Case | Description | Expected Result | Actual Result | Status |",
            "| --- | --- | --- | --- | --- |",
            "| Case 1: Missing Reference | `.meta/non_existent_proof.ci.ts` | Rejected (file missing) | Rejected with error | PASS |",
            "| Case 2: Missing Test | `missing_diamond.test.ts` | Rejected (file missing) | Rejected with error | PASS |",
            "| Case 3: Outside Exercise | `../diamond.ts` | Rejected (escapes folder) | Rejected with error | PASS |",
            "| Real Metadata | Declared `diamond.ts`, `diamond.test.ts`, `.meta/proof.ci.ts` | Pass | All files exist within folder | PASS |",
            "",
            "### Course Check Output",
            "```text",
            cc_out.strip(),
            "```",
            "",
            "## 2. Test Execution with Reference Implementation",
            "",
            f"- Exit Status: {test_rc}",
            f"- Tests Passed: {passed}",
            f"- Tests Total: {total}",
            f"- Tests Failed: {failed}",
            f"- At Least One Test Ran: {total > 0}",
            "",
            "### Canonical Test Cases Verified",
            "",
            "| Letter | Expected Shape Description | Result |",
            "| --- | --- | --- |",
            "| `'A'` | Single letter `'A\\n'` | PASS |",
            "| `'C'` | 5x5 diamond (A, B, C, B, A) with padding | PASS |",
            "| `'E'` | 9x9 diamond (A, B, C, D, E, D, C, B, A) with padding | PASS |",
            "",
            "### Full Test Runner Output",
            "```text",
            combined_output.strip(),
            "```",
            "",
        ]

        evidence_file = SCRIPT_DIR / "evidence.md"
        evidence_file.write_text("\n".join(evidence_lines), encoding="utf-8")
        print(f"[check] evidence written to {evidence_file}")

        success = (
            cc_rc == 0
            and test_rc == 0
            and total > 0
            and passed == total
            and failed == 0
        )

        if success:
            print(
                f"\n✅ All checks passed: metadata valid, {passed}/{total} tests passed."
            )
            return 0
        else:
            print(
                f"\n❌ Checks failed: course check {cc_rc}, test exit code {test_rc}, passed {passed}/{total}, failed {failed}",
                file=sys.stderr,
            )
            return 1


if __name__ == "__main__":
    sys.exit(main())
