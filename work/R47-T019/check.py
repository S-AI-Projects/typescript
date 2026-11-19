#!/usr/bin/env python3
"""
check.py — Verification script for Word Count Isolated Runner (R47-T019)
-----------------------------------------------------------------------
Verifies that tools/course_checks/r47-t019.py behaves correctly across
three distinct scenarios:
  1. Real reference (.meta/proof.ci.ts) -> MUST PASS (14/14 tests)
  2. Deliberately failing reference -> MUST FAIL (non-zero exit)
  3. Empty test selection -> MUST FAIL (zero-test detection, non-zero exit)

Crucially verifies that the learner solution file (word-count.ts)
SHA256 hash remains 100% IDENTICAL before and after every scenario.

Writes test inputs, expected/actual results, tool versions, and logs
to work/R47-T019/evidence.md.
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "word-count"
LEARNER_SOLUTION = EXERCISE_DIR / "word-count.ts"
RUNNER_SCRIPT = REPO_ROOT / "tools" / "course_checks" / "r47-t019.py"
FAILING_REF = SCRIPT_DIR / "failing_reference.ts"
EVIDENCE_FILE = SCRIPT_DIR / "evidence.md"


def get_file_sha256(path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def run_command(
    command: List[str], cwd: Path, env: Dict[str, str]
) -> Tuple[Optional[int], str, str]:
    """Runs a command and returns (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except OSError as err:
        return None, "", str(err)


def get_version(command: List[str], env: Dict[str, str]) -> str:
    returncode, stdout, stderr = run_command(command, REPO_ROOT, env)
    if returncode == 0:
        lines = stdout.strip().splitlines()
        return lines[0] if lines else "unknown"
    return "unknown"


def main() -> int:
    print("==================================================")
    print("R47-T019 Word Count Runner Verification")
    print("==================================================")

    if not LEARNER_SOLUTION.is_file():
        print(f"[FAIL] Learner solution missing at: {LEARNER_SOLUTION}", file=sys.stderr)
        return 1

    if not RUNNER_SCRIPT.is_file():
        print(f"[FAIL] Runner script missing at: {RUNNER_SCRIPT}", file=sys.stderr)
        return 1

    if not FAILING_REF.is_file():
        print(f"[FAIL] Failing reference missing at: {FAILING_REF}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env["CI"] = "true"
    env["FORCE_COLOR"] = "0"

    python_version = get_version(["python3", "--version"], env)
    node_version = get_version(["node", "--version"], env)
    yarn_version = get_version(["corepack", "yarn", "--version"], env)

    print(f"Python:  {python_version}")
    print(f"Node.js: {node_version}")
    print(f"Yarn:    {yarn_version}")

    initial_hash = get_file_sha256(LEARNER_SOLUTION)
    print(f"\nInitial word-count.ts SHA256: {initial_hash}")

    scenarios = [
        {
            "id": "scenario_1",
            "name": "Scenario 1: Real Reference Implementation",
            "description": "Runs r47-t019.py with canonical .meta/proof.ci.ts",
            "cmd": ["python3", str(RUNNER_SCRIPT)],
            "expected_success": True,
            "expected_exit_code": 0,
        },
        {
            "id": "scenario_2",
            "name": "Scenario 2: Deliberately Failing Reference",
            "description": "Runs r47-t019.py with a reference returning an empty Map",
            "cmd": [
                "python3",
                str(RUNNER_SCRIPT),
                "--reference",
                str(FAILING_REF),
            ],
            "expected_success": False,
            "expected_exit_code": 1,
        },
        {
            "id": "scenario_3",
            "name": "Scenario 3: Empty Test Selection",
            "description": "Runs r47-t019.py with --empty-tests (0 tests executed)",
            "cmd": ["python3", str(RUNNER_SCRIPT), "--empty-tests"],
            "expected_success": False,
            "expected_exit_code": 1,
        },
    ]

    all_assertions_passed = True
    results_records = []

    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        print(f"Description: {scenario['description']}")
        print(f"Command:     {' '.join(scenario['cmd'])}")

        rc, out, err = run_command(scenario["cmd"], REPO_ROOT, env)
        combined = (out or "") + "\n" + (err or "")
        print(f"Exit code:   {rc}")

        # Check hash immediately after scenario
        post_hash = get_file_sha256(LEARNER_SOLUTION)
        hash_matched = (post_hash == initial_hash)
        print(f"Hash check:  {'MATCHED' if hash_matched else 'CHANGED!'}")
        if not hash_matched:
            print(
                f"[CRITICAL ERROR] Learner stub word-count.ts was modified during {scenario['name']}!",
                file=sys.stderr,
            )
            all_assertions_passed = False

        # Validate scenario expectations
        if scenario["expected_success"]:
            scenario_passed = (rc == 0) and ("14/14" in combined or "Success:      True" in combined)
        else:
            scenario_passed = (rc != 0)

        status_str = "PASS" if (scenario_passed and hash_matched) else "FAIL"
        if not scenario_passed:
            all_assertions_passed = False
            print(f"[FAIL] {scenario['name']} did not meet expected outcome!", file=sys.stderr)
        else:
            print(f"[PASS] {scenario['name']} correctly met all expectations.")

        results_records.append(
            {
                "name": scenario["name"],
                "description": scenario["description"],
                "expected": f"Exit code {scenario['expected_exit_code']} (success={scenario['expected_success']})",
                "actual": f"Exit code {rc}",
                "hash_matched": hash_matched,
                "status": status_str,
                "output": combined.strip(),
            }
        )

    # Final hash verification
    final_hash = get_file_sha256(LEARNER_SOLUTION)
    overall_hash_ok = (final_hash == initial_hash)

    # Write evidence.md
    evidence_lines = [
        "# Evidence — R47-T019 (Word Count Isolated Test Runner)",
        "",
        "## Tool Versions",
        f"- Python: {python_version}",
        f"- Node.js: {node_version}",
        f"- Yarn: {yarn_version}",
        "",
        "## Learner Solution Immutability",
        f"- File: `exercises/practice/word-count/word-count.ts`",
        f"- Initial SHA-256: `{initial_hash}`",
        f"- Final SHA-256:   `{final_hash}`",
        f"- Immutability Verified: **{overall_hash_ok}** (file was never modified or solved)",
        "",
        "## Scenario Verification Results",
        "",
        "| Scenario | Description | Expected Result | Actual Result | File Hash Unchanged | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for rec in results_records:
        evidence_lines.append(
            f"| {rec['name']} | {rec['description']} | {rec['expected']} | {rec['actual']} | {'Yes' if rec['hash_matched'] else 'NO'} | {rec['status']} |"
        )

    evidence_lines.extend(
        [
            "",
            "## Scenario Execution Logs",
            "",
        ]
    )

    for rec in results_records:
        evidence_lines.extend(
            [
                f"### {rec['name']}",
                "```text",
                rec["output"],
                "```",
                "",
            ]
        )

    EVIDENCE_FILE.write_text("\n".join(evidence_lines), encoding="utf-8")
    print(f"\n[check] Evidence recorded at: {EVIDENCE_FILE}")

    if all_assertions_passed and overall_hash_ok:
        print("\n==================================================")
        print("RESULT: ALL 3 SCENARIOS AND HASH CHECKS PASSED")
        print("==================================================")
        return 0
    else:
        print("\n==================================================")
        print("RESULT: ONE OR MORE VERIFICATION ASSERTIONS FAILED", file=sys.stderr)
        print("==================================================")
        return 1


if __name__ == "__main__":
    sys.exit(main())
