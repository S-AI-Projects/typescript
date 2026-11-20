#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib

EXERCISE_DIR = "exercises/practice/square-root"
TARGET_UUIDS = [
    "9b748478-7b0a-490c-b87a-609dacf631fd",
    "7d3aa9ba-9ac6-4e93-a18b-2e8b477139bb",
    "6624aabf-3659-4ae0-a1c8-25ae7f33c6ef",
]
NAMED_CASES = ["root of 1", "root of 4", "root of 25"]


def get_tool_versions():
    node_v = (
        subprocess.check_output(
            ["/opt/homebrew/bin/node", "-v"], text=True
        ).strip()
        if os.path.exists("/opt/homebrew/bin/node")
        else sys.version
    )
    python_v = sys.version.split()[0]
    yarn_v = subprocess.check_output(
        [
            "/opt/homebrew/bin/node",
            "/opt/homebrew/bin/yarn",
            "--version",
        ],
        text=True,
    ).strip()
    return {"node": node_v, "python": python_v, "yarn": yarn_v}


def check_learner_stub(solution_path):
    print(f"[1/4] Checking learner stub at {solution_path}...")
    with open(solution_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "throw new Error" not in content and "Remove this line" not in content:
        raise AssertionError("Learner stub appears to be solved in the working tree!")
    print("  ✓ Learner stub remains unsolved.")


def check_tests_toml(tests_toml_path):
    print(f"[2/4] Validating {tests_toml_path}...")
    with open(tests_toml_path, "rb") as f:
        toml_data = tomllib.load(f)

    total_cases = 0
    included_cases = 0
    excluded_cases = 0

    for uuid, entry in toml_data.items():
        if isinstance(entry, dict) and "description" in entry:
            total_cases += 1
            if entry.get("include") is False:
                excluded_cases += 1
            else:
                included_cases += 1

    print(f"  Total cases: {total_cases}, Included: {included_cases}, Excluded: {excluded_cases}")

    for uuid in TARGET_UUIDS:
        if uuid not in toml_data:
            raise AssertionError(f"UUID {uuid} not found in tests.toml")
        entry = toml_data[uuid]
        comment = entry.get("comment", "")
        if not comment:
            raise AssertionError(f"UUID {uuid} is missing a rationale comment in tests.toml")
        print(f"  ✓ UUID {uuid} ({entry.get('description')}): {comment}")

    return {
        "total_cases": total_cases,
        "included_cases": included_cases,
        "excluded_cases": excluded_cases,
    }


def run_tests_in_sandbox(config_path):
    print(f"[3/4] Running automated tests in temporary copy...")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    solution_rel = config["files"]["solution"][0]
    test_rel = config["files"]["test"][0]
    example_rel = config["files"]["example"][0]

    with tempfile.TemporaryDirectory(dir=".") as tmpdir:
        temp_exercise = os.path.join(tmpdir, "square-root")
        shutil.copytree(EXERCISE_DIR, temp_exercise)

        # Substitute reference into solution in temporary copy
        shutil.copy(
            os.path.join(temp_exercise, example_rel),
            os.path.join(temp_exercise, solution_rel),
        )

        # Enable all test cases (replace xit with it)
        temp_test_path = os.path.join(temp_exercise, test_rel)
        with open(temp_test_path, "r", encoding="utf-8") as f:
            test_content = f.read()

        with open(temp_test_path, "w", encoding="utf-8") as f:
            f.write(test_content.replace("xit(", "it("))

        # Run Jest via node/yarn
        cmd = [
            "/opt/homebrew/bin/node",
            "/opt/homebrew/bin/yarn",
            "jest",
            "--watchAll=false",
            "--json",
            temp_test_path,
        ]
        env = os.environ.copy()
        env["YARN_ENABLE_GLOBAL_CACHE"] = "0"

        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if proc.returncode != 0:
            print(f"Child process stderr: {proc.stderr}")
            print(f"Child process stdout: {proc.stdout}")
            raise AssertionError(f"Jest test runner failed with exit code {proc.returncode}")

        try:
            report = json.loads(proc.stdout)
        except Exception as e:
            print(f"Could not parse Jest json output: {e}\nstdout: {proc.stdout}")
            raise

        passed = report.get("numPassedTests", 0)
        total = report.get("numTotalTests", 0)
        failed = report.get("numFailedTests", 0)

        print(f"  Test results: {passed}/{total} passed, {failed} failed.")

        if total == 0:
            raise AssertionError("Zero-test run: no tests were executed!")
        if failed > 0:
            raise AssertionError(f"{failed} tests failed!")

        # Verify named cases
        executed_titles = [
            t["title"]
            for r in report.get("testResults", [])
            for t in r.get("assertionResults", [])
            if t.get("status") == "passed"
        ]

        for named in NAMED_CASES:
            if named not in executed_titles:
                raise AssertionError(f"Named case '{named}' was not among passed tests: {executed_titles}")
            print(f"  ✓ Passed named case: '{named}'")

        return {
            "total_executed": total,
            "passed": passed,
            "failed": failed,
            "executed_titles": executed_titles,
        }


def main():
    print("=== Running R47-T001 Automated Check ===")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    tool_versions = get_tool_versions()

    # 1. Learner stub check
    check_learner_stub(os.path.join(EXERCISE_DIR, "square-root.ts"))

    # 2. tests.toml validation
    counts = check_tests_toml(os.path.join(EXERCISE_DIR, ".meta/tests.toml"))

    # 3. Test execution in isolated copy
    test_results = run_tests_in_sandbox(os.path.join(EXERCISE_DIR, ".meta/config.json"))

    # 4. Save results and evidence
    print(f"[4/4] Saving evidence to {work_dir}...")
    evidence = {
        "task_id": "R47-T001",
        "exercise": "exercises/practice/square-root",
        "tool_versions": tool_versions,
        "counts": counts,
        "test_results": test_results,
        "status": "PASSED",
    }
    with open(os.path.join(work_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    with open(os.path.join(work_dir, "tool_versions.json"), "w", encoding="utf-8") as f:
        json.dump(tool_versions, f, indent=2)

    print("=== All checks PASSED successfully! ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Check failed: {err}", file=sys.stderr)
        sys.exit(1)
