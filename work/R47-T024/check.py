#!/usr/bin/env python3
"""
work/R47-T024/check.py: Automated verification checker for saddle-points refactoring.

Requirements:
1. Use Python 3 subprocess and tempfile.
2. Resolve paths from exercises/practice/saddle-points/.meta/config.json.
3. Copy the entire exercise, including hidden files.
4. Substitute the reference implementation only inside the temporary copy.
5. Run the exercise package.json test script with watch mode disabled.
6. Ensure all exercise cases are enabled (xit( -> it().
7. Run both original (un-refactored) and refactored reference implementations against identical enabled tests.
8. Verify all 3 named cases and every other enabled case.
9. Fail on zero executed tests, failed assertions, or non-zero child exit codes.
10. Save test inputs, before/after outputs, tool versions, and verification results in work/R47-T024/.
11. Never rewrite the original working tree.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

# Paths
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EX = REPO / "exercises/practice/saddle-points"
META_CFG = EX / ".meta/config.json"
TOML_PATH = EX / ".meta/tests.toml"

NAMED_CASES = [
    "Can identify single saddle point",
    "Can identify that empty matrix has no saddle points",
    "Can identify lack of saddle points when there are none",
]

EXPECTED_TOTAL_TESTS = 9
failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    label = "PASS  " if ok else "FAIL  "
    print(label + msg)
    if not ok:
        failures.append(msg)


def check_prerequisites() -> None:
    if sys.version_info < (3, 11):
        print("ERROR: Python 3.11+ required for tomllib.", file=sys.stderr)
        sys.exit(1)
    for binary in ["node", "corepack"]:
        if not shutil.which(binary):
            print(f"ERROR: Missing prerequisite '{binary}' in PATH.", file=sys.stderr)
            sys.exit(1)
    if not EX.is_dir():
        print(f"ERROR: Exercise directory not found: {EX}", file=sys.stderr)
        sys.exit(1)
    for f in [META_CFG, TOML_PATH, EX / "package.json"]:
        if not f.is_file():
            print(f"ERROR: Required file missing: {f}", file=sys.stderr)
            sys.exit(1)


def run_cmd(cmd: list[str], cwd: Path, log_name: str | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if log_name:
        log = HERE / log_name
        log.write_text(
            f"$ {' '.join(cmd)}\nexit={p.returncode}\n"
            f"--- stdout ---\n{p.stdout}\n"
            f"--- stderr ---\n{p.stderr}\n"
        )
    return p


def collect_tool_versions() -> dict:
    v = {"python": sys.version.split()[0]}
    p_node = run_cmd(["node", "-v"], EX, "version-node.log")
    v["node"] = p_node.stdout.strip()
    p_yarn = run_cmd(["corepack", "yarn", "-v"], EX, "version-yarn.log")
    v["yarn"] = p_yarn.stdout.strip()
    return v


# Original reference implementation prior to refactoring (from git HEAD)
ORIGINAL_REFERENCE_CODE = """export function saddlePoints(
  matrix: number[][]
): Array<{ row: number; column: number }> {
  const maximumRowValues: number[] = []
  const minimumColumnValues: number[] = []

  for (let i = 0; i <= matrix.length - 1; i++) {
    let maximumRowValue = Number.MIN_VALUE
    for (let j = 0; j < matrix[0].length; j++) {
      maximumRowValue = Math.max(maximumRowValue, matrix[i][j])
    }
    maximumRowValues.push(maximumRowValue)
  }

  for (let i = 0; i <= matrix[0].length - 1; i++) {
    let minimumColumnValue = Number.MAX_VALUE
    for (let j = 0; j <= matrix.length - 1; j++) {
      minimumColumnValue = Math.min(minimumColumnValue, matrix[j][i])
    }
    minimumColumnValues.push(minimumColumnValue)
  }

  const resultPoints: Array<{ row: number; column: number }> = []
  for (let i = 0; i < maximumRowValues.length; i++) {
    for (let j = 0; j < minimumColumnValues.length; j++) {
      if (maximumRowValues[i] === minimumColumnValues[j]) {
        resultPoints.push({ row: i + 1, column: j + 1 })
      }
    }
  }

  return resultPoints
}
"""


def main() -> None:
    check_prerequisites()

    # 1. Tool versions
    versions = collect_tool_versions()
    (HERE / "tool-versions.json").write_text(json.dumps(versions, indent=2) + "\n")
    print("Tool versions:", versions)

    # 2. Resolve paths from config.json
    cfg = json.loads(META_CFG.read_text())["files"]
    solution_rel = cfg["solution"][0]
    test_rel = cfg["test"][0]
    example_rel = cfg["example"][0]
    print(f"solution={solution_rel} test={test_rel} example={example_rel}")

    # Check tests.toml
    toml_data = tomllib.loads(TOML_PATH.read_text())
    check(len(toml_data) == EXPECTED_TOTAL_TESTS,
          f"tests.toml has {EXPECTED_TOTAL_TESTS} canonical cases (found {len(toml_data)})")

    # Verify learner stub is unsolved in working tree
    stub_path = EX / solution_rel
    check("Remove this line and implement the function" in stub_path.read_text(),
          "learner stub is unsolved in working tree")

    for rel in (solution_rel, test_rel):
        diff = run_cmd(["git", "diff", "--quiet", "HEAD", "--", str((EX / rel).relative_to(REPO))], REPO)
        check(diff.returncode == 0, f"{rel} unchanged in working tree")

    # Hash working tree test file to ensure it is untouched
    wt_test_file = EX / test_rel
    wt_hash_before = __import__("hashlib").md5(wt_test_file.read_bytes()).hexdigest()

    # Save inputs and configuration
    inputs_and_config = {
        "exercise": "exercises/practice/saddle-points",
        "config": {"solution": solution_rel, "test": test_rel, "example": example_rel},
        "named_cases": NAMED_CASES,
        "expected_total_tests": EXPECTED_TOTAL_TESTS,
        "package_test_script": json.loads((EX / "package.json").read_text())["scripts"]["test"],
    }
    (HERE / "test-inputs-and-config.json").write_text(json.dumps(inputs_and_config, indent=2) + "\n")

    # 3. Test Original Reference in Isolated Temporary Directory
    print("\n--- Running Original Reference ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_copy = Path(tmp_dir) / "saddle-points"
        shutil.copytree(EX, tmp_copy, symlinks=True)

        # Substitute original reference
        (tmp_copy / solution_rel).write_text(ORIGINAL_REFERENCE_CODE)

        # Enable all test cases: xit( -> it(
        test_file = tmp_copy / test_rel
        enabled_tests = re.sub(r"\bxit\(", "it(", test_file.read_text())
        test_file.write_text(enabled_tests)

        active_count = len(re.findall(r"\bit\(", enabled_tests))
        check(active_count == EXPECTED_TOTAL_TESTS,
              f"{EXPECTED_TOTAL_TESTS} test cases enabled in temporary copy (got {active_count})")

        env = dict(os.environ, CI="1")

        # Install dependencies
        inst = run_cmd(["corepack", "yarn", "install", "--no-immutable"], tmp_copy, "yarn-install.log", env)
        check(inst.returncode == 0, f"yarn install succeeded (exit {inst.returncode})")

        # Run package test script
        pkg_test = run_cmd(["corepack", "yarn", "test"], tmp_copy, "package-test-run.log", env)
        check(pkg_test.returncode == 0, f"package test script exit code is 0 (got {pkg_test.returncode})")

        # Run jest with json output
        orig_res_file = tmp_copy / "jest-original-results.json"
        jest_orig = run_cmd(
            ["corepack", "yarn", "test:implementation", "--ci", "--watchAll=false", "--json", f"--outputFile={orig_res_file}"],
            tmp_copy,
            "jest-original-run.log",
            env
        )
        check(jest_orig.returncode == 0, f"original jest exit code is 0 (got {jest_orig.returncode})")

        if orig_res_file.exists():
            shutil.copyfile(orig_res_file, HERE / "original-results.json")
            r_orig = json.loads(orig_res_file.read_text())
            total = r_orig["numTotalTests"]
            passed = r_orig["numPassedTests"]
            failed = r_orig["numFailedTests"]
            print(f"Original results: total={total} passed={passed} failed={failed}")
            check(total == EXPECTED_TOTAL_TESTS, f"all {EXPECTED_TOTAL_TESTS} cases executed (got {total})")
            check(passed == EXPECTED_TOTAL_TESTS, f"all {EXPECTED_TOTAL_TESTS} cases passed (got {passed})")
            check(failed == 0, f"zero failures in original reference (got {failed})")
        else:
            check(False, "original jest produced results JSON")

    # 4. Test Refactored Reference in Isolated Temporary Directory
    print("\n--- Running Refactored Reference ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_copy = Path(tmp_dir) / "saddle-points"
        shutil.copytree(EX, tmp_copy, symlinks=True)

        # Substitute refactored reference (.meta/proof.ci.ts from working tree)
        shutil.copyfile(EX / example_rel, tmp_copy / solution_rel)

        # Enable all test cases: xit( -> it(
        test_file = tmp_copy / test_rel
        enabled_tests = re.sub(r"\bxit\(", "it(", test_file.read_text())
        test_file.write_text(enabled_tests)

        active_count = len(re.findall(r"\bit\(", enabled_tests))
        check(active_count == EXPECTED_TOTAL_TESTS,
              f"{EXPECTED_TOTAL_TESTS} test cases enabled in temporary copy (got {active_count})")

        env = dict(os.environ, CI="1")

        # Install dependencies
        inst = run_cmd(["corepack", "yarn", "install", "--no-immutable"], tmp_copy, "yarn-refactored-install.log", env)
        check(inst.returncode == 0, f"yarn install for refactored succeeded (exit {inst.returncode})")

        # Run package test script
        pkg_test = run_cmd(["corepack", "yarn", "test"], tmp_copy, "package-refactored-test-run.log", env)
        check(pkg_test.returncode == 0, f"package test script exit code is 0 for refactored (got {pkg_test.returncode})")

        # Run jest with json output
        ref_res_file = tmp_copy / "jest-refactored-results.json"
        jest_ref = run_cmd(
            ["corepack", "yarn", "test:implementation", "--ci", "--watchAll=false", "--json", f"--outputFile={ref_res_file}"],
            tmp_copy,
            "jest-refactored-run.log",
            env
        )
        check(jest_ref.returncode == 0, f"refactored jest exit code is 0 (got {jest_ref.returncode})")

        if ref_res_file.exists():
            shutil.copyfile(ref_res_file, HERE / "refactored-results.json")
            r_ref = json.loads(ref_res_file.read_text())
            total = r_ref["numTotalTests"]
            passed = r_ref["numPassedTests"]
            failed = r_ref["numFailedTests"]
            print(f"Refactored results: total={total} passed={passed} failed={failed}")
            check(total == EXPECTED_TOTAL_TESTS, f"all {EXPECTED_TOTAL_TESTS} cases executed (got {total})")
            check(passed == EXPECTED_TOTAL_TESTS, f"all {EXPECTED_TOTAL_TESTS} cases passed (got {passed})")
            check(failed == 0, f"zero failures in refactored reference (got {failed})")

            # Verify every assertion and specifically all 3 named cases
            assertions = [a for suite in r_ref["testResults"] for a in suite["assertionResults"]]
            by_title = {a["title"]: a["status"] for a in assertions}
            for named_case in NAMED_CASES:
                st = by_title.get(named_case)
                check(st == "passed", f"named case '{named_case}' passed (got {st})")

            # Save before vs after comparison
            comparison = {
                "summary": "Original and refactored implementations pass identical test cases",
                "total_executed": total,
                "passed": passed,
                "failed": failed,
                "named_cases_verification": [
                    {"case": nc, "status": by_title.get(nc)} for nc in NAMED_CASES
                ],
                "all_cases": [
                    {"title": a["title"], "status": a["status"]} for a in assertions
                ]
            }
            (HERE / "before-after-comparison.json").write_text(json.dumps(comparison, indent=2) + "\n")
        else:
            check(False, "refactored jest produced results JSON")

    # 5. Confirm working-tree test file was NOT modified
    wt_hash_after = __import__("hashlib").md5(wt_test_file.read_bytes()).hexdigest()
    check(wt_hash_before == wt_hash_after, "working tree test file was not modified")

    print(f"\nRESULT: {'FAILED' if failures else 'ALL CHECKS PASSED'}")
    if failures:
        print("Failures:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
