#!/usr/bin/env python3
"""
Automated verification checker for Difference of Squares (GitHub Issue #14 — R47-T014).

This script verifies:
1. The refactored reference implementation (.meta/proof.ci.ts) passes all 9 canonical test cases.
2. The 3 named cases ('gets the square of sum', 'gets the sum of squares', 'gets the difference')
   across all tested ranges pass against the reference.
3. The learner stub (difference-of-squares.ts) remains untouched and unsolved.
4. Test execution results, expected/actual evidence, and tool versions are recorded in work/R47-T014/.
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


TEST_CASES_DATA = [
    {"group": "up to 5", "property": "squareOfSum", "input": 5, "expected": 225},
    {"group": "up to 5", "property": "sumOfSquares", "input": 5, "expected": 55},
    {"group": "up to 5", "property": "difference", "input": 5, "expected": 170},
    {"group": "up to 10", "property": "squareOfSum", "input": 10, "expected": 3025},
    {"group": "up to 10", "property": "sumOfSquares", "input": 10, "expected": 385},
    {"group": "up to 10", "property": "difference", "input": 10, "expected": 2640},
    {"group": "up to 100", "property": "squareOfSum", "input": 100, "expected": 25502500},
    {"group": "up to 100", "property": "sumOfSquares", "input": 100, "expected": 338350},
    {"group": "up to 100", "property": "difference", "input": 100, "expected": 25164150},
]


def get_tool_versions():
    """Collects Python and Node.js versions for evidence logging."""
    py_ver = sys.version.replace("\n", " ")
    try:
        node_ver = subprocess.check_output(
            ["node", "--version"], text=True
        ).strip()
    except Exception as e:
        node_ver = f"unknown ({e})"
    try:
        yarn_ver = subprocess.check_output(
            ["corepack", "yarn", "--version"], text=True
        ).strip()
    except Exception as e:
        yarn_ver = f"unknown ({e})"
    return {"python": py_ver, "node": node_ver, "yarn": yarn_ver}


def run_checks(repo_root: Path, simulate: str = None) -> bool:
    exercise_dir = repo_root / "exercises" / "practice" / "difference-of-squares"
    config_file = exercise_dir / ".meta" / "config.json"
    evidence_dir = repo_root / "work" / "R47-T014"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    if not config_file.exists():
        print(f"[FAIL] Missing config file: {config_file}", file=sys.stderr)
        return False

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    solution_rel = config["files"]["solution"][0]
    test_rel = config["files"]["test"][0]
    example_rel = config["files"]["example"][0]

    original_stub = exercise_dir / solution_rel
    reference_file = exercise_dir / example_rel

    print("==================================================")
    print("Difference of Squares Automated Checker (R47-T014)")
    print("==================================================")
    print(f"Exercise Directory:  {exercise_dir}")
    print(f"Solution File:       {solution_rel}")
    print(f"Test File:           {test_rel}")
    print(f"Reference File:      {example_rel}")

    # Safety check: Ensure original learner stub remains unsolved
    with open(original_stub, "r", encoding="utf-8") as f:
        stub_content = f.read()
    if "Remove this line and implement the function" not in stub_content:
        print("[FAIL] Original learner stub in exercises/ has been modified!", file=sys.stderr)
        return False
    print("[PASS] Original learner stub is verified untouched and unsolved.")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"Temporary Directory: {temp_path}")

        # Copy entire exercise directory including hidden files
        shutil.copytree(exercise_dir, temp_path, dirs_exist_ok=True)

        temp_solution = temp_path / solution_rel
        temp_test = temp_path / test_rel
        temp_reference = temp_path / example_rel

        # Replace learner solution with reference implementation in temp copy only
        if simulate == "failure":
            with open(temp_solution, "w", encoding="utf-8") as f:
                f.write("export class Squares { constructor() {} get squareOfSum() { return -1; } }\n")
            print("[SIMULATION] Injected failing solution in temp copy.")
        else:
            shutil.copy2(temp_reference, temp_solution)
            print("[PASS] Replaced learner solution with refactored reference in temporary copy.")

        # Update test file in temp copy: enable skipped tests and describe blocks
        with open(temp_test, "r", encoding="utf-8") as f:
            test_content = f.read()

        if simulate == "zero_tests":
            test_content = "import { describe } from '@jest/globals';\ndescribe('Empty', () => {});\n"
            print("[SIMULATION] Injected zero-test suite in temp copy.")
        else:
            test_content = test_content.replace("xit(", "it(")
            test_content = test_content.replace("xdescribe(", "describe(")
            print("[PASS] Enabled all skipped tests (xit -> it, xdescribe -> describe) in temporary test file.")

        with open(temp_test, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Set non-interactive test environment
        env = os.environ.copy()
        env["CI"] = "true"
        env["JEST_WATCH"] = "false"
        env["NODE_ENV"] = "test"

        print("Running 'corepack yarn install --no-immutable' in temporary copy...")
        install_res = subprocess.run(
            ["corepack", "yarn", "install", "--no-immutable"],
            cwd=temp_path,
            env=env,
            capture_output=True,
            text=True,
        )
        if install_res.returncode != 0:
            err = (install_res.stdout or "") + "\n" + (install_res.stderr or "")
            print(f"[FAIL] yarn install failed in temporary copy:\n{err}", file=sys.stderr)
            return False

        print("Running exercise test script: corepack yarn test...")
        test_res = subprocess.run(
            ["corepack", "yarn", "test"],
            cwd=temp_path,
            env=env,
            capture_output=True,
            text=True,
        )

        output = (test_res.stdout or "") + "\n" + (test_res.stderr or "")

        tests_line_match = re.search(
            r"Tests:\s+(?:(\d+)\s+failed,\s+)?(\d+)\s+passed,\s+(\d+)\s+total",
            output,
        )
        if tests_line_match:
            passed_count = int(tests_line_match.group(2))
            total_count = int(tests_line_match.group(3))
        else:
            passed_count, total_count = 0, 0

        tools = get_tool_versions()

        # Evidence logging
        evidence_content = f"""# Verification Evidence: Difference of Squares (Issue #14 — R47-T014)

