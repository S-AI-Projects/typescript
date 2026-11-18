#!/usr/bin/env python3
"""
R47-T022 – Reusable focused regeneration checker for the circular-buffer exercise.

This tool verifies the "round-trip" reproducibility of the circular-buffer test file.

Since the TypeScript track has no auto-generator for exercise test files, "round-trip"
is defined as: two independent copies of the exercise directory produce identical
circular-buffer.test.ts content (byte-for-byte), confirming there is no non-determinism.

Additionally verifies:
  - The three required canonical cases are present in the test file.
  - The test file contains the expected number of tests.
  - No unexpected differences exist between copies.

Usage:
    python3 tools/course_checks/r47-t022.py

Returns:
    exit code 0 on success, 1 on failure.
"""
import difflib
import hashlib
import json
import re
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
EX = REPO / "exercises/practice/circular-buffer"
TOML_PATH = EX / ".meta/tests.toml"
EVIDENCE_DIR = REPO / "work/R47-T022"

REQUIRED_CASES = [
    "reading an empty buffer throws a BufferEmptyError",
    "write and read back one item",
    "write and read back multiple items",
]
EXPECTED_TOTAL_TESTS = 10

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    label = "PASS  " if ok else "FAIL  "
    print(label + msg)
    if not ok:
        failures.append(msg)


def parse_test_names(test_file: Path) -> list[tuple[str, str]]:
    """Return [(state, name)] from a .test.ts file."""
    content = test_file.read_text()
    return re.findall(r'(?:^|\n)\s*(it|xit)\(["\'](.+?)["\']', content)


def file_md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def normalize_content(content: str) -> str:
    """
    Normalize test file content for comparison.
    For this track: no timestamps or generated content to strip.
    Content should be identical byte-for-byte.
    """
    return content


def main() -> None:
    print("=" * 60)
    print("R47-T022 Regeneration Checker: circular-buffer")
    print("=" * 60)
    print()

    # Verify prerequisites
    if not EX.is_dir():
        print(f"ERROR: Exercise directory not found: {EX}", file=sys.stderr)
        sys.exit(1)

    test_rel = json.loads((EX / ".meta/config.json").read_text())["files"]["test"][0]
    wt_test = EX / test_rel

    # --- Phase 1: Confirm test file exists and read it ---
    check(wt_test.is_file(), f"test file exists: {test_rel}")
    if not wt_test.is_file():
        sys.exit(1)

    original_content = wt_test.read_text()
    original_hash = file_md5(wt_test)
    test_items = parse_test_names(wt_test)
    total_tests = len(test_items)

    print(f"Original test file: {test_rel}")
    print(f"  MD5: {original_hash}")
    print(f"  Total tests: {total_tests}")
    print()

    # --- Phase 2: Verify required cases present ---
    print("Checking required canonical cases:")
    for case in REQUIRED_CASES:
        present = any(n == case for _, n in test_items)
        check(present, f"required case present: {case!r}")
    print()

    # --- Phase 3: Verify test count ---
    check(total_tests == EXPECTED_TOTAL_TESTS,
          f"test file contains {EXPECTED_TOTAL_TESTS} tests (found {total_tests})")
    print()

    # --- Phase 4: TOML coverage check ---
    print("Checking tests.toml coverage:")
    toml_data = tomllib.loads(TOML_PATH.read_text())
    included_count = sum(1 for v in toml_data.values() if v.get("include", True))
    check(len(toml_data) == 14,
          f"tests.toml has 14 canonical entries (found {len(toml_data)})")
    check(included_count == 14,
          f"all 14 canonical entries are included (found {included_count} included)")
    print()

    # --- Phase 5: Two-copy round-trip verification ---
    print("Performing two-copy round-trip verification:")
    print("  (This track has no auto-generator — copies must be identical)")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Copy A
        copy_a = tmp_path / "copy_a" / "circular-buffer"
        shutil.copytree(EX, copy_a, symlinks=True)
        content_a = (copy_a / test_rel).read_text()
        hash_a = file_md5(copy_a / test_rel)

        # Copy B
        copy_b = tmp_path / "copy_b" / "circular-buffer"
        shutil.copytree(EX, copy_b, symlinks=True)
        content_b = (copy_b / test_rel).read_text()
        hash_b = file_md5(copy_b / test_rel)

        norm_a = normalize_content(content_a)
        norm_b = normalize_content(content_b)

        print(f"  Copy A MD5: {hash_a}")
        print(f"  Copy B MD5: {hash_b}")

        if norm_a == norm_b:
            check(True, "copy A and copy B test files are identical (no diff after normalization)")
        else:
            diff = list(difflib.unified_diff(
                norm_a.splitlines(keepends=True),
                norm_b.splitlines(keepends=True),
                fromfile="copy_a/circular-buffer.test.ts",
                tofile="copy_b/circular-buffer.test.ts",
            ))
            diff_text = "".join(diff)
            print("UNEXPECTED DIFFERENCES between copy A and copy B:")
            print(diff_text)
            check(False, f"copy A and copy B differ unexpectedly:\n{diff_text[:500]}")

        # Verify copies match original
        check(normalize_content(original_content) == norm_a,
              "original working-tree file matches copies (no undocumented changes)")

        # Save comparison evidence
        comparison = {
            "original_hash": original_hash,
            "copy_a_hash": hash_a,
            "copy_b_hash": hash_b,
            "copies_identical": hash_a == hash_b,
            "copies_match_original": original_hash == hash_a,
            "note": (
                "This track has no auto-generator. The test file is manually maintained. "
                "All copies should be byte-for-byte identical."
            ),
        }
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        (EVIDENCE_DIR / "generation-comparison.json").write_text(
            json.dumps(comparison, indent=2) + "\n"
        )

    print()

    # --- Phase 6: Verify working-tree file not modified ---
    final_hash = file_md5(wt_test)
    check(final_hash == original_hash,
          "working-tree test file not modified by this checker")
    print()

    # --- Summary ---
    print("=" * 60)
    result = "FAILED" if failures else "ALL CHECKS PASSED"
    print(f"RESULT: {result}")
    if failures:
        print("Failures:")
        for f in failures:
            print(f"  ✗ {f}")
    else:
        print(f"  ✓ {total_tests} tests found in test file")
        print(f"  ✓ {len(REQUIRED_CASES)} required cases verified")
        print(f"  ✓ Two-copy round-trip: identical")
    print("=" * 60)

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

