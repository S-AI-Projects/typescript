#!/usr/bin/env python3
"""Verification check for R47-T033 (sieve)."""

from __future__ import annotations

import difflib
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
SLUG = "sieve"
EX = REPO / "exercises" / "practice" / SLUG
WORK = REPO / "work" / "R47-T033"
MUTANT_PATH = WORK / "mutant.ts"
EXPECTED_CASES = 5

NAMED_CASES = [
    "no primes under two",
    "find first prime",
    "find primes up to 10",
]
REJECTING_CASE = "find primes up to 10"

ENABLE_RULES = [
    (re.compile(r"x(test|it)\("), "it("),
    (re.compile(r"xdescribe\("), "describe("),
    (re.compile(r"x(test|it|describe), ?"), ""),
    (re.compile(r", ?x(test|it|describe) ?}"), "}"),
]

CASE_RE = re.compile(r"^\s*(it|test)\(", re.MULTILINE)
TOKEN_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*|\d+|===|!==|<=|>=|=>|\S")


def enable_all(src: str) -> str:
    """Mirror scripts/helpers.mjs prepare(): first match per line, rules in order."""
    for rx, rep in ENABLE_RULES:
        src = "".join(rx.sub(rep, ln, count=1) for ln in src.splitlines(keepends=True))
    return src


def strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def tokenize_ts(src: str) -> list[str]:
    return TOKEN_RE.findall(strip_comments(src))


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
        if not path_part.startswith("work/R47-T033/"):
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


