#!/usr/bin/env python3
"""
R47-T008 check script — bank-account
Verifies:
  1. Learner stub is unsolved
  2. docs/maintenance/bank-account.md exists with correct sections
  3. tools/course_checks/r47-t008.py runs and passes all checks
  4. Reference proof.ci.ts passes all 15 tests (via pr.mjs pattern)
"""
import subprocess, re, sys, json, os, shutil, tempfile, pathlib

WORKSPACE = pathlib.Path(__file__).parent.parent.parent
EXERCISE = WORKSPACE / "exercises/practice/bank-account"
PROOF = EXERCISE / ".meta/proof.ci.ts"
STUB = EXERCISE / "bank-account.ts"
TEST_FILE = EXERCISE / "bank-account.test.ts"
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
        (td / "bank-account.test.ts").write_text(test_enabled)
        (td / "bank-account.ts").write_text(impl_path.read_text())
        for cfg in ["babel.config.cjs", "jest.config.cjs", "tsconfig.json", "package.json"]:
            src = EXERCISE / cfg
            if src.exists():
                shutil.copy(str(src), str(td / cfg))
        env = os.environ.copy()
        env["YARN_ENABLE_GLOBAL_CACHE"] = "0"
        result = subprocess.run(
            ["/opt/homebrew/bin/node", "/opt/homebrew/bin/yarn", "jest",
             "--watchAll=false", "--no-coverage",
             str(td / "bank-account.test.ts")],
            capture_output=True, text=True, env=env, cwd=str(WORKSPACE)
        )
        output = result.stdout + result.stderr
        passed = re.findall(r'✓\s+([^\(\n]+?)(?:\s+\(\d+\s*m?s\))?$', output, re.MULTILINE)
        return passed, output

print("\n=== R47-T008 check: bank-account ===\n")

# 1. Stub check
print("[1] Learner stub must be unsolved")
stub_text = STUB.read_text()
stub_unsolved = "throw new Error" in stub_text
check("stub_is_unsolved", stub_unsolved)

# 2. Maintenance doc
print("\n[2] docs/maintenance/bank-account.md")
maintenance_doc = WORKSPACE / "docs/maintenance/bank-account.md"
if not maintenance_doc.exists():
    check("maintenance_doc_exists", False, "docs/maintenance/bank-account.md not found")
else:
    doc = maintenance_doc.read_text()
    check("maintenance_doc_exists", True)
    check("doc_has_maintained_files", "Maintained Files" in doc)
    check("doc_has_config_verification", "config.json" in doc and "Path Verification" in doc)
    check("doc_has_class_structure", "BankAccount" in doc and "ValueError" in doc)
    check("doc_has_15_tests", "15" in doc)

# 3. course check tool runs and passes
print("\n[3] tools/course_checks/r47-t008.py")
course_check = WORKSPACE / "tools/course_checks/r47-t008.py"
if not course_check.exists():
    check("course_check_exists", False)
else:
    check("course_check_exists", True)
    result = subprocess.run([sys.executable, str(course_check)],
                           capture_output=True, text=True, cwd=str(WORKSPACE))
    cc_ok = result.returncode == 0
    check("course_check_passes", cc_ok,
          "" if cc_ok else result.stdout[-500:] + result.stderr[-500:])

# 4. Reference proof.ci.ts — all 15 tests
print("\n[4] Reference proof.ci.ts — all 15 tests")
test_src = TEST_FILE.read_text()
passed_ref, out_ref = run_jest(PROOF, test_src)
print("    Jest output snippet:\n    " + "\n    ".join(out_ref.splitlines()[-12:]))

REQUIRED = [
    "newly opened account has zero balance",
    "can deposit money",
    "can deposit money sequentially",
    "can withdraw money",
    "can withdraw money sequentially",
    "checking balance of closed account throws error",
    "deposit into closed account throws error",
    "withdraw from closed account throws error",
    "close already closed account throws error",
    "open already opened account throws error",
    "reopened account does not retain balance",
    "cannot withdraw more than deposited",
    "cannot withdraw negative amount",
    "cannot deposit negative amount",
    "changing balance directly throws error",
]
passed_names = [t.strip() for t in passed_ref]
for tc in REQUIRED:
    matched = any(tc.lower() in p.lower() for p in passed_names)
    check(f"test:{tc[:40]}", matched, "" if matched else f"not found in: {passed_names}")

check("total_tests_15", len(passed_ref) >= 15, f"Got {len(passed_ref)}/15")

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
