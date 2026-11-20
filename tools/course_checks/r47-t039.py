#!/usr/bin/env python3
"""Isolated runner for Exercism TypeScript exercises that protects learner files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ENABLE_RULES = [
    (re.compile(r"x(test|it)\("), "it("),
    (re.compile(r"xdescribe\("), "describe("),
    (re.compile(r"x(test|it|describe), ?"), ""),
    (re.compile(r", ?x(test|it|describe) ?}"), "}"),
]

CASE_RE = re.compile(r"^\s*(it|test)\(", re.MULTILINE)

_ACTIVE_PROC: subprocess.Popen[str] | None = None


def _handle_interrupt(signum: int, _frame: object) -> None:
    global _ACTIVE_PROC
    if _ACTIVE_PROC is not None and _ACTIVE_PROC.poll() is None:
        try:
            _ACTIVE_PROC.terminate()
        except OSError:
            pass
    raise KeyboardInterrupt(f"Interrupted by signal {signum}")


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


def resolve_files(ex_dir: Path, repo_root: Path) -> dict[str, list[str]]:
    cfg_path = ex_dir / ".meta" / "config.json"
    if cfg_path.is_file():
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        if data.get("files") and len(data["files"].get("test", [])) > 0:
            files_map = data["files"]
        else:
            files_map = json.loads((repo_root / "config.json").read_text(encoding="utf-8"))["files"]
    else:
        files_map = json.loads((repo_root / "config.json").read_text(encoding="utf-8"))["files"]

    slug = ex_dir.name
    ex_resolved = ex_dir.resolve()
    resolved_map: dict[str, list[str]] = {}
    for role in ("solution", "test", "example", "exemplar"):
        if role not in files_map:
            continue
        entries = [e.replace("%{kebab_slug}", slug) for e in files_map[role]]
        for rel in entries:
            p = (ex_dir / rel).resolve()
            if not p.exists():
                raise FileNotFoundError(f"Missing {role} file: {p}")
            if not p.is_relative_to(ex_resolved):
                raise ValueError(f"Path escapes exercise dir: {p}")
        resolved_map[role] = entries
    return resolved_map


def run_step(cmd: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    global _ACTIVE_PROC
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    _ACTIVE_PROC = proc
    try:
        out, _ = proc.communicate(timeout=900)
        return proc.returncode, out
    except KeyboardInterrupt:
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
            proc.wait(timeout=5)
        raise
    finally:
        _ACTIVE_PROC = None


def evaluate(
    returncode: int,
    jest_json: dict | None,
    expected_cases: int | None,
    named_cases: list[str] | None = None,
) -> list[str]:
    failures: list[str] = []
    if returncode != 0:
        failures.append(f"non-zero exit code: {returncode}")
    if jest_json is None:
        failures.append("missing or invalid jest JSON output")
        return failures

    total = jest_json.get("numTotalTests", 0)
    failed = jest_json.get("numFailedTests", 0)
    pending = jest_json.get("numPendingTests", 0)
    executed = total - pending

    if total == 0 or executed == 0:
        failures.append(f"zero tests executed (total={total}, pending={pending})")
    if expected_cases is not None and total != expected_cases:
        failures.append(f"expected {expected_cases} total tests, got {total}")
    if failed > 0:
        failures.append(f"numFailedTests == {failed}")
    if pending > 0:
        failures.append(f"numPendingTests == {pending}")

    if named_cases:
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

    return failures


def remove_tree_with_retry(path: Path) -> None:
    if not path.exists():
        return
    for attempt in range(8):
        try:
            shutil.rmtree(path)
            return
        except OSError:
            if attempt < 7:
                time.sleep(0.25)
    shutil.rmtree(path, ignore_errors=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an Exercism TypeScript exercise in an isolated temp copy without altering learner files."
    )
    parser.add_argument(
        "--exercise",
        default="practice/isbn-verifier",
        help="Assignment path relative to exercises/, e.g. practice/isbn-verifier",
    )
    parser.add_argument(
        "--reference",
        default=None,
        help="Optional replacement TypeScript implementation file to test inside the isolated copy",
    )
    parser.add_argument(
        "--test-name-pattern",
        default=None,
        help="Optional Jest --testNamePattern regex",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional path to save Jest JSON results",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    signal.signal(signal.SIGINT, _handle_interrupt)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _handle_interrupt)

    args = parse_args(argv)
    repo = Path(__file__).resolve().parents[2]
    ex_rel = args.exercise.strip().replace("\\", "/")
    ex_dir = repo / "exercises" / ex_rel
    if not ex_dir.is_dir():
        print(f"FAIL: exercise directory not found: {ex_dir}")
        return 1

    files_map = resolve_files(ex_dir, repo)
    hashes_before = hash_tree(ex_dir)

    stub_path = ex_dir / files_map["solution"][0]
    test_path = ex_dir / files_map["test"][0]
    if "Remove this line and implement the function" not in stub_path.read_text(encoding="utf-8"):
        print("FAIL: learner solution stub appears modified or solved")
        return 1

    base_ref = "org/main"
    if subprocess.run(["git", "rev-parse", "--verify", "org/main"], cwd=repo, capture_output=True).returncode != 0:
        base_ref = subprocess.check_output(["git", "merge-base", "HEAD", "HEAD"], cwd=repo, text=True).strip()
    if subprocess.run(
        ["git", "diff", "--quiet", base_ref, "--", str(stub_path), str(test_path)],
        cwd=repo,
    ).returncode != 0:
        print(f"FAIL: learner files differ from {base_ref}")
        return 1

    corepack_bin = shutil.which("corepack")
    if corepack_bin is None:
        print("FAIL: corepack executable not found")
        return 1

    tmp_root = Path(tempfile.mkdtemp(prefix="r47-t039-"))
    print(f"TEMP_DIR: {tmp_root}", flush=True)

    exit_code = 1
    try:
        copy_dir = tmp_root / ex_dir.name
        shutil.copytree(
            ex_dir,
            copy_dir,
            ignore=shutil.ignore_patterns("node_modules", ".yarn", ".pnp.*"),
        )
        for req in (".meta", ".docs", ".yarnrc.yml", ".vscode"):
            if not (copy_dir / req).exists():
                raise RuntimeError(f"Missing {req} in temp copy")

        if args.reference:
            ref_src = Path(args.reference).read_text(encoding="utf-8").replace("from '../", "from './")
            (copy_dir / files_map["solution"][0]).write_text(ref_src, encoding="utf-8")
        else:
            ref_role = "exemplar" if ex_rel.startswith("concept/") else "example"
            for i, ref_rel in enumerate(files_map[ref_role]):
                ref_src = (copy_dir / ref_rel).read_text(encoding="utf-8").replace("from '../", "from './")
                (copy_dir / files_map["solution"][i]).write_text(ref_src, encoding="utf-8")

        test_copy = copy_dir / files_map["test"][0]
        enabled_src = enable_all(test_copy.read_text(encoding="utf-8"))
        test_copy.write_text(enabled_src, encoding="utf-8")

        if any(tok in enabled_src for tok in ("xit", "xtest", "xdescribe", ".skip(", ".only(")):
            print("FAIL: leftover skipped/focused tokens after enable_all")
            return 1
        static_count = len(CASE_RE.findall(enabled_src))

        env = {
            **os.environ,
            "CI": "true",
            "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0",
            "FORCE_COLOR": "0",
            "YARN_ENABLE_TELEMETRY": "0",
            "YARN_ENABLE_IMMUTABLE_INSTALLS": "false",
        }

        print("STEP: yarn install", flush=True)
        rc1, out1 = run_step([corepack_bin, "yarn", "install"], copy_dir, env)
        if rc1 != 0:
            print(f"FAIL: corepack yarn install exited {rc1}\n{out1}")
            return 1

        if args.test_name_pattern is None:
            print("STEP: yarn test", flush=True)
            rc2, out2 = run_step([corepack_bin, "yarn", "test"], copy_dir, env)
            if rc2 != 0:
                print(f"FAIL: corepack yarn test exited {rc2}\n{out2}")
                return 1
        else:
            print("STEP: yarn lint:types", flush=True)
            rc2, out2 = run_step([corepack_bin, "yarn", "lint:types"], copy_dir, env)
            if rc2 != 0:
                print(f"FAIL: corepack yarn lint:types exited {rc2}\n{out2}")
                return 1

        jest_out_path = tmp_root / "jest-results.json"
        cmd3 = [
            corepack_bin,
            "yarn",
            "test:implementation",
            "--ci",
            "--watchAll=false",
            "--json",
            f"--outputFile={jest_out_path}",
        ]
        if args.test_name_pattern is not None:
            cmd3.append(f"--testNamePattern={args.test_name_pattern}")

        print("STEP: yarn test:implementation", flush=True)
        rc3, out3 = run_step(cmd3, copy_dir, env)
        jest_json = json.loads(jest_out_path.read_text(encoding="utf-8")) if jest_out_path.exists() else None
        if args.json_out and jest_json is not None:
            Path(args.json_out).write_text(json.dumps(jest_json, indent=2) + "\n", encoding="utf-8")

        expected = None if args.test_name_pattern is not None else static_count
        failures = evaluate(rc3, jest_json, expected)
        if failures:
            print(f"FAIL: evaluation failed: {'; '.join(failures)}")
            return 1

        total = jest_json.get("numTotalTests", 0) if jest_json else 0
        pending = jest_json.get("numPendingTests", 0) if jest_json else 0
        executed = total - pending
        print(f"RESULT: PASS - executed {executed} cases", flush=True)
        exit_code = 0
        return 0

    except KeyboardInterrupt as exc:
        print(f"INTERRUPTED: {exc}", file=sys.stderr, flush=True)
        exit_code = 130
        return 130

    finally:
        remove_tree_with_retry(tmp_root)
        hashes_after = hash_tree(ex_dir)
        if hashes_before != hashes_after:
            print("FAIL: learner files changed during execution!", file=sys.stderr, flush=True)
            exit_code = 1
        else:
            print("HASH_CHECK: PASS - learner files unchanged", flush=True)
        if tmp_root.exists():
            print(f"CLEANUP_CHECK: FAIL - temp dir still exists: {tmp_root}", file=sys.stderr, flush=True)
            exit_code = 1
        else:
            print(f"CLEANUP_CHECK: PASS - temp dir removed: {tmp_root}", flush=True)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
