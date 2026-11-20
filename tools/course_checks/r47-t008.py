#!/usr/bin/env python3
"""
tools/course_checks/r47-t008.py
R47-T008 — bank-account maintenance check

Verifies:
  1. All files declared in .meta/config.json (solution, test, example) exist on disk
  2. Each declared file is non-empty
  3. The reference proof.ci.ts exports BankAccount and ValueError classes
  4. The learner stub exports the same public API surface (class names present)
  5. docs/maintenance/bank-account.md exists and covers key sections
"""
import sys, json, pathlib, re

WORKSPACE = pathlib.Path(__file__).parent.parent.parent
EXERCISE = WORKSPACE / "exercises/practice/bank-account"
CONFIG = EXERCISE / ".meta/config.json"
MAINTENANCE_DOC = WORKSPACE / "docs/maintenance/bank-account.md"

passed = 0
failed = 0

def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")

print("\n=== r47-t008.py: bank-account maintenance check ===\n")

# 1. config.json exists
print("[1] .meta/config.json exists and is valid JSON")
if not CONFIG.exists():
    check("config_json_exists", False, str(CONFIG))
    sys.exit(1)

config = json.loads(CONFIG.read_text())
check("config_json_exists", True)
check("config_json_has_files", "files" in config,
      "" if "files" in config else "Missing 'files' key")

# 2. Declared files exist and are non-empty
print("\n[2] Declared files exist on disk and are non-empty")
files_block = config.get("files", {})
for role in ("solution", "test", "example"):
    paths = files_block.get(role, [])
    for rel in paths:
        fp = EXERCISE / rel
        exists = fp.exists()
        nonempty = exists and fp.stat().st_size > 0
        check(f"file_exists[{role}]:{rel}", exists,
              f"Not found: {fp}" if not exists else "")
        if exists:
            check(f"file_nonempty[{role}]:{rel}", nonempty,
                  f"Empty file: {fp}" if not nonempty else "")

# 3. proof.ci.ts API surface
print("\n[3] proof.ci.ts exports BankAccount and ValueError")
proof_path = EXERCISE / ".meta/proof.ci.ts"
if proof_path.exists():
    proof = proof_path.read_text()
    check("proof_exports_BankAccount",
          "class BankAccount" in proof or "export class BankAccount" in proof,
          "Missing BankAccount class")
    check("proof_exports_ValueError",
          "class ValueError" in proof or "export class ValueError" in proof,
          "Missing ValueError class")
    check("proof_has_open_method", "open()" in proof, "Missing open() method")
    check("proof_has_close_method", "close()" in proof, "Missing close() method")
    check("proof_has_deposit_method", "deposit(" in proof, "Missing deposit() method")
    check("proof_has_withdraw_method", "withdraw(" in proof, "Missing withdraw() method")
    check("proof_has_balance_getter", "get balance()" in proof, "Missing balance getter")
else:
    check("proof_exists", False, str(proof_path))

# 4. Stub API surface (must have class names, must still throw)
print("\n[4] Stub file has correct class names and remains unsolved")
stub_paths = files_block.get("solution", [])
for rel in stub_paths:
    stub = (EXERCISE / rel).read_text()
    check(f"stub_has_BankAccount:{rel}",
          "BankAccount" in stub, "Missing BankAccount class name")
    check(f"stub_has_ValueError:{rel}",
          "ValueError" in stub, "Missing ValueError class name")
    check(f"stub_is_unsolved:{rel}",
          "throw new Error" in stub, "Stub appears to be solved — must remain as-is")

# 5. Maintenance doc
print("\n[5] docs/maintenance/bank-account.md")
if not MAINTENANCE_DOC.exists():
    check("maintenance_doc_exists", False, str(MAINTENANCE_DOC))
else:
    doc = MAINTENANCE_DOC.read_text()
    check("maintenance_doc_exists", True)
    check("doc_has_maintained_files_table",
          "Maintained Files" in doc or "maintained files" in doc.lower(),
          "Missing 'Maintained Files' section")
    check("doc_has_config_json_verification",
          "config.json" in doc and ("Path Verification" in doc or "files" in doc.lower()),
          "Missing config.json path verification section")
    check("doc_has_class_structure",
          "BankAccount" in doc and "ValueError" in doc,
          "Missing class structure documentation")
    check("doc_has_test_summary",
          "15" in doc and ("test" in doc.lower()),
          "Missing test summary (expected 15 tests)")

print(f"\n=== Summary: {passed} passed, {failed} failed ===")
sys.exit(0 if failed == 0 else 1)
