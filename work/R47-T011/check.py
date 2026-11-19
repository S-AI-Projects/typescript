#!/usr/bin/env python3
"""
Automated verification checker for nth-prime (GitHub Issue #11 — R47-T011).

This script verifies that the TypeScript reference implementation (.meta/proof.ci.ts)
passes all five canonical test cases for exercises/practice/nth-prime.

Behavior:
1. Reads .meta/config.json to find solution, test, and reference implementation files.
2. Creates an isolated temporary directory.
3. Copies the entire exercise (including hidden files) into the temporary directory.
4. Replaces the learner solution stub with .meta/proof.ci.ts in the copy only.
5. Enables all skipped tests (xit -> it) in the copy only.
6. Runs the package.json test script via subprocess in non-interactive mode.
7. Validates that tests pass, exit code is 0, and executed test count is exactly 5 (> 0).
8. Saves verification evidence in work/R47-T011/.
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


CANONICAL_CASES = [
    {
        "name": "first",
        "description": "first prime",
        "uuid": "75c65189-8aef-471a-81de-0a90c728160c",
        "input": 1,
        "expected": "2",
    },
    {
        "name": "second",
        "description": "second prime",
        "uuid": "2c38804c-295f-4701-b728-56dea34fd1a0",
        "input": 2,
        "expected": "3",
    },
    {
        "name": "sixth",
        "description": "sixth prime",
        "uuid": "56692534-781e-4e8c-b1f9-3e82c1640259",
        "input": 6,
        "expected": "13",
    },
    {
        "name": "big prime",
        "description": "big prime",
        "uuid": "fce1e979-0edb-412d-93aa-2c744e8f50ff",
        "input": 10001,
        "expected": "104743",
    },
    {
        "name": "weird case",
        "description": "there is no zeroth prime",
        "uuid": "bd0a9eae-6df7-485b-a144-80e13c7d55b2",
        "input": 0,
        "expected": "throws 'Prime is not possible'",
    },
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
    exercise_dir = repo_root / "exercises" / "practice" / "nth-prime"
    config_file = exercise_dir / ".meta" / "config.json"
    evidence_dir = repo_root / "work" / "R47-T011"
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
    original_test = exercise_dir / test_rel

    print("==================================================")
    print("nth-prime Automated Checker (R47-T011)")
    print("==================================================")
    print(f"Exercise Directory:  {exercise_dir}")
    print(f"Solution File:       {solution_rel}")
    print(f"Test File:           {test_rel}")
    print(f"Reference File:      {example_rel}")

    # Safety check: Ensure original learner stub remains unsolved
    with open(original_stub, "r", encoding="utf-8") as f:
        stub_content = f.read()
    if "Remove this line and implement the function" not in stub_content:
        print(
            "[FAIL] Original learner stub in exercises/ has been modified!",
            file=sys.stderr,
        )
        return False
    print("[PASS] Original learner stub is verified untouched and unsolved.")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"Temporary Directory: {temp_path}")

        # Copy entire exercise directory including hidden dotfiles
        shutil.copytree(exercise_dir, temp_path, dirs_exist_ok=True)

        temp_solution = temp_path / solution_rel
        temp_test = temp_path / test_rel
        temp_reference = temp_path / example_rel

        # Replace learner solution with reference implementation in temp copy only
        if simulate == "failure":
            # Simulate a broken implementation that fails tests
            with open(temp_solution, "w", encoding="utf-8") as f:
                f.write("export function nth(n: number): number { return 0; }\n")
            print("[SIMULATION] Injected failing solution in temp copy.")
        else:
            shutil.copy2(temp_reference, temp_solution)
            print("[PASS] Replaced learner solution with reference in temporary copy.")

        # Update test file in temp copy: enable skipped tests
        with open(temp_test, "r", encoding="utf-8") as f:
            test_content = f.read()

        if simulate == "zero_tests":
            # Simulate empty test suite
            test_content = "import { describe } from '@jest/globals';\ndescribe('Empty', () => {});\n"
            with open(temp_test, "w", encoding="utf-8") as f:
                f.write(test_content)
            print("[SIMULATION] Injected zero-test suite in temp copy.")
        else:
            # Unskip xit -> it
            unskipped_content = test_content.replace("xit(", "it(")
            with open(temp_test, "w", encoding="utf-8") as f:
                f.write(unskipped_content)
            print("[PASS] Enabled all skipped tests (xit -> it) in temporary test file.")

        # Non-interactive test environment (disable Jest watch mode)
        env = os.environ.copy()
        env["CI"] = "true"
        env["JEST_WATCH"] = "false"
        env["NODE_ENV"] = "test"

        # Ensure dependencies in temporary directory
        # Pass --no-immutable because exercise yarn.lock files in this track are empty stubs
        print("Running 'corepack yarn install --no-immutable' in temporary copy...")
        install_res = subprocess.run(
            ["corepack", "yarn", "install", "--no-immutable"],
            cwd=temp_path,
            env=env,
            capture_output=True,
            text=True,
        )
        if install_res.returncode != 0:
            install_err = (install_res.stdout or "") + "\n" + (install_res.stderr or "")
            print(
                f"[FAIL] 'yarn install' failed in temporary copy (exit {install_res.returncode}):\n"
                f"{install_err.strip()}",
                file=sys.stderr,
            )
            return False

        # Read test command from package.json
        with open(temp_path / "package.json", "r", encoding="utf-8") as f:
            pkg = json.load(f)
        test_script = pkg.get("scripts", {}).get("test", "corepack yarn test")
        print(f"Running exercise test script: {test_script}")

        test_res = subprocess.run(
            ["corepack", "yarn", "test"],
            cwd=temp_path,
            env=env,
            capture_output=True,
            text=True,
        )

        output = (test_res.stdout or "") + "\n" + (test_res.stderr or "")

        # Extract test results
        tests_match = re.search(r"Tests:\s+(\d+)\s+passed,\s+(\d+)\s+total", output)
        passed_count = int(tests_match.group(1)) if tests_match else 0
        total_count = int(tests_match.group(2)) if tests_match else 0

        if not tests_match:
            # Check for alternative total test count
            alt_match = re.search(r"Tests:\s+(\d+)\s+total", output)
            if alt_match:
                total_count = int(alt_match.group(1))

        tools = get_tool_versions()

        # Verification evidence document
        evidence_content = f"""# Verification Evidence: nth-prime (Issue #11 — R47-T011)

