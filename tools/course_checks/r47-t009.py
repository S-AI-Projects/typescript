#!/usr/bin/env python3
"""
tools/course_checks/r47-t009.py
R47-T009 — two-fer isolated runner with file-hash immutability proof

Design goals:
  1. Run the reference proof.ci.ts against all tests in a fully isolated
     temporary directory — the learner's stub file is NEVER touched.
  2. Record SHA-256 hashes of every learner-facing file BEFORE and AFTER the
     run to prove that the runner did not modify them.
  3. Assert that all hashes match — any mutation is flagged as a failure.
  4. Report pass/fail counts and exit non-zero on any failure.

Usage:
  python3 tools/course_checks/r47-t009.py [--verbose]
"""
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile

WORKSPACE = pathlib.Path(__file__).parent.parent.parent
EXERCISE  = WORKSPACE / "exercises/practice/two-fer"
PROOF     = EXERCISE / ".meta/proof.ci.ts"

# Files whose integrity we monitor (relative to EXERCISE)
LEARNER_FILES = [
    "two-fer.ts",          # stub — must never be modified
    "two-fer.test.ts",     # test — must never be modified
]

REQUIRED_TESTS = [
    "no name given",
    "a name given",
    "another name given",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256(path: pathlib.Path) -> str:
    """Return hex SHA-256 of a file's contents."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def snapshot(files) -> dict:
    """Record {rel_path: sha256} for each file in the list."""
    return {f: sha256(EXERCISE / f) for f in files}


def run_jest(impl_path: pathlib.Path, test_src: str) -> tuple[list, str]:
    """Run jest in a temp dir with impl_path as the solution; return (passed_names, raw_output)."""
    with tempfile.TemporaryDirectory(dir=str(WORKSPACE)) as tmpdir:
        td = pathlib.Path(tmpdir)
        # Enable all tests
        test_enabled = test_src.replace("xit(", "it(").replace("xdescribe(", "describe(")
        (td / "two-fer.test.ts").write_text(test_enabled)
        (td / "two-fer.ts").write_text(impl_path.read_text())
        for cfg in ["babel.config.cjs", "jest.config.cjs", "tsconfig.json", "package.json"]:
            src = EXERCISE / cfg
            if src.exists():
                shutil.copy(str(src), str(td / cfg))
        env = os.environ.copy()
        env["YARN_ENABLE_GLOBAL_CACHE"] = "0"
        result = subprocess.run(
            ["/opt/homebrew/bin/node", "/opt/homebrew/bin/yarn", "jest",
             "--watchAll=false", "--no-coverage",
             str(td / "two-fer.test.ts")],
            capture_output=True, text=True, env=env, cwd=str(WORKSPACE),
        )
        output = result.stdout + result.stderr
        passed = re.findall(r"✓\s+([^\(\n]+?)(?:\s+\(\d+\s*m?s\))?$", output, re.MULTILINE)
        return passed, output


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="R47-T009 isolated runner")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    ok_count = 0
    fail_count = 0

    def check(name, cond, detail=""):
        nonlocal ok_count, fail_count
        if cond:
            ok_count += 1
            print(f"  ✅ {name}")
        else:
            fail_count += 1
            msg = f": {detail}" if detail else ""
            print(f"  ❌ {name}{msg}")

    print("\n=== r47-t009.py: two-fer isolated runner ===\n")

    # --- Phase 1: Pre-run snapshot -------------------------------------------
    print("[1] Recording pre-run file hashes")
    for f in LEARNER_FILES:
        fp = EXERCISE / f
        check(f"learner_file_exists:{f}", fp.exists(), str(fp))

    pre_hashes = snapshot(LEARNER_FILES)
    for f, digest in pre_hashes.items():
        print(f"    {f}: {digest[:16]}…")

    # --- Phase 2: Run reference in isolation ---------------------------------
    print("\n[2] Running reference proof.ci.ts in isolated temp directory")
    test_src = (EXERCISE / "two-fer.test.ts").read_text()
    passed_names, raw_output = run_jest(PROOF, test_src)

    if args.verbose:
        print("    --- jest output ---")
        for line in raw_output.splitlines():
            print(f"    {line}")
        print("    --- end ---")
    else:
        # Print last 10 lines as summary
        snippet = raw_output.splitlines()[-10:]
        print("    Jest summary:\n    " + "\n    ".join(snippet))

    # --- Phase 3: Post-run snapshot ------------------------------------------
    print("\n[3] Recording post-run file hashes")
    post_hashes = snapshot(LEARNER_FILES)

    for f in LEARNER_FILES:
        pre  = pre_hashes[f]
        post = post_hashes[f]
        unchanged = pre == post
        check(f"file_unchanged:{f}", unchanged,
              f"Hash changed! before={pre[:16]}… after={post[:16]}…")
        if args.verbose:
            print(f"    before: {pre}")
            print(f"    after:  {post}")

    # --- Phase 4: Test results -----------------------------------------------
    print("\n[4] Test results")
    passed_set = [n.strip() for n in passed_names]
    for tc in REQUIRED_TESTS:
        matched = any(tc.lower() in p.lower() for p in passed_set)
        check(f"test:{tc}", matched, "" if matched else f"not in {passed_set}")

    check("total_tests_3", len(passed_names) >= 3, f"got {len(passed_names)}/3")

    # --- Phase 5: Stub remains unsolved --------------------------------------
    print("\n[5] Learner stub integrity")
    stub_text = (EXERCISE / "two-fer.ts").read_text()
    # Stub is considered "unsolved" if it has no return statement that constructs the phrase
    stub_unsolved = "One for" not in stub_text
    check("stub_does_not_contain_solution", stub_unsolved,
          "Stub appears to contain the solution — must stay as the original skeleton")

    # --- Summary -------------------------------------------------------------
    print(f"\n=== Summary: {ok_count} passed, {fail_count} failed ===")

    result_data = {
        "pre_hashes": pre_hashes,
        "post_hashes": post_hashes,
        "tests_passed": passed_set,
        "ok": ok_count,
        "failed": fail_count,
    }
    out_path = pathlib.Path(__file__).parent / "r47-t009-result.json"
    out_path.write_text(json.dumps(result_data, indent=2))

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
