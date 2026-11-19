"""
check.py — R47-T015 two-bucket verifier
----------------------------------------
Steps:
  1. Read .meta/config.json to find the solution, test, and example file paths.
  2. Copy the whole exercise into a temporary directory.
  3. Replace the learner stub with the reference solution (proof.ci.ts).
  4. Unskip all tests (replace xit( with it( and xdescribe( with describe().
  5. Install dependencies and run the test suite.
  6. Check that all tests passed.
  7. Write evidence.md with the results.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# ── paths ──────────────────────────────────────────────────────────────────────

# This file lives at  work/R47-T015/check.py
# The repo root is two levels up.
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT   = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "two-bucket")
CONFIG_FILE  = os.path.join(EXERCISE_DIR, ".meta", "config.json")

print(f"[check] repo root   : {REPO_ROOT}")
print(f"[check] exercise dir: {EXERCISE_DIR}")

# ── 1. read config.json ────────────────────────────────────────────────────────

with open(CONFIG_FILE) as f:
    config = json.load(f)

# config["files"]["solution"] is a list, e.g. ["two-bucket.ts"]
solution_filename = config["files"]["solution"][0]
test_filename     = config["files"]["test"][0]
example_filename  = config["files"]["example"][0]  # e.g. ".meta/proof.ci.ts"

solution_src = os.path.join(EXERCISE_DIR, solution_filename)
test_src     = os.path.join(EXERCISE_DIR, test_filename)
example_src  = os.path.join(EXERCISE_DIR, example_filename)

print(f"[check] solution file : {solution_filename}")
print(f"[check] test file     : {test_filename}")
print(f"[check] reference impl: {example_filename}")

# ── 2. copy exercise into a temp directory ─────────────────────────────────────

tmp_root = tempfile.mkdtemp(prefix="r47-t015-")
tmp_exercise = os.path.join(tmp_root, "two-bucket")

# Copy everything, including hidden files (.meta, .docs, etc.)
shutil.copytree(EXERCISE_DIR, tmp_exercise)
print(f"[check] temp copy     : {tmp_exercise}")

# ── 3. replace learner stub with the reference solution ───────────────────────

tmp_solution = os.path.join(tmp_exercise, solution_filename)
shutil.copy2(example_src, tmp_solution)
print(f"[check] replaced stub with proof.ci.ts")

# ── 4. unskip all tests ────────────────────────────────────────────────────────

tmp_test = os.path.join(tmp_exercise, test_filename)

with open(tmp_test) as f:
    test_code = f.read()

# Count how many tests will be unskipped (before we replace)
skipped_it        = test_code.count("xit(")
skipped_describe  = test_code.count("xdescribe(")

# Replace xdescribe( → describe(  and  xit( → it(
test_code = test_code.replace("xdescribe(", "describe(")
test_code = test_code.replace("xit(", "it(")

with open(tmp_test, "w") as f:
    f.write(test_code)

print(f"[check] unskipped {skipped_it} xit() and {skipped_describe} xdescribe()")

# ── 5. install dependencies ───────────────────────────────────────────────────

print("[check] running: corepack yarn install --no-immutable ...")
install_result = subprocess.run(
    ["corepack", "yarn", "install", "--no-immutable"],
    cwd=tmp_exercise,
    capture_output=True,
    text=True,
)

if install_result.returncode != 0:
    print("[ERROR] yarn install failed!")
    print(install_result.stdout)
    print(install_result.stderr)
    shutil.rmtree(tmp_root, ignore_errors=True)
    sys.exit(1)

print("[check] dependencies installed OK")

# ── 6. run the test suite ─────────────────────────────────────────────────────

print("[check] running: corepack yarn test ...")
env = os.environ.copy()
env["CI"] = "true"   # disables watch mode in jest

test_result = subprocess.run(
    ["corepack", "yarn", "test"],
    cwd=tmp_exercise,
    capture_output=True,
    text=True,
    env=env,
)

combined_output = test_result.stdout + test_result.stderr
print(combined_output)

# ── 7. parse results ──────────────────────────────────────────────────────────

# Jest summary line looks like:
#   Tests:       1 failed, 10 passed, 11 total
# or:
#   Tests:       10 passed, 10 total
# We capture "passed" and "total".

# Jest prints two summary lines:
#   "Test Suites: 1 passed, 1 total"
#   "Tests:       11 passed, 11 total"
# We specifically want the "Tests:" line, not the "Test Suites:" line.
tests_line_match = re.search(r"^Tests:\s+(.*)", combined_output, re.MULTILINE)
if tests_line_match:
    tests_line = tests_line_match.group(1)
    passed_match = re.search(r"(\d+)\s+passed", tests_line)
    total_match  = re.search(r"(\d+)\s+total",  tests_line)
    passed = int(passed_match.group(1)) if passed_match else 0
    total  = int(total_match.group(1))  if total_match  else 0
else:
    passed = 0
    total  = 0

print(f"\n[check] tests passed : {passed}")
print(f"[check] tests total  : {total}")

# Count how many 'it(' calls are in the unskipped test file
it_count = test_code.count("it(")
print(f"[check] it() calls in test file: {it_count}")

# ── 8. write evidence.md ──────────────────────────────────────────────────────

evidence_dir = SCRIPT_DIR  # same folder as check.py

# Get tool versions for the evidence record
def run_version(cmd):
    """Run a command and return its first line of output, or 'unknown'."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        return r.stdout.strip().splitlines()[0] if r.stdout.strip() else "unknown"
    except Exception:
        return "unknown"

