#!/usr/bin/env python3
"""Verification check for R47-T038 (dnd-character)."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SLUG = "dnd-character"
EX = REPO / "exercises" / "practice" / SLUG
WORK = REPO / "work" / "R47-T038"
VALIDATOR = REPO / "tools" / "course_checks" / "r47-t038.py"
EXPECTED_CASES = 25

NAMED_CASES = [
    "Ability modifier for score 3 is -4",
    "Ability modifier for score 4 is -3",
    "Ability modifier for score 5 is -3",
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
        if not path_part.startswith("work/R47-T038/"):
            lines.append(ln)
    return lines


def normalize_log(text: str, tmp_dir: Path) -> str:
    text = text.replace(str(tmp_dir), "<TMP>")
    text = text.replace(str(tmp_dir.resolve()), "<TMP>")
    text = text.replace(str(REPO), "<REPO>")
    text = text.replace(str(REPO.resolve()), "<REPO>")
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


def run_validator_fixtures(tmp_root: Path) -> dict[str, dict]:
    """Run tools/course_checks/r47-t038.py on real config and 3 temp-dir fixtures."""
    results: dict[str, dict] = {}

    # Real config
    real_res = run_cmd([sys.executable, str(VALIDATOR), str(EX)], REPO, dict(os.environ))
    (WORK / "validator-real.log").write_text(normalize_log(real_res.stdout + real_res.stderr, tmp_root), encoding="utf-8")
    results["real"] = {
        "returncode": real_res.returncode,
        "passed": real_res.returncode == 0 and "VALID:" in real_res.stdout,
        "stdout": normalize_log(real_res.stdout, tmp_root),
    }

    fixtures_root = tmp_root / "fixtures"
    fixtures_root.mkdir(parents=True, exist_ok=True)
    # Create sibling two-fer file so the escape path target actually exists on disk
    sibling = fixtures_root / "two-fer"
    sibling.mkdir(parents=True, exist_ok=True)
    (sibling / "two-fer.ts").write_text("export function twoFer(): string { return '' }\n", encoding="utf-8")

    specs = [
        ("missing_example", {"example": [".meta/nonexistent-proof.ci.ts"]}, "ERR_MISSING_FILE:example"),
        ("missing_test", {"test": ["missing.test.ts"]}, "ERR_MISSING_FILE:test"),
        ("outside_escape", {"solution": ["../two-fer/two-fer.ts"]}, "ERR_PARENT_TRAVERSAL:solution"),
    ]

    for fname, overrides, expected_err in specs:
        fdir = fixtures_root / fname
        shutil.copytree(EX, fdir, ignore=shutil.ignore_patterns("node_modules", ".yarn", ".pnp.*"))
        cfg_p = fdir / ".meta" / "config.json"
        cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
        for k, v in overrides.items():
            cfg["files"][k] = v
        cfg_p.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

        f_res = run_cmd([sys.executable, str(VALIDATOR), str(fdir)], REPO, dict(os.environ))
        out = f_res.stdout + f_res.stderr
        results[fname] = {
            "returncode": f_res.returncode,
            "expected_error_code": expected_err,
            "failed_for_intended_reason": f_res.returncode != 0 and expected_err in out,
            "output": normalize_log(out, tmp_root),
        }

    return results


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
            ["git", "diff", "--quiet", base_ref, "--", str(stub_path), str(test_path), str(config_path)],
            cwd=REPO,
        )
        record(
            "C. stub unsolved and solution/test/config.json match base",
            stub_unsolved and diff_res.returncode == 0,
            f"base={base_ref}",
        )

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

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            tmp_root = Path(td)

            # T038 extra: validator on real config + 3 negative fixtures
            fixture_results = run_validator_fixtures(tmp_root)
            (WORK / "validator-fixtures.json").write_text(
                json.dumps(fixture_results, indent=2) + "\n", encoding="utf-8"
            )
            fixtures_ok = fixture_results["real"]["passed"] and all(
                fixture_results[k]["failed_for_intended_reason"]
                for k in ("missing_example", "missing_test", "outside_escape")
            )
            record(
                "T038. r47-t038.py passes real config and fails all 3 fixtures for intended reasons",
                fixtures_ok,
            )

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

            # E.1 yarn install
            r1 = run_cmd([corepack_bin, "yarn", "install"], copy_dir, env)
            (WORK / "yarn-install.log").write_text(normalize_log(r1.stdout + r1.stderr, tmp_root), encoding="utf-8")
            record("E1. corepack yarn install", r1.returncode == 0, f"rc={r1.returncode}")
            if r1.returncode != 0:
                return 1

            # E.2 yarn test
            r2 = run_cmd([corepack_bin, "yarn", "test"], copy_dir, env)
            step2_out = r2.stdout + r2.stderr
            (WORK / "yarn-test.log").write_text(normalize_log(step2_out, tmp_root), encoding="utf-8")
            record("E2. corepack yarn test (tsc + jest)", r2.returncode == 0, f"rc={r2.returncode}")

            # E.3 yarn test:implementation JSON
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
                "tests_toml_entries": 19,
                "extra_track_cases": 6,
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
            sol_copy.write_text(
                orig_sol.replace("Math.floor((abilityValue - 10) / 2)", "99", 1),
                encoding="utf-8",
            )
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
