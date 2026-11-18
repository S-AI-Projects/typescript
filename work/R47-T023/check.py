#!/usr/bin/env python3
"""
work/R47-T023/check.py: Automated verification checker for the ETL mutation experiment.

Requirements:
- Use Python subprocess and tempfile.
- Resolve paths using .meta/config.json.
- Copy the exercise including hidden files.
- Substitute the reference only in the temporary copy.
- Run the exercise package.json test script with watch mode disabled.
- Enable all exercise test cases.
- Verify child return codes and test counts.
- Fail on zero tests, failed assertions or non-zero child exit codes.
- Test the original reference implementation (must PASS all tests).
- Test the mutated implementation (must FAIL the rejecting test).
- Never rewrite the original working tree.
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
EX = REPO / "exercises/practice/etl"
META_CFG = EX / ".meta/config.json"
TOML_PATH = EX / ".meta/tests.toml"

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


def main() -> None:
    check_prerequisites()

    # 1. Collect and write tool versions
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
    check(len(toml_data) == 4, f"tests.toml has 4 canonical cases (found {len(toml_data)})")

    # Verify working tree has untouched learner stub and test file
    stub_path = EX / solution_rel
    check("Remove this line and implement the function" in stub_path.read_text(),
          "learner stub is unsolved in working tree")

    for rel in (solution_rel, test_rel, example_rel):
        diff = run_cmd(["git", "diff", "--quiet", "HEAD", "--", str((EX / rel).relative_to(REPO))], REPO)
        check(diff.returncode == 0, f"{rel} unchanged in working tree")

    # Hash of working tree test file to ensure it's not modified
    wt_test_file = EX / test_rel
    wt_hash_before = __import__("hashlib").md5(wt_test_file.read_bytes()).hexdigest()

    # 3. Test Original Reference in Isolated Temporary Directory
    print("\n--- Running Original Reference ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_copy = Path(tmp_dir) / "etl"
        shutil.copytree(EX, tmp_copy, symlinks=True)

        # Substitute original reference
        shutil.copyfile(EX / example_rel, tmp_copy / solution_rel)

        # Enable all test cases: xit( -> it(
        test_file = tmp_copy / test_rel
        enabled_tests = re.sub(r"\bxit\(", "it(", test_file.read_text())
        test_file.write_text(enabled_tests)

        active_count = len(re.findall(r"\bit\(", enabled_tests))
        check(active_count == 4, f"4 test cases enabled in temporary copy (got {active_count})")

        env = dict(os.environ, CI="1")

        # Install dependencies
        inst = run_cmd(["corepack", "yarn", "install", "--no-immutable"], tmp_copy, "yarn-install.log", env)
        check(inst.returncode == 0, f"yarn install succeeded (exit {inst.returncode})")

        # Run package.json test script
        pkg_test = run_cmd(["corepack", "yarn", "test"], tmp_copy, "package-test-run.log", env)
        check(pkg_test.returncode == 0, f"package test script exit code is 0 (got {pkg_test.returncode})")

        # Run test:implementation with JSON results
        res_file = tmp_copy / "jest-results.json"
        jest_p = run_cmd(
            ["corepack", "yarn", "test:implementation", "--ci", "--watchAll=false", "--json", f"--outputFile={res_file}"],
            tmp_copy,
            "jest-original-run.log",
            env
        )
        check(jest_p.returncode == 0, f"original jest exit code is 0 (got {jest_p.returncode})")

        if res_file.exists():
            shutil.copyfile(res_file, HERE / "original-results.json")
            r = json.loads(res_file.read_text())
            total = r["numTotalTests"]
            passed = r["numPassedTests"]
            failed = r["numFailedTests"]
            print(f"Original results: total={total} passed={passed} failed={failed}")
            check(total > 0, "original test run executed more than zero tests")
            check(total == 4, f"all 4 cases executed (got {total})")
            check(passed == 4, f"all 4 cases passed (got {passed})")
            check(failed == 0, f"zero failures in original reference (got {failed})")
        else:
            check(False, "original jest produced results JSON")

    # 4. Test Mutated Reference in Isolated Temporary Directory
    print("\n--- Running Mutated Reference Experiment ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_copy = Path(tmp_dir) / "etl"
        shutil.copytree(EX, tmp_copy, symlinks=True)

        # Create mutated implementation (omits .toLowerCase())
        original_code = (EX / example_rel).read_text()
        mutated_code = original_code.replace("each.toLowerCase()", "each")
        assert mutated_code != original_code, "Mutation must change code"

        (tmp_copy / solution_rel).write_text(mutated_code)

        # Enable all test cases: xit( -> it(
        test_file = tmp_copy / test_rel
        enabled_tests = re.sub(r"\bxit\(", "it(", test_file.read_text())
        test_file.write_text(enabled_tests)

        env = dict(os.environ, CI="1")

        # Install dependencies
        inst = run_cmd(["corepack", "yarn", "install", "--no-immutable"], tmp_copy, env=env)
        check(inst.returncode == 0, f"yarn install for mutant succeeded (exit {inst.returncode})")

        # Run test:implementation with JSON results
        mut_res_file = tmp_copy / "jest-mutant-results.json"
        jest_mut = run_cmd(
            ["corepack", "yarn", "test:implementation", "--ci", "--watchAll=false", "--json", f"--outputFile={mut_res_file}"],
            tmp_copy,
            "jest-mutant-run.log",
            env
        )
        check(jest_mut.returncode != 0, f"mutant jest exit code is non-zero as expected (got {jest_mut.returncode})")

        if mut_res_file.exists():
            shutil.copyfile(mut_res_file, HERE / "mutated-results.json")
            r = json.loads(mut_res_file.read_text())
            total = r["numTotalTests"]
            passed = r["numPassedTests"]
            failed = r["numFailedTests"]
            print(f"Mutant results: total={total} passed={passed} failed={failed}")
            check(total == 4, f"mutant run executed 4 tests (got {total})")
            check(failed > 0, f"mutant caused expected test failures (failed={failed})")

            # Check rejecting test
            assertions = [
                a for suite in r["testResults"] for a in suite["assertionResults"]
            ]
            by_title = {a["title"]: a["status"] for a in assertions}
            rejecting_title = "transforms one value"
            check(by_title.get(rejecting_title) == "failed",
                  f"minimal test '{rejecting_title}' rejects mutant (got {by_title.get(rejecting_title)})")

            # Save expected vs actual analysis
            comparison = {
                "mutation": "Omit .toLowerCase() when inserting into modern format dictionary (phase1[each] instead of phase1[each.toLowerCase()])",
                "minimal_input": {"1": ["A"]},
                "rejecting_test_uuid": "78a7a9f9-4490-4a47-8ee9-5a38bb47d28f",
                "rejecting_test_name": rejecting_title,
                "expected_output": {"a": 1},
                "mutated_output": {"A": 1},
                "test_outcomes": [
                    {
                        "title": a["title"],
                        "original_status": "passed",
                        "mutant_status": a["status"]
                    }
                    for a in assertions
                ]
            }
            (HERE / "expected-vs-actual.json").write_text(json.dumps(comparison, indent=2) + "\n")
        else:
            check(False, "mutant jest produced results JSON")

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
