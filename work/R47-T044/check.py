#!/usr/bin/env python3
"""Automated check for R47-T044 (pangram).

Runs the pangram exercise tests against the maintained reference
implementation (.meta/proof.ci.ts) in a temporary copy of the exercise,
so the working tree — in particular the learner stub — is never touched.

What it does:
  1. Resolves solution / test / example paths from
     exercises/practice/pangram/.meta/config.json.
  2. Copies the whole exercise (including dotfiles) to a temp directory.
  3. Substitutes the reference example over the solution file(s) in the
     copy only, adjusting relative imports the way the track CI does
     ("from '../" -> "from './").
  4. Enables every exercise case in the copied tests (xit/xtest ->
     it/test, xdescribe -> describe), mirroring scripts/helpers.mjs.
  5. Runs the exercise package.json test script
     (`corepack yarn test`, watch mode disabled via CI=true). If that
     route cannot execute any test in this environment (for example a
     registry/network failure during `yarn install`), it falls back to
     the identical steps test-runner.mjs performs — `tsc --noEmit -p .`
     then `jest --no-cache` — with dependencies installed by npm, and
     records which route produced the results.
  6. Fails (exit non-zero) when the test child process exits non-zero,
     when zero tests are executed, or when any test fails.
  7. Saves the tool versions, the test counts (expected vs actual) and
     the full test output as evidence next to this script.

Usage: python3 work/R47-T044/check.py
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK_ID = "R47-T044"
EXERCISE = Path("exercises/practice/pangram")

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = Path(__file__).resolve().parent


def run(cmd, cwd):
    env = dict(os.environ)
    env.update({"CI": "true"})
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc.returncode, proc.stdout


def tool_version(cmd):
    try:
        code, out = run(cmd, cwd=ROOT)
        return out.strip().splitlines()[0] if out.strip() else "unknown"
    except Exception as exc:  # pragma: no cover
        return f"unavailable ({exc})"


def enable_tests(path: Path) -> None:
    """Enable xit/xtest/xdescribe cases, mirroring scripts/helpers.mjs."""
    text = path.read_text()
    text = re.sub(r"x(test|it)\(", r"it(", text)
    text = re.sub(r"xdescribe\(", r"describe(", text)
    text = re.sub(r"x(test|it|describe), ?", r"", text)
    text = re.sub(r", ?x(test|it|describe) ?}", r"}", text)
    path.write_text(text)


def parse_jest_summary(out: str):
    total = passed = failed = skipped = 0
    for line in out.splitlines():
        m = re.match(r"\s*Tests:\s+(.*)", line)
        if m:
            for amount, kind in re.findall(
                r"(\d+)\s+(failed|passed|skipped|total)", m.group(1)
            ):
                if kind == "failed":
                    failed = int(amount)
                elif kind == "passed":
                    passed = int(amount)
                elif kind == "skipped":
                    skipped = int(amount)
                elif kind == "total":
                    total = int(amount)
    return total, passed, failed, skipped


def main() -> int:
    exercise_dir = ROOT / EXERCISE
    config = json.loads((exercise_dir / ".meta" / "config.json").read_text())
    files = config["files"]
    solutions = files["solution"]
    tests = files["test"]
    examples = files["example"]

    failures = []
    log_parts = []
    runner_used = None
    total = passed = failed = skipped = 0

    versions = {
        "node": tool_version(["node", "--version"]),
        "yarn": tool_version(["corepack", "yarn", "--version"]),
        "npm": tool_version(["npm", "--version"]),
        "python": sys.version.split()[0],
    }
    log_parts.append(f"tool versions: {versions}")

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-") as tmp:
        work = Path(tmp) / "exercise"
        shutil.copytree(exercise_dir, work, symlinks=True)

        # Substitute the reference example over the solution file(s),
        # in the temporary copy only.
        for example_rel, solution_rel in zip(examples, solutions):
            src = work / example_rel
            dst = work / solution_rel
            content = src.read_text()
            content = content.replace("from '../", "from './").replace(
                'from "../', 'from "./'
            )
            dst.write_text(content)
            log_parts.append(f"substituted {example_rel} -> {solution_rel}")

        # Enable all exercise cases in the copied test files.
        for test_rel in tests:
            enable_tests(work / test_rel)
            log_parts.append(f"enabled all cases in {test_rel}")

        # Primary route: the exercise package.json test script via Yarn.
        code, out = run(["corepack", "yarn", "install"], cwd=work)
        log_parts.append(f"$ corepack yarn install (exit {code})\n{out}")
        if code == 0:
            code, out = run(["corepack", "yarn", "test"], cwd=work)
            log_parts.append(f"$ corepack yarn test (exit {code})\n{out}")
            total, passed, failed, skipped = parse_jest_summary(out)
            if total > 0:
                runner_used = "corepack yarn test (package.json test script)"
                if code != 0:
                    failures.append(f"test run exited {code}")
            else:
                log_parts.append("yarn route executed no tests; trying fallback")

        # Fallback route: npm install + the same steps test-runner.mjs
        # performs (tsc type check, then Jest).
        if runner_used is None:
            code, out = run(["npm", "install", "--no-audit", "--no-fund"], cwd=work)
            log_parts.append(f"$ npm install (exit {code})\n{out}")
            if code != 0:
                failures.append(f"npm install exited {code}")
            else:
                code, out = run(["npx", "tsc", "--noEmit", "-p", "."], cwd=work)
                log_parts.append(f"$ npx tsc --noEmit -p . (exit {code})\n{out}")
                if code != 0:
                    failures.append(f"tsc exited {code}")
                code, out = run(["npx", "jest", "--no-cache"], cwd=work)
                log_parts.append(f"$ npx jest --no-cache (exit {code})\n{out}")
                total, passed, failed, skipped = parse_jest_summary(out)
                if total > 0:
                    runner_used = "npm install + tsc + jest (test-runner steps)"
                    if code != 0:
                        failures.append(f"jest exited {code}")

        log_parts.append(
            f"jest summary: total={total} passed={passed} failed={failed} skipped={skipped}"
        )

        if runner_used is None:
            failures.append("no test route executed any tests")
        if total == 0:
            failures.append("zero tests were executed")
        if failed != 0:
            failures.append(f"{failed} test(s) failed")
        if total > 0 and passed + skipped != total:
            failures.append(
                f"test counts do not add up: passed {passed} + skipped {skipped} != total {total}"
            )

    evidence = {
        "task": TASK_ID,
        "exercise": str(EXERCISE),
        "reference_substituted": dict(zip(solutions, examples)),
        "tool_versions": versions,
        "runner_used": runner_used,
        "expected": "all enabled exercise cases pass against the reference",
        "actual": {
            "tests_total": total,
            "tests_passed": passed,
            "tests_failed": failed,
            "tests_skipped": skipped,
        },
        "failures": failures,
        "result": "PASS" if not failures else "FAIL",
    }

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "results.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (EVIDENCE_DIR / "test-output.txt").write_text("\n".join(log_parts) + "\n")
    (EVIDENCE_DIR / "RESULTS.md").write_text(
        f"# {TASK_ID} check results\n\n"
        f"- Exercise: `{EXERCISE}`\n"
        f"- Reference: {', '.join(examples)} substituted for {', '.join(solutions)} "
        f"in a temporary copy only; the learner stub in the working tree is unchanged.\n"
        f"- Runner: {runner_used}\n"
        f"- Tool versions: node {versions['node']}, yarn {versions['yarn']}, "
        f"npm {versions['npm']}, python {versions['python']}\n"
        f"- Expected: all enabled exercise cases pass against the reference.\n"
        f"- Actual: {passed} passed, {failed} failed, {skipped} skipped, "
        f"{total} total.\n"
        f"- Result: **{evidence['result']}**\n"
        + ("" if not failures else "\nFailures:\n" + "\n".join(f"- {f}" for f in failures) + "\n")
    )

    print(json.dumps(evidence, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
