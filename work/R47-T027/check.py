#!/usr/bin/env python3
"""
work/R47-T027/check.py: Automated verification checker for Connect language-specific hint.

Requirements:
1. Resolve solution, test, and example paths from exercises/practice/connect/.meta/config.json.
2. Run the reference implementation in an isolated temporary directory (including dotfiles).
3. Substitute reference implementation into solution file ONLY in the temp copy.
4. Enable all test cases (xit( -> it() ONLY in the temp copy.
5. Run the exercise package.json test script with watch mode disabled.
6. Assert child return code is 0, executed test count > 0.
7. Assert the three named cases pass:
   - "an empty board has no winner"
   - "X can win on a 1x1 board"
   - "O can win on a 1x1 board"
8. Execute and assert the micro-example in work/R47-T027/example.ts:
   - Match documented vs actual outputs.
   - Assert contrasting pitfall output.
9. Assert learner stub is still unsolved and working tree canonical files are unmodified.
10. Save evidence into work/R47-T027/ (inputs.json, expected-results.json, actual-results.json,
    test-results.md, tool-versions.txt, output.txt, final-report.md).
11. Exit non-zero on any failed assertion.
"""

import hashlib
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
EX = REPO / "exercises/practice/connect"
META_CFG = EX / ".meta/config.json"
TOML_PATH = EX / ".meta/tests.toml"
HINTS_PATH = EX / ".docs/hints.md"
EXAMPLE_TS = HERE / "example.ts"
INPUTS_JSON = HERE / "inputs.json"
EXPECTED_JSON = HERE / "expected-results.json"
ACTUAL_JSON = HERE / "actual-results.json"
TOOL_VERSIONS_TXT = HERE / "tool-versions.txt"
TEST_RESULTS_MD = HERE / "test-results.md"
OUTPUT_TXT = HERE / "output.txt"
FINAL_REPORT_MD = HERE / "final-report.md"

MANDATORY_CASES = [
    "an empty board has no winner",
    "X can win on a 1x1 board",
    "O can win on a 1x1 board",
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
    log_name: str | None = None,
    env: dict | None = None,
) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if log_name:
        log_file = HERE / log_name
        log_file.write_text(
            f"$ {' '.join(cmd)}\nexit={p.returncode}\n"
            f"--- stdout ---\n{p.stdout}\n"
            f"--- stderr ---\n{p.stderr}\n"
        )
    return p


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


def verify_micro_example() -> dict:
    log("\n--- Verifying Micro-Example (work/R47-T027/example.ts) ---")
    p = run_cmd(["node", str(EXAMPLE_TS)], HERE, "example-run.log")
    check(p.returncode == 0, f"example.ts executed with return code 0 (got {p.returncode})")

    try:
        actual_data = json.loads(p.stdout)
    except Exception as e:
        check(False, f"example.ts produced valid JSON output: {e}")
        return {}

    ACTUAL_JSON.write_text(json.dumps(actual_data, indent=2) + "\n")

    expected_data = json.loads(EXPECTED_JSON.read_text())
    check(
        actual_data == expected_data,
        "actual-results.json matches expected-results.json exactly",
    )

    # Verify both micro-example outputs
    narrowed = actual_data.get("narrowed", {})
    check("X" in narrowed and "horizontal" in narrowed["X"], "Micro-example asserts player 'X' horizontal")
    check("O" in narrowed and "vertical" in narrowed["O"], "Micro-example asserts player 'O' vertical")

    pitfall = actual_data.get("pitfall", {})
    check("." in pitfall and "vertical" in pitfall["."], "Contrasting pitfall asserts '.' falls into 'O'")
    check("?" in pitfall and "vertical" in pitfall["?"], "Contrasting pitfall asserts '?' falls into 'O'")

    # Verify hints.md documents the exact strings
    hints_text = HINTS_PATH.read_text()
    check(narrowed["X"] in hints_text, "hints.md documents Player X output")
    check(narrowed["O"] in hints_text, "hints.md documents Player O output")
    check(pitfall["."] in hints_text, "hints.md documents contrasting pitfall '.' output")
    check(pitfall["?"] in hints_text, "hints.md documents contrasting pitfall '?' output")
    check(
        "https://www.typescriptlang.org/docs/handbook/2/narrowing.html#equality-narrowing"
        in hints_text,
        "hints.md links official TypeScript equality narrowing documentation",
    )

    return actual_data


