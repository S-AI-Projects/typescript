#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib

EXERCISE_DIR = "exercises/practice/rotational-cipher"
NAMED_CASES = [
    "rotate a by 1",
    "rotate a by 26, same output as input",
    "rotate a by 0, same output as input",
]


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


def check_reproducibility():
    print("[2/4] Checking test-generation reproducibility via tools/course_checks/r47-t002.py...")
    cmd = [sys.executable, "tools/course_checks/r47-t002.py"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"course_check failed: {res.stderr}")
        raise AssertionError(f"course_check r47-t002 failed with code {res.returncode}")
    print("  ✓ Test generation reproducibility verified.")


def run_tests_in_sandbox(config_path):
    print(f"[3/4] Running automated tests in temporary copy...")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    solution_rel = config["files"]["solution"][0]
    test_rel = config["files"]["test"][0]
    example_rel = config["files"]["example"][0]

    with tempfile.TemporaryDirectory(dir=".") as tmpdir:
        temp_exercise = os.path.join(tmpdir, "rotational-cipher")
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
    print("=== Running R47-T002 Automated Check ===")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    tool_versions = get_tool_versions()

    # 1. Learner stub check
    check_learner_stub(os.path.join(EXERCISE_DIR, "rotational-cipher.ts"))

    # 2. Test generation reproducibility check
    check_reproducibility()

    # 3. Test execution in isolated copy
    test_results = run_tests_in_sandbox(os.path.join(EXERCISE_DIR, ".meta/config.json"))

    # 4. Save results and evidence
    print(f"[4/4] Saving evidence to {work_dir}...")
    evidence = {
        "task_id": "R47-T002",
        "exercise": "exercises/practice/rotational-cipher",
        "tool_versions": tool_versions,
        "named_cases": NAMED_CASES,
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
