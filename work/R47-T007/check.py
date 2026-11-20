#!/usr/bin/env python3
"""
R47-T007 check script — space-age
Verifies:
  1. Learner stub is unsolved
  2. hints.md covers: keyof typeof, Planet union, static vs runtime validation
  3. Reference proof.ci.ts passes all 8 tests
"""
import subprocess, re, sys, json, os, shutil, tempfile, pathlib

WORKSPACE = pathlib.Path(__file__).parent.parent.parent
EXERCISE = WORKSPACE / "exercises/practice/space-age"
PROOF = EXERCISE / ".meta/proof.ci.ts"
STUB = EXERCISE / "space-age.ts"
TEST_FILE = EXERCISE / "space-age.test.ts"
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
        (td / "space-age.test.ts").write_text(test_enabled)
        (td / "space-age.ts").write_text(impl_path.read_text())
        for cfg in ["babel.config.cjs", "jest.config.cjs", "tsconfig.json", "package.json"]:
            src = EXERCISE / cfg
            if src.exists():
                shutil.copy(str(src), str(td / cfg))
        env = os.environ.copy()
        env["YARN_ENABLE_GLOBAL_CACHE"] = "0"
        result = subprocess.run(
            ["/opt/homebrew/bin/node", "/opt/homebrew/bin/yarn", "jest",
             "--watchAll=false", "--no-coverage",
             str(td / "space-age.test.ts")],
            capture_output=True, text=True, env=env, cwd=str(WORKSPACE)
        )
        output = result.stdout + result.stderr
        passed = re.findall(r'✓\s+([^\(\n]+?)(?:\s+\(\d+\s*m?s\))?$', output, re.MULTILINE)
        return passed, output

print("\n=== R47-T007 check: space-age ===\n")

# 1. Stub check
print("[1] Learner stub must be unsolved")
stub_text = STUB.read_text()
stub_unsolved = "throw new Error" in stub_text
check("stub_is_unsolved", stub_unsolved,
      "" if stub_unsolved else "Stub appears solved — must stay as-is for learners")

# 2. hints.md structure
print("\n[2] hints.md TypeScript content")
if not HINTS.exists():
    check("hints_md_exists", False, "hints.md not found")
else:
    h = HINTS.read_text()
    check("hints_md_exists", True)
    check("hints_has_keyof_typeof", "keyof typeof" in h,
          "" if "keyof typeof" in h else "Missing 'keyof typeof' explanation")
    check("hints_has_planet_union", "Planet" in h and ("union" in h.lower() or "keyof" in h),
          "" if "Planet" in h else "Missing Planet type discussion")
    check("hints_has_static_vs_runtime", "static" in h.lower() and "runtime" in h.lower(),
          "" if ("static" in h.lower() and "runtime" in h.lower()) else "Missing static vs runtime section")
    check("hints_has_toFixed", "toFixed" in h,
          "" if "toFixed" in h else "Missing toFixed(2) rounding note")
    check("hints_has_earth_year", "31" in h and "557" in h,
          "" if ("31" in h and "557" in h) else "Missing Earth year seconds constant")

# 3. Reference proof.ci.ts — all 8 tests
print("\n[3] Reference proof.ci.ts — all 8 tests")
test_src = TEST_FILE.read_text()
passed_ref, out_ref = run_jest(PROOF, test_src)
print("    Jest output snippet:\n    " + "\n    ".join(out_ref.splitlines()[-12:]))

REQUIRED = [
    "age on Earth",
    "age on Mercury",
    "age on Venus",
    "age on Mars",
    "age on Jupiter",
    "age on Saturn",
    "age on Uranus",
    "age on Neptune",
]
passed_names = [t.strip() for t in passed_ref]
for tc in REQUIRED:
    matched = any(tc.lower() in p.lower() for p in passed_names)
    check(f"test:{tc}", matched, "" if matched else f"Not found in: {passed_names}")

check("total_tests_8", len(passed_ref) >= 8, f"Got {len(passed_ref)}/8")

# Save results
results["total_passed_ref"] = len(passed_ref)
tool_versions = {}
try:
    nv = subprocess.run(["/opt/homebrew/bin/node", "--version"], capture_output=True, text=True)
    tool_versions["node"] = nv.stdout.strip()
    yv = subprocess.run(["/opt/homebrew/bin/yarn", "--version"], capture_output=True, text=True,
                        env={**os.environ, "YARN_ENABLE_GLOBAL_CACHE": "0"})
    tool_versions["yarn"] = yv.stdout.strip()
except Exception as e:
    tool_versions["error"] = str(e)

RESULTS_PATH.write_text(json.dumps({"results": results, "tool_versions": tool_versions}, indent=2))
(pathlib.Path(__file__).parent / "tool_versions.json").write_text(json.dumps(tool_versions, indent=2))

print(f"\n=== Summary: {results['passed']} passed, {results['failed']} failed ===")
sys.exit(0 if results["failed"] == 0 else 1)
