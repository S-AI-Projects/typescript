#!/usr/bin/env python3
"""
work/R47-T030/check.py: Automated verification checker for Strain contract examples.

Requirements:
1. Resolve solution, test, and example paths from real config.json.
2. Validate that declared paths exist, stay inside exercises/practice/strain, and forbid '..' traversal.
3. Run the reference implementation in an isolated temporary directory (including dotfiles).
4. Substitute reference implementation into solution file ONLY in the temporary copy.
5. Enable all canonical test cases (xit( -> it()) in the temporary copy.
6. Run the exercise package.json test script with watch mode disabled.
7. Assert child return code is 0, executed test count > 0, all canonical tests pass.
8. Verify named cases:
   - "keeps on empty array returns empty array"
   - "keeps everything"
   - "keeps nothing"
9. Independently execute and verify the three examples directly against the reference implementation.
10. Assert learner stub remains unsolved and working tree canonical files are unmodified.
11. Save all evidence into work/R47-T030/ (inputs.json, expected-results.json, actual-results.json,
    decision-table.md, test-results.md, tool-versions.txt, output.txt, final-report.md).
12. Exit non-zero on any failed assertion.
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
EX = REPO / "exercises" / "practice" / "strain"
META_CFG = EX / ".meta" / "config.json"
TOML_PATH = EX / ".meta" / "tests.toml"
HINTS_PATH = EX / ".docs" / "hints.md"

INPUTS_JSON = HERE / "inputs.json"
EXPECTED_JSON = HERE / "expected-results.json"
ACTUAL_JSON = HERE / "actual-results.json"
TOOL_VERSIONS_TXT = HERE / "tool-versions.txt"
TEST_RESULTS_MD = HERE / "test-results.md"
DECISION_TABLE_MD = HERE / "decision-table.md"
OUTPUT_TXT = HERE / "output.txt"
FINAL_REPORT_MD = HERE / "final-report.md"

NAMED_CASES = [
    "keeps on empty array returns empty array",
    "keeps everything",
    "keeps nothing",
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


def validate_config() -> dict[str, str]:
    log("\n--- Validating Configuration Paths from .meta/config.json ---")
    check(META_CFG.is_file(), f"config.json exists at {META_CFG}")
    data = json.loads(META_CFG.read_text(encoding="utf-8"))
    files_obj = data.get("files", {})

    resolved = {}
    ex_resolved = EX.resolve()

    for role in ("solution", "test", "example"):
        check(role in files_obj and len(files_obj[role]) > 0, f"Role '{role}' declared in config.json")
        for p in files_obj.get(role, []):
            check(".." not in Path(p).parts, f"Role '{role}': path '{p}' has no parent traversal")
            target = (EX / p).resolve()
            try:
                target.relative_to(ex_resolved)
                is_inside = True
            except ValueError:
                is_inside = False
            check(is_inside, f"Role '{role}': path '{p}' remains inside exercise directory")
            check(target.is_file(), f"Role '{role}': file '{p}' exists on disk")
            if role not in resolved:
                resolved[role] = p

    return resolved


def independently_verify_examples(example_rel: str) -> dict:
    log("\n--- Independently Verifying the Three Examples against Reference Implementation ---")
    proof_path = (EX / example_rel).resolve()
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w") as f:
        f.write(f"""
import {{ keep }} from '{proof_path}';

const case1 = keep<number>([], (_: number) => true);
const case2 = keep<number>([1, 3, 5], (_: number) => true);
const case3 = keep<number>([1, 3, 5], (_: number) => false);

