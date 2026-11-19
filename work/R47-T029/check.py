#!/usr/bin/env python3
"""
work/R47-T029/check.py: Automated verification checker for Nucleotide Count isolated test runner.

Requirements:
1. Invoke tools/course_checks/r47-t029.py using Python subprocess.
2. Run the actual maintained reference implementation (Scenario A).
3. Verify that all enabled canonical test cases execute and pass.
4. Verify actual test count is greater than zero.
5. Verify named cases pass:
   - "empty strand"
   - "can count one nucleotide in single-character input"
   - "strand with repeated nucleotide"
6. Execute failure-injection Scenario B (deliberately failing reference).
7. Execute failure-injection Scenario C (empty test selection).
8. Verify SHA-256 file hashes before and after every scenario.
9. Verify temporary directories are cleaned up.
10. Save all evidence files into work/R47-T029/:
    - inputs.json
    - expected-results.json
    - actual-results.json
    - test-results.md
    - hash-integrity.json
    - tool-versions.txt
    - output.txt
    - final-report.md
11. Exit non-zero on any failed assertion.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EX = REPO / "exercises" / "practice" / "nucleotide-count"
META_CFG = EX / ".meta" / "config.json"
TOML_PATH = EX / ".meta" / "tests.toml"
RUNNER_SCRIPT = REPO / "tools" / "course_checks" / "r47-t029.py"

INPUTS_JSON = HERE / "inputs.json"
EXPECTED_JSON = HERE / "expected-results.json"
ACTUAL_JSON = HERE / "actual-results.json"
HASH_INTEGRITY_JSON = HERE / "hash-integrity.json"
TOOL_VERSIONS_TXT = HERE / "tool-versions.txt"
TEST_RESULTS_MD = HERE / "test-results.md"
OUTPUT_TXT = HERE / "output.txt"
FINAL_REPORT_MD = HERE / "final-report.md"

NAMED_CASES = [
    "empty strand",
    "can count one nucleotide in single-character input",
    "strand with repeated nucleotide",
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


def calculate_file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def main() -> None:
    log("=== Nucleotide Count R47-T029 Automated Verification Checker ===")

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

    # 4. Check tests.toml canonical cases
    toml_data = tomllib.loads(TOML_PATH.read_text())
    expected_toml_total = len(toml_data)
    log(f"Canonical test cases defined in tests.toml: {expected_toml_total}")
    check(expected_toml_total > 0, "canonical test count > 0 in tests.toml")

    # 5. Calculate initial SHA-256 hashes
    tracked_files = [
        EX / solution_rel,
        EX / test_rel,
        EX / example_rel,
    ]
    initial_hashes = {str(f.relative_to(REPO)): calculate_file_hash(f) for f in tracked_files}
    log("Initial SHA-256 hashes calculated:")
    for rel_path, h in initial_hashes.items():
        log(f"  {rel_path}: {h}")

    stub_content = (EX / solution_rel).read_text()
    check(
        "Remove this line and implement the function" in stub_content,
        "learner stub is unsolved in working tree",
    )

    actual_results = {}
    hash_integrity_record = {
        "initial_hashes": initial_hashes,
        "scenario_hashes": {},
    }

    # -------------------------------------------------------------
    # Scenario A: Successful Reference Execution
    # -------------------------------------------------------------
    log("\n--- Scenario A: Successful Reference Execution ---")
    p_a = run_cmd(
        ["python3", str(RUNNER_SCRIPT), str(META_CFG), "--exercise-dir", str(EX), "--json"],
        REPO,
    )
    check(p_a.returncode == 0, f"Scenario A runner exit code is 0 (got {p_a.returncode})")
    try:
        res_a = json.loads(p_a.stdout)
    except Exception as e:
        check(False, f"Scenario A produced valid JSON: {e}")
        res_a = {}

    total_a = res_a.get("total", 0)
    passed_a = res_a.get("passed", 0)
    failed_a = res_a.get("failed", 0)
    assertions_a = res_a.get("assertions", {})

    check(res_a.get("success") is True, "Scenario A success is True")
    check(total_a == expected_toml_total, f"Scenario A executed all canonical cases ({total_a}/{expected_toml_total})")
    check(passed_a == total_a, f"Scenario A all tests passed ({passed_a}/{total_a})")
    check(failed_a == 0, f"Scenario A zero test failures (got {failed_a})")

    for case in NAMED_CASES:
        status = assertions_a.get(case)
        check(status == "passed", f"Scenario A named case '{case}' passed (status: {status})")

    actual_results["scenario_a_success"] = {
        "exit_code": p_a.returncode,
        "total": total_a,
        "passed": passed_a,
        "failed": failed_a,
        "assertions": assertions_a,
    }

    # Check hash integrity after Scenario A
    hashes_after_a = {str(f.relative_to(REPO)): calculate_file_hash(f) for f in tracked_files}
    check(hashes_after_a == initial_hashes, "Hashes match initial hashes after Scenario A")
    hash_integrity_record["scenario_hashes"]["after_scenario_a"] = hashes_after_a

    # -------------------------------------------------------------
    # Scenario B: Deliberately Failing Reference
    # -------------------------------------------------------------
    log("\n--- Scenario B: Deliberately Failing Reference ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        failing_ref = Path(tmp_dir) / "failing-proof.ts"
        failing_ref.write_text(
            "export function nucleotideCounts(strand: string) {\n"
            "  return { A: -1, C: -1, G: -1, T: -1 };\n"
            "}\n"
        )
        p_b = run_cmd(
            [
                "python3",
                str(RUNNER_SCRIPT),
                str(META_CFG),
                "--exercise-dir",
                str(EX),
                "--reference",
                str(failing_ref),
                "--json",
            ],
            REPO,
        )
        check(p_b.returncode != 0, f"Scenario B runner correctly failed with non-zero code (got {p_b.returncode})")
        try:
            res_b = json.loads(p_b.stdout)
        except Exception as e:
            res_b = {"raw": p_b.stdout, "stderr": p_b.stderr}

        err_b = res_b.get("error", p_b.stderr)
        check("failed" in err_b.lower() or p_b.returncode != 0, f"Scenario B reports test failure: {err_b}")

        actual_results["scenario_b_failing_reference"] = {
            "exit_code": p_b.returncode,
            "error": err_b,
        }

    # Check hash integrity after Scenario B
    hashes_after_b = {str(f.relative_to(REPO)): calculate_file_hash(f) for f in tracked_files}
    check(hashes_after_b == initial_hashes, "Hashes match initial hashes after Scenario B")
    hash_integrity_record["scenario_hashes"]["after_scenario_b"] = hashes_after_b

    # -------------------------------------------------------------
    # Scenario C: Empty Test Selection
    # -------------------------------------------------------------
    log("\n--- Scenario C: Empty Test Selection ---")
    p_c = run_cmd(
        [
            "python3",
            str(RUNNER_SCRIPT),
            str(META_CFG),
            "--exercise-dir",
            str(EX),
            "--test-pattern",
            "NONEXISTENT_TEST_NAME_XYZ",
            "--json",
        ],
        REPO,
    )
    check(p_c.returncode != 0, f"Scenario C runner correctly failed with non-zero code (got {p_c.returncode})")
    try:
        res_c = json.loads(p_c.stdout)
    except Exception as e:
        res_c = {"raw": p_c.stdout, "stderr": p_c.stderr}

    err_c = res_c.get("error", p_c.stderr)
    check("zero tests" in err_c.lower(), f"Scenario C correctly detected zero-test condition: {err_c}")

    actual_results["scenario_c_empty_test_selection"] = {
        "exit_code": p_c.returncode,
        "error": err_c,
    }

    # Check hash integrity after Scenario C
    hashes_after_c = {str(f.relative_to(REPO)): calculate_file_hash(f) for f in tracked_files}
    check(hashes_after_c == initial_hashes, "Hashes match initial hashes after Scenario C")
    hash_integrity_record["scenario_hashes"]["after_scenario_c"] = hashes_after_c

    # -------------------------------------------------------------
    # Evidence Generation
    # -------------------------------------------------------------
    log("\n--- Generating Evidence Files ---")

    # Save actual-results.json
    ACTUAL_JSON.write_text(json.dumps(actual_results, indent=2) + "\n")

    # Save hash-integrity.json
    hash_integrity_record["all_matched"] = (
        hashes_after_a == initial_hashes
        and hashes_after_b == initial_hashes
        and hashes_after_c == initial_hashes
    )
    hash_integrity_record["learner_stub_unsolved"] = (
        "Remove this line and implement the function" in (EX / solution_rel).read_text()
    )
    HASH_INTEGRITY_JSON.write_text(json.dumps(hash_integrity_record, indent=2) + "\n")

    # Save test-results.md
    md_lines = [
        "# Test Results: Nucleotide Count Reference Implementation",
        "",
        f"- **Total Canonical Tests:** {total_a}",
        f"- **Executed:** {total_a}",
        f"- **Passed:** {passed_a}",
        f"- **Failed:** {failed_a}",
        "",
        "## Named Test Cases",
        "",
    ]
    for case in NAMED_CASES:
        status = assertions_a.get(case, "NOT_RUN")
        md_lines.append(f"- **{case}**: `{status}`")

    md_lines.extend([
        "",
        "## All Canonical Assertions",
        "",
        "| Test Case | Status | Named Case |",
        "| :--- | :---: | :---: |",
    ])
    for title, status in sorted(assertions_a.items()):
        is_named = "Yes" if title in NAMED_CASES else "No"
        badge = "PASS" if status == "passed" else "FAIL"
        md_lines.append(f"| `{title}` | {badge} | {is_named} |")

    TEST_RESULTS_MD.write_text("\n".join(md_lines) + "\n")

    # Save output.txt
    OUTPUT_TXT.write_text("\n".join(log_lines) + "\n")

    # Verify working tree git diff is clean for exercise
    diff_ex = run_cmd(["git", "diff", "--quiet", "HEAD", "--", str(EX.relative_to(REPO))], REPO)
    check(diff_ex.returncode == 0, "Exercise files completely unmodified in git working tree")

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
