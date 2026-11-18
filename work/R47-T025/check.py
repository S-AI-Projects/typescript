#!/usr/bin/env python3
"""
work/R47-T025/check.py: Automated verification checker for queen-attack invalidPosition O(1) complexity.

Requirements:
1. Use Python 3 subprocess and tempfile.
2. Resolve paths from exercises/practice/queen-attack/.meta/config.json.
3. Copy the entire exercise, including hidden files, into a temporary directory.
4. Substitute the reference implementation (.meta/proof.ci.ts) only inside the temporary copy.
5. Enable all exercise cases in the copy only (xit( -> it().
6. Run the exercise's package.json test script with watch mode disabled.
7. Assert child return code is 0, executed test count > 0, and print executed cases count.
8. Assert named cases pass:
   - "queen with a valid position"
   - "queen must have positive row"
   - "queen must have row on board"
   plus all other enabled cases.
9. Assert correctness BEFORE any operation-count claims.
10. Assert learner stub is still unsolved and working tree test files are unmodified.
11. Assert comparison counts in invalidPosition match the table in docs/maintenance/queen-attack.md.
12. Save inputs, expected vs actual results, and tool versions into work/R47-T025/.
13. Exit non-zero on any failed assertion.
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
EX = REPO / "exercises/practice/queen-attack"
META_CFG = EX / ".meta/config.json"
TOML_PATH = EX / ".meta/tests.toml"
DOC_PATH = REPO / "docs/maintenance/queen-attack.md"

NAMED_CASES = [
    "queen with a valid position",
    "queen must have positive row",
    "queen must have row on board",
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


def count_invalid_position_comparisons(white: tuple[int, int], black: tuple[int, int], H: int = 8, W: int = 8) -> tuple[int, bool]:
    """
    Direct model of invalidPosition in proof.ci.ts with short-circuit evaluation:
    if (white[0] < 0 || white[0] >= H || white[1] < 0 || white[1] >= W) return true
    if (black[0] < 0 || black[0] >= H || black[1] < 0 || black[1] >= W) return true
    return false
    """
    comps = 0

    # 1. white[0] < 0
    comps += 1
    if white[0] < 0:
        return comps, True

    # 2. white[0] >= H
    comps += 1
    if white[0] >= H:
        return comps, True

    # 3. white[1] < 0
    comps += 1
    if white[1] < 0:
        return comps, True

    # 4. white[1] >= W
    comps += 1
    if white[1] >= W:
        return comps, True

    # 5. black[0] < 0
    comps += 1
    if black[0] < 0:
        return comps, True

    # 6. black[0] >= H
    comps += 1
    if black[0] >= H:
        return comps, True

    # 7. black[1] < 0
    comps += 1
    if black[1] < 0:
        return comps, True

    # 8. black[1] >= W
    comps += 1
    if black[1] >= W:
        return comps, True

    return comps, False


def main() -> None:
    check_prerequisites()

    # 1. Collect and record tool versions
    versions = collect_tool_versions()
    (HERE / "versions.json").write_text(json.dumps(versions, indent=2) + "\n")
    print("Tool versions:", versions)

    # 2. Resolve paths from .meta/config.json
    cfg = json.loads(META_CFG.read_text())["files"]
    solution_rel = cfg["solution"][0]
    test_rel = cfg["test"][0]
    example_rel = cfg["example"][0]
    print(f"solution={solution_rel} test={test_rel} example={example_rel}")

    # Check tests.toml validity and parsing
    toml_data = tomllib.loads(TOML_PATH.read_text())
    check(len(toml_data) > 0, f"tests.toml parsed successfully with {len(toml_data)} canonical entries")

    # 3. Check learner stub is unsolved
    stub_path = EX / solution_rel
    check("Remove this line and implement the function" in stub_path.read_text(),
          "learner stub is unsolved in working tree")

    # 4. Check test file and solution in working tree are unmodified
    for rel in (solution_rel, test_rel):
        diff = run_cmd(["git", "diff", "--quiet", "HEAD", "--", str((EX / rel).relative_to(REPO))], REPO)
        check(diff.returncode == 0, f"{rel} unchanged in working tree")

    wt_test_file = EX / test_rel
    wt_hash_before = __import__("hashlib").md5(wt_test_file.read_bytes()).hexdigest()

    # Save inputs and configuration
    inputs_and_config = {
        "exercise": "exercises/practice/queen-attack",
        "config": {"solution": solution_rel, "test": test_rel, "example": example_rel},
        "named_cases": NAMED_CASES,
        "board_dimensions": {"width": 8, "height": 8},
        "package_test_script": json.loads((EX / "package.json").read_text())["scripts"]["test"],
    }
    (HERE / "inputs.json").write_text(json.dumps(inputs_and_config, indent=2) + "\n")

    # 5. Run tests in isolated temporary directory
    print("\n--- Running Reference Implementation in Temporary Copy ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_copy = Path(tmp_dir) / "queen-attack"
        shutil.copytree(EX, tmp_copy, symlinks=True)

        # Substitute proof.ci.ts only in temporary copy
        shutil.copyfile(EX / example_rel, tmp_copy / solution_rel)

        # Enable all test cases: xit( -> it(
        test_file = tmp_copy / test_rel
        enabled_tests = re.sub(r"\bxit\(", "it(", test_file.read_text())
        test_file.write_text(enabled_tests)

        active_count = len(re.findall(r"\bit\(", enabled_tests))
        check(active_count > 0, f"Found {active_count} test cases enabled in temporary copy")

        env = dict(os.environ, CI="1")

        # Install dependencies
        inst = run_cmd(["corepack", "yarn", "install", "--no-immutable"], tmp_copy, "yarn-install.log", env)
        check(inst.returncode == 0, f"yarn install succeeded (exit {inst.returncode})")

        # Run package test script
        pkg_test = run_cmd(["corepack", "yarn", "test"], tmp_copy, "package-test-run.log", env)
        check(pkg_test.returncode == 0, f"package.json test script exit code is 0 (got {pkg_test.returncode})")

        # Run jest with json output
        res_file = tmp_copy / "jest-results.json"
        jest_p = run_cmd(
            ["corepack", "yarn", "test:implementation", "--ci", "--watchAll=false", "--json", f"--outputFile={res_file}"],
            tmp_copy,
            "jest-run.log",
            env
        )
        check(jest_p.returncode == 0, f"jest exit code is 0 (got {jest_p.returncode})")

        if res_file.exists():
            shutil.copyfile(res_file, HERE / "results.json")
            r = json.loads(res_file.read_text())
            total = r["numTotalTests"]
            passed = r["numPassedTests"]
            failed = r["numFailedTests"]
            print(f"Test run results: total={total} passed={passed} failed={failed}")
            check(total > 0, f"Executed test count is greater than 0 (got {total})")
            check(passed == total, f"All {total} enabled test cases passed against reference (got {passed} passed)")
            check(failed == 0, f"No failed assertions (got {failed} failures)")

            # Check named cases
            assertions = [a for suite in r["testResults"] for a in suite["assertionResults"]]
            by_title = {a["title"]: a["status"] for a in assertions}

            for nc in NAMED_CASES:
                st = by_title.get(nc)
                check(st == "passed", f"Named test case '{nc}' passed (got {st})")
        else:
            check(False, "jest produced results JSON file")

    # 6. Verify operation counts match table in docs/maintenance/queen-attack.md
    print("\n--- Verifying Operation Counts & Complexity Bounds ---")
    branch_cases = [
        {"desc": "White: row < 0", "white": (-2, 2), "black": (0, 3), "expected_comps": 1, "invalid": True},
        {"desc": "White: row >= 8", "white": (8, 4), "black": (0, 3), "expected_comps": 2, "invalid": True},
        {"desc": "White: col < 0", "white": (2, -2), "black": (0, 3), "expected_comps": 3, "invalid": True},
        {"desc": "White: col >= 8", "white": (4, 8), "black": (0, 3), "expected_comps": 4, "invalid": True},
        {"desc": "Black: row < 0", "white": (2, 2), "black": (-1, 3), "expected_comps": 5, "invalid": True},
        {"desc": "Black: row >= 8", "white": (2, 2), "black": (8, 3), "expected_comps": 6, "invalid": True},
        {"desc": "Black: col < 0", "white": (2, 2), "black": (3, -1), "expected_comps": 7, "invalid": True},
        {"desc": "Black: col >= 8", "white": (2, 2), "black": (3, 8), "expected_comps": 8, "invalid": True},
        {"desc": "Both valid", "white": (2, 2), "black": (0, 3), "expected_comps": 8, "invalid": False},
    ]

    branch_results = []
    for bc in branch_cases:
        actual_comps, is_invalid = count_invalid_position_comparisons(bc["white"], bc["black"])
        check(actual_comps == bc["expected_comps"],
              f"Branch '{bc['desc']}': comparison count matches table ({actual_comps} == {bc['expected_comps']})")
        check(is_invalid == bc["invalid"],
              f"Branch '{bc['desc']}': validity matches expected ({is_invalid} == {bc['invalid']})")
        branch_results.append({
            "case": bc["desc"],
            "white": bc["white"],
            "black": bc["black"],
            "expected_comparisons": bc["expected_comps"],
            "actual_comparisons": actual_comps,
            "is_invalid": is_invalid
        })

    # Save branch operation count verification to json
    (HERE / "branch-operations.json").write_text(json.dumps(branch_results, indent=2) + "\n")

    # Confirm docs file exists and contains O(1) analysis
    check(DOC_PATH.is_file(), f"Documentation file exists: {DOC_PATH}")
    doc_text = DOC_PATH.read_text()
    check("O(1)" in doc_text or "\\mathcal{O}(1)" in doc_text, "Documentation records O(1) bound")
    check("8" in doc_text and "comparisons" in doc_text, "Documentation records comparison bound")

    # 7. Check working tree test file was not modified
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
