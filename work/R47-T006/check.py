#!/usr/bin/env python3
"""
R47-T006 check script — run-length-encoding
Verifies:
  1. Learner stub is unsolved (functions not implemented)
  2. Reference proof.ci.ts passes all 13 tests (encode x6, decode x6, roundtrip x1)
  3. Alternative loop-based implementation agrees with regex-based reference on all test cases
  4. hints.md exists with both approach sections
"""
import subprocess, re, sys, json, os, shutil, tempfile, pathlib

WORKSPACE = pathlib.Path(__file__).parent.parent.parent
EXERCISE = WORKSPACE / "exercises/practice/run-length-encoding"
PROOF = EXERCISE / ".meta/proof.ci.ts"
STUB = EXERCISE / "run-length-encoding.ts"
TEST_FILE = EXERCISE / "run-length-encoding.test.ts"
HINTS = EXERCISE / ".docs/hints.md"
ALT = WORKSPACE / "work/R47-T006/alternative.ts"
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

def run_jest(impl_path, test_src, label):
    """Copy impl to temp dir alongside test, run jest, return (passed_tests, all_output)."""
    with tempfile.TemporaryDirectory(dir=str(WORKSPACE)) as tmpdir:
        td = pathlib.Path(tmpdir)
        # Enable all tests: xit→it, xdescribe→describe
        test_enabled = test_src.replace("xit(", "it(").replace("xdescribe(", "describe(")
        (td / "run-length-encoding.test.ts").write_text(test_enabled)
        (td / "run-length-encoding.ts").write_text(impl_path.read_text())
        # Copy config files from exercise dir
        for cfg in ["babel.config.cjs", "jest.config.cjs", "tsconfig.json", "package.json"]:
            src = EXERCISE / cfg
            if src.exists():
                shutil.copy(str(src), str(td / cfg))
        env = os.environ.copy()
        env["YARN_ENABLE_GLOBAL_CACHE"] = "0"
        result = subprocess.run(
            ["/opt/homebrew/bin/node", "/opt/homebrew/bin/yarn", "jest",
             "--watchAll=false", "--no-coverage",
             str(td / "run-length-encoding.test.ts")],
            capture_output=True, text=True, env=env, cwd=str(WORKSPACE)
        )
        output = result.stdout + result.stderr
        passed = re.findall(r'✓\s+([^\(\n]+?)(?:\s+\(\d+\s*m?s\))?$', output, re.MULTILINE)
        if not passed:
            passed = re.findall(r'✔\s+([^\(\n]+?)(?:\s+\(\d+\s*m?s\))?$', output, re.MULTILINE)
        return passed, output

print("\n=== R47-T006 check: run-length-encoding ===\n")

# 1. Stub check
print("[1] Learner stub must be unsolved")
stub_text = STUB.read_text()
stub_unsolved = "throw new Error" in stub_text or stub_text.strip() == "" or \
    ("export function encode" not in stub_text and "export const encode" not in stub_text)
check("stub_is_unsolved", stub_unsolved,
      "" if stub_unsolved else "Stub appears to be solved — must remain as-is for learners")

# 2. hints.md check
print("\n[2] hints.md structure")
if not HINTS.exists():
    check("hints_md_exists", False, "hints.md not found")
else:
    hints_text = HINTS.read_text()
    has_regex = "Regex" in hints_text or "regex" in hints_text
    has_loop = "Loop" in hints_text or "loop" in hints_text or "Imperative" in hints_text
    has_edge = "empty" in hints_text.lower() and "XYZ" in hints_text
    check("hints_md_exists", True)
    check("hints_has_regex_approach", has_regex, "" if has_regex else "Missing regex approach section")
    check("hints_has_loop_approach", has_loop, "" if has_loop else "Missing loop approach section")
    check("hints_has_edge_cases", has_edge, "" if has_edge else "Missing edge-case table")

# 3. Reference proof.ci.ts — run all 13 tests
print("\n[3] Reference implementation (proof.ci.ts) — all 13 tests")
test_src = TEST_FILE.read_text()
passed_ref, out_ref = run_jest(PROOF, test_src, "proof.ci.ts")
print(f"    Jest output snippet:\n    " + "\n    ".join(out_ref.splitlines()[-15:]))

REQUIRED_ENCODE = [
    "empty string",
    "single characters only are encoded without count",
    "string with no single characters",
    "single characters mixed with repeated characters",
    "multiple whitespace mixed in string",
    "lowercase characters",
]
REQUIRED_DECODE = [
    "single characters only",
    "string with no single characters",
    "single characters with repeated characters",
    "multiple whitespace mixed in string",
    "lower case string",
]
REQUIRED_ROUNDTRIP = ["encode followed by decode gives original string"]

passed_names = [t.strip() for t in passed_ref]

for tc in REQUIRED_ENCODE:
    matched = any(tc.lower() in p.lower() for p in passed_names)
    check(f"encode:{tc}", matched, "" if matched else f"Not found in: {passed_names}")

for tc in REQUIRED_DECODE:
    matched = any(tc.lower() in p.lower() for p in passed_names)
    check(f"decode:{tc}", matched, "" if matched else f"Not found in: {passed_names}")

for tc in REQUIRED_ROUNDTRIP:
    matched = any(tc.lower() in p.lower() for p in passed_names)
    check(f"roundtrip:{tc}", matched, "" if matched else f"Not found in: {passed_names}")

total_expected = 13
check(f"total_tests_passed_13", len(passed_ref) >= total_expected,
      f"Got {len(passed_ref)}/{total_expected}")

# 4. Alternative implementation agreement
print("\n[4] Alternative loop-based implementation agreement")
if ALT.exists():
    passed_alt, out_alt = run_jest(ALT, test_src, "alternative.ts")
    alt_names = [t.strip() for t in passed_alt]
    agree = len(passed_alt) >= total_expected
    check("alternative_passes_all_tests", agree,
          f"Got {len(passed_alt)}/{total_expected}" if not agree else "")
else:
    check("alternative_exists", False, f"work/R47-T006/alternative.ts not found")

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