console.log(JSON.stringify({{
  case_1_empty_array: case1,
  case_2_keeps_everything: case2,
  case_3_keeps_nothing: case3,
}}));
""")
        f.flush()
        p = run_cmd(["node", f.name], HERE)
        check(p.returncode == 0, f"Node executed reference micro-example with exit code 0 (got {p.returncode})")
        actual_examples = json.loads(p.stdout.strip())

    expected_data = json.loads(EXPECTED_JSON.read_text(encoding="utf-8"))["selected_cases"]

    check(actual_examples["case_1_empty_array"] == expected_data["case_1_empty_array"]["expected_output"],
          f"Case 1 (empty array) output matches expected: {actual_examples['case_1_empty_array']}")
    check(actual_examples["case_2_keeps_everything"] == expected_data["case_2_keeps_everything"]["expected_output"],
          f"Case 2 (keeps everything) output matches expected: {actual_examples['case_2_keeps_everything']}")
    check(actual_examples["case_3_keeps_nothing"] == expected_data["case_3_keeps_nothing"]["expected_output"],
          f"Case 3 (keeps nothing) output matches expected: {actual_examples['case_3_keeps_nothing']}")

    # Check that hints.md documents these exact cases
    hints_text = HINTS_PATH.read_text(encoding="utf-8")
    check("keeps on empty array returns empty array" in hints_text, "hints.md documents Case 1")
    check("keeps everything" in hints_text, "hints.md documents Case 2")
    check("keeps nothing" in hints_text, "hints.md documents Case 3")
    check("Decision Table" in hints_text, "hints.md includes Decision Table section")

    return actual_examples


def run_canonical_tests(solution_rel: str, test_rel: str, example_rel: str) -> dict:
    log("\n--- Running Canonical Tests against Reference in Isolated Temporary Sandbox ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_copy = Path(tmp_dir) / "strain"
        shutil.copytree(EX, tmp_copy, symlinks=True)

        # Substitute reference into solution path ONLY in temporary copy
        shutil.copyfile(EX / example_rel, tmp_copy / solution_rel)

        # Enable all tests (xit( -> it())
        test_file = tmp_copy / test_rel
        enabled_test_code = re.sub(r"\bxit\(", "it(", test_file.read_text(encoding="utf-8"))
        test_file.write_text(enabled_test_code, encoding="utf-8")

        env = dict(os.environ, CI="1")

        # 1. Install dependencies
        inst = run_cmd(["corepack", "yarn", "install", "--no-immutable"], tmp_copy, env=env)
        check(inst.returncode == 0, f"corepack yarn install succeeded (exit {inst.returncode})")

        # 2. Run package.json test script
        pkg_test = run_cmd(["corepack", "yarn", "test"], tmp_copy, env=env)
        check(pkg_test.returncode == 0, f"package.json test script exit code is 0 (got {pkg_test.returncode})")

        # 3. Run Jest implementation test with JSON reporting
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
        check(jest_p.returncode == 0, f"Jest implementation test exit code is 0 (got {jest_p.returncode})")

        if not res_file.is_file():
            check(False, "Jest produced results JSON file")
            return {"total": 0, "passed": 0, "failed": 0, "assertions": {}}

        data = json.loads(res_file.read_text(encoding="utf-8"))
        total = data.get("numTotalTests", 0)
        passed = data.get("numPassedTests", 0)
        failed = data.get("numFailedTests", 0)

        assertions = {
            a["title"]: a["status"]
            for suite in data.get("testResults", [])
            for a in suite.get("assertionResults", [])
        }

        return {"total": total, "passed": passed, "failed": failed, "assertions": assertions}


def main() -> None:
    log("=== Strain R47-T030 Automated Verification Checker ===")

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

    # 3. Configuration path resolution and validation
    paths = validate_config()
    solution_rel = paths["solution"]
    test_rel = paths["test"]
    example_rel = paths["example"]

    # 4. Check tests.toml
    toml_data = tomllib.loads(TOML_PATH.read_text(encoding="utf-8"))
    expected_toml_total = len(toml_data)
    log(f"Canonical test cases defined in tests.toml: {expected_toml_total}")
    check(expected_toml_total > 0, "canonical test count > 0 in tests.toml")

    # 5. Check working tree learner stub and canonical files are intact
    stub_content = (EX / solution_rel).read_text(encoding="utf-8")
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

    # 6. Independently verify the three examples
    actual_examples = independently_verify_examples(example_rel)

    # 7. Run canonical test suite in temporary sandbox
    test_res = run_canonical_tests(solution_rel, test_rel, example_rel)
    total = test_res["total"]
    passed = test_res["passed"]
    failed = test_res["failed"]
    assertions = test_res["assertions"]

    log(f"\nTest Execution Summary: total={total}, passed={passed}, failed={failed}")
    check(total > 0, f"Executed test count > 0 (got {total})")
    check(total == expected_toml_total, f"All canonical tests executed ({total}/{expected_toml_total})")
    check(passed == total, f"All executed tests passed ({passed}/{total})")
    check(failed == 0, f"No tests failed (failed={failed})")

    # 8. Verify the three named cases in canonical test suite
    for case in NAMED_CASES:
        status = assertions.get(case)
        check(status == "passed", f"Canonical named case '{case}' passed (status: {status})")

    # 9. Save actual-results.json
    actual_data = {
        "selected_cases": actual_examples,
        "test_execution": {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "named_cases": {case: assertions.get(case, "NOT_FOUND") for case in NAMED_CASES},
        },
    }
    ACTUAL_JSON.write_text(json.dumps(actual_data, indent=2) + "\n", encoding="utf-8")

    # 10. Generate test-results.md
    md_lines = [
        "# Test Results: Strain Reference Implementation",
        "",
        f"- **Total Tests Executed:** {total}",
        f"- **Passed:** {passed}",
        f"- **Failed:** {failed}",
        "",
        "## Selected Named Cases",
        "",
    ]
    for case in NAMED_CASES:
        md_lines.append(f"- **{case}**: `{assertions.get(case, 'NOT RUN')}`")

    md_lines.extend([
        "",
        "## All Canonical Test Cases",
        "",
        "| Test Case | Status | Named Case |",
        "| :--- | :---: | :---: |",
    ])
    for title, status in sorted(assertions.items()):
        is_named = "Yes" if title in NAMED_CASES else "No"
        badge = "PASS" if status == "passed" else "FAIL"
        md_lines.append(f"| `{title}` | {badge} | {is_named} |")

    TEST_RESULTS_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # 11. Verify working tree learner stub remains intact
    stub_after = (EX / solution_rel).read_text(encoding="utf-8")
    check(stub_content == stub_after, "Learner stub remained completely unmodified throughout checker execution")

    # 12. Write output.txt
    OUTPUT_TXT.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

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
