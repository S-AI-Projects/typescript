#!/usr/bin/env python3
"""R47-T021: check line-up canonical cases against the maintained reference."""
import json, os, re, shutil, subprocess, sys, tempfile, tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EX = REPO / "exercises/practice/line-up"
TOML_AFTER = EX / ".meta/tests.toml"
TOML_BEFORE = HERE / "tests.before.toml"
TARGETS = {
    "7760d1b8-4864-4db4-953b-0fa7c047dbc0": "format smallest non-exceptional ordinal numeral 4",
    "e8b7c715-6baa-4f7b-8fb3-2fa48044ab7a": "format greatest single digit non-exceptional ordinal numeral 9",
    "f370aae9-7ae7-4247-90ce-e8ff8c6934df": "format non-exceptional ordinal numeral 5",
}
EXPECTED_CASES = 19
failures = []


def check(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        failures.append(msg)


def run(cmd, cwd, log_name, env=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    (HERE / log_name).write_text(
        f"$ {' '.join(cmd)}\nexit={p.returncode}\n--- stdout ---\n{p.stdout}\n--- stderr ---\n{p.stderr}\n"
    )
    return p


def counts(path):
    data = tomllib.loads(path.read_text())
    included = sum(1 for v in data.values() if v.get("include", True))
    return data, included, len(data) - included


def main():
    # 1. tool versions
    versions = {"python": sys.version.split()[0]}
    versions["node"] = run(["node", "-v"], EX, "version-node.log").stdout.strip()
    versions["yarn"] = run(["corepack", "yarn", "-v"], EX, "version-yarn.log").stdout.strip()
    (HERE / "tool-versions.json").write_text(json.dumps(versions, indent=2))
    print("tool versions:", versions)

    # 2. config paths (never hard-coded)
    cfg = json.loads((EX / ".meta/config.json").read_text())["files"]
    solution, test, example = cfg["solution"][0], cfg["test"][0], cfg["example"][0]
    print(f"solution={solution} test={test} example={example}")

    # 3. TOML before / after
    before, inc_b, exc_b = counts(TOML_BEFORE)
    after, inc_a, exc_a = counts(TOML_AFTER)
    (HERE / "counts.json").write_text(json.dumps(
        {"before": {"included": inc_b, "excluded": exc_b},
         "after": {"included": inc_a, "excluded": exc_a}}, indent=2))
    check(len(after) == EXPECTED_CASES, f"tests.toml parses with {len(after)} entries")
    check((inc_b, exc_b) == (inc_a, exc_a), f"included/excluded unchanged: {inc_b}/{exc_b} -> {inc_a}/{exc_a}")
    for uuid, desc in TARGETS.items():
        entry = after.get(uuid, {})
        comment = entry.get("comment", "")
        check(bool(comment) and desc in comment, f"rationale for {uuid} names the test")
        check(entry.get("include", True) == before[uuid].get("include", True), f"include unchanged for {uuid}")

    # 4. learner stub untouched and still unsolved
    stub = (EX / solution).read_text()
    check("Remove this line and implement the function" in stub, "learner stub still unsolved")
    for f in (solution, test):
        d = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str((EX / f).relative_to(REPO))], cwd=REPO)
        check(d.returncode == 0, f"{f} unchanged in working tree")

    # 5. temp copy with reference substituted, all cases enabled
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "line-up"
        shutil.copytree(EX, copy, symlinks=True)  # includes dotfiles
        shutil.copyfile(EX / example, copy / solution)
        t = copy / test
        enabled = re.sub(r"\bxit\(", "it(", t.read_text())
        t.write_text(enabled)
        n_it = len(re.findall(r"\bit\(", enabled))
        check(n_it == EXPECTED_CASES, f"{n_it} cases enabled in temp copy (expected {EXPECTED_CASES})")

        env = dict(os.environ, CI="1")
        inst = run(["corepack", "yarn", "install"], copy, "yarn-install.log", env)
        check(inst.returncode == 0, f"yarn install in temp copy (exit {inst.returncode})")

        res_file = copy / "jest-results.json"
        p = run(["corepack", "yarn", "test:implementation", "--ci", "--watchAll=false",
                 "--json", f"--outputFile={res_file}"], copy, "jest-run.log", env)
        check(p.returncode == 0, f"jest child exit code is 0 (got {p.returncode})")
        if res_file.exists():
            shutil.copyfile(res_file, HERE / "jest-results.json")
            r = json.loads(res_file.read_text())
            total, passed = r["numTotalTests"], r["numPassedTests"]
            print(f"executed={total} passed={passed} failed={r['numFailedTests']} pending={r['numPendingTests']}")
            check(total > 0, "test run executed more than zero tests")
            check(total == EXPECTED_CASES and passed == EXPECTED_CASES and r["numPendingTests"] == 0,
                  f"all {EXPECTED_CASES} cases passed against the reference")
            status = {a["title"]: a["status"] for s in r["testResults"] for a in s["assertionResults"]}
            rows = []
            for uuid, desc in TARGETS.items():
                actual = status.get(desc)
                rows.append({"uuid": uuid, "test": desc, "expected": "passed", "actual": actual})
                check(actual == "passed", f"named case passes: {desc}")
            (HERE / "expected-vs-actual.json").write_text(json.dumps(rows, indent=2))
        else:
            check(False, "jest produced no results file")

    print("\nRESULT:", "FAILED" if failures else "ALL CHECKS PASSED")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