def prepare_temp_copy(tmp_root: Path, name: str, files_map: dict, solution_src: str) -> tuple[Path, int, bool]:
    copy_dir = tmp_root / name
    shutil.copytree(
        EX,
        copy_dir,
        ignore=shutil.ignore_patterns("node_modules", ".yarn", ".pnp.*"),
    )
    for req in (".meta", ".docs", ".yarnrc.yml", ".vscode"):
        assert (copy_dir / req).exists(), f"Missing {req} in temp copy"

    (copy_dir / files_map["solution"][0]).write_text(solution_src, encoding="utf-8")

    test_copy = copy_dir / files_map["test"][0]
    enabled_src = enable_all(test_copy.read_text(encoding="utf-8"))
    test_copy.write_text(enabled_src, encoding="utf-8")

    leftover = any(tok in enabled_src for tok in ("xit", "xtest", "xdescribe", ".skip(", ".only("))
    static_count = len(CASE_RE.findall(enabled_src))
    return copy_dir, static_count, leftover


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

        # T033-specific: check mutant token diff (more than whitespace)
        ref_src = ref_path.read_text(encoding="utf-8").replace("from '../", "from './")
        mutant_src = MUTANT_PATH.read_text(encoding="utf-8").replace("from '../", "from './")
        ref_tokens = tokenize_ts(ref_src)
        mut_tokens = tokenize_ts(mutant_src)
        token_diffs = [
            (i, a, b)
            for i, (a, b) in enumerate(zip(ref_tokens, mut_tokens))
            if a != b
        ]
        if len(ref_tokens) != len(mut_tokens) or token_diffs:
            non_ws_diff = True
        else:
            non_ws_diff = False

        diff_text = "".join(
            difflib.unified_diff(
                ref_src.splitlines(keepends=True),
                mutant_src.splitlines(keepends=True),
                fromfile="exercises/practice/sieve/.meta/proof.ci.ts",
                tofile="work/R47-T033/mutant.ts",
            )
        )
        (WORK / "mutant-diff.patch").write_text(diff_text, encoding="utf-8")
        record(
            "T033. mutant differs from reference by non-whitespace tokens",
            non_ws_diff,
            f"token_diffs={token_diffs}",
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

            # Copy 1: Original reference
            copy_orig, static_count, leftover = prepare_temp_copy(tmp_root, "sieve-orig", files_map, ref_src)
            record(
                "D. enable-all transform clean and static count matches",
                (not leftover) and static_count == EXPECTED_CASES,
                f"static_count={static_count}",
            )

            r1 = run_cmd([corepack_bin, "yarn", "install"], copy_orig, env)
            (WORK / "yarn-install.log").write_text(normalize_log(r1.stdout + r1.stderr, tmp_root), encoding="utf-8")
            record("E1. corepack yarn install (original)", r1.returncode == 0, f"rc={r1.returncode}")
            if r1.returncode != 0:
                return 1

            r2 = run_cmd([corepack_bin, "yarn", "test"], copy_orig, env)
            step2_out = r2.stdout + r2.stderr
            (WORK / "yarn-test.log").write_text(normalize_log(step2_out, tmp_root), encoding="utf-8")
            record("E2. corepack yarn test (original)", r2.returncode == 0, f"rc={r2.returncode}")

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
                copy_orig,
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
                "F. evaluate passing original run",
                len(eval_failures) == 0,
                "; ".join(eval_failures) if eval_failures else f"{EXPECTED_CASES} passed",
            )

            # Copy 2: Mutant in separate temp copy
            copy_mut, mut_static, mut_leftover = prepare_temp_copy(tmp_root, "sieve-mutant", files_map, mutant_src)
            assert (not mut_leftover) and mut_static == EXPECTED_CASES

            mr1 = run_cmd([corepack_bin, "yarn", "install"], copy_mut, env)
            (WORK / "mutant-yarn-install.log").write_text(
                normalize_log(mr1.stdout + mr1.stderr, tmp_root), encoding="utf-8"
            )
            assert mr1.returncode == 0, "mutant copy yarn install failed"

            mr2 = run_cmd([corepack_bin, "yarn", "test"], copy_mut, env)
            (WORK / "mutant-yarn-test.log").write_text(
                normalize_log(mr2.stdout + mr2.stderr, tmp_root), encoding="utf-8"
            )

            mut_jest_path = tmp_root / "mutant-jest-results.json"
            mr3 = run_cmd(
                [
                    corepack_bin,
                    "yarn",
                    "test:implementation",
                    "--ci",
                    "--watchAll=false",
                    "--json",
                    f"--outputFile={mut_jest_path}",
                ],
                copy_mut,
                env,
            )
            (WORK / "mutant-jest-implementation.log").write_text(
                normalize_log(mr3.stdout + mr3.stderr, tmp_root), encoding="utf-8"
            )
            mut_jest_json = json.loads(mut_jest_path.read_text(encoding="utf-8")) if mut_jest_path.exists() else None
            if mut_jest_json is not None:
                (WORK / "mutant-jest-results.json").write_text(
                    normalize_log(json.dumps(mut_jest_json, indent=2) + "\n", tmp_root),
                    encoding="utf-8",
                )

            mut_statuses: dict[str, str] = {}
            if mut_jest_json:
                for suite in mut_jest_json.get("testResults", []):
                    for ar in suite.get("assertionResults", []):
                        mut_statuses[ar.get("title", "")] = ar.get("status", "")

            mut_failures = evaluate(mr3.returncode, mut_jest_json, EXPECTED_CASES, NAMED_CASES)
            rejected_on_named = (
                mr2.returncode != 0
                and mr3.returncode != 0
                and mut_statuses.get(REJECTING_CASE) == "failed"
                and any(REJECTING_CASE in f for f in mut_failures)
            )
            record(
                "T033. mutant fails specifically on 'find primes up to 10'",
                rejected_on_named,
                f"status={mut_statuses.get(REJECTING_CASE)!r}",
            )

            # Node probe for minimal input (9) and duplicate-prime observation
            probe_js = (
                "import { primes as orig } from './orig.ts';\n"
                "import { primes as mut } from './mut.ts';\n"
                "const limits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 16, 24, 25, 36, 48, 100, 120];\n"
                "function exactPrimes(limit) {\n"
                "  const out = [];\n"
                "  for (let n = 2; n <= limit; n++) {\n"
                "    let p = true;\n"
                "    for (let d = 2; d * d <= n; d++) { if (n % d === 0) { p = false; break; } }\n"
                "    if (p) out.push(n);\n"
                "  }\n"
                "  return out;\n"
                "}\n"
                "const rows = limits.map(n => ({\n"
                "  limit: n,\n"
                "  expected: exactPrimes(n),\n"
                "  original: orig(n),\n"
                "  mutant: mut(n),\n"
                "}));\n"
                "console.log(JSON.stringify(rows, null, 2));\n"
            )
            probe_dir = tmp_root / "probe"
            probe_dir.mkdir(parents=True, exist_ok=True)
            (probe_dir / "orig.ts").write_text(ref_src, encoding="utf-8")
            (probe_dir / "mut.ts").write_text(mutant_src, encoding="utf-8")
            probe_res = run_cmd(
                ["node", "--experimental-strip-types", "--input-type=module", "-e", probe_js],
                probe_dir,
                env,
            )
            probe_rows = json.loads(probe_res.stdout) if probe_res.returncode == 0 else []
            (WORK / "probe-outputs.json").write_text(json.dumps(probe_rows, indent=2) + "\n", encoding="utf-8")

            by_limit = {r["limit"]: r for r in probe_rows}
            min_valid_ok = (
                9 in by_limit
                and by_limit[9]["original"] == [2, 3, 5, 7]
                and by_limit[9]["mutant"] == [2, 3, 5, 7, 9]
                and 10 in by_limit
                and by_limit[10]["original"] == [2, 3, 5, 7]
                and by_limit[10]["mutant"] == [2, 3, 5, 7, 10]
                and 5 in by_limit
                and by_limit[5]["original"] == [2, 3, 3, 5]
            )
            record(
                "T033. minimal input (9) and duplicate-prime probe reproduced",
                probe_res.returncode == 0 and min_valid_ok,
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
                                "actual_original": ar.get("status"),
                                "actual_mutant": mut_statuses.get(title),
                            }
                        )
            (WORK / "expected-vs-actual.json").write_text(
                json.dumps(expected_vs_actual, indent=2) + "\n", encoding="utf-8"
            )
            (WORK / "mutant-comparison.json").write_text(
                json.dumps(
                    {
                        "rejecting_test": REJECTING_CASE,
                        "rejecting_uuid": "974945d8-8cd9-4f00-9463-7d813c7f17b7",
                        "minimal_distinguishing_limit": 9,
                        "original_jest_rc": r3.returncode,
                        "mutant_jest_rc": mr3.returncode,
                        "token_diffs": token_diffs,
                        "per_case": expected_vs_actual,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            counts_data = {
                "static_case_count": static_count,
                "expected_cases": EXPECTED_CASES,
                "jest_original": {
                    "numTotalTests": jest_json.get("numTotalTests") if jest_json else None,
                    "numPassedTests": jest_json.get("numPassedTests") if jest_json else None,
                    "numFailedTests": jest_json.get("numFailedTests") if jest_json else None,
                    "numPendingTests": jest_json.get("numPendingTests") if jest_json else None,
                },
                "jest_mutant": {
                    "numTotalTests": mut_jest_json.get("numTotalTests") if mut_jest_json else None,
                    "numPassedTests": mut_jest_json.get("numPassedTests") if mut_jest_json else None,
                    "numFailedTests": mut_jest_json.get("numFailedTests") if mut_jest_json else None,
                    "numPendingTests": mut_jest_json.get("numPendingTests") if mut_jest_json else None,
                },
            }
            (WORK / "counts.json").write_text(json.dumps(counts_data, indent=2) + "\n", encoding="utf-8")

            # G. Negative controls (using copy_orig)
            sol_copy = copy_orig / files_map["solution"][0]
            orig_sol = sol_copy.read_text(encoding="utf-8")
            sol_copy.write_text(mutant_src, encoding="utf-8")
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
                copy_orig,
                env,
            )
            nc1_json = json.loads(nc1_json_path.read_text(encoding="utf-8")) if nc1_json_path.exists() else None
            nc1_fail = evaluate(nc1_r.returncode, nc1_json, EXPECTED_CASES, NAMED_CASES)
            nc1_ok = nc1_r.returncode != 0 and len(nc1_fail) > 0
            sol_copy.write_text(orig_sol, encoding="utf-8")

            test_copy = copy_orig / files_map["test"][0]
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
                copy_orig,
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
            tsc_ver = run_cmd([corepack_bin, "yarn", "tsc", "--version"], copy_orig, env).stdout.strip()
            jest_ver = run_cmd([corepack_bin, "yarn", "jest", "--version"], copy_orig, env).stdout.strip()
            head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
            org_sha = subprocess.check_output(["git", "rev-parse", base_ref], cwd=REPO, text=True).strip()
            tool_versions = {
                "python": sys.version.split()[0],
                "node": subprocess.check_output(["node", "--version"], text=True).strip(),
                "corepack": subprocess.check_output([corepack_bin, "--version"], text=True).strip(),
                "yarn": subprocess.check_output([corepack_bin, "yarn", "--version"], cwd=REPO, text=True).strip(),
                "tsc": tsc_ver,
                "jest": jest_ver,
                "ts_probe_method": "node --experimental-strip-types",
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
                "mutant_file": "work/R47-T033/mutant.ts",
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