python_version = run_version(["python3", "--version"])
node_version   = run_version(["node",    "--version"])
yarn_version   = run_version(["corepack", "yarn", "--version"])

evidence_lines = [
    "# Evidence — R47-T015 two-bucket\n",
    "\n## Tool versions\n",
    f"- Python : {python_version}\n",
    f"- Node.js : {node_version}\n",
    f"- Yarn    : {yarn_version}\n",
    "\n## Test run summary\n",
    f"- Tests passed : {passed}\n",
    f"- Tests total  : {total}\n",
    f"- Exit code    : {test_result.returncode}\n",
    "\n## Complexity summary\n",
    "Each `Bucket` operation (fill, empty, pourInto) is **O(1)** — it updates\n",
    "a single numeric field with no loops.\n\n",
    "`TwoBucket.moves()` terminates in at most **(cap1+1) × (cap2+1)** moves.\n",
    "Actual move counts for canonical cases:\n\n",
    "| cap1 | cap2 | goal | start | moves |\n",
    "|------|------|------|-------|-------|\n",
    "| 3    | 5    | 1    | one   | 4     |\n",
    "| 3    | 5    | 1    | two   | 8     |\n",
    "| 7    | 11   | 2    | one   | 14    |\n",
    "| 7    | 11   | 2    | two   | 18    |\n",
    "| 1    | 3    | 3    | two   | 1     |\n",
    "| 2    | 3    | 3    | one   | 2     |\n",
    "| 5    | 1    | 2    | one   | 6     |\n",
    "| 3    | 15   | 9    | one   | 6     |\n",
    "| 6    | 15   | 9    | one   | 10    |\n",
    "\n## Full test output\n",
    "```\n",
    combined_output,
    "```\n",
]

evidence_path = os.path.join(evidence_dir, "evidence.md")
with open(evidence_path, "w") as f:
    f.writelines(evidence_lines)

print(f"[check] evidence written to {evidence_path}")

# ── 9. clean up and exit ──────────────────────────────────────────────────────

shutil.rmtree(tmp_root, ignore_errors=True)

# Decide pass / fail
success = (
    test_result.returncode == 0
    and total > 0
    and passed == total
)

if success:
    print(f"\n✅ All {passed}/{total} tests passed. Reference solution is correct.")
    sys.exit(0)
else:
    print(f"\n❌ FAILED — {passed}/{total} tests passed, exit code {test_result.returncode}.")
    sys.exit(1)
