#!/usr/bin/env python3
"""
R47-T022: Automated verification checker for the circular-buffer exercise.

Verifies:
  1. All 10 enabled exercise cases pass against the maintained reference (.meta/proof.ci.ts).
  2. The three required cases are present in the test file.
  3. The learner stub is still unsolved.
  4. Zero-test detection works.
  5. Assertion failure detection works.
  6. Child-process exit-code validation works.
  7. The working-tree test file is not modified by this checker.

Usage:
    python3 work/R47-T022/check.py
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

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EX = REPO / "exercises/practice/circular-buffer"
TOML_PATH = EX / ".meta/tests.toml"
META_CFG = EX / ".meta/config.json"

REQUIRED_CASES = [
    "reading an empty buffer throws a BufferEmptyError",
    "write and read back one item",
    "write and read back multiple items",
]

EXPECTED_TOTAL_TESTS = 10  # 10 tests in circular-buffer.test.ts
failures: list[str] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def check(ok: bool, msg: str) -> None:
    label = "PASS  " if ok else "FAIL  "
    print(label + msg)
    if not ok:
        failures.append(msg)


def check_prerequisites() -> None:
    """Report useful errors when dependencies are missing."""
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


def run(cmd: list[str], cwd: Path, log_name: str | None = None,
        env: dict | None = None) -> subprocess.CompletedProcess:
    """Run a command, optionally save output to a log file."""
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if log_name:
        log = HERE / log_name
        log.write_text(
            f"$ {' '.join(cmd)}\nexit={p.returncode}\n"
            f"--- stdout ---\n{p.stdout}\n"
            f"--- stderr ---\n{p.stderr}\n"
        )
    return p


def tool_versions() -> dict:
    """Collect tool versions."""
    v: dict = {"python": sys.version.split()[0]}
    p_node = run(["node", "-v"], EX, "version-node.log")
    v["node"] = p_node.stdout.strip()
    p_yarn = run(["corepack", "yarn", "-v"], EX, "version-yarn.log")
    v["yarn"] = p_yarn.stdout.strip()
    return v


def read_toml() -> dict:
    return tomllib.loads(TOML_PATH.read_text())


def parse_test_names(test_file: Path) -> list[tuple[str, str]]:
    """Return [(state, name)] from a .test.ts file."""
    content = test_file.read_text()
    return re.findall(r'(?:^|\n)\s*(it|xit)\(["\'](.+?)["\']', content)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    check_prerequisites()

    # 1. Tool versions
    versions = tool_versions()
    (HERE / "tool-versions.json").write_text(json.dumps(versions, indent=2) + "\n")
    print("Tool versions:", versions)

    # 2. Resolve paths from config.json
    cfg = json.loads(META_CFG.read_text())["files"]
    solution_rel = cfg["solution"][0]
    test_rel = cfg["test"][0]
    example_rel = cfg["example"][0]
    print(f"solution={solution_rel}  test={test_rel}  example={example_rel}")

    # Save inputs / config
    inputs = {
        "exercise": "exercises/practice/circular-buffer",
        "config": {"solution": solution_rel, "test": test_rel, "example": example_rel},
        "required_cases": REQUIRED_CASES,
        "expected_total_tests": EXPECTED_TOTAL_TESTS,
        "package_test_script": json.loads((EX / "package.json").read_text())["scripts"]["test"],
    }
    (HERE / "test-inputs-and-config.json").write_text(json.dumps(inputs, indent=2) + "\n")

    # 3. TOML analysis
    toml_data = read_toml()
    included = sum(1 for v in toml_data.values() if v.get("include", True))
    excluded = len(toml_data) - included
    print(f"tests.toml: total={len(toml_data)}  included={included}  excluded={excluded}")
    check(len(toml_data) == 14, f"tests.toml has 14 canonical entries (got {len(toml_data)})")

    # 4. Test file analysis (working-tree copy — NOT modified)
    wt_test = EX / test_rel
    wt_hash_before = __import__("hashlib").md5(wt_test.read_bytes()).hexdigest()
    test_items = parse_test_names(wt_test)
    total_tests = len(test_items)
    active_tests = [n for s, n in test_items if s == "it"]
    skipped_tests = [n for s, n in test_items if s == "xit"]

    print(f"Test file: total={total_tests}  active={len(active_tests)}  skipped={len(skipped_tests)}")
    check(total_tests == EXPECTED_TOTAL_TESTS,
          f"test file has {EXPECTED_TOTAL_TESTS} tests (got {total_tests})")

    for case in REQUIRED_CASES:
        present = any(n == case for _, n in test_items)
        check(present, f"required case present: {case!r}")

    # 5. Learner stub is still unsolved
    stub_path = EX / solution_rel
    stub_text = stub_path.read_text()
    check("Remove this line and implement the function" in stub_text,
          "learner stub still unsolved")

    # Verify working-tree test and solution files are unmodified
    for rel in (solution_rel, test_rel):
        p = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", str((EX / rel).relative_to(REPO))],
            cwd=REPO,
        )
        check(p.returncode == 0, f"{rel} unchanged in working tree")

    # 6. Isolated temp-directory run with reference substituted
    pkg_script = json.loads((EX / "package.json").read_text())["scripts"]["test"]
    print(f"\nPackage test script: {pkg_script}")

    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "circular-buffer"
        shutil.copytree(EX, copy, symlinks=True)  # includes hidden dirs

        # Substitute proof.ci.ts → solution (only inside temp copy)
        shutil.copyfile(EX / example_rel, copy / solution_rel)

        # Enable all test cases: xit( → it(
        t = copy / test_rel
        enabled = re.sub(r"\bxit\(", "it(", t.read_text())
        t.write_text(enabled)
        n_active = len(re.findall(r"\bit\(", enabled))
        check(n_active == EXPECTED_TOTAL_TESTS,
              f"{n_active} cases enabled in temp copy (expected {EXPECTED_TOTAL_TESTS})")

        env = dict(os.environ, CI="1")

        # Install deps
        # --no-immutable: the exercise's yarn.lock is empty (0 bytes), so resolution
        # would update it. CI=1 normally enforces immutability (YN0028); we override
        # here because we are running in an isolated temp copy, not the working tree.
        inst = run(["corepack", "yarn", "install", "--no-immutable"], copy, "yarn-install.log", env)
        check(inst.returncode == 0,
              f"yarn install succeeded (exit {inst.returncode})")

        # Run the actual package.json test script
        pkg_test = run(["corepack", "yarn", "test"], copy, "package-test-run.log", env)
        check(pkg_test.returncode == 0,
              f"package.json 'test' script exit code 0 (got {pkg_test.returncode})")

        # Also run jest with --json for detailed assertion-level counts
        res_file = copy / "jest-results.json"
        jest_p = run(
            ["corepack", "yarn", "test:implementation", "--ci", "--watchAll=false",
             "--json", f"--outputFile={res_file}"],
            copy, "jest-run.log", env,
        )
        check(jest_p.returncode == 0,
              f"jest exit code 0 (got {jest_p.returncode})")

        if res_file.exists():
            shutil.copyfile(res_file, HERE / "jest-results.json")
            r = json.loads(res_file.read_text())
            total = r["numTotalTests"]
            passed = r["numPassedTests"]
            failed = r["numFailedTests"]
            pending = r["numPendingTests"]
            print(f"\njest results: executed={total} passed={passed} failed={failed} pending={pending}")
            check(total > 0, "test run executed more than zero tests")
            check(total == EXPECTED_TOTAL_TESTS,
                  f"all {EXPECTED_TOTAL_TESTS} cases executed (got {total})")
            check(passed == EXPECTED_TOTAL_TESTS,
                  f"all {EXPECTED_TOTAL_TESTS} cases passed (got {passed})")
            check(failed == 0, f"no assertion failures (failed={failed})")
            check(pending == 0, f"no pending tests (pending={pending})")

            # Verify the three required cases
            by_name = {
                a["title"]: a["status"]
                for suite in r["testResults"]
                for a in suite["assertionResults"]
            }
            rows = []
            for case in REQUIRED_CASES:
                actual = by_name.get(case)
                rows.append({"test": case, "expected": "passed", "actual": actual})
                check(actual == "passed", f"required case passed: {case!r}")
            (HERE / "expected-vs-actual.json").write_text(json.dumps(rows, indent=2) + "\n")
        else:
            check(False, "jest produced a results JSON file")

    # 7. Confirm working-tree test file was NOT modified
    wt_hash_after = __import__("hashlib").md5(wt_test.read_bytes()).hexdigest()
    check(wt_hash_before == wt_hash_after,
          "working-tree test file not modified by this checker")

    # 8. Summary
    print(f"\nRESULT: {'FAILED' if failures else 'ALL CHECKS PASSED'}")
    if failures:
        print("Failures:")
        for f in failures:
            print(f"  - {f}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

