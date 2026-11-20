#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

EXERCISE_DIR = "exercises/practice/list-ops"
NAMED_CASES = ["empty lists", "list to empty list", "empty list to list"]


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
    print(f"[1/5] Checking learner stub at {solution_path}...")
    with open(solution_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "throw new Error" not in content and "Remove this line" not in content:
        raise AssertionError("Learner stub appears to be solved in the working tree!")
    print("  ✓ Learner stub remains unsolved.")


def run_jest_on_copy(temp_exercise, config):
    test_rel = config["files"]["test"][0]
    temp_test_path = os.path.join(temp_exercise, test_rel)

    with open(temp_test_path, "r", encoding="utf-8") as f:
        test_content = f.read()

    with open(temp_test_path, "w", encoding="utf-8") as f:
        f.write(test_content.replace("xit(", "it("))

    cmd = [
        "/opt/homebrew/bin/node",
        "/opt/homebrew/bin/yarn",
        "jest",
        "--watchAll=false",
        temp_test_path,
    ]
    env = os.environ.copy()
    env["YARN_ENABLE_GLOBAL_CACHE"] = "0"

    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    output = (proc.stderr or "") + "\n" + (proc.stdout or "")

    passed = [
        p.strip()
        for p in re.findall(
            r"✓\s+([^\(\n]+?)(?:\s+\(\d+\s*m?s\))?$", output, re.MULTILINE
        )
    ]
    failed = [
        f.strip()
        for f in re.findall(
            r"✕\s+([^\(\n]+?)(?:\s+\(\d+\s*m?s\))?$", output, re.MULTILINE
        )
    ]

    total = len(passed) + len(failed)
    summary_match = re.search(
        r"Tests:\s+(\d+)\s+failed,\s+(\d+)\s+passed,\s+(\d+)\s+total", output
    )
    if summary_match:
        failed_count, passed_count, total_count = map(int, summary_match.groups())
    else:
        summary_pass = re.search(r"Tests:\s+(\d+)\s+passed,\s+(\d+)\s+total", output)
        if summary_pass:
            passed_count, total_count = map(int, summary_pass.groups())
            failed_count = 0
        else:
            passed_count, failed_count, total_count = len(passed), len(failed), total

    report = {
        "passed": passed,
        "failed": failed,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "total_count": total_count,
    }
    return proc.returncode, report, output


def check_original_reference(config):
    print("[2/5] Testing original reference implementation...")
    solution_rel = config["files"]["solution"][0]
    example_rel = config["files"]["example"][0]

    with tempfile.TemporaryDirectory(dir=".") as tmpdir:
        temp_exercise = os.path.join(tmpdir, "list-ops")
        shutil.copytree(EXERCISE_DIR, temp_exercise)

        shutil.copy(
            os.path.join(temp_exercise, example_rel),
            os.path.join(temp_exercise, solution_rel),
        )

        code, report, output = run_jest_on_copy(temp_exercise, config)
        if code != 0:
            raise AssertionError(f"Original reference failed tests with exit code {code}")

        passed = report["passed_count"]
        total = report["total_count"]
        failed = report["failed_count"]

        print(f"  Test results: {passed}/{total} passed, {failed} failed.")
        if total == 0:
            raise AssertionError("Zero-test run: no tests were executed!")
        if failed > 0:
            raise AssertionError(f"Expected 0 failures in original, found {failed}")

        for named in NAMED_CASES:
            if named not in report["passed"]:
                raise AssertionError(f"Named case '{named}' not among passed tests: {report['passed']}")
            print(f"  ✓ Passed named case: '{named}'")

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "executed_titles": report["passed"],
        }


def check_mutant_rejection(config):
    print("[3/5] Testing deliberate Cons.append mutant...")
    solution_rel = config["files"]["solution"][0]
    example_rel = config["files"]["example"][0]

    with tempfile.TemporaryDirectory(dir=".") as tmpdir:
        temp_exercise = os.path.join(tmpdir, "list-ops")
        shutil.copytree(EXERCISE_DIR, temp_exercise)

        ref_path = os.path.join(temp_exercise, example_rel)
        with open(ref_path, "r", encoding="utf-8") as f:
            ref_code = f.read()

        target_str = """  public append(other: Cons<T>): Cons<T> {
    return other.foldl((result, item) => result.push(item), this)
  }"""
        mutant_str = """  public append(other: Cons<T>): Cons<T> {
    if (other.length() === 0) {
      return other
    }
    return other.foldl((result, item) => result.push(item), this)
  }"""
        if target_str not in ref_code:
            raise AssertionError("Target append method not found in reference code for mutation!")

        mutated_code = ref_code.replace(target_str, mutant_str)
        sol_path = os.path.join(temp_exercise, solution_rel)
        with open(sol_path, "w", encoding="utf-8") as f:
            f.write(mutated_code)

        code, report, output = run_jest_on_copy(temp_exercise, config)
        if code == 0:
            raise AssertionError("Mutant unexpectedly passed all tests!")

        failed_titles = report["failed"]
        print(f"  ✓ Mutant failed as expected with returncode {code}.")
        print(f"  Failed test cases: {failed_titles}")

        if "empty list to list" not in failed_titles:
            raise AssertionError(f"'empty list to list' was not rejected by mutant! Failed: {failed_titles}")
        print("  ✓ Confirmed rejecting test case: 'empty list to list'")

        return {
            "mutant_return_code": code,
            "failed_titles": failed_titles,
            "rejecting_case": "empty list to list",
        }


def main():
    print("=== Running R47-T003 Automated Check ===")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    tool_versions = get_tool_versions()

    config_path = os.path.join(EXERCISE_DIR, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 1. Learner stub check
    check_learner_stub(os.path.join(EXERCISE_DIR, "list-ops.ts"))

    # 2. Original reference execution
    original_results = check_original_reference(config)

    # 3. Mutant rejection check
    mutant_results = check_mutant_rejection(config)

    # 4. Save evidence
    print(f"[4/5] Saving evidence to {work_dir}...")
    evidence = {
        "task_id": "R47-T003",
        "exercise": "exercises/practice/list-ops",
        "tool_versions": tool_versions,
        "named_cases": NAMED_CASES,
        "original_results": original_results,
        "mutant_results": mutant_results,
        "status": "PASSED",
    }
    with open(os.path.join(work_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    with open(os.path.join(work_dir, "tool_versions.json"), "w", encoding="utf-8") as f:
        json.dump(tool_versions, f, indent=2)

    print("[5/5] All checks PASSED successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Check failed: {err}", file=sys.stderr)
        sys.exit(1)
