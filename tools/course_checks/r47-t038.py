#!/usr/bin/env python3
"""Validate maintained file paths in an exercise's .meta/config.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

ROLES = ("solution", "test", "example", "editor", "exemplar")
REQUIRED_ROLES = ("solution", "test", "example")


def validate_exercise(ex_dir: Path) -> tuple[bool, list[dict[str, str | bool]], list[str]]:
    errors: list[str] = []
    rows: list[dict[str, str | bool]] = []

    if not ex_dir.is_dir():
        errors.append(f"ERR_MISSING_EXERCISE_DIR: {ex_dir}")
        return False, rows, errors

    ex_resolved = ex_dir.resolve()
    config_path = ex_dir / ".meta" / "config.json"
    if not config_path.is_file():
        errors.append(f"ERR_MISSING_CONFIG: {config_path}")
        return False, rows, errors

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"ERR_INVALID_JSON: {exc}")
        return False, rows, errors

    files_obj = config.get("files")
    if not isinstance(files_obj, dict):
        errors.append("ERR_MISSING_FILES_MAP: config.json missing 'files' object")
        return False, rows, errors

    for req_role in REQUIRED_ROLES:
        entries = files_obj.get(req_role)
        if not isinstance(entries, list) or len(entries) == 0:
            errors.append(f"ERR_EMPTY_ROLE:{req_role}: expected at least one {req_role} file")

    for role in ROLES:
        if role not in files_obj:
            continue
        entries = files_obj[role]
        if not isinstance(entries, list):
            errors.append(f"ERR_INVALID_ROLE:{role}: value must be a list")
            continue

        for raw_path in entries:
            if not isinstance(raw_path, str) or not raw_path.strip():
                errors.append(f"ERR_INVALID_PATH:{role}: empty or non-string path")
                rows.append({"role": role, "path": str(raw_path), "exists": False})
                continue

            posix_norm = raw_path.replace("\\", "/")
            if (
                Path(raw_path).is_absolute()
                or PureWindowsPath(raw_path).is_absolute()
                or posix_norm.startswith("/")
            ):
                errors.append(f"ERR_ABSOLUTE_PATH:{role}: {raw_path!r} must be relative")
                rows.append({"role": role, "path": raw_path, "exists": False})
                continue

            parts = PurePosixPath(posix_norm).parts
            if ".." in parts:
                errors.append(f"ERR_PARENT_TRAVERSAL:{role}: {raw_path!r} contains '..'")
                rows.append({"role": role, "path": raw_path, "exists": False})
                continue

            candidate = (ex_dir / posix_norm).resolve()
            if not candidate.is_relative_to(ex_resolved):
                errors.append(
                    f"ERR_ESCAPE_DIR:{role}: {raw_path!r} resolves outside exercise directory ({candidate})"
                )
                rows.append({"role": role, "path": raw_path, "exists": False})
                continue

            exists = candidate.is_file()
            rows.append({"role": role, "path": raw_path, "exists": exists})
            if not exists:
                errors.append(f"ERR_MISSING_FILE:{role}: {raw_path!r} not found at {candidate}")

    return len(errors) == 0, rows, errors


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("Usage: python3 tools/course_checks/r47-t038.py <exercise-dir>")
        return 1

    ex_dir = Path(args[0])
    ok, rows, errors = validate_exercise(ex_dir)

    print(f"Exercise: {ex_dir}")
    print(f"{'role':<10} | {'path':<30} | {'exists'}")
    print(f"{'-' * 10}-+-{'-' * 30}-+-{'-' * 6}")
    for r in rows:
        print(f"{str(r['role']):<10} | {str(r['path']):<30} | {r['exists']}")

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("\nVALID: all configured file roles resolved and exist inside exercise directory.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
