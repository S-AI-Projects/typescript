#!/usr/bin/env python3
"""
tools/course_checks/r47-t028.py

Metadata path validator for exercises/practice/split-second-stopwatch.

Requirements:
1. Parse the JSON configuration (config.json).
2. Read the 'files' object.
3. Resolve every declared file path relative to the exercise directory.
4. Ensure every resolved path remains inside the exercise directory.
5. Reject:
   - Parent-directory traversal such as ../
   - Absolute paths outside the exercise
   - Missing files
   - Invalid or malformed configuration entries
6. Check that every declared file exists on disk.
7. Produce clear error messages identifying the invalid file role and path.
8. Exit with code 0 for valid metadata.
9. Exit with code 1 for invalid metadata.
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXERCISE_DIR = (
    DEFAULT_REPO_ROOT / "exercises" / "practice" / "split-second-stopwatch"
)
DEFAULT_CONFIG_PATH = DEFAULT_EXERCISE_DIR / ".meta" / "config.json"


def validate_metadata(
    config_path: Path, exercise_dir: Path | None = None
) -> tuple[bool, list[str]]:
    """Validate that all file paths declared in config.json exist and do not escape the exercise directory.

    Returns (is_valid, error_messages).
    """
    errors: list[str] = []

    config_path = Path(config_path)
    if not config_path.is_file():
        errors.append(f"Configuration file not found: {config_path}")
        return False, errors

    if exercise_dir is None:
        # If config is at <exercise>/.meta/config.json, exercise_dir is parent of .meta
        if config_path.parent.name == ".meta":
            exercise_dir = config_path.parents[1].resolve()
        else:
            exercise_dir = config_path.parent.resolve()
    else:
        exercise_dir = Path(exercise_dir).resolve()

    if not exercise_dir.is_dir():
        errors.append(f"Exercise directory not found: {exercise_dir}")
        return False, errors

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Malformed JSON configuration in {config_path}: {exc}")
        return False, errors
    except Exception as exc:
        errors.append(f"Unable to read configuration {config_path}: {exc}")
        return False, errors

    if not isinstance(data, dict):
        errors.append("Configuration root must be a JSON object")
        return False, errors

    files_obj = data.get("files")
    if files_obj is None:
        errors.append("Configuration missing required 'files' object")
        return False, errors

    if not isinstance(files_obj, dict):
        errors.append("'files' property must be a JSON object")
        return False, errors

    if len(files_obj) == 0:
        errors.append("'files' object is empty; must declare file roles")
        return False, errors

    for role, file_list in files_obj.items():
        if not isinstance(file_list, list):
            errors.append(
                f"Role '{role}': Expected list of path strings, got {type(file_list).__name__}"
            )
            continue

        if len(file_list) == 0:
            errors.append(f"Role '{role}': Declared path list is empty")
            continue

        for entry in file_list:
            if not isinstance(entry, str):
                errors.append(
                    f"Role '{role}': Path entry must be a string, got {type(entry).__name__}: {entry!r}"
                )
                continue

            entry_str = entry.strip()
            if not entry_str:
                errors.append(f"Role '{role}': Path string cannot be empty")
                continue

            # Check for parent-directory traversal in path specification
            parts = Path(entry_str).parts
            if ".." in parts:
                errors.append(
                    f"Role '{role}': Path '{entry_str}' contains forbidden parent-directory traversal ('..')"
                )
                continue

            entry_path = Path(entry_str)
            if entry_path.is_absolute():
                resolved_path = entry_path.resolve()
            else:
                resolved_path = (exercise_dir / entry_path).resolve()

            # Ensure resolved path remains strictly inside the exercise directory
            try:
                resolved_path.relative_to(exercise_dir)
            except ValueError:
                errors.append(
                    f"Role '{role}': Path '{entry_str}' escapes exercise directory (resolved to '{resolved_path}')"
                )
                continue

            # Check that declared file actually exists on disk
            if not resolved_path.is_file():
                errors.append(
                    f"Role '{role}': Declared file '{entry_str}' does not exist on disk (resolved to '{resolved_path}')"
                )

    is_valid = len(errors) == 0
    return is_valid, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate exercise metadata file paths in config.json"
    )
    parser.add_argument(
        "config_path",
        nargs="?",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to config.json (default: exercises/practice/split-second-stopwatch/.meta/config.json)",
    )
    parser.add_argument(
        "--exercise-dir",
        default=None,
        help="Explicit exercise directory override",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config_path).resolve()
    ex_dir = Path(args.exercise_dir).resolve() if args.exercise_dir else None

    print(f"Validating exercise metadata: {cfg_path}")
    is_valid, errors = validate_metadata(cfg_path, ex_dir)

    if is_valid:
        print("[SUCCESS] All declared file paths are valid and exist on disk.")
        return 0
    else:
        print(f"[ERROR] Validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
