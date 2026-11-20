#!/usr/bin/env python3
"""Verification check for R47-T039 (isbn-verifier)."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SLUG = "isbn-verifier"
EX = REPO / "exercises" / "practice" / SLUG
WORK = REPO / "work" / "R47-T039"
RUNNER = REPO / "tools" / "course_checks" / "r47-t039.py"
EXPECTED_CASES = 22

NAMED_CASES = [
    "valid isbn",
    "invalid isbn check digit",
    "valid isbn with a check digit of 10",
]

ENABLE_RULES = [
    (re.compile(r"x(test|it)\("), "it("),
    (re.compile(r"xdescribe\("), "describe("),
    (re.compile(r"x(test|it|describe), ?"), ""),
    (re.compile(r", ?x(test|it|describe) ?}"), "}"),
]

CASE_RE = re.compile(r"^\s*(it|test)\(", re.MULTILINE)


def enable_all(src: str) -> str:
    """Mirror scripts/helpers.mjs prepare(): first match per line, rules in order."""
    for rx, rep in ENABLE_RULES:
        src = "".join(rx.sub(rep, ln, count=1) for ln in src.splitlines(keepends=True))
    return src


def hash_tree(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes


def git_status_outside_work() -> list[str]:
    res = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    lines = []
    for ln in res.stdout.splitlines():
        if not ln.strip():
            continue
        path_part = ln[3:].strip()
        if not path_part.startswith("work/R47-T039/"):
            lines.append(ln)
    return lines


def normalize_log(text: str, tmp_dir: Path | None = None) -> str:
    if tmp_dir is not None:
        text = text.replace(str(tmp_dir), "<TMP>")
        text = text.replace(str(tmp_dir.resolve()), "<TMP>")
    text = text.replace(str(REPO), "<REPO>")
    text = text.replace(str(REPO.resolve()), "<REPO>")
    text = re.sub(r"/[^\s'\"]*r47-t039-[^\s'\"]+", "<RUNNER_TMP>", text)
    return text


def evaluate(
    returncode: int,
    jest_json: dict | None,
    expected_cases: int,
    named_cases: list[str],
    step2_stdout: str | None = None,
) -> list[str]:
    failures: list[str] = []
    if returncode != 0:
        failures.append(f"non-zero exit code: {returncode}")
    if jest_json is None:
        failures.append("missing or invalid jest JSON output")
        return failures

    total = jest_json.get("numTotalTests", 0)
    passed = jest_json.get("numPassedTests", 0)
    failed = jest_json.get("numFailedTests", 0)
    pending = jest_json.get("numPendingTests", 0)

    if total == 0:
        failures.append("zero tests executed (numTotalTests == 0)")
    if total != expected_cases:
        failures.append(f"expected {expected_cases} total tests, got {total}")
    if failed > 0:
        failures.append(f"numFailedTests == {failed}")
    if pending > 0:
        failures.append(f"numPendingTests == {pending}")

    assertions: dict[str, str] = {}
    for suite in jest_json.get("testResults", []):
        for ar in suite.get("assertionResults", []):
            assertions[ar.get("title", "")] = ar.get("status", "")

    for name in named_cases:
        status = assertions.get(name)
        if status is None:
            failures.append(f"named case missing: {name!r}")
        elif status != "passed":
            failures.append(f"named case {name!r} has status {status!r}")

    if step2_stdout is not None:
        m = re.search(r"Tests:\s+(\d+)\s+passed,\s+(\d+)\s+total", step2_stdout)
        if not m:
            failures.append("step 2 output missing 'Tests: N passed, N total' summary")
        else:
            s2_passed, s2_total = int(m.group(1)), int(m.group(2))
            if s2_passed != expected_cases or s2_total != expected_cases or s2_passed != passed:
                failures.append(
                    f"step 2 summary ({s2_passed} passed, {s2_total} total) disagrees with expected {expected_cases}"
                )

    return failures


def run_cmd(cmd: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        timeout=900,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def extract_temp_dir(output: str) -> Path | None:
    m = re.search(r"^TEMP_DIR:\s*(.+)$", output, flags=re.MULTILINE)
    return Path(m.group(1).strip()) if m else None


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    assertions_out: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        assertions_out.append((name, ok, detail))
        tag = "PASS" if ok else "FAIL"
        msg = f"{tag}: {name}"
        if detail:
            msg += f" ({detail})"
        print(msg)

    # A. Locate paths from .meta/config.json
    config_path = EX / ".meta" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    files_map = config["files"]
    ex_resolved = EX.resolve()

    resolved_files: dict[str, list[Path]] = {}
    for role in ("solution", "test", "example"):
        resolved_files[role] = []
        for rel in files_map.get(role, []):
            p = (EX / rel).resolve()
            assert p.exists(), f"Missing {role} file: {p}"
            assert p.is_relative_to(ex_resolved), f"Path escapes exercise dir: {p}"
            resolved_files[role].append(p)
    record("A. config.json paths resolved inside exercise", True)

    hashes_before = hash_tree(EX)
    status_before = git_status_outside_work()

    try:
        # C. Prove stub unsolved and untouched vs org/main
        stub_path = resolved_files["solution"][0]
        test_path = resolved_files["test"][0]
        ref_path = resolved_files["example"][0]
        stub_unsolved = "Remove this line and implement the function" in stub_path.read_text(encoding="utf-8")

        base_ref = "org/main"
        ref_check = subprocess.run(
            ["git", "rev-parse", "--verify", "org/main"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if ref_check.returncode != 0:
            mb = subprocess.run(
                ["git", "merge-base", "HEAD", "HEAD"],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=True,
            )
            base_ref = mb.stdout.strip()
            print(f"NOTE: org/main missing, falling back to {base_ref}")

        diff_res = subprocess.run(
            ["git", "diff", "--quiet", base_ref, "--", str(stub_path), str(test_path), str(ref_path)],
            cwd=REPO,
        )
        record(
            "C. stub unsolved and solution/test/reference match base",
            stub_unsolved and diff_res.returncode == 0,
            f"base={base_ref}",
        )

        # T039 Scenarios against tools/course_checks/r47-t039.py
        scenarios: list[dict] = []
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            tmp_root = Path(td)

            # Scenario 1: Real reference
            s1_before = hash_tree(EX)
            s1_json_path = tmp_root / "s1-jest.json"
            s1_res = run_cmd(
                [sys.executable, str(RUNNER), "--exercise", f"practice/{SLUG}", "--json-out", str(s1_json_path)],
                REPO,
                dict(os.environ),
            )
            s1_after = hash_tree(EX)
            s1_out = s1_res.stdout + s1_res.stderr
            s1_td = extract_temp_dir(s1_out)
            s1_cleaned = s1_td is not None and not s1_td.exists()
            s1_ok = (
                s1_res.returncode == 0
                and f"RESULT: PASS - executed {EXPECTED_CASES} cases" in s1_out
                and s1_before == s1_after
                and s1_cleaned
            )
            (WORK / "scenario-1-real.log").write_text(normalize_log(s1_out, tmp_root), encoding="utf-8")
            scenarios.append(
                {
                    "scenario": "real_reference",
                    "expected_exit": "0",
                    "actual_exit": s1_res.returncode,
                    "temp_dir_removed": s1_cleaned,
                    "learner_hashes_unchanged": s1_before == s1_after,
                    "passed": s1_ok,
                }
            )
            record("T039 scenario 1. real reference passes 22 cases & cleans temp dir", s1_ok, f"rc={s1_res.returncode}")

            # Scenario 2: Deliberately failing reference
            s2_before = hash_tree(EX)
            failing_ref = tmp_root / "failing-isbn.ts"
            failing_ref.write_text(
                ref_path.read_text(encoding="utf-8").replace("return sum % 11 === 0", "return sum % 11 !== 0", 1),
                encoding="utf-8",
            )
            s2_res = run_cmd(
                [sys.executable, str(RUNNER), "--exercise", f"practice/{SLUG}", "--reference", str(failing_ref)],
                REPO,
                dict(os.environ),
            )
            s2_after = hash_tree(EX)
            s2_out = s2_res.stdout + s2_res.stderr
            s2_td = extract_temp_dir(s2_out)
            s2_cleaned = s2_td is not None and not s2_td.exists()
            s2_ok = s2_res.returncode != 0 and s2_before == s2_after and s2_cleaned
            (WORK / "scenario-2-failing-ref.log").write_text(normalize_log(s2_out, tmp_root), encoding="utf-8")
            scenarios.append(
                {
                    "scenario": "failing_reference",
                    "expected_exit": "non-zero",
                    "actual_exit": s2_res.returncode,
                    "temp_dir_removed": s2_cleaned,
                    "learner_hashes_unchanged": s2_before == s2_after,
                    "passed": s2_ok,
                }
            )
            record("T039 scenario 2. failing reference exits non-zero & cleans temp dir", s2_ok, f"rc={s2_res.returncode}")

            # Scenario 3: Empty test selection (zero-test guard)
            s3_before = hash_tree(EX)
            s3_res = run_cmd(
                [
                    sys.executable,
                    str(RUNNER),
                    "--exercise",
                    f"practice/{SLUG}",
                    "--test-name-pattern",
                    "__no_matching_test_case__",
                ],
                REPO,
                dict(os.environ),
            )
            s3_after = hash_tree(EX)
            s3_out = s3_res.stdout + s3_res.stderr
            s3_td = extract_temp_dir(s3_out)
            s3_cleaned = s3_td is not None and not s3_td.exists()
            s3_ok = (
                s3_res.returncode != 0
                and "zero tests executed" in s3_out
                and s3_before == s3_after
                and s3_cleaned
            )
            (WORK / "scenario-3-empty-selection.log").write_text(normalize_log(s3_out, tmp_root), encoding="utf-8")
            scenarios.append(
                {
                    "scenario": "empty_test_selection",
                    "expected_exit": "non-zero (zero-test guard)",
                    "actual_exit": s3_res.returncode,
                    "temp_dir_removed": s3_cleaned,
                    "learner_hashes_unchanged": s3_before == s3_after,
                    "passed": s3_ok,
                }
            )
            record("T039 scenario 3. empty test selection caught by zero-test guard", s3_ok, f"rc={s3_res.returncode}")

            # Scenario 4: Interrupted run mid-execution
            s4_before = hash_tree(EX)
            popen_kwargs: dict = {
                "cwd": REPO,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                "encoding": "utf-8",
                "errors": "replace",
            }
            if os.name == "nt":
                popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen(
                [sys.executable, str(RUNNER), "--exercise", f"practice/{SLUG}"],
                **popen_kwargs,
            )
            collected_lines: list[str] = []
            s4_td: Path | None = None
            sent_interrupt = False
            assert proc.stdout is not None
            for line in proc.stdout:
                collected_lines.append(line)
                if line.startswith("TEMP_DIR:"):
                    s4_td = Path(line.split("TEMP_DIR:", 1)[1].strip())
                if line.startswith("STEP: yarn install") or line.startswith("STEP: yarn test"):
                    # Brief pause so yarn child is active inside temp dir before interrupting
                    time.sleep(0.3)
                    if os.name == "nt":
                        proc.send_signal(signal.CTRL_BREAK_EVENT)
                    else:
                        proc.send_signal(signal.SIGINT)
                    sent_interrupt = True
                    break

            rest_out, _ = proc.communicate(timeout=60)
            collected_lines.append(rest_out)
            s4_out = "".join(collected_lines)
            s4_after = hash_tree(EX)
            s4_cleaned = s4_td is not None and not s4_td.exists()
            s4_ok = sent_interrupt and proc.returncode != 0 and s4_before == s4_after and s4_cleaned
            (WORK / "scenario-4-interrupted.log").write_text(normalize_log(s4_out, tmp_root), encoding="utf-8")
            scenarios.append(
                {
                    "scenario": "interrupted_run",
                    "expected_exit": "non-zero",
                    "actual_exit": proc.returncode,
                    "sent_interrupt": sent_interrupt,
                    "temp_dir_removed": s4_cleaned,
                    "learner_hashes_unchanged": s4_before == s4_after,
                    "passed": s4_ok,
                }
            )
            record(
                "T039 scenario 4. interrupted run preserves learner hashes & removes temp dir",
                s4_ok,
                f"rc={proc.returncode}, cleaned={s4_cleaned}",
            )

            (WORK / "scenarios.json").write_text(json.dumps(scenarios, indent=2) + "\n", encoding="utf-8")

            # Also run standard shared contract A-H directly on isolated copy
            corepack_bin = shutil.which("corepack")
            if corepack_bin is None:
                record("E. corepack executable found", False, "shutil.which('corepack') returned None")
                return 1

            env = {
                **os.environ,
                "CI": "true",
                "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0",
                "FORCE_COLOR": "0",
                "YARN_ENABLE_TELEMETRY": "0",
                "YARN_ENABLE_IMMUTABLE_INSTALLS": "false",
            }
            copy_dir = tmp_root / SLUG
            shutil.copytree(
                EX,
                copy_dir,
                ignore=shutil.ignore_patterns("node_modules", ".yarn", ".pnp.*"),
            )
            for req in (".meta", ".docs", ".yarnrc.yml", ".vscode"):
                assert (copy_dir / req).exists(), f"Missing {req} in temp copy"

            for i, ex_file in enumerate(files_map["example"]):
                src_ex = (copy_dir / ex_file).read_text(encoding="utf-8").replace("from '../", "from './")
                (copy_dir / files_map["solution"][i]).write_text(src_ex, encoding="utf-8")

            test_copy = copy_dir / files_map["test"][0]
            enabled_src = enable_all(test_copy.read_text(encoding="utf-8"))
            test_copy.write_text(enabled_src, encoding="utf-8")

            leftover = any(tok in enabled_src for tok in ("xit", "xtest", "xdescribe", ".skip(", ".only("))
            static_count = len(CASE_RE.findall(enabled_src))
            record(
                "D. enable-all transform clean and static count matches",
                (not leftover) and static_count == EXPECTED_CASES,
                f"static_count={static_count}",
            )

            r1 = run_cmd([corepack_bin, "yarn", "install"], copy_dir, env)
            (WORK / "yarn-install.log").write_text(normalize_log(r1.stdout + r1.stderr, tmp_root), encoding="utf-8")
            record("E1. corepack yarn install", r1.returncode == 0, f"rc={r1.returncode}")
            if r1.returncode != 0:
                return 1

            r2 = run_cmd([corepack_bin, "yarn", "test"], copy_dir, env)
            step2_out = r2.stdout + r2.stderr
            (WORK / "yarn-test.log").write_text(normalize_log(step2_out, tmp_root), encoding="utf-8")
            record("E2. corepack yarn test (tsc + jest)", r2.returncode == 0, f"rc={r2.returncode}")

            jest_out_path = tmp_root / "jest-results.json"
            r3 = run_cmd(
                [
                    corepack_bin,
                    "yarn",
                    "test:implementation",
                    "--ci",
                    "--watchAll=false",
                    "--json",
                    f"--outputFile={jest_out_path}",
                ],
                copy_dir,
                env,
            )
            (WORK / "jest-implementation.log").write_text(
                normalize_log(r3.stdout + r3.stderr, tmp_root), encoding="utf-8"
            )
            jest_json = json.loads(jest_out_path.read_text(encoding="utf-8")) if jest_out_path.exists() else None
            if jest_json is not None:
                (WORK / "jest-results.json").write_text(
                    normalize_log(json.dumps(jest_json, indent=2) + "\n", tmp_root),
                    encoding="utf-8",
                )

            eval_failures = evaluate(r3.returncode, jest_json, EXPECTED_CASES, NAMED_CASES, step2_stdout=step2_out)
            record(
                "F. evaluate passing run",
                len(eval_failures) == 0,
                "; ".join(eval_failures) if eval_failures else f"{EXPECTED_CASES} passed",
            )

            expected_vs_actual = []
            named_set = set(NAMED_CASES)
            if jest_json:
                for suite in jest_json.get("testResults", []):
                    for ar in suite.get("assertionResults", []):
                        title = ar.get("title", "")
                        expected_vs_actual.append(
                            {
                                "title": title,
                                "named_case": title in named_set,
                                "expected": "passed",
                                "actual": ar.get("status"),
                            }
                        )
            (WORK / "expected-vs-actual.json").write_text(
                json.dumps(expected_vs_actual, indent=2) + "\n", encoding="utf-8"
            )

            counts_data = {
                "static_case_count": static_count,
                "expected_cases": EXPECTED_CASES,
                "tests_toml_entries": 21,
                "extra_track_cases": 1,
                "jest": {
                    "numTotalTests": jest_json.get("numTotalTests") if jest_json else None,
                    "numPassedTests": jest_json.get("numPassedTests") if jest_json else None,
                    "numFailedTests": jest_json.get("numFailedTests") if jest_json else None,
                    "numPendingTests": jest_json.get("numPendingTests") if jest_json else None,
                },
            }
            (WORK / "counts.json").write_text(json.dumps(counts_data, indent=2) + "\n", encoding="utf-8")

            # G. Negative controls
            sol_copy = copy_dir / files_map["solution"][0]
            orig_sol = sol_copy.read_text(encoding="utf-8")
            sol_copy.write_text(orig_sol.replace("return sum % 11 === 0", "return sum % 11 !== 0", 1), encoding="utf-8")
            nc1_json_path = tmp_root / "nc1-jest.json"
            nc1_r = run_cmd(
                [
                    corepack_bin,
                    "yarn",
                    "test:implementation",
                    "--ci",
                    "--watchAll=false",
                    "--json",
                    f"--outputFile={nc1_json_path}",
                ],
                copy_dir,
                env,
            )
            nc1_json = json.loads(nc1_json_path.read_text(encoding="utf-8")) if nc1_json_path.exists() else None
            nc1_fail = evaluate(nc1_r.returncode, nc1_json, EXPECTED_CASES, NAMED_CASES)
            nc1_ok = nc1_r.returncode != 0 and len(nc1_fail) > 0
            sol_copy.write_text(orig_sol, encoding="utf-8")

            orig_test = test_copy.read_text(encoding="utf-8")
            test_copy.write_text("export {}\n", encoding="utf-8")
            nc2_json_path = tmp_root / "nc2-jest.json"
            nc2_r = run_cmd(
                [
                    corepack_bin,
                    "yarn",
                    "test:implementation",
                    "--ci",
                    "--watchAll=false",
                    "--json",
                    f"--outputFile={nc2_json_path}",
                ],
                copy_dir,
                env,
            )
            nc2_json = json.loads(nc2_json_path.read_text(encoding="utf-8")) if nc2_json_path.exists() else None
            nc2_fail = evaluate(nc2_r.returncode, nc2_json, EXPECTED_CASES, NAMED_CASES)
            nc2_guard_fail = evaluate(
                0,
                {"numTotalTests": 0, "numPassedTests": 0, "numFailedTests": 0, "numPendingTests": 0, "testResults": []},
                EXPECTED_CASES,
                NAMED_CASES,
            )
            nc2_ok = any("zero tests" in f for f in nc2_fail) and any("zero tests" in f for f in nc2_guard_fail)
            test_copy.write_text(orig_test, encoding="utf-8")

            nc3_fail = evaluate(1, jest_json, EXPECTED_CASES, NAMED_CASES)
            nc3_ok = any("non-zero exit code" in f for f in nc3_fail)

            nc_report = {
                "assertion_failure": {"detected": nc1_ok, "returncode": nc1_r.returncode, "failures": nc1_fail},
                "zero_tests": {"detected": nc2_ok, "returncode": nc2_r.returncode, "failures": nc2_fail},
                "child_failure": {"detected": nc3_ok, "returncode": 1, "failures": nc3_fail},
            }
            (WORK / "negative-controls.json").write_text(json.dumps(nc_report, indent=2) + "\n", encoding="utf-8")
            record("G. negative controls all caught", nc1_ok and nc2_ok and nc3_ok)

            # H. tool-versions.json and inputs.json
            tsc_ver = run_cmd([corepack_bin, "yarn", "tsc", "--version"], copy_dir, env).stdout.strip()
            jest_ver = run_cmd([corepack_bin, "yarn", "jest", "--version"], copy_dir, env).stdout.strip()
            head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
            org_sha = subprocess.check_output(["git", "rev-parse", base_ref], cwd=REPO, text=True).strip()
            tool_versions = {
                "python": sys.version.split()[0],
                "node": subprocess.check_output(["node", "--version"], text=True).strip(),
                "corepack": subprocess.check_output([corepack_bin, "--version"], text=True).strip(),
                "yarn": subprocess.check_output([corepack_bin, "yarn", "--version"], cwd=REPO, text=True).strip(),
                "tsc": tsc_ver,
                "jest": jest_ver,
                "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
                "git_head": head_sha,
                "org_main_sha": org_sha,
            }
            (WORK / "tool-versions.json").write_text(json.dumps(tool_versions, indent=2) + "\n", encoding="utf-8")

            inputs_data = {
                "exercise": f"exercises/practice/{SLUG}",
                "files": files_map,
                "expected_cases": EXPECTED_CASES,
                "named_cases": NAMED_CASES,
                "learner_file_hashes_before": hashes_before,
            }
            (WORK / "inputs.json").write_text(json.dumps(inputs_data, indent=2) + "\n", encoding="utf-8")

    finally:
        hashes_after = hash_tree(EX)
        status_after = git_status_outside_work()
        record("B. learner files and git status unchanged during check", hashes_before == hashes_after and status_before == status_after)

    all_ok = all(ok for _, ok, _ in assertions_out)
    if all_ok:
        print(f"RESULT: PASS - executed {EXPECTED_CASES} cases")
        return 0
    failed_names = [n for n, ok, _ in assertions_out if not ok]
    print(f"RESULT: FAIL - {', '.join(failed_names)}")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"RESULT: FAIL - unexpected exception: {exc}")
        sys.exit(1)
