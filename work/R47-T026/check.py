#!/usr/bin/env python3
"""
work/R47-T026/check.py: Automated verification checker for bowling implementation comparison.

Requirements:
1. Resolve solution/test/example paths from exercises/practice/bowling/.meta/config.json.
2. Run the reference AND the alternative in isolated temp copies (including dotfiles).
3. Substitute implementation for solution file only in the temp copies.
4. Enable all test cases (xit( -> it() only in temp copies.
5. Run the exercise's package.json test script with watch mode disabled.
6. Assert child return code is 0, executed test count > 0, and print counts for both.
7. Assert the three named cases pass for both:
   - "should be able to score a game with all zeros"
   - "should be able to score a game with no strikes or spares"
   - "a spare followed by zeros is worth ten points"
8. Assert both implementations pass the exact same set of enabled test cases.
9. Assert learner stub is still unsolved and working tree is unmodified.
10. Save inputs, expected vs actual results and tool versions in work/R47-T026/.
11. Exit non-zero on any failed assertion.
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

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EX = REPO / "exercises/practice/bowling"
META_CFG = EX / ".meta/config.json"
TOML_PATH = EX / ".meta/tests.toml"
ALT_PATH = HERE / "alternative.ts"

NAMED_CASES = [
    "should be able to score a game with all zeros",
    "should be able to score a game with no strikes or spares",
    "a spare followed by zeros is worth ten points",
]

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
    for f in [META_CFG, TOML_PATH, EX / "package.json", ALT_PATH]:
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
    p_node = run_cmd(["node", "-v"], EX)
    v["node"] = p_node.stdout.strip()
    p_yarn = run_cmd(["corepack", "yarn", "-v"], EX)
    v["yarn"] = p_yarn.stdout.strip()
    p_corepack = run_cmd(["corepack", "-v"], EX)
    v["corepack"] = p_corepack.stdout.strip()
    return v


def run_implementation_test(impl_path: Path, tag: str, solution_rel: str, test_rel: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_copy = Path(tmp_dir) / "bowling"
        shutil.copytree(EX, tmp_copy, symlinks=True)

        # Substitute implementation into solution file only
        shutil.copyfile(impl_path, tmp_copy / solution_rel)

        # Enable all test cases
        test_file = tmp_copy / test_rel
        enabled = re.sub(r"\bxit\(", "it(", test_file.read_text())
        test_file.write_text(enabled)

        env = dict(os.environ, CI="1")

        # Install dependencies
        inst = run_cmd(["corepack", "yarn", "install", "--no-immutable"], tmp_copy, f"yarn-{tag}-install.log", env)
        check(inst.returncode == 0, f"[{tag}] yarn install succeeded (exit {inst.returncode})")

        # Run package test script
        pkg_test = run_cmd(["corepack", "yarn", "test"], tmp_copy, f"package-{tag}-test-run.log", env)
        check(pkg_test.returncode == 0, f"[{tag}] package.json test script exit code is 0 (got {pkg_test.returncode})")

        # Run jest with JSON output
        res_file = tmp_copy / f"jest-{tag}-results.json"
        jest_p = run_cmd(
            ["corepack", "yarn", "test:implementation", "--ci", "--watchAll=false", "--json", f"--outputFile={res_file}"],
            tmp_copy,
            f"jest-{tag}-run.log",
            env
        )
        check(jest_p.returncode == 0, f"[{tag}] jest exit code is 0 (got {jest_p.returncode})")

        if not res_file.exists():
            check(False, f"[{tag}] jest produced results JSON file")
            return {"total": 0, "passed": 0, "failed": 0, "assertions": {}}

        r = json.loads(res_file.read_text())
        total = r["numTotalTests"]
        passed = r["numPassedTests"]
        failed = r["numFailedTests"]

        assertions = {
            a["title"]: a["status"]
            for suite in r["testResults"]
            for a in suite["assertionResults"]
        }

        return {"total": total, "passed": passed, "failed": failed, "assertions": assertions}


def main() -> None:
    check_prerequisites()

    # 1. Collect tool versions
    versions = collect_tool_versions()
    (HERE / "versions.json").write_text(json.dumps(versions, indent=2) + "\n")
    print("Tool versions:", versions)

    # 2. Resolve paths from config.json
    cfg = json.loads(META_CFG.read_text())["files"]
    solution_rel = cfg["solution"][0]
    test_rel = cfg["test"][0]
    example_rel = cfg["example"][0]
    print(f"solution={solution_rel} test={test_rel} example={example_rel}")

    # Check tests.toml
    toml_data = tomllib.loads(TOML_PATH.read_text())
    expected_total = len(toml_data)
    check(expected_total > 0, f"tests.toml has {expected_total} canonical cases")

    # 3. Check learner stub is unsolved
    stub_path = EX / solution_rel
    check("Remove this line and implement the function" in stub_path.read_text(),
          "learner stub is unsolved in working tree")

    # 4. Check test file and solution in working tree are unmodified
    for rel in (solution_rel, test_rel, example_rel):
        diff = run_cmd(["git", "diff", "--quiet", "HEAD", "--", str((EX / rel).relative_to(REPO))], REPO)
        check(diff.returncode == 0, f"{rel} unchanged in working tree")

    wt_test_file = EX / test_rel
    wt_hash_before = __import__("hashlib").md5(wt_test_file.read_bytes()).hexdigest()

    # 5. Run Reference Implementation
    print("\n--- Running Reference Implementation ---")
    ref_results = run_implementation_test(EX / example_rel, "reference", solution_rel, test_rel)
    print(f"Reference: executed={ref_results['total']}, passed={ref_results['passed']}, failed={ref_results['failed']}")

    # 6. Run Alternative Implementation
    print("\n--- Running Alternative Implementation ---")
    alt_results = run_implementation_test(ALT_PATH, "alternative", solution_rel, test_rel)
    print(f"Alternative: executed={alt_results['total']}, passed={alt_results['passed']}, failed={alt_results['failed']}")

    # 7. Verification and Comparison Assertions
    print("\n--- Verifying Equivalence & Test Requirements ---")
    check(ref_results["total"] > 0, f"Reference executed > 0 tests (got {ref_results['total']})")
    check(alt_results["total"] > 0, f"Alternative executed > 0 tests (got {alt_results['total']})")

    check(ref_results["total"] == expected_total,
          f"Reference executed all {expected_total} tests (got {ref_results['total']})")
    check(alt_results["total"] == expected_total,
          f"Alternative executed all {expected_total} tests (got {alt_results['total']})")

    check(ref_results["passed"] == expected_total and ref_results["failed"] == 0,
          f"Reference passed all {expected_total} tests without failures")
    check(alt_results["passed"] == expected_total and alt_results["failed"] == 0,
          f"Alternative passed all {expected_total} tests without failures")

    # Verify named test cases
    for nc in NAMED_CASES:
        ref_st = ref_results["assertions"].get(nc)
        alt_st = alt_results["assertions"].get(nc)
        check(ref_st == "passed", f"Reference passed named case '{nc}' (got {ref_st})")
        check(alt_st == "passed", f"Alternative passed named case '{nc}' (got {alt_st})")

    # Verify both implementations agree on all test cases
    all_agreed = True
    disagreements = []
    for title, ref_status in ref_results["assertions"].items():
        alt_status = alt_results["assertions"].get(title)
        if ref_status != alt_status:
            all_agreed = False
            disagreements.append(f"{title}: ref={ref_status}, alt={alt_status}")

    check(all_agreed, "Both implementations agree on all enabled test cases")
    if disagreements:
        print("Disagreements found:", disagreements)

    # Save detailed results to JSON
    detailed_results = {
        "exercise": "exercises/practice/bowling",
        "reference_summary": {
            "executed": ref_results["total"],
            "passed": ref_results["passed"],
            "failed": ref_results["failed"]
        },
        "alternative_summary": {
            "executed": alt_results["total"],
            "passed": alt_results["passed"],
            "failed": alt_results["failed"]
        },
        "named_cases": [
            {
                "case": nc,
                "reference": ref_results["assertions"].get(nc),
                "alternative": alt_results["assertions"].get(nc)
            }
            for nc in NAMED_CASES
        ],
        "all_cases_agreement": all_agreed
    }
    (HERE / "results.json").write_text(json.dumps(detailed_results, indent=2) + "\n")

    # 8. Check working tree test file was not modified
    wt_hash_after = __import__("hashlib").md5(wt_test_file.read_bytes()).hexdigest()
    check(wt_hash_before == wt_hash_after, "working tree test file was not modified")

    print(f"\nResult: {'FAILED' if failures else 'BOTH APPROACHES PASSED'}")
    if failures:
        print("Failures:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
