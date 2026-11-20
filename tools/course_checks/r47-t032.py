#!/usr/bin/env python3
"""Verify that scripts/helpers.mjs prepare() produces byte-identical outputs across fresh repo archives."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ENABLE_RULES = [
    (re.compile(r"x(test|it)\("), "it("),
    (re.compile(r"xdescribe\("), "describe("),
    (re.compile(r"x(test|it|describe), ?"), ""),
    (re.compile(r", ?x(test|it|describe) ?}"), "}"),
]


def enable_all(src: str) -> str:
    """Mirror scripts/helpers.mjs prepare(): first match per line, rules in order."""
    for rx, rep in ENABLE_RULES:
        src = "".join(rx.sub(rep, ln, count=1) for ln in src.splitlines(keepends=True))
    return src


def normalize_generated(data: bytes) -> bytes:
    """Normalisation step for generated exercise files.

    Neither tmp_exercises/<slug>.test.ts nor tmp_exercises/<slug>.ts produced by
    scripts/helpers.mjs prepare() embeds timestamps, absolute paths, or
    invocation-specific tokens, so the normalisation step is the identity
    function (data -> data).
    """
    return data


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_git_archive(repo: Path, rev: str, dst: Path) -> None:
    res = subprocess.run(
        ["git", "archive", "--format=tar", rev],
        cwd=repo,
        capture_output=True,
        timeout=300,
    )
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git archive failed for rev {rev!r}: {err}")
    with tarfile.open(fileobj=io.BytesIO(res.stdout), mode="r|*") as tf:
        if hasattr(tarfile, "data_filter"):
            tf.extractall(dst, filter="data")
        else:
            tf.extractall(dst)


def resolve_exercise_files(repo_copy: Path, exercise: str) -> tuple[list[str], list[str]]:
    ex_config = repo_copy / "exercises" / exercise / ".meta" / "config.json"
    files_cfg = None
    if ex_config.is_file():
        data = json.loads(ex_config.read_text(encoding="utf-8"))
        if data.get("files") and len(data["files"].get("test", [])) > 0:
            files_cfg = data["files"]
    if files_cfg is None:
        root_cfg = json.loads((repo_copy / "config.json").read_text(encoding="utf-8"))
        files_cfg = root_cfg["files"]

    slug = Path(exercise).name
    resolved: dict[str, list[str]] = {}
    for key, entries in files_cfg.items():
        resolved[key] = [e.replace("%{kebab_slug}", slug) for e in entries]
    return resolved["test"], resolved["solution"]


def run_prepare_in_copy(
    repo: Path,
    rev: str,
    exercise: str,
    corepack_bin: str,
    label: str,
) -> tuple[dict[str, bytes], str]:
    with tempfile.TemporaryDirectory(prefix=f"r47-t032-{label}-", ignore_cleanup_errors=True) as td:
        copy_dir = Path(td) / "repo"
        copy_dir.mkdir(parents=True, exist_ok=True)
        extract_git_archive(repo, rev, copy_dir)

        base_env = {
            **os.environ,
            "CI": "true",
            "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0",
            "FORCE_COLOR": "0",
            "YARN_ENABLE_TELEMETRY": "0",
        }

        install_res = subprocess.run(
            [corepack_bin, "yarn", "install", "--immutable"],
            cwd=copy_dir,
            env=base_env,
            timeout=900,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if install_res.returncode != 0:
            raise RuntimeError(
                f"[{label}] corepack yarn install --immutable failed (rc={install_res.returncode}):\n"
                + install_res.stdout
                + install_res.stderr
            )

        driver_path = copy_dir / "driver.mjs"
        driver_path.write_text(
            "import { prepareAndRun } from './scripts/helpers.mjs'\n"
            "prepareAndRun('node -e \"0\"', 'Preparing assignment...', 'Prepare failed')\n",
            encoding="utf-8",
        )

        prep_env = {
            **base_env,
            "PREPARE": "true",
            "CLEANUP": "false",
            "ASSIGNMENT": exercise,
        }
        prep_res = subprocess.run(
            [corepack_bin, "yarn", "node", "driver.mjs"],
            cwd=copy_dir,
            env=prep_env,
            timeout=900,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if prep_res.returncode != 0:
            raise RuntimeError(
                f"[{label}] driver.mjs failed (rc={prep_res.returncode}):\n"
                + prep_res.stdout
                + prep_res.stderr
            )

        test_rels, sol_rels = resolve_exercise_files(copy_dir, exercise)
        source_test = (copy_dir / "exercises" / exercise / test_rels[0]).read_text(encoding="utf-8")

        outputs: dict[str, bytes] = {}
        for rel in test_rels + sol_rels:
            gen_path = copy_dir / "tmp_exercises" / rel
            if not gen_path.is_file():
                raise RuntimeError(f"[{label}] expected generated file missing: {gen_path}")
            outputs[rel] = gen_path.read_bytes()

        return outputs, source_test


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify reproducibility of scripts/helpers.mjs prepare() across two clean git archives."
    )
    parser.add_argument(
        "--exercise",
        default="practice/accumulate",
        help="Assignment path relative to exercises/, e.g. practice/accumulate (default: practice/accumulate)",
    )
    parser.add_argument(
        "--rev",
        default="org/main",
        help="Git revision to archive into two isolated copies (default: org/main)",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Optional directory to write generated files and reproducibility.json",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(__file__).resolve().parents[2]
    exercise = args.exercise.strip().replace("\\", "/")
    if "/" not in exercise or len(exercise.split("/")) != 2:
        print(f"FAIL: --exercise must have form <type>/<slug>, got {exercise!r}")
        return 1

    corepack_bin = shutil.which("corepack")
    if corepack_bin is None:
        print("FAIL: corepack executable not found on PATH")
        return 1

    rev = args.rev
    rev_check = subprocess.run(
        ["git", "rev-parse", "--verify", rev],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if rev_check.returncode != 0:
        print(f"FAIL: git revision {rev!r} not found")
        return 1
    rev_sha = rev_check.stdout.strip()

    outputs_1, src_test_1 = run_prepare_in_copy(repo, rev, exercise, corepack_bin, "copy1")
    outputs_2, src_test_2 = run_prepare_in_copy(repo, rev, exercise, corepack_bin, "copy2")

    if src_test_1 != src_test_2:
        print("FAIL: source test file differed between git archives")
        return 1

    expected_enabled = enable_all(src_test_1).encode("utf-8")

    files_report: dict[str, dict] = {}
    all_ok = True

    for rel in sorted(set(outputs_1.keys()) | set(outputs_2.keys())):
        b1 = normalize_generated(outputs_1[rel])
        b2 = normalize_generated(outputs_2[rel])
        h1 = sha256_bytes(b1)
        h2 = sha256_bytes(b2)
        match = b1 == b2
        diff_lines: list[str] = []
        if not match:
            all_ok = False
            diff_lines = list(
                difflib.unified_diff(
                    b1.decode("utf-8", errors="replace").splitlines(keepends=True),
                    b2.decode("utf-8", errors="replace").splitlines(keepends=True),
                    fromfile=f"copy1/tmp_exercises/{rel}",
                    tofile=f"copy2/tmp_exercises/{rel}",
                )
            )
            print(f"FAIL: mismatch for tmp_exercises/{rel}: {h1} != {h2}")
            sys.stdout.writelines(diff_lines)
        else:
            print(f"PASS: tmp_exercises/{rel} identical across both copies (sha256={h1})")

        entry: dict = {
            "copy1_sha256": h1,
            "copy2_sha256": h2,
            "identical": match,
            "byte_length": len(b1),
            "diff": "".join(diff_lines),
        }

        if rel.endswith(".test.ts"):
            eq_enable_all = b1 == expected_enabled and b2 == expected_enabled
            entry["equals_enable_all"] = eq_enable_all
            if not eq_enable_all:
                all_ok = False
                enable_diff = list(
                    difflib.unified_diff(
                        expected_enabled.decode("utf-8", errors="replace").splitlines(keepends=True),
                        b1.decode("utf-8", errors="replace").splitlines(keepends=True),
                        fromfile="enable_all(source)",
                        tofile=f"copy1/tmp_exercises/{rel}",
                    )
                )
                entry["enable_all_diff"] = "".join(enable_diff)
                print(f"FAIL: tmp_exercises/{rel} differs from enable_all(source)")
                sys.stdout.writelines(enable_diff)
            else:
                print(f"PASS: tmp_exercises/{rel} equals enable_all(source test)")

        files_report[rel] = entry

    summary = {
        "exercise": exercise,
        "rev": rev,
        "rev_sha": rev_sha,
        "normalization": "identity (no timestamps or run-specific tokens exist in prepare() outputs)",
        "reproducible": all_ok,
        "files": files_report,
    }

    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for idx, outs in ((1, outputs_1), (2, outputs_2)):
            cdir = out_dir / f"copy{idx}"
            cdir.mkdir(parents=True, exist_ok=True)
            for rel, raw in outs.items():
                target = cdir / Path(rel).name
                target.write_bytes(raw)
        (out_dir / "reproducibility.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )

    if all_ok:
        print(f"RESULT: PASS - {exercise} prepare() outputs are byte-for-byte reproducible")
        return 0
    print(f"RESULT: FAIL - {exercise} prepare() reproducibility check failed")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"RESULT: FAIL - unexpected exception: {exc}")
        sys.exit(1)