def run_reference_tests(solution_rel: str, test_rel: str, example_rel: str) -> dict:
    log("\n--- Running Reference Implementation Tests in Isolated Temp Dir ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_copy = Path(tmp_dir) / "connect"
        shutil.copytree(EX, tmp_copy, symlinks=True)

        # Substitute proof.ci.ts into connect.ts ONLY in the copy
        shutil.copyfile(EX / example_rel, tmp_copy / solution_rel)

        # Enable all tests
        test_file = tmp_copy / test_rel
        enabled_code = re.sub(r"\bxit\(", "it(", test_file.read_text())
        test_file.write_text(enabled_code)

        env = dict(os.environ, CI="1")

        # yarn install
        inst = run_cmd(
            ["corepack", "yarn", "install", "--no-immutable"],
            tmp_copy,
            "yarn-install.log",
            env,
        )
        check(inst.returncode == 0, f"yarn install succeeded (exit {inst.returncode})")

        # package.json test script
        pkg_test = run_cmd(
            ["corepack", "yarn", "test"],
            tmp_copy,
            "package-test-run.log",
            env,
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
            "jest-run.log",
            env,
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
    log("=== Connect R47-T027 Automated Verification Checker ===")

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
    log(f"Resolved paths: solution={solution_rel}, test={test_rel}, example={example_rel}")

    # 4. Check tests.toml
    toml_data = tomllib.loads(TOML_PATH.read_text())
    expected_total = len(toml_data)
    log(f"Canonical test cases in tests.toml: {expected_total}")
    check(expected_total > 0, "canonical test count > 0 in tests.toml")

    # 5. Check working tree learner stub and canonical files
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

    # 6. Verify micro-example
    verify_micro_example()

    # 7. Run reference tests in temp directory
    res = run_reference_tests(solution_rel, test_rel, example_rel)
    total = res["total"]
    passed = res["passed"]
    failed = res["failed"]
    assertions = res["assertions"]

    log(f"\nTest Execution Summary: total={total}, passed={passed}, failed={failed}")
    check(total > 0, f"Executed test count > 0 (got {total})")
    check(total == expected_total, f"All canonical tests executed ({total}/{expected_total})")
    check(passed == total, f"All executed tests passed ({passed}/{total})")
    check(failed == 0, f"No tests failed (failed={failed})")

    # Verify three mandatory cases
    for case in MANDATORY_CASES:
        status = assertions.get(case)
        check(status == "passed", f"Mandatory case '{case}' passed (status: {status})")

    # 8. Generate test-results.md
    md_lines = [
        "# Test Results: Connect Reference Implementation",
        "",
        f"- **Total Tests Executed:** {total}",
        f"- **Passed:** {passed}",
        f"- **Failed:** {failed}",
        "",
        "## Canonical Cases",
        "",
        "| Test Case | Status | Mandatory |",
        "| :--- | :---: | :---: |",
    ]
    for title, status in sorted(assertions.items()):
        is_mand = "Yes" if title in MANDATORY_CASES else "No"
        badge = "PASS" if status == "passed" else "FAIL"
        md_lines.append(f"| `{title}` | {badge} | {is_mand} |")

    md_lines.extend([
        "",
        "## Mandatory Cases Verification",
        "",
    ])
    for case in MANDATORY_CASES:
        md_lines.append(f"- **{case}**: `{assertions.get(case, 'NOT RUN')}`")

    TEST_RESULTS_MD.write_text("\n".join(md_lines) + "\n")

    # 9. Verify working tree files remain pristine
    stub_after = (EX / solution_rel).read_text()
    check(stub_content == stub_after, "Learner stub remained completely unmodified throughout checker execution")

    # 10. Write output.txt
    OUTPUT_TXT.write_text("\n".join(log_lines) + "\n")

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
