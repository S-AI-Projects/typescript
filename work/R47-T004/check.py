#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

EXERCISE_DIR = "exercises/practice/linked-list"
NAMED_CASES = [
    "add/extract elements to the end of the list with push/pop",
    "extract elements from the beginning of the list with shift",
    "add/extract elements from the beginning of the list with unshift/shift",
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


def run_tests_in_sandbox(config_path):
    print("[2/4] Running automated tests in temporary copy...")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    solution_rel = config["files"]["solution"][0]
    test_rel = config["files"]["test"][0]
    example_rel = config["files"]["example"][0]

    with tempfile.TemporaryDirectory(dir=".") as tmpdir:
        temp_exercise = os.path.join(tmpdir, "linked-list")
        shutil.copytree(EXERCISE_DIR, temp_exercise)

        shutil.copy(
            os.path.join(temp_exercise, example_rel),
            os.path.join(temp_exercise, solution_rel),
        )

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

        if proc.returncode != 0:
            print(f"Child process failed:\n{output}")
            raise AssertionError(f"Jest failed with exit code {proc.returncode}")

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
        print(f"  Test results: {len(passed)}/{total} passed, {len(failed)} failed.")

        if total == 0:
            raise AssertionError("Zero-test run: no tests were executed!")
        if len(failed) > 0:
            raise AssertionError(f"{len(failed)} tests failed!")

        for named in NAMED_CASES:
            if named not in passed:
                raise AssertionError(f"Named case '{named}' was not among passed tests: {passed}")
            print(f"  ✓ Passed named case: '{named}'")

        return {
            "total_executed": total,
            "passed": len(passed),
            "failed": len(failed),
            "executed_titles": passed,
        }


def check_readability_diff():
    print("[3/4] Verifying readability refactor and invariant documentation...")
    proof_path = os.path.join(EXERCISE_DIR, ".meta/proof.ci.ts")
    with open(proof_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "Exercise-specific invariant:" not in content:
        raise AssertionError("Invariant documentation comment missing from proof.ci.ts")
    if "public readonly value: T" not in content:
        raise AssertionError("Concise parameter property refactor missing from Node constructor")
    print("  ✓ Node refactored to concise constructor parameter properties with invariant docs.")


def main():
    print("=== Running R47-T004 Automated Check ===")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    tool_versions = get_tool_versions()

    # 1. Learner stub check
    check_learner_stub(os.path.join(EXERCISE_DIR, "linked-list.ts"))

    # 2. Refactor verification
    check_readability_diff()

    # 3. Test execution in isolated copy
    test_results = run_tests_in_sandbox(os.path.join(EXERCISE_DIR, ".meta/config.json"))

    # 4. Save results and evidence
    print(f"[4/4] Saving evidence to {work_dir}...")
    evidence = {
        "task_id": "R47-T004",
        "exercise": "exercises/practice/linked-list",
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
