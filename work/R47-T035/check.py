#!/usr/bin/env python3
"""Verification check for R47-T035 (darts)."""

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
SLUG = "darts"
EX = REPO / "exercises" / "practice" / SLUG
WORK = REPO / "work" / "R47-T035"
DOC_PATH = REPO / "docs" / "maintenance" / "darts.md"
EXPECTED_CASES = 13

NAMED_CASES = [
    "Missed target",
    "On the outer circle",
    "On the middle circle",
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


def strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def normalize_non_comment_code(src: str) -> str:
    return "\n".join(line.strip() for line in strip_comments(src).splitlines() if line.strip())


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
        if not path_part.startswith("work/R47-T035/"):
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


def parse_doc_operation_table(doc_text: str) -> dict[int, dict[str, int | str]]:
    """Parse markdown operation table rows for regions 0, 1, 5, 10."""
    rows: dict[int, dict[str, int | str]] = {}
    row_re = re.compile(
        r"^\|\s*`?(0|1|5|10)`?\s*\|"
        r"\s*([^|]+?)\s*\|"
        r"\s*`?(\d+)`?\s*\|"
        r"\s*`?(\d+)`?\s*\|"
        r"\s*`?(\d+)`?\s*\|"
        r"\s*`?(\d+)`?\s*\|"
        r"\s*([^|]+?)\s*\|$",
        re.MULTILINE,
    )
    for m in row_re.finditer(doc_text):
        pts = int(m.group(1))
        rows[pts] = {
            "points": pts,
            "representative": m.group(2).strip(),
            "multiplications": int(m.group(3)),
            "additions": int(m.group(4)),
            "sqrt_calls": int(m.group(5)),
            "comparisons": int(m.group(6)),
            "return_stmt": m.group(7).strip(),
        }
    return rows


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

        # T035 extra 1: assert only comment lines changed in proof.ci.ts vs org/main
        ref_rel = f"exercises/practice/{SLUG}/{files_map['example'][0]}"
        before_ref_src = subprocess.check_output(
            ["git", "show", f"{base_ref}:{ref_rel}"],
            cwd=REPO,
            text=True,
            encoding="utf-8",
        )
        after_ref_src = ref_path.read_text(encoding="utf-8")
        comment_only_change = (
            before_ref_src != after_ref_src
            and normalize_non_comment_code(before_ref_src) == normalize_non_comment_code(after_ref_src)
        )
        record("T035. only comment lines changed in proof.ci.ts vs org/main", comment_only_change)

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

            # Exercise eslint check on edited .meta/proof.ci.ts
            lint_res = run_cmd([corepack_bin, "yarn", "lint:ci"], copy_dir, env)
            (WORK / "eslint.log").write_text(normalize_log(lint_res.stdout + lint_res.stderr, tmp_root), encoding="utf-8")
            record("T035. exercise eslint passes on .meta/proof.ci.ts", lint_res.returncode == 0, f"rc={lint_res.returncode}")

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

            # T035 extra 2: Instrumented operation counts + separate timing measurement
            inst_dir = tmp_root / "inst"
            inst_dir.mkdir(parents=True, exist_ok=True)
            out_dir = inst_dir / "out"
            out_dir.mkdir(parents=True, exist_ok=True)

            # Compile unmodified score in temp copy and measure compile time separately
            import time

            ref_ts = inst_dir / "score_ref.ts"
            ref_ts.write_text(after_ref_src, encoding="utf-8")
            t_tsc_start = time.perf_counter_ns()
            tsc_res = run_cmd(
                [
                    corepack_bin,
                    "yarn",
                    "tsc",
                    str(ref_ts),
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
                copy_dir,
                env,
            )
            tsc_compile_ms = (time.perf_counter_ns() - t_tsc_start) / 1_000_000.0
            assert tsc_res.returncode == 0, f"tsc failed: {tsc_res.stdout} {tsc_res.stderr}"
            (out_dir / "package.json").write_text('{"type": "commonjs"}\n', encoding="utf-8")

            # Instrumented JS version matching proof.ci.ts exact branch structure
            inst_script = (
                "import { createRequire } from 'node:module';\n"
                "const require = createRequire(import.meta.url);\n"
                f"const {{ score }} = require({json.dumps(str(out_dir / 'score_ref.js'))});\n"
                "function instrumentedScore(x, y) {\n"
                "  const ops = { multiplications: 0, additions: 0, sqrt_calls: 0, comparisons: 0, return_branch: '' };\n"
                "  const mul = (a, b) => { ops.multiplications++; return a * b; };\n"
                "  const add = (a, b) => { ops.additions++; return a + b; };\n"
                "  const sq = (v) => { ops.sqrt_calls++; return Math.sqrt(v); };\n"
                "  const gt = (a, b) => { ops.comparisons++; return a > b; };\n"
                "  const distanceToDart = sq(add(mul(x, x), mul(y, y)));\n"
                "  if (gt(distanceToDart, 10)) { ops.return_branch = 'return 0'; return { points: 0, ops }; }\n"
                "  if (gt(distanceToDart, 5)) { ops.return_branch = 'return 1'; return { points: 1, ops }; }\n"
                "  if (gt(distanceToDart, 1)) { ops.return_branch = 'return 5'; return { points: 5, ops }; }\n"
                "  ops.return_branch = 'return 10';\n"
                "  return { points: 10, ops };\n"
                "}\n"
                "const cases = [\n"
                "  { name: 'Missed target', x: -9, y: 9, expected: 0 },\n"
                "  { name: 'On the outer circle', x: 0, y: 10, expected: 1 },\n"
                "  { name: 'On the middle circle', x: -5, y: 0, expected: 5 },\n"
                "  { name: 'On the inner circle', x: 0, y: -1, expected: 10 },\n"
                "];\n"
                "const instrumented = [];\n"
                "for (const c of cases) {\n"
                "  const realVal = score(c.x, c.y);\n"
                "  const res = instrumentedScore(c.x, c.y);\n"
                "  if (realVal !== c.expected || res.points !== c.expected) {\n"
                "    throw new Error(`Correctness assertion failed for ${c.name}`);\n"
                "  }\n"
                "  instrumented.push({ name: c.name, x: c.x, y: c.y, points: res.points, ...res.ops });\n"
                "}\n"
                "// Warm-up\n"
                "let sink = 0;\n"
                "for (const c of cases) {\n"
                "  for (let i = 0; i < 100000; i++) sink += score(c.x, c.y);\n"
                "}\n"
                "// Measure inside one Node process: N=1,000,000 calls x 7 repetitions\n"
                "const N = 1000000;\n"
                "const REPS = 7;\n"
                "const timings = [];\n"
                "for (const c of cases) {\n"
                "  const perRepNs = [];\n"
                "  for (let r = 0; r < REPS; r++) {\n"
                "    const t0 = process.hrtime.bigint();\n"
                "    for (let i = 0; i < N; i++) sink += score(c.x, c.y);\n"
                "    const dt = Number(process.hrtime.bigint() - t0);\n"
                "    perRepNs.push(dt / N);\n"
                "  }\n"
                "  const sorted = [...perRepNs].sort((a, b) => a - b);\n"
                "  const medianNs = sorted[Math.floor(REPS / 2)];\n"
                "  timings.push({ name: c.name, points: c.expected, n_calls: N, reps: REPS, per_rep_ns: perRepNs, median_ns_per_call: medianNs });\n"
                "}\n"
                "console.log(JSON.stringify({ sink, instrumented, timings }, null, 2));\n"
            )
            t_node_start = time.perf_counter_ns()
            startup_probe = run_cmd(["node", "-e", "0"], inst_dir, env)
            node_startup_ms = (time.perf_counter_ns() - t_node_start) / 1_000_000.0
            assert startup_probe.returncode == 0

            bench_res = run_cmd(["node", "--input-type=module", "-e", inst_script], inst_dir, env)
            assert bench_res.returncode == 0, f"bench failed: {bench_res.stderr}"
            bench_data = json.loads(bench_res.stdout)
            bench_data["tsc_compile_ms"] = round(tsc_compile_ms, 3)
            bench_data["node_startup_ms"] = round(node_startup_ms, 3)
            (WORK / "operation-counts-and-timing.json").write_text(
                json.dumps(bench_data, indent=2) + "\n", encoding="utf-8"
            )

            doc_ok = False
            if DOC_PATH.is_file():
                parsed_rows = parse_doc_operation_table(DOC_PATH.read_text(encoding="utf-8"))
                inst_by_pts = {row["points"]: row for row in bench_data["instrumented"]}
                doc_ok = len(parsed_rows) == 4 and all(
                    pts in parsed_rows
                    and parsed_rows[pts]["multiplications"] == inst_by_pts[pts]["multiplications"]
                    and parsed_rows[pts]["additions"] == inst_by_pts[pts]["additions"]
                    and parsed_rows[pts]["sqrt_calls"] == inst_by_pts[pts]["sqrt_calls"]
                    and parsed_rows[pts]["comparisons"] == inst_by_pts[pts]["comparisons"]
                    and inst_by_pts[pts]["return_branch"] in str(parsed_rows[pts]["return_stmt"])
                    for pts in (0, 1, 5, 10)
                )
            record("T035. docs/maintenance/darts.md operation table matches instrumented counts", doc_ok)

            # Standard evidence
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
            sol_copy.write_text(orig_sol.replace("return 0", "return 99", 1), encoding="utf-8")
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
                "ts_outside_jest_method": "corepack yarn tsc <file> --outDir <tmp>/out --target es2020 --module nodenext --moduleResolution nodenext --strict (no -p)",
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