## Environment
- **Python Version**: {tools['python']}
- **Node.js Version**: {tools['node']}
- **Yarn Version**: {tools['yarn']}
- **Simulation Mode**: {simulate if simulate else 'None (Standard Verification)'}

## Canonical Cases Evaluation

| Group | Property | Input (N) | Expected Output | Status |
|---|---|---|---|---|
"""
        for case in TEST_CASES_DATA:
            status = "PASSED" if test_res.returncode == 0 else "CHECK_OUTPUT"
            evidence_content += f"| {case['group']} | `{case['property']}` | {case['input']} | {case['expected']} | {status} |\n"

        evidence_content += f"""
## Test Execution Results
- **Child Process Return Code**: {test_res.returncode}
- **Tests Passed**: {passed_count}
- **Total Tests**: {total_count}
- **Zero Tests Detected**: {'YES' if total_count == 0 else 'NO'}

## Output Details
```text
{output.strip()}
```
"""
        evidence_file = evidence_dir / (
            f"evidence_{simulate}.md" if simulate else "evidence.md"
        )
        with open(evidence_file, "w", encoding="utf-8") as f:
            f.write(evidence_content)
        print(f"[EVIDENCE] Written to {evidence_file}")

        # Assertions
        if test_res.returncode != 0:
            print(f"[FAIL] Child test command exited with code: {test_res.returncode}", file=sys.stderr)
            return False

        if total_count == 0:
            print("[FAIL] Zero tests executed!", file=sys.stderr)
            return False

        if passed_count != 9 or total_count != 9:
            print(f"[FAIL] Expected 9 passed tests out of 9 total, got {passed_count}/{total_count}", file=sys.stderr)
            return False

        print(f"[PASS] All {passed_count} tests executed and passed successfully!")
        print("==================================================")
        print("RESULT: SUCCESS (All 9 canonical cases verified)")
        print("==================================================")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Verify difference-of-squares refactored reference implementation."
    )
    parser.add_argument(
        "--simulate-failure",
        action="store_true",
        help="Simulate a failing solution to verify error detection.",
    )
    parser.add_argument(
        "--simulate-zero-tests",
        action="store_true",
        help="Simulate an empty test suite to verify zero-test detection.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    simulate = None
    if args.simulate_failure:
        simulate = "failure"
    elif args.simulate_zero_tests:
        simulate = "zero_tests"

    success = run_checks(repo_root, simulate=simulate)
    if not success:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
