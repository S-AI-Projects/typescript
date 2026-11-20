#!/usr/bin/env python3
"""
R47-T009 check script — two-fer
Verifies:
  1. Learner stub is unsolved
  2. tools/course_checks/r47-t009.py exists and runs clean
  3. File-hash immutability: learner files unchanged after isolated run
  4. Reference proof.ci.ts passes all 3 tests
"""
import subprocess, re, sys, json, os, shutil, tempfile, pathlib

WORKSPACE = pathlib.Path(__file__).parent.parent.parent
EXERCISE = WORKSPACE / "exercises/practice/two-fer"
PROOF = EXERCISE / ".meta/proof.ci.ts"
STUB = EXERCISE / "two-fer.ts"
TEST_FILE = EXERCISE / "two-fer.test.ts"
RESULTS_PATH = pathlib.Path(__file__).parent / "results.json"

results = {"checks": {}, "passed": 0, "failed": 0}

def check(name, ok, detail=""):
    results["checks"][name] = {"ok": ok, "detail": detail}
    if ok:
        results["passed"] += 1
        print(f"  ✅ {name}")
    else:
        results["failed"] += 1
        print(f"  ❌ {name}: {detail}")

def run_jest(impl_path, test_src):
    with tempfile.TemporaryDirectory(dir=str(WORKSPACE)) as tmpdir:
        td = pathlib.Path(tmpdir)
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
            capture_output=True, text=True, env=env, cwd=str(WORKSPACE)
        )
        output = result.stdout + result.stderr
        passed = re.findall(r'✓\s+([^\(\n]+?)(?:\s+\(\d+\s*m?s\))?$', output, re.MULTILINE)
        return passed, output

print("\n=== R47-T009 check: two-fer ===\n")

# 1. Stub check
print("[1] Learner stub must be unsolved")
stub_text = STUB.read_text()
stub_unsolved = "One for" not in stub_text
check("stub_is_unsolved", stub_unsolved)

# 2. Isolated runner tool
print("\n[2] tools/course_checks/r47-t009.py")
tool = WORKSPACE / "tools/course_checks/r47-t009.py"
check("tool_exists", tool.exists(), str(tool))
if tool.exists():
    result = subprocess.run([sys.executable, str(tool)],
                           capture_output=True, text=True, cwd=str(WORKSPACE))
    tool_ok = result.returncode == 0
    check("tool_passes", tool_ok,
          "" if tool_ok else (result.stdout[-400:] + result.stderr[-400:]))
    # Parse immutability check from tool output
    if tool_ok:
        immutable_ok = "file_unchanged:two-fer.ts" in result.stdout and \
                       "file_unchanged:two-fer.test.ts" in result.stdout and \
                       "❌" not in result.stdout
        check("immutability_verified", immutable_ok,
              "" if immutable_ok else "File hash mismatch or ❌ in output")

# 3. Direct reference test
print("\n[3] Reference proof.ci.ts — all 3 tests")
test_src = TEST_FILE.read_text()
passed_ref, out_ref = run_jest(PROOF, test_src)
print("    Jest output snippet:\n    " + "\n    ".join(out_ref.splitlines()[-8:]))

REQUIRED = ["no name given", "a name given", "another name given"]
passed_names = [t.strip() for t in passed_ref]
for tc in REQUIRED:
    matched = any(tc.lower() in p.lower() for p in passed_names)
    check(f"test:{tc}", matched, "" if matched else f"not found in: {passed_names}")

check("total_tests_3", len(passed_ref) >= 3, f"Got {len(passed_ref)}/3")

# Save results
results["total_passed_ref"] = len(passed_ref)
tool_versions = {}
try:
    nv = subprocess.run(["/opt/homebrew/bin/node", "--version"], capture_output=True, text=True)
    tool_versions["node"] = nv.stdout.strip()
except Exception as e:
    tool_versions["error"] = str(e)

RESULTS_PATH.write_text(json.dumps({"results": results, "tool_versions": tool_versions}, indent=2))
(pathlib.Path(__file__).parent / "tool_versions.json").write_text(json.dumps(tool_versions, indent=2))

print(f"\n=== Summary: {results['passed']} passed, {results['failed']} failed ===")
sys.exit(0 if results["failed"] == 0 else 1)
