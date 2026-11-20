#!/usr/bin/env python3
"""
R47-T010 check script — all-your-base
Verifies:
  1. Learner stub is unsolved
  2. hints.md covers 3 anchor cases + Horner's method + special cases
  3. Reference proof.ci.ts passes all 22 tests
"""
import subprocess, re, sys, json, os, shutil, tempfile, pathlib

WORKSPACE = pathlib.Path(__file__).parent.parent.parent
EXERCISE = WORKSPACE / "exercises/practice/all-your-base"
PROOF = EXERCISE / ".meta/proof.ci.ts"
STUB = EXERCISE / "all-your-base.ts"
TEST_FILE = EXERCISE / "all-your-base.test.ts"
HINTS = EXERCISE / ".docs/hints.md"
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
        (td / "all-your-base.test.ts").write_text(test_enabled)
        (td / "all-your-base.ts").write_text(impl_path.read_text())
        for cfg in ["babel.config.cjs", "jest.config.cjs", "tsconfig.json", "package.json"]:
            src = EXERCISE / cfg
            if src.exists():
                shutil.copy(str(src), str(td / cfg))
        env = os.environ.copy()
        env["YARN_ENABLE_GLOBAL_CACHE"] = "0"
        result = subprocess.run(
            ["/opt/homebrew/bin/node", "/opt/homebrew/bin/yarn", "jest",
             "--watchAll=false", "--no-coverage",
             str(td / "all-your-base.test.ts")],
            capture_output=True, text=True, env=env, cwd=str(WORKSPACE)
        )
        output = result.stdout + result.stderr
        passed = re.findall(r'✓\s+([^\(\n]+?)(?:\s+\(\d+\s*m?s\))?$', output, re.MULTILINE)
        return passed, output

print("\n=== R47-T010 check: all-your-base ===\n")

# 1. Stub check
print("[1] Learner stub must be unsolved")
stub_text = STUB.read_text()
stub_unsolved = "throw new Error" in stub_text
check("stub_is_unsolved", stub_unsolved)

# 2. hints.md structure
print("\n[2] hints.md content")
if not HINTS.exists():
    check("hints_md_exists", False, "hints.md not found")
else:
    h = HINTS.read_text()
    check("hints_md_exists", True)
    check("hints_has_anchor_case_1", "single bit one to decimal" in h or "single bit" in h.lower(),
          "Missing anchor case 1 (single bit one to decimal)")
    check("hints_has_anchor_case_2", "binary to single decimal" in h or "1, 0, 1" in h,
          "Missing anchor case 2 (binary to single decimal)")
    check("hints_has_anchor_case_3", "single decimal to binary" in h or "decimal to binary" in h.lower(),
          "Missing anchor case 3 (single decimal to binary)")
    check("hints_has_horner", "Horner" in h or "acc * base" in h or "acc * inputBase" in h,
          "Missing Horner's method explanation")
    check("hints_has_special_cases", "Leading zeros" in h or "leading zeros" in h.lower(),
          "Missing special cases table")
    check("hints_has_wrong_input_base_note", "Wrong input base" in h or "input base" in h.lower(),
          "Missing wrong input base note")

# 3. All 22 tests pass
print("\n[3] Reference proof.ci.ts — all 22 tests")
test_src = TEST_FILE.read_text()
passed_ref, out_ref = run_jest(PROOF, test_src)
print("    Jest output snippet:\n    " + "\n    ".join(out_ref.splitlines()[-12:]))

REQUIRED = [
    "single bit one to decimal",
    "binary to single decimal",
    "single decimal to binary",
    "binary to multiple decimal",
    "decimal to binary",
    "trinary to hexadecimal",
    "hexadecimal to trinary",
    "15-bit integer",
    "empty list",
    "single zero",
    "multiple zeros",
    "leading zeros",
    "negative digit",
    "invalid positive digit",
    "first base is one",
    "second base is one",
    "first base is zero",
    "second base is zero",
    "first base is negative",
    "second base is negative",
    "both bases are negative",
    "wrong output_base base not integer",
]
passed_names = [t.strip() for t in passed_ref]
for tc in REQUIRED:
    matched = any(tc.lower() in p.lower() for p in passed_names)
    check(f"test:{tc[:45]}", matched, "" if matched else f"not found")

check("total_tests_22", len(passed_ref) >= 22, f"Got {len(passed_ref)}/22")

# Save
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
