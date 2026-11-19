#!/usr/bin/env python3
"""
work/R47-T028/check.py: Automated verification checker for Split-Second Stopwatch metadata validation & testing.

Requirements:
1. Resolve solution, test, and example paths from real config.json.
2. Validate metadata on real config.json and three invalid fixtures (missing reference, missing test, path escaping).
3. Run the reference implementation in an isolated temporary directory (including dotfiles).
4. Substitute reference implementation into solution file ONLY in the temp copy.
5. Enable all test cases (xit( -> it()) ONLY in the temp copy.
6. Run the exercise package.json test script with watch mode disabled.
7. Assert child return code is 0, executed test count > 0.
8. Assert named cases pass:
   - "new stopwatch starts in ready state"
   - "new stopwatch's current lap has no elapsed time"
   - "new stopwatch's total has no elapsed time"
   - "new stopwatch does not have previous laps"
9. Assert learner stub remains unsolved and working tree canonical files are unmodified.
10. Save evidence into work/R47-T028/ (inputs.json, expected-results.json, actual-results.json,
    test-results.md, tool-versions.txt, execution.log, final-report.md).
11. Exit non-zero on any failed assertion.
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

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EX = REPO / "exercises" / "practice" / "split-second-stopwatch"
META_CFG = EX / ".meta" / "config.json"
TOML_PATH = EX / ".meta" / "tests.toml"
VALIDATOR_SCRIPT = REPO / "tools" / "course_checks" / "r47-t028.py"

INPUTS_JSON = HERE / "inputs.json"
EXPECTED_JSON = HERE / "expected-results.json"
ACTUAL_JSON = HERE / "actual-results.json"
TOOL_VERSIONS_TXT = HERE / "tool-versions.txt"
TEST_RESULTS_MD = HERE / "test-results.md"
EXECUTION_LOG = HERE / "execution.log"
FINAL_REPORT_MD = HERE / "final-report.md"

NAMED_CASES = [
    "new stopwatch starts in ready state",
    "new stopwatch's current lap has no elapsed time",
    "new stopwatch's total has no elapsed time",
    "new stopwatch does not have previous laps",
]

failures: list[str] = []
log_lines: list[str] = []


def log(msg: str) -> None:
    print(msg)
    log_lines.append(msg)


def check(ok: bool, msg: str) -> None:
    label = "PASS  " if ok else "FAIL  "
    log(f"{label}{msg}")
    if not ok:
        failures.append(msg)


def run_cmd(
    cmd: list[str],
    cwd: Path,
    env: dict | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)



def collect_tool_versions() -> dict[str, str]:
    versions = {"Python": sys.version.split()[0]}
    p_node = run_cmd(["node", "-v"], EX)
    versions["Node"] = p_node.stdout.strip()
    p_yarn = run_cmd(["corepack", "yarn", "-v"], EX)
    versions["Yarn"] = p_yarn.stdout.strip()
    p_corepack = run_cmd(["corepack", "-v"], EX)
    versions["Corepack"] = p_corepack.stdout.strip()

    content = (
        f"Python: {versions['Python']}\n"
        f"Node: {versions['Node']}\n"
        f"Corepack: {versions['Corepack']}\n"
        f"Yarn: {versions['Yarn']}\n"
    )
    TOOL_VERSIONS_TXT.write_text(content)
    return versions


def test_metadata_validator() -> dict:
    log("\n--- Testing Metadata Path Validator (tools/course_checks/r47-t028.py) ---")
    results = {}

    # 1. Test real config
    p_real = run_cmd(
        ["python3", str(VALIDATOR_SCRIPT), str(META_CFG), "--exercise-dir", str(EX)],
        REPO,
    )
    check(p_real.returncode == 0, f"Real config.json validation exited with code 0 (got {p_real.returncode})")
    check("[SUCCESS]" in p_real.stdout, "Real config.json validation reported [SUCCESS]")
    results["real_config"] = {
        "valid": p_real.returncode == 0,
        "exit_code": p_real.returncode,
        "output": p_real.stdout.strip(),
    }

    # 2. Test fixtures from inputs.json
    inputs_data = json.loads(INPUTS_JSON.read_text())
    fixtures = inputs_data.get("fixtures", {})

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        for key, fix in fixtures.items():
            fix_cfg = tmp_path / f"{key}.json"
            fix_cfg.write_text(json.dumps(fix["config_data"], indent=2))

            p_fix = run_cmd(
                ["python3", str(VALIDATOR_SCRIPT), str(fix_cfg), "--exercise-dir", str(EX)],
                REPO,
            )
            check(p_fix.returncode != 0, f"{key} correctly failed with non-zero exit code (got {p_fix.returncode})")
            check("[ERROR]" in p_fix.stdout, f"{key} output contains [ERROR]")

            # Check expected error substring
            expected_json = json.loads(EXPECTED_JSON.read_text())
            expected_fix = expected_json["metadata_validation"].get(key, {})
            for exp_err in expected_fix.get("expected_errors", []):
                check(exp_err in p_fix.stdout, f"{key} error contains expected snippet '{exp_err}'")

            results[key] = {
                "valid": p_fix.returncode == 0,
                "exit_code": p_fix.returncode,
                "output": p_fix.stdout.strip(),
            }

    return results


def run_reference_tests(solution_rel: str, test_rel: str, example_rel: str) -> dict:
    log("\n--- Running Reference Implementation Tests in Isolated Temp Dir ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_copy = Path(tmp_dir) / "split-second-stopwatch"
        shutil.copytree(EX, tmp_copy, symlinks=True)

        # Substitute proof.ci.ts into solution file ONLY in the copy
        shutil.copyfile(EX / example_rel, tmp_copy / solution_rel)

        # Enable all test cases (xit( -> it()
        test_file = tmp_copy / test_rel
        enabled_code = re.sub(r"\bxit\(", "it(", test_file.read_text())
        test_file.write_text(enabled_code)

        env = dict(os.environ, CI="1")

        # yarn install
        inst = run_cmd(
            ["corepack", "yarn", "install", "--no-immutable"],
            tmp_copy,
            env=env,
        )
        check(inst.returncode == 0, f"yarn install succeeded (exit {inst.returncode})")

        # package.json test script
        pkg_test = run_cmd(
            ["corepack", "yarn", "test"],
            tmp_copy,
            env=env,
        )
        check(pkg_test.returncode == 0, f"package.json test script exit code is 0 (got {pkg_test.returncode})")

        # jest implementation test with JSON report
        res_file = tmp_copy / "jest-results.json"
        jest_p = run_cmd(
            [
                "corepack",
                "yarn",
                "test:implementation",
                "--ci",
                "--watchAll=false",
                "--json",
                f"--outputFile={res_file}",
            ],
            tmp_copy,
            env=env,
        )
        check(jest_p.returncode == 0, f"jest exit code is 0 (got {jest_p.returncode})")

        if not res_file.exists():
            check(False, "jest produced results JSON file")
            return {"total": 0, "passed": 0, "failed": 0, "assertions": {}}

        data = json.loads(res_file.read_text())
        total = data["numTotalTests"]
        passed = data["numPassedTests"]
        failed = data["numFailedTests"]

        assertions = {
            a["title"]: a["status"]
            for suite in data["testResults"]
            for a in suite["assertionResults"]
        }

        return {"total": total, "passed": passed, "failed": failed, "assertions": assertions}


def main() -> None:
    log("=== Split-Second Stopwatch R47-T028 Automated Verification Checker ===")

    # 1. Prerequisite checks
    if sys.version_info < (3, 11):
        log("FAIL  Python 3.11+ required for tomllib.")
        sys.exit(1)

    for binary in ["node", "corepack"]:
        if not shutil.which(binary):
            log(f"FAIL  Missing prerequisite binary in PATH: {binary}")
            sys.exit(1)

    # 2. Collect tool versions
    versions = collect_tool_versions()
    log(f"Tool versions: {versions}")

    # 3. Read config.json
    cfg = json.loads(META_CFG.read_text())["files"]
    solution_rel = cfg["solution"][0]
    test_rel = cfg["test"][0]
    example_rel = cfg["example"][0]
    log(f"Resolved paths from config.json: solution={solution_rel}, test={test_rel}, example={example_rel}")

    # 4. Check tests.toml
    toml_data = tomllib.loads(TOML_PATH.read_text())
    expected_toml_total = len(toml_data)
    log(f"Canonical test cases defined in tests.toml: {expected_toml_total}")
    check(expected_toml_total > 0, "canonical test count > 0 in tests.toml")

    # 5. Check working tree learner stub and canonical files are intact
    stub_content = (EX / solution_rel).read_text()
    check(
        "Remove this line and implement the function" in stub_content,
        "learner stub is unsolved in working tree",
    )

    diff_sol = run_cmd(["git", "diff", "--quiet", "HEAD", "--", str((EX / solution_rel).relative_to(REPO))], REPO)
    check(diff_sol.returncode == 0, f"{solution_rel} unchanged in working tree")

    diff_test = run_cmd(["git", "diff", "--quiet", "HEAD", "--", str((EX / test_rel).relative_to(REPO))], REPO)
    check(diff_test.returncode == 0, f"{test_rel} unchanged in working tree")

    diff_ex = run_cmd(["git", "diff", "--quiet", "HEAD", "--", str((EX / example_rel).relative_to(REPO))], REPO)
    check(diff_ex.returncode == 0, f"{example_rel} unchanged in working tree")

    # 6. Test metadata validator and fixtures
    meta_results = test_metadata_validator()

    # 7. Run reference tests in temporary directory
    test_res = run_reference_tests(solution_rel, test_rel, example_rel)
    total = test_res["total"]
    passed = test_res["passed"]
    failed = test_res["failed"]
    assertions = test_res["assertions"]

    log(f"\nTest Execution Summary: total={total}, passed={passed}, failed={failed}")
    check(total > 0, f"Executed test count > 0 (got {total})")
    check(passed == total, f"All executed tests passed ({passed}/{total})")
    check(failed == 0, f"No tests failed (failed={failed})")

    # Verify named cases
    for case in NAMED_CASES:
        status = assertions.get(case)
        check(status == "passed", f"Named case '{case}' passed (status: {status})")

    # 8. Save actual-results.json
    actual_data = {
        "metadata_validation": meta_results,
        "test_execution": {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "named_cases": {case: assertions.get(case, "NOT_FOUND") for case in NAMED_CASES},
        },
    }
    ACTUAL_JSON.write_text(json.dumps(actual_data, indent=2) + "\n")

    # 9. Generate test-results.md
    md_lines = [
        "# Test Results: Split-Second Stopwatch Reference Implementation",
        "",
        f"- **Total Tests Executed:** {total}",
        f"- **Passed:** {passed}",
        f"- **Failed:** {failed}",
        "",
        "## Named Test Cases",
        "",
    ]
    for case in NAMED_CASES:
        md_lines.append(f"- **{case}**: `{assertions.get(case, 'NOT RUN')}`")

    md_lines.extend([
        "",
        "## All Executed Cases",
        "",
        "| Test Case | Status | Named Case |",
        "| :--- | :---: | :---: |",
    ])
    for title, status in sorted(assertions.items()):
        is_named = "Yes" if title in NAMED_CASES else "No"
        badge = "PASS" if status == "passed" else "FAIL"
        md_lines.append(f"| `{title}` | {badge} | {is_named} |")

    TEST_RESULTS_MD.write_text("\n".join(md_lines) + "\n")

    # 10. Verify working tree learner stub remains intact
    stub_after = (EX / solution_rel).read_text()
    check(stub_content == stub_after, "Learner stub remained completely unmodified throughout checker execution")

    # 11. Write execution.log
    EXECUTION_LOG.write_text("\n".join(log_lines) + "\n")

    # Final verdict
    log("\n=== Final Verification Summary ===")
    if failures:
        log(f"Verification FAILED with {len(failures)} issue(s):")
        for f in failures:
            log(f"  - {f}")
        sys.exit(1)
    else:
        log("All verification checks PASSED successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
