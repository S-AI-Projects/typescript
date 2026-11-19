#!/usr/bin/env python3
"""
Automated verification checker for Game of Life (GitHub Issue #12 — R47-T012).

This script verifies that the TypeScript reference implementation (.meta/proof.ci.ts)
passes all eight canonical test cases for exercises/practice/game-of-life.

Behavior:
1. Reads .meta/config.json to find solution, test, and reference implementation files.
2. Asserts original learner stub remains untouched and unsolved.
3. Creates an isolated temporary directory.
4. Copies the entire exercise (including hidden dotfiles) into the temporary directory.
5. Replaces the learner solution stub with .meta/proof.ci.ts in the copy only.
6. Enables all skipped tests (xit -> it) in the copy only.
7. Runs the package.json test script via subprocess in non-interactive mode.
8. Validates that tests pass, exit code is 0, and executed test count is exactly 8.
9. Saves verification evidence in work/R47-T012/.
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
        "name": "empty matrix",
        "uuid": "ae86ea7d-bd07-4357-90b3-ac7d256bd5c5",
        "input": "[]",
        "expected": "[]",
    },
    {
        "name": "live cells with zero live neighbors die",
        "uuid": "4ea5ccb7-7b73-4281-954a-bed1b0f139a5",
        "input": "[[0, 0, 0], [0, 1, 0], [0, 0, 0]]",
        "expected": "[[0, 0, 0], [0, 0, 0], [0, 0, 0]]",
    },
    {
        "name": "live cells with only one live neighbor die",
        "uuid": "df245adc-14ff-4f9c-b2ae-f465ef5321b2",
        "input": "[[0, 0, 0], [0, 1, 0], [0, 1, 0]]",
        "expected": "[[0, 0, 0], [0, 0, 0], [0, 0, 0]]",
    },
    {
        "name": "live cells with two live neighbors stay alive",
        "uuid": "2a713b56-283c-48c8-adae-1d21306c80ae",
        "input": "[[1, 0, 1], [1, 0, 1], [1, 0, 1]]",
        "expected": "[[0, 0, 0], [1, 0, 1], [0, 0, 0]]",
    },
    {
        "name": "live cells with three live neighbors stay alive",
        "uuid": "86d5c5a5-ab7b-41a1-8907-c9b3fc5e9dae",
        "input": "[[0, 1, 0], [1, 0, 0], [1, 1, 0]]",
        "expected": "[[0, 0, 0], [1, 0, 0], [1, 1, 0]]",
    },
    {
        "name": "dead cells with three live neighbors become alive",
        "uuid": "015f60ac-39d8-4c6c-8328-57f334fc9f89",
        "input": "[[1, 1, 0], [0, 0, 0], [1, 0, 0]]",
        "expected": "[[0, 0, 0], [1, 1, 0], [0, 0, 0]]",
    },
    {
        "name": "live cells with four or more neighbors die",
        "uuid": "2ee69c00-9d41-4b8b-89da-5832e735ccf1",
        "input": "[[1, 1, 1], [1, 1, 1], [1, 1, 1]]",
        "expected": "[[1, 0, 1], [0, 0, 0], [1, 0, 1]]",
    },
    {
        "name": "bigger matrix",
        "uuid": "a79b42be-ed6c-4e27-9206-43da08697ef6",
        "input": "8x8 matrix",
        "expected": "8x8 next generation matrix",
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
    exercise_dir = repo_root / "exercises" / "practice" / "game-of-life"
    config_file = exercise_dir / ".meta" / "config.json"
    evidence_dir = repo_root / "work" / "R47-T012"
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
    print("Game of Life Automated Checker (R47-T012)")
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
                f.write(
                    "export class GameOfLife {\n"
                    "  constructor(private m: number[][]) {}\n"
                    "  tick(): void {}\n"
                    "  state(): number[][] { return [[99]]; }\n"
                    "}\n"
                )
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
            alt_match = re.search(r"Tests:\s+(\d+)\s+total", output)
            if alt_match:
                total_count = int(alt_match.group(1))

        tools = get_tool_versions()

        # Verification evidence document
        evidence_content = f"""# Verification Evidence: Game of Life (Issue #12 — R47-T012)

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
            evidence_content += f"| {case['name']} | `{case['uuid']}` | `{case['input']}` | `{case['expected']}` | {status_str} |\n"

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

        if passed_count != 8 or total_count != 8:
            print(
                f"[FAIL] Expected 8 passed tests out of 8 total, but got {passed_count}/{total_count}.",
                file=sys.stderr,
            )
            return False

        print(
            f"[PASS] All {passed_count} tests executed and passed successfully!"
        )
        print("==================================================")
        print("RESULT: SUCCESS (All 8 canonical cases verified)")
        print("==================================================")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Verify Game of Life reference implementation against all canonical cases."
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

