#!/usr/bin/env python3
"""Isolated reference runner for ocr-numbers (R47-T049).

Runs the ocr-numbers exercise tests against the maintained reference
(`.meta/proof.ci.ts`, as declared in `.meta/config.json`) without ever
touching the learner files in the working tree:

  * the exercise is copied, including dotfiles, into a temporary
    directory that is always deleted afterwards;
  * the reference replaces the solution file **in that copy only**;
  * every test case is enabled in the copy (the same transformation
    the track's own test-runner.mjs performs);
  * the tests run via the exercise package.json test script (Yarn as
    pinned), falling back to the equivalent npm/tsc/Jest steps the
    track runner itself performs when Yarn cannot run;
  * the learner files in the real exercise directory are hashed
    before and after the run and must be byte-identical;
  * the exit code is 0 only when at least one test executed and all
    of them passed — a zero-test run, a failing assertion or a
    non-zero child exit all propagate as failure.

Usage:
  python3 tools/course_checks/r47-t049.py [path-to-exercise-dir]
  python3 tools/course_checks/r47-t049.py --self-test

`--self-test` additionally runs two sabotage scenarios and requires
both to fail with a non-zero exit while the learner files stay
untouched: a deliberately wrong reference, and an empty test
selection (a Jest name filter that matches nothing).
"""

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BROKEN_REFERENCE = (
    "export function convert(_text: string): string {\n"
    "  return 'deliberately-wrong'\n"
    "}\n"
)
EMPTY_SELECTION = "__no_such_test_name__"


def run(cmd, cwd, timeout=900):
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )
    return proc.returncode, proc.stdout + proc.stderr


def hash_solutions(exercise: Path, solutions: list[str]) -> dict[str, str]:
    hashes = {}
    for rel in solutions:
        target = exercise / rel
        hashes[rel] = hashlib.sha256(target.read_bytes()).hexdigest()
    return hashes


def enable_all_tests(test_path: Path) -> None:
    text = test_path.read_text()
    text = re.sub(r"\bx(test|it)\(", r"\1(", text)
    text = re.sub(r"\bxdescribe\(", "describe(", text)
    text = re.sub(r"\bx(test|it|describe), ", r"\1, ", text)
    text = re.sub(r", x(test|it|describe)}", r", \1}", text)
    test_path.write_text(text)


def parse_summary(output: str):
    match = re.findall(
        r"Tests:\s+(?:(\d+) failed,?\s*)?(?:(\d+) skipped,?\s*)?(?:(\d+) passed,?\s*)?(\d+) total",
        output,
    )
    if not match:
        return 0, 0, 0, 0
    failed, skipped, passed, total = (int(g or 0) for g in match[-1])
    return total, passed, failed, skipped


def run_once(exercise: Path, mode: str = "reference") -> dict:
    """One isolated run. mode: reference | broken | empty."""
    config = json.loads((exercise / ".meta" / "config.json").read_text())
    files = config["files"]
    solutions = files["solution"]
    tests = files["test"]
    examples = files["example"]

    before = hash_solutions(exercise, solutions)
    result = {"mode": mode, "cleaned_up": False}
    tmp = Path(tempfile.mkdtemp(prefix="r47-t049-"))
    try:
        work = tmp / "exercise"
        shutil.copytree(
            exercise,
            work,
            ignore=shutil.ignore_patterns("node_modules"),
            symlinks=False,
        )
        for test_rel in tests:
            enable_all_tests(work / test_rel)

        if mode == "broken":
            for solution_rel in solutions:
                (work / solution_rel).write_text(BROKEN_REFERENCE)
        else:
            for solution_rel, example_rel in zip(solutions, examples):
                content = (work / example_rel).read_text()
                content = content.replace("from '../", "from './")
                (work / solution_rel).write_text(content)

        total = passed = failed = skipped = 0
        runner = None
        code, out = 1, ""
        if mode != "empty":
            # The empty-selection scenario needs a Jest name filter,
            # which the package test script does not take; it goes
            # straight to the Jest route below.
            code, out = run(["corepack", "yarn", "install"], cwd=work)
            if code == 0:
                code, out = run(["corepack", "yarn", "test"], cwd=work)
                total, passed, failed, skipped = parse_summary(out)
                runner = "corepack yarn test"
        if total == 0:
            code, out = run(["npm", "install", "--no-audit", "--no-fund"], cwd=work)
            if code == 0:
                tsc_code, tsc_out = run(["npx", "tsc", "--noEmit", "-p", "."], cwd=work)
                out += tsc_out
                if tsc_code == 0:
                    cmd = ["npx", "jest", "--no-cache"]
                    if mode == "empty":
                        cmd += ["-t", EMPTY_SELECTION]
                    code, jest_out = run(cmd, cwd=work)
                    out += jest_out
                    total, passed, failed, skipped = parse_summary(out)
                    runner = "npm install + tsc + jest"
        result.update(
            {
                "runner": runner,
                "tests_total": total,
                "tests_passed": passed,
                "tests_failed": failed,
                "tests_skipped": skipped,
                "child_exit": code,
            }
        )
        executed = passed + failed
        success = executed > 0 and failed == 0 and code == 0
        result["exit"] = 0 if success else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        result["cleaned_up"] = not tmp.exists()

    after = hash_solutions(exercise, solutions)
    result["learner_files_unchanged"] = before == after
    if not result["learner_files_unchanged"]:
        result["exit"] = 1
    return result


def default_exercise() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "exercises/practice/ocr-numbers"
    )


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    exercise = Path(args[0]) if args else default_exercise()

    if "--self-test" in sys.argv:
        report = {
            "reference": run_once(exercise, "reference"),
            "broken_reference": run_once(exercise, "broken"),
            "empty_selection": run_once(exercise, "empty"),
        }
        expectations = {
            "reference": 0,
            "broken_reference": 1,
            "empty_selection": 1,
        }
        ok = all(
            report[name]["exit"] == expected
            and report[name]["learner_files_unchanged"]
            and report[name]["cleaned_up"]
            for name, expected in expectations.items()
        )
        report["self_test"] = "PASS" if ok else "FAIL"
        print(json.dumps(report, indent=2))
        return 0 if ok else 1

    result = run_once(exercise, "reference")
    print(json.dumps(result, indent=2))
    return result["exit"]


if __name__ == "__main__":
    sys.exit(main())
