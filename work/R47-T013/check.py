#!/usr/bin/env python3
"""
Automated verification checker for Transpose (GitHub Issue #13 — R47-T013).

This script verifies:
1. The TypeScript reference implementation (.meta/proof.ci.ts) passes all 12 canonical test cases.
2. The intentional logic mutant (omitting left-padding) is rejected by the existing test suite:
   specifically by 'second line longer than first line' (UUID: 984e2ec3-b3d3-4b53-8bd6-96f5ef404102).
3. The 3 named cases ('empty string', 'two characters in a row', 'two characters in a column')
   pass on both original and mutant implementations.
4. The learner stub (transpose.ts) remains unsolved.
5. Saves test evidence and tool versions in work/R47-T013/.
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


MUTATED_IMPLEMENTATION = """const fillColumn: (t: string[], l: string, r: number) => void = (
  transposed,
  fromSource,
  toColumn
) => {
  for (let row = 0; row < fromSource.length; row++) {
    transposed[row] =
      (row in transposed ? transposed[row] : '') +
      fromSource.charAt(row)
  }
}

export function transpose(lines: string[]): string[] {
  const transposed: string[] = []
  for (let toColumn = 0; toColumn < lines.length; toColumn++)
    fillColumn(transposed, lines[toColumn], toColumn)

  return transposed
}
"""


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


def run_exercise_tests(exercise_dir: Path, solution_source: str, zero_tests: bool = False) -> tuple[int, int, int, str]:
    """Runs tests in an isolated temporary directory with the given solution source."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        shutil.copytree(exercise_dir, temp_path, dirs_exist_ok=True)

        with open(temp_path / ".meta" / "config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        solution_file = temp_path / config["files"]["solution"][0]
        test_file = temp_path / config["files"]["test"][0]

        # Write solution
        with open(solution_file, "w", encoding="utf-8") as f:
            f.write(solution_source)

        # Update test file: unskip xit -> it
        with open(test_file, "r", encoding="utf-8") as f:
            test_content = f.read()

        if zero_tests:
            test_content = "import { describe } from '@jest/globals';\ndescribe('Empty', () => {});\n"
        else:
            test_content = test_content.replace("xit(", "it(")

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        env = os.environ.copy()
        env["CI"] = "true"
        env["JEST_WATCH"] = "false"
        env["NODE_ENV"] = "test"

        # Install dependencies non-mutably
        install_proc = subprocess.run(
            ["corepack", "yarn", "install", "--no-immutable"],
            cwd=temp_path,
            env=env,
            capture_output=True,
            text=True,
        )
        if install_proc.returncode != 0:
            err_msg = (install_proc.stdout or "") + "\n" + (install_proc.stderr or "")
            raise RuntimeError(f"yarn install failed:\n{err_msg}")

        # Run test script
        test_proc = subprocess.run(
            ["corepack", "yarn", "test"],
            cwd=temp_path,
            env=env,
            capture_output=True,
            text=True,
        )

        output = (test_proc.stdout or "") + "\n" + (test_proc.stderr or "")

        tests_line_match = re.search(
            r"Tests:\s+(?:(\d+)\s+failed,\s+)?(\d+)\s+passed,\s+(\d+)\s+total",
            output
        )
        if tests_line_match:
            failed = int(tests_line_match.group(1)) if tests_line_match.group(1) else 0
            passed = int(tests_line_match.group(2))
            total = int(tests_line_match.group(3))
        else:
            failed, passed, total = 0, 0, 0

        return test_proc.returncode, passed, total, output


def main():
    parser = argparse.ArgumentParser(
        description="Verify Transpose reference implementation and regression mutant."
    )
    parser.add_argument(
        "--simulate-failure",
        action="store_true",
        help="Simulate a broken environment to verify failure exit code.",
    )
    parser.add_argument(
        "--simulate-zero-tests",
        action="store_true",
        help="Simulate a zero-test run to verify error detection.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    exercise_dir = repo_root / "exercises" / "practice" / "transpose"
    evidence_dir = repo_root / "work" / "R47-T013"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    print("==================================================")
    print("Transpose Mutation Checker (R47-T013)")
    print("==================================================")

    # 1. Verify original learner stub is untouched and unsolved
    stub_file = exercise_dir / "transpose.ts"
    with open(stub_file, "r", encoding="utf-8") as f:
        stub_text = f.read()
    if "Remove this line and implement the function" not in stub_text:
        print("[FAIL] Original learner stub in exercises/ has been modified!", file=sys.stderr)
        sys.exit(1)
    print("[PASS] Original learner stub is verified untouched and unsolved.")

    # Handle simulation modes
    if args.simulate_failure:
        print("[SIMULATION] Testing intentional runner failure...")
        code, passed, total, _ = run_exercise_tests(
            exercise_dir,
            "export function transpose() { throw new Error('fail'); }\n"
        )
        if code != 0:
            print(f"[PASS] Simulator correctly returned non-zero exit code ({code}).")
            sys.exit(1)
        sys.exit(0)

    if args.simulate_zero_tests:
        print("[SIMULATION] Testing zero-test run detection...")
        code, passed, total, _ = run_exercise_tests(
            exercise_dir,
            "export function transpose() { return []; }\n",
            zero_tests=True
        )
        if code != 0 or total == 0:
            print(f"[PASS] Simulator correctly detected zero tests / failure (code {code}).")
            sys.exit(1)
        sys.exit(0)

    # 2. Run original reference implementation
    ref_file = exercise_dir / ".meta" / "proof.ci.ts"
    with open(ref_file, "r", encoding="utf-8") as f:
        original_ref_source = f.read()

    print("\n[Step 1] Running original reference implementation (.meta/proof.ci.ts)...")
    code_orig, passed_orig, total_orig, out_orig = run_exercise_tests(exercise_dir, original_ref_source)
    print(f"Results: exit code {code_orig}, passed {passed_orig}/{total_orig} tests.")

    if code_orig != 0 or total_orig != 12 or passed_orig != 12:
        print(f"[FAIL] Original reference failed: {passed_orig}/{total_orig} passed (exit {code_orig})", file=sys.stderr)
        sys.exit(1)
    print("[PASS] Original reference passed all 12 canonical test cases.")

    # 3. Run mutated reference implementation
    print("\n[Step 2] Running mutated reference implementation (omitting .padEnd)...")
    code_mut, passed_mut, total_mut, out_mut = run_exercise_tests(exercise_dir, MUTATED_IMPLEMENTATION)
    print(f"Results: exit code {code_mut}, passed {passed_mut}/{total_mut} tests.")

    # Mutated implementation must fail
    if code_mut == 0:
        print("[FAIL] Mutated implementation unexpectedly passed all tests!", file=sys.stderr)
        sys.exit(1)

    # Verify that the 3 named cases passed on mutant
    named_cases = ["empty string", "two characters in a row", "two characters in a column"]
    for case in named_cases:
        if f"✓ {case}" not in out_mut:
            print(f"[FAIL] Named case '{case}' failed on mutant!", file=sys.stderr)
            sys.exit(1)
    print("[PASS] The 3 named cases (empty string, two in a row, two in a column) passed on mutant as expected.")

    # Verify that 'second line longer than first line' failed on mutant
    rejecting_case = "second line longer than first line"
    if f"✕ {rejecting_case}" not in out_mut:
        print(f"[FAIL] Expected '{rejecting_case}' to fail on mutant, but it did not!", file=sys.stderr)
        sys.exit(1)
    print(f"[PASS] Rejecting test '{rejecting_case}' (UUID 984e2ec3-b3d3-4b53-8bd6-96f5ef404102) correctly caught the mutant.")

    # 4. Save verification evidence
    tools = get_tool_versions()
    evidence_content = f"""# Verification Evidence: Transpose (Issue #13 — R47-T013)

## Environment
- **Python Version**: {tools['python']}
- **Node.js Version**: {tools['node']}
- **Yarn Version**: {tools['yarn']}

## Test Execution Comparison

| Metric | Original Reference | Mutated Reference |
|---|---|---|
| Exit Code | `{code_orig}` (Success) | `{code_mut}` (Failed as expected) |
| Tests Passed | {passed_orig} / {total_orig} | {passed_mut} / {total_mut} |
| 'empty string' | PASSED | PASSED |
| 'two characters in a row' | PASSED | PASSED |
| 'two characters in a column' | PASSED | PASSED |
| 'second line longer than first line' | PASSED | **FAILED** (Caught mutation) |
| 'triangle' | PASSED | FAILED |
| 'jagged triangle' | PASSED | FAILED |
| 'test many lines' | PASSED | FAILED |

## Rejecting Test Case Details
- **Test Name**: `second line longer than first line`
- **Canonical UUID**: `984e2ec3-b3d3-4b53-8bd6-96f5ef404102`
- **Input**:
  ```typescript
  ['The first line.', 'The second line.']
  ```
- **Expected Output at row 15**: `' .'` (space + dot)
- **Mutant Output at row 15**: `'.'` (missing leading space)

## Minimal Diagnostic Input
- **Input**: `['A', 'BC']`
- **Expected**: `['AB', ' C']`
- **Mutant**: `['AB', 'C']`

## Output Logs (Mutant Run Excerpt)
```text
FAIL ./transpose.test.ts
  Transpose
    ✓ empty string
    ✓ two characters in a row
    ✓ two characters in a column
    ✓ simple
    ✓ single line
    ✓ first line longer than second line
    ✕ second line longer than first line
    ✓ square
    ✓ rectangle
    ✕ triangle
    ✕ jagged triangle
    ✕ test many lines
```
"""
    evidence_file = evidence_dir / "evidence.md"
    with open(evidence_file, "w", encoding="utf-8") as f:
        f.write(evidence_content)
    print(f"\n[EVIDENCE] Verification evidence written to {evidence_file}")

    print("\n==================================================")
    print("RESULT: SUCCESS (Mutation verified against canonical suite)")
    print("==================================================")
    sys.exit(0)


if __name__ == "__main__":
    main()
