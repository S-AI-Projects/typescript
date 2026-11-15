#!/usr/bin/env python3
"""Metadata path checker for complex-numbers (R47-T048).

Reads the `files` object of
`exercises/practice/complex-numbers/.meta/config.json` — the same
object the exercise test runner uses to find the learner solution,
the test file and the reference (`.meta/proof.ci.ts`) — and verifies
that every declared path:

  * is a non-empty relative path,
  * resolves to a location inside the exercise directory (any path
    that escapes via `..` or an absolute path is rejected), and
  * names a file that actually exists.

The checker also runs three deliberately broken fixtures against
itself — a missing reference file, a missing test file, and a path
that escapes the exercise — and requires each of them to fail for
the intended reason, so a checker that passes everything is itself
caught.

Usage: python3 tools/course_checks/r47-t048.py [path-to-exercise-dir]
Exit code is non-zero when the real metadata or any fixture behaves
unexpectedly.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

FILE_KEYS = ("solution", "test", "example", "editor")


def validate(exercise: Path) -> list[str]:
    """Return a list of problems with the exercise's declared files."""
    problems = []
    config_path = exercise / ".meta" / "config.json"
    try:
        config = json.loads(config_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {config_path}: {exc}"]

    files = config.get("files")
    if not isinstance(files, dict):
        return ["config.json has no 'files' object"]

    root = exercise.resolve()
    for key in FILE_KEYS:
        declared = files.get(key)
        if declared is None:
            continue
        if not isinstance(declared, list) or not declared:
            problems.append(f"files.{key} is not a non-empty list")
            continue
        for rel in declared:
            if not isinstance(rel, str) or not rel:
                problems.append(f"files.{key} contains a non-string/empty entry")
                continue
            resolved = (exercise / rel).resolve()
            if resolved != root and root not in resolved.parents:
                problems.append(f"files.{key}: '{rel}' escapes the exercise directory")
                continue
            if not resolved.is_file():
                problems.append(f"files.{key}: '{rel}' does not exist")
    return problems


def make_fixture(tmp: Path, mutate) -> Path:
    """Copy the real exercise's config into a scratch exercise and mutate it."""
    fixture = tmp / "exercise"
    (fixture / ".meta").mkdir(parents=True)
    source = Path(__file__).resolve().parents[2] / (
        "exercises/practice/complex-numbers"
    )
    config = json.loads((source / ".meta" / "config.json").read_text())
    mutate(config, fixture, source)
    (fixture / ".meta" / "config.json").write_text(json.dumps(config))
    return fixture


def fixture_missing_reference(tmp: Path) -> list[str]:
    def mutate(config, fixture, source):
        # keep solution + test real, point example at a missing file
        for key in ("solution", "test"):
            for rel in config["files"][key]:
                shutil.copy(source / rel, fixture / rel)
        config["files"]["example"] = [".meta/does-not-exist.ts"]

    return validate(make_fixture(tmp, mutate))


def fixture_missing_test(tmp: Path) -> list[str]:
    def mutate(config, fixture, source):
        for rel in config["files"]["solution"]:
            shutil.copy(source / rel, fixture / rel)
        for rel in config["files"]["example"]:
            dest = fixture / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source / rel, dest)
        config["files"]["test"] = ["no-such-test.test.ts"]

    return validate(make_fixture(tmp, mutate))


def fixture_outside_path(tmp: Path) -> list[str]:
    def mutate(config, fixture, source):
        for key in ("solution", "test", "example"):
            for rel in config["files"][key]:
                dest = fixture / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(source / rel, dest)
        config["files"]["solution"] = ["../outside-the-exercise.ts"]

    return validate(make_fixture(tmp, mutate))


def main() -> int:
    if len(sys.argv) > 1:
        exercise = Path(sys.argv[1])
    else:
        exercise = (
            Path(__file__).resolve().parents[2]
            / "exercises/practice/complex-numbers"
        )

    failures = []

    real_problems = validate(exercise)
    print(f"real config ({exercise}): {'PASS' if not real_problems else 'FAIL'}")
    for problem in real_problems:
        print(f"  - {problem}")
        failures.append(problem)

    fixtures = [
        ("missing reference", fixture_missing_reference, "does-not-exist"),
        ("missing test", fixture_missing_test, "no-such-test"),
        ("outside-exercise path", fixture_outside_path, "escapes"),
    ]
    for name, fn, needle in fixtures:
        with tempfile.TemporaryDirectory() as tmp:
            problems = fn(Path(tmp))
        ok = bool(problems) and any(needle in p for p in problems)
        print(f"fixture '{name}': {'PASS (rejected as intended)' if ok else 'FAIL'} -> {problems}")
        if not ok:
            failures.append(f"fixture '{name}' was not rejected for the intended reason")

    print("RESULT:", "PASS" if not failures else "FAIL")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
