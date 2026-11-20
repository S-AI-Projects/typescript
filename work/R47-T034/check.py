#!/usr/bin/env python3
"""Verification check for R47-T034 (collatz-conjecture)."""

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
SLUG = "collatz-conjecture"
EX = REPO / "exercises" / "practice" / SLUG
WORK = REPO / "work" / "R47-T034"
EXPECTED_CASES = 7

NAMED_CASES = [
    "zero steps for one",
    "divide if even",
    "even and odd steps",
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
        if not path_part.startswith("work/R47-T034/"):
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


def prepare_and_run_copy(
    tmp_root: Path,
    label: str,
    files_map: dict,
    ref_src: str,
    corepack_bin: str,
    env: dict[str, str],
) -> tuple[Path, int, bool, dict | None, list[str], str]:
    copy_dir = tmp_root / label
    shutil.copytree(
        EX,
        copy_dir,
        ignore=shutil.ignore_patterns("node_modules", ".yarn", ".pnp.*"),
    )
    for req in (".meta", ".docs", ".yarnrc.yml", ".vscode"):
        assert (copy_dir / req).exists(), f"Missing {req} in temp copy"

    (copy_dir / files_map["solution"][0]).write_text(ref_src, encoding="utf-8")
    (copy_dir / files_map["example"][0]).write_text(ref_src, encoding="utf-8")

    test_copy = copy_dir / files_map["test"][0]
    enabled_src = enable_all(test_copy.read_text(encoding="utf-8"))
    test_copy.write_text(enabled_src, encoding="utf-8")

    leftover = any(tok in enabled_src for tok in ("xit", "xtest", "xdescribe", ".skip(", ".only("))
    static_count = len(CASE_RE.findall(enabled_src))

    r1 = run_cmd([corepack_bin, "yarn", "install"], copy_dir, env)
    (WORK / f"{label}-yarn-install.log").write_text(
        normalize_log(r1.stdout + r1.stderr, tmp_root), encoding="utf-8"
    )
    if r1.returncode != 0:
        return copy_dir, static_count, leftover, None, [f"{label} yarn install failed (rc={r1.returncode})"], ""

    r2 = run_cmd([corepack_bin, "yarn", "test"], copy_dir, env)
    step2_out = r2.stdout + r2.stderr
    (WORK / f"{label}-yarn-test.log").write_text(normalize_log(step2_out, tmp_root), encoding="utf-8")
    if r2.returncode != 0:
        return copy_dir, static_count, leftover, None, [f"{label} yarn test failed (rc={r2.returncode})"], step2_out

    jest_out_path = tmp_root / f"{label}-jest-results.json"
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
    (WORK / f"{label}-jest-implementation.log").write_text(
        normalize_log(r3.stdout + r3.stderr, tmp_root), encoding="utf-8"
    )
    jest_json = json.loads(jest_out_path.read_text(encoding="utf-8")) if jest_out_path.exists() else None
    failures = evaluate(r3.returncode, jest_json, EXPECTED_CASES, NAMED_CASES, step2_stdout=step2_out)
    return copy_dir, static_count, leftover, jest_json, failures, step2_out


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
        # C. Prove stub unsolved and solution/test untouched vs org/main
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
            ["git", "diff", "--quiet", base_ref, "--", str(stub_path), str(test_path)],
            cwd=REPO,
        )
        record(
            "C. stub unsolved and solution/test match base",
            stub_unsolved and diff_res.returncode == 0,
            f"base={base_ref}",
        )

        ref_rel = f"exercises/practice/{SLUG}/{files_map['example'][0]}"
        before_src = subprocess.check_output(
            ["git", "show", f"{base_ref}:{ref_rel}"],
            cwd=REPO,
            text=True,
            encoding="utf-8",
        ).replace("from '../", "from './")
        after_src = ref_path.read_text(encoding="utf-8").replace("from '../", "from './")

        (WORK / "before.proof.ci.ts").write_text(before_src, encoding="utf-8")
        (WORK / "after.proof.ci.ts").write_text(after_src, encoding="utf-8")

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

            # Run BEFORE reference in isolated temp copy
            copy_before, before_static, before_leftover, before_jest, before_failures, _ = prepare_and_run_copy(
                tmp_root, "before", files_map, before_src, corepack_bin, env
            )
            if before_jest is not None:
                (WORK / "before-jest-results.json").write_text(
                    normalize_log(json.dumps(before_jest, indent=2) + "\n", tmp_root),
                    encoding="utf-8",
                )
            record(
                "T034. BEFORE reference passes all 7 cases",
                (not before_leftover) and before_static == EXPECTED_CASES and len(before_failures) == 0,
                "; ".join(before_failures) if before_failures else f"{EXPECTED_CASES} passed",
            )

            # Run AFTER reference in isolated temp copy
            copy_after, after_static, after_leftover, after_jest, after_failures, _ = prepare_and_run_copy(
                tmp_root, "after", files_map, after_src, corepack_bin, env
            )
            if after_jest is not None:
                (WORK / "jest-results.json").write_text(
                    normalize_log(json.dumps(after_jest, indent=2) + "\n", tmp_root),
                    encoding="utf-8",
                )

            record(
                "D. enable-all transform clean and static count matches",
                (not after_leftover) and after_static == EXPECTED_CASES,
                f"static_count={after_static}",
            )
            record(
                "F. evaluate passing AFTER run (7 passed)",
                len(after_failures) == 0,
                "; ".join(after_failures) if after_failures else f"{EXPECTED_CASES} passed",
            )

            # ESLint check inside installed temp copy on AFTER .meta/proof.ci.ts
            lint_res = run_cmd([corepack_bin, "yarn", "lint:ci"], copy_after, env)
            (WORK / "eslint-after.log").write_text(
                normalize_log(lint_res.stdout + lint_res.stderr, tmp_root), encoding="utf-8"
            )
            record("T034. exercise eslint passes on AFTER .meta/proof.ci.ts", lint_res.returncode == 0, f"rc={lint_res.returncode}")

            # Equivalence sweep: compile both BEFORE and AFTER with single-file tsc (no -p)
            sweep_dir = tmp_root / "sweep"
            sweep_dir.mkdir(parents=True, exist_ok=True)
            (sweep_dir / "before.ts").write_text(before_src, encoding="utf-8")
            (sweep_dir / "after.ts").write_text(after_src, encoding="utf-8")
            out_dir = sweep_dir / "out"
            out_dir.mkdir(parents=True, exist_ok=True)

            # Copy compiled using tsc from installed copy_after
            tsc_res = run_cmd(
                [
                    corepack_bin,
                    "yarn",
                    "tsc",
                    str(sweep_dir / "before.ts"),
                    str(sweep_dir / "after.ts"),
                    "--outDir",
                    str(out_dir),
                    "--target",
                    "es2020",
                    "--module",
                    "nodenext",
                    "--moduleResolution",
                    "nodenext",
                    "--strict",
                ],
                copy_after,
                env,
            )
            (WORK / "sweep-tsc.log").write_text(
                normalize_log(tsc_res.stdout + tsc_res.stderr, tmp_root), encoding="utf-8"
            )
            (out_dir / "package.json").write_text('{"type": "commonjs"}\n', encoding="utf-8")

            sweep_script = (
                "import { createRequire } from 'node:module';\n"
                "const require = createRequire(import.meta.url);\n"
                f"const beforeMod = require({json.dumps(str(out_dir / 'before.js'))});\n"
                f"const afterMod = require({json.dumps(str(out_dir / 'after.js'))});\n"
                "function callSteps(fn, x) {\n"
                "  try {\n"
                "    return { ok: true, value: fn(x) };\n"
                "  } catch (err) {\n"
                "    return { ok: false, name: err?.name || typeof err, message: err?.message || String(err) };\n"
                "  }\n"
                "}\n"
                "let mismatches = [];\n"
                "let totalChecked = 0;\n"
                "const samples = {};\n"
                "for (let n = 1; n <= 100000; n++) {\n"
                "  totalChecked++;\n"
                "  const b = callSteps(beforeMod.steps, n);\n"
                "  const a = callSteps(afterMod.steps, n);\n"
                "  if (JSON.stringify(b) !== JSON.stringify(a)) {\n"
                "    if (mismatches.length < 20) mismatches.push({ input: n, before: b, after: a });\n"
                "  }\n"
                "  if (n === 1 || n === 12 || n === 16 || n === 100000) samples[String(n)] = a;\n"
                "}\n"
                "const errorInputs = [0, -15, 1.5, NaN];\n"
                "const errorResults = {};\n"
                "for (const x of errorInputs) {\n"
                "  totalChecked++;\n"
                "  const b = callSteps(beforeMod.steps, x);\n"
                "  const a = callSteps(afterMod.steps, x);\n"
                "  if (JSON.stringify(b) !== JSON.stringify(a) || a.ok !== false) {\n"
                "    mismatches.push({ input: String(x), before: b, after: a });\n"
                "  }\n"
                "  errorResults[String(x)] = a;\n"
                "}\n"
                "console.log(JSON.stringify({\n"
                "  range: '1..100000',\n"
                "  error_inputs: ['0', '-15', '1.5', 'NaN'],\n"
                "  total_checked: totalChecked,\n"
                "  mismatch_count: mismatches.length,\n"
                "  mismatches,\n"
                "  samples,\n"
                "  error_results: errorResults,\n"
                "}, null, 2));\n"
            )
            sweep_run = run_cmd(["node", "--input-type=module", "-e", sweep_script], sweep_dir, env)
            sweep_json = json.loads(sweep_run.stdout) if sweep_run.returncode == 0 else None
            if sweep_json is not None:
                (WORK / "equivalence-sweep.json").write_text(
                    json.dumps(sweep_json, indent=2) + "\n", encoding="utf-8"
                )
            sweep_ok = (
                tsc_res.returncode == 0
                and sweep_run.returncode == 0
                and sweep_json is not None
                and sweep_json.get("total_checked") == 100004
                and sweep_json.get("mismatch_count") == 0
            )
            record(
                "T034. equivalence sweep (1..100000 + error inputs) 0 mismatches",
                sweep_ok,
                f"checked={sweep_json.get('total_checked') if sweep_json else None}",
            )

            # Expected vs actual & counts
            expected_vs_actual = []
            named_set = set(NAMED_CASES)
            if after_jest:
                for suite in after_jest.get("testResults", []):
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
                "static_case_count": after_static,
                "expected_cases": EXPECTED_CASES,
                "jest": {
                    "numTotalTests": after_jest.get("numTotalTests") if after_jest else None,
                    "numPassedTests": after_jest.get("numPassedTests") if after_jest else None,
                    "numFailedTests": after_jest.get("numFailedTests") if after_jest else None,
                    "numPendingTests": after_jest.get("numPendingTests") if after_jest else None,
                },
                "jest_before": {
                    "numTotalTests": before_jest.get("numTotalTests") if before_jest else None,
                    "numPassedTests": before_jest.get("numPassedTests") if before_jest else None,
                    "numFailedTests": before_jest.get("numFailedTests") if before_jest else None,
                    "numPendingTests": before_jest.get("numPendingTests") if before_jest else None,
                },
            }
            (WORK / "counts.json").write_text(json.dumps(counts_data, indent=2) + "\n", encoding="utf-8")

            # G. Negative controls (reusing copy_after)
            sol_copy = copy_after / files_map["solution"][0]
            orig_sol = sol_copy.read_text(encoding="utf-8")
            sol_copy.write_text(
                orig_sol.replace("return stepsSoFar", "return stepsSoFar + 1", 1),
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
                copy_after,
                env,
            )
            nc1_json = json.loads(nc1_json_path.read_text(encoding="utf-8")) if nc1_json_path.exists() else None
            nc1_fail = evaluate(nc1_r.returncode, nc1_json, EXPECTED_CASES, NAMED_CASES)
            nc1_ok = nc1_r.returncode != 0 and len(nc1_fail) > 0
            sol_copy.write_text(orig_sol, encoding="utf-8")

            test_copy = copy_after / files_map["test"][0]
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
                copy_after,
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

            nc3_fail = evaluate(1, after_jest, EXPECTED_CASES, NAMED_CASES)
            nc3_ok = any("non-zero exit code" in f for f in nc3_fail)

            nc_report = {
                "assertion_failure": {"detected": nc1_ok, "returncode": nc1_r.returncode, "failures": nc1_fail},
                "zero_tests": {"detected": nc2_ok, "returncode": nc2_r.returncode, "failures": nc2_fail},
                "child_failure": {"detected": nc3_ok, "returncode": 1, "failures": nc3_fail},
            }
            (WORK / "negative-controls.json").write_text(json.dumps(nc_report, indent=2) + "\n", encoding="utf-8")
            record("G. negative controls all caught", nc1_ok and nc2_ok and nc3_ok)

            # H. tool-versions.json and inputs.json
            tsc_ver = run_cmd([corepack_bin, "yarn", "tsc", "--version"], copy_after, env).stdout.strip()
            jest_ver = run_cmd([corepack_bin, "yarn", "jest", "--version"], copy_after, env).stdout.strip()
            head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
            org_sha = subprocess.check_output(["git", "rev-parse", base_ref], cwd=REPO, text=True).strip()
            tool_versions = {
                "python": sys.version.split()[0],
                "node": subprocess.check_output(["node", "--version"], text=True).strip(),
                "corepack": subprocess.check_output([corepack_bin, "--version"], text=True).strip(),
                "yarn": subprocess.check_output([corepack_bin, "yarn", "--version"], cwd=REPO, text=True).strip(),
                "tsc": tsc_ver,
                "jest": jest_ver,
                "ts_outside_jest_method": "corepack yarn tsc <files> --outDir <tmp>/out --target es2020 --module nodenext --moduleResolution nodenext --strict (no -p)",
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