## Environment
- **Python Version**: {tools['python']}
- **Node.js Version**: {tools['node']}
- **Yarn Version**: {tools['yarn']}
- **Simulation Mode**: {simulate if simulate else 'None (Standard Verification)'}

## Canonical Cases Evaluation

| Test Name | Canonical UUID | Input | Expected Output | Status |
|---|---|---|---|---|
"""
        for case in CANONICAL_CASES:
            case_passed = f"✓ {case['name']}" in output
            status_str = "PASSED" if case_passed else "FAILED"
            evidence_content += f"| {case['name']} | `{case['uuid']}` | {case['input']} | {case['expected']} | {status_str} |\n"

        evidence_content += f"""
## Test Execution Results
- **Child Process Return Code**: {test_res.returncode}
- **Tests Passed**: {passed_count}
- **Total Tests**: {total_count}
- **Zero Tests Detected**: {'YES' if total_count == 0 else 'NO'}

## Command Output Details
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
            print(
                f"[FAIL] Child test command exited with non-zero code: {test_res.returncode}",
                file=sys.stderr,
            )
            return False

        if total_count == 0:
            print("[FAIL] Zero tests executed!", file=sys.stderr)
            return False

        if passed_count != 5 or total_count != 5:
            print(
                f"[FAIL] Expected 5 passed tests out of 5 total, but got {passed_count}/{total_count}.",
                file=sys.stderr,
            )
            return False

        print(
            f"[PASS] All {passed_count} tests executed and passed successfully!"
        )
        print("==================================================")
        print("RESULT: SUCCESS (All 5 canonical cases verified)")
        print("==================================================")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Verify nth-prime reference implementation against all canonical cases."
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
