#!/usr/bin/env python3
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

EXERCISE_DIR = "exercises/practice/rna-transcription"
NAMED_CASES = [
    "transcribes cytosine to guanine",
    "transcribes guanine to cytosine",
    "transcribes adenine to uracil",
]
TEST_INPUT_SIZES = [
    {"name": "single_nucleotide", "size": 1, "input": "C", "expected": "G"},
    {"name": "short_sequence", "size": 4, "input": "ACGT", "expected": "UGCA"},
    {
        "name": "full_canonical",
        "size": 12,
        "input": "ACGTGGTCTTAA",
        "expected": "UGCACCAGAAUU",
    },
]


def get_tool_versions():
    node_v = (
        subprocess.check_output(
            ["/opt/homebrew/bin/node", "-v"], text=True
        ).strip()
        if os.path.exists("/opt/homebrew/bin/node")
        else sys.version
    )
    python_v = sys.version.split()[0]
    yarn_v = subprocess.check_output(
        [
            "/opt/homebrew/bin/node",
            "/opt/homebrew/bin/yarn",
            "--version",
        ],
        text=True,
    ).strip()
    return {"node": node_v, "python": python_v, "yarn": yarn_v}


def check_learner_stub(solution_path):
    print(f"[1/5] Checking learner stub at {solution_path}...")
    with open(solution_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "throw new Error" not in content and "Remove this line" not in content:
        raise AssertionError("Learner stub appears to be solved in the working tree!")
    print("  ✓ Learner stub remains unsolved.")


def run_tests_in_sandbox(config_path):
    print("[2/5] Running automated tests in temporary copy...")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    solution_rel = config["files"]["solution"][0]
    test_rel = config["files"]["test"][0]
    example_rel = config["files"]["example"][0]

    with tempfile.TemporaryDirectory(dir=".") as tmpdir:
        temp_exercise = os.path.join(tmpdir, "rna-transcription")
        shutil.copytree(EXERCISE_DIR, temp_exercise)

        shutil.copy(
            os.path.join(temp_exercise, example_rel),
            os.path.join(temp_exercise, solution_rel),
        )

        temp_test_path = os.path.join(temp_exercise, test_rel)
        with open(temp_test_path, "r", encoding="utf-8") as f:
            test_content = f.read()

        with open(temp_test_path, "w", encoding="utf-8") as f:
            f.write(test_content.replace("xit(", "it("))

        cmd = [
            "/opt/homebrew/bin/node",
            "/opt/homebrew/bin/yarn",
            "jest",
            "--watchAll=false",
            temp_test_path,
        ]
        env = os.environ.copy()
        env["YARN_ENABLE_GLOBAL_CACHE"] = "0"

        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        output = (proc.stderr or "") + "\n" + (proc.stdout or "")

        if proc.returncode != 0:
            print(f"Child process failed:\n{output}")
            raise AssertionError(f"Jest failed with exit code {proc.returncode}")

        passed = [
            p.strip()
            for p in re.findall(
                r"✓\s+([^\(\n]+?)(?:\s+\(\d+\s*m?s\))?$", output, re.MULTILINE
            )
        ]
        failed = [
            f.strip()
            for f in re.findall(
                r"✕\s+([^\(\n]+?)(?:\s+\(\d+\s*m?s\))?$", output, re.MULTILINE
            )
        ]

        total = len(passed) + len(failed)
        print(f"  Test results: {len(passed)}/{total} passed, {len(failed)} failed.")

        if total == 0:
            raise AssertionError("Zero-test run: no tests were executed!")
        if len(failed) > 0:
            raise AssertionError(f"{len(failed)} tests failed!")

        for named in NAMED_CASES:
            if named not in passed:
                raise AssertionError(f"Named case '{named}' was not among passed tests: {passed}")
            print(f"  ✓ Passed named case: '{named}'")

        return {
            "total_executed": total,
            "passed": len(passed),
            "failed": len(failed),
            "executed_titles": passed,
        }


def measure_scaling():
    print("[3/5] Measuring empirical scaling across 3 input sizes (7 repetitions each)...")
    # Inline node micro-benchmark script to isolate algorithmic runtime from process startup
    bench_js = """
const { toRna } = require('./exercises/practice/rna-transcription/.meta/proof.ci.ts');
const sizes = [
  { name: 'N1', input: 'C', expected: 'G' },
  { name: 'N4', input: 'ACGT', expected: 'UGCA' },
  { name: 'N12', input: 'ACGTGGTCTTAA', expected: 'UGCACCAGAAUU' }
];

// Assert correctness first
for (const s of sizes) {
  const actual = toRna(s.input);
  if (actual !== s.expected) {
    throw new Error(`Correctness failed for ${s.name}: expected ${s.expected}, got ${actual}`);
  }
}

// Warm up JIT
for (let i = 0; i < 5000; i++) {
  toRna('ACGTGGTCTTAA');
}

const reps = 7;
const iterations = 10000;
const results = {};

for (const s of sizes) {
  const timings = [];
  for (let r = 0; r < reps; r++) {
    const start = process.hrtime.bigint();
    for (let i = 0; i < iterations; i++) {
      toRna(s.input);
    }
    const end = process.hrtime.bigint();
    timings.push(Number(end - start) / 1e6); // convert to ms
  }
  timings.sort((a, b) => a - b);
  const median = timings[Math.floor(timings.length / 2)];
  results[s.name] = {
    input_size: s.input.length,
    repetitions: timings,
    median_ms_for_10k_calls: median,
    avg_ns_per_call: (median / iterations) * 1e6
  };
}

console.log(JSON.stringify(results));
"""
    cmd = [
        "/opt/homebrew/bin/node",
        "--require",
        "./.pnp.cjs",
        "-e",
        bench_js,
    ]
    env = os.environ.copy()
    env["YARN_ENABLE_GLOBAL_CACHE"] = "0"

    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        print(f"Benchmarking failed: {proc.stderr}")
        raise AssertionError(f"Scaling measurement script failed with code {proc.returncode}")

    bench_results = json.loads(proc.stdout)
    for name, data in bench_results.items():
        print(
            f"  ✓ Size {name} (N={data['input_size']}): median = {data['median_ms_for_10k_calls']:.3f} ms "
            f"({data['avg_ns_per_call']:.1f} ns/call across 7 reps)"
        )
    return bench_results


def check_complexity_doc():
    print("[4/5] Verifying complexity comments in proof.ci.ts...")
    proof_path = os.path.join(EXERCISE_DIR, ".meta/proof.ci.ts")
    with open(proof_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "Time Complexity: O(N)" not in content:
        raise AssertionError("O(N) time complexity comment missing from proof.ci.ts")
    if "Auxiliary Space Complexity: O(N)" not in content:
        raise AssertionError("O(N) space complexity comment missing from proof.ci.ts")
    print("  ✓ Complexity and invariant documentation verified.")


def main():
    print("=== Running R47-T005 Automated Check ===")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    tool_versions = get_tool_versions()

    # 1. Learner stub check
    check_learner_stub(os.path.join(EXERCISE_DIR, "rna-transcription.ts"))

    # 2. Test execution in isolated copy
    test_results = run_tests_in_sandbox(os.path.join(EXERCISE_DIR, ".meta/config.json"))

    # 3. Micro-benchmark across 3 input sizes
    bench_results = measure_scaling()

    # 4. Complexity doc verification
    check_complexity_doc()

    # 5. Save results and evidence
    print(f"[5/5] Saving evidence to {work_dir}...")
    evidence = {
        "task_id": "R47-T005",
        "exercise": "exercises/practice/rna-transcription",
        "tool_versions": tool_versions,
        "named_cases": NAMED_CASES,
        "bench_results": bench_results,
        "test_results": test_results,
        "status": "PASSED",
    }
    with open(os.path.join(work_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    with open(os.path.join(work_dir, "tool_versions.json"), "w", encoding="utf-8") as f:
        json.dump(tool_versions, f, indent=2)

    print("=== All checks PASSED successfully! ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Check failed: {err}", file=sys.stderr)
        sys.exit(1)
