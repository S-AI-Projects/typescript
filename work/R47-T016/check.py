#!/usr/bin/env python3
"""Compare two tournament implementations against the exercise's full test suite."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "tournament"
CONFIG_FILE = EXERCISE_DIR / ".meta" / "config.json"

HEADER = "Team                           | MP |  W |  D |  L |  P"
WIN_TABLE = "\n".join(
    [
        HEADER,
        "Allegoric Alaskans             |  1 |  1 |  0 |  0 |  3",
        "Blithering Badgers             |  1 |  0 |  0 |  1 |  0",
    ]
)

PROBE_TEST = """import { describe, expect, it } from '@jest/globals'
import { Tournament } from './tournament.ts'

const HEADER = 'Team                           | MP |  W |  D |  L |  P'
const WIN_TABLE = [
  HEADER,
  'Allegoric Alaskans             |  1 |  1 |  0 |  0 |  3',
  'Blithering Badgers             |  1 |  0 |  0 |  1 |  0',
].join('\\n')

const examples = [
  { name: 'empty input returns only the header', input: '', expected: HEADER },
  {
    name: 'a win earns three points and the other team loses',
    input: 'Allegoric Alaskans;Blithering Badgers;win',
    expected: WIN_TABLE,
  },
  {
    name: 'a loss for the first team is a win for the second',
    input: 'Blithering Badgers;Allegoric Alaskans;loss',
    expected: WIN_TABLE,
  },
]

describe('R47-T016 contract examples', () => {
  for (const example of examples) {
    it(example.name, () => {
      const actual = new Tournament().tally(example.input)
      console.log(
        `\\n${example.name}\\nExpected:\\n${example.expected}\\nActual:\\n${actual}`
      )
      expect(actual).toBe(example.expected)
    })
  }
})
"""


def configured_file(config: Dict[str, object], kind: str) -> str:
    files = config.get("files", {})
    if not isinstance(files, dict):
        raise ValueError("config.json must contain a files object")
    values = files.get(kind)
    if not isinstance(values, list) or not values or not isinstance(values[0], str):
        raise ValueError("config.json must contain a " + kind + " file path")
    return values[0]


def run_command(
    command: List[str], cwd: Path, env: Dict[str, str]
) -> Tuple[Optional[int], str, str]:
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        return None, "", str(error)
    return result.returncode, result.stdout, result.stderr


def command_text(returncode: Optional[int], stdout: str, stderr: str) -> str:
    if returncode is None:
        status = "could not start"
    else:
        status = "exit code " + str(returncode)
    return "\n".join(
        [
            "Status: " + status,
            "stdout:",
            stdout.rstrip() or "(empty)",
            "stderr:",
            stderr.rstrip() or "(empty)",
        ]
    )


def version(command: List[str], env: Dict[str, str]) -> str:
    returncode, stdout, stderr = run_command(command, REPO_ROOT, env)
    if returncode == 0:
        lines = stdout.strip().splitlines()
        return lines[0] if lines else "(no version output)"
    detail = stderr.strip() or stdout.strip()
    return "unavailable (" + command_text(returncode, stdout, detail) + ")"


def run_implementation(
    label: str,
    implementation: Path,
    solution_path: str,
    test_path: str,
    exercise_test_count: int,
    temp_root: Path,
    env: Dict[str, str],
) -> Dict[str, object]:
    temp_exercise = temp_root / label
    shutil.copytree(EXERCISE_DIR, temp_exercise)

    temp_solution = temp_exercise / solution_path
    shutil.copy2(implementation, temp_solution)

    temp_test = temp_exercise / test_path
    test_code = temp_test.read_text()
    test_code = re.sub(r"\bxdescribe\s*\(", "describe(", test_code)
    test_code = re.sub(r"\bxit\s*\(", "it(", test_code)
    temp_test.write_text(test_code)

    probe_path = temp_exercise / "r47-t016.probe.test.ts"
    probe_path.write_text(PROBE_TEST)

    install = run_command(
        ["corepack", "yarn", "install", "--no-immutable"], temp_exercise, env
    )
    record: Dict[str, object] = {
        "label": label,
        "install": install,
        "test": None,
        "expected_tests": exercise_test_count + 3,
        "passed": 0,
        "total": 0,
        "success": False,
    }

    if install[0] != 0:
        return record

    test = run_command(["corepack", "yarn", "test"], temp_exercise, env)
    output = test[1] + test[2]
    summary = re.search(r"^Tests:\s*(.*)$", output, re.MULTILINE)
    passed_match = re.search(r"(\d+)\s+passed", summary.group(1)) if summary else None
    total_match = re.search(r"(\d+)\s+total", summary.group(1)) if summary else None
    failed_match = re.search(r"(\d+)\s+failed", summary.group(1)) if summary else None
    passed = int(passed_match.group(1)) if passed_match else 0
    total = int(total_match.group(1)) if total_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0

    record.update(
        {
            "test": test,
            "passed": passed,
            "total": total,
            "failed": failed,
            "success": (
                test[0] == 0
                and total > 0
                and total == exercise_test_count + 3
                and passed == total
                and failed == 0
            ),
        }
    )
    return record


def render_run(record: Dict[str, object]) -> str:
    label = str(record["label"])
    install = record["install"]
    lines = [
        "## " + label.capitalize() + " implementation",
        "",
        "- Result: " + ("PASS" if record["success"] else "FAIL"),
        "- Expected tests: " + str(record["expected_tests"]),
        "- Tests passed: " + str(record["passed"]),
        "- Tests reported: " + str(record["total"]),
        "- Failed tests: " + str(record.get("failed", 0)),
        "",
        "### Dependency installation",
        "",
        "```text",
        command_text(install[0], install[1], install[2]),
        "```",
        "",
    ]
    test = record.get("test")
    if test is None:
        lines.extend(["Test command was not run because dependency installation failed.", ""])
    else:
        lines.extend(
            [
                "### Exercise test command (`CI=true corepack yarn test`)",
                "",
                "```text",
                command_text(test[0], test[1], test[2]),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    with CONFIG_FILE.open() as config_file:
        config = json.load(config_file)

    solution_path = configured_file(config, "solution")
    test_path = configured_file(config, "test")
    example_path = configured_file(config, "example")
    example_file = EXERCISE_DIR / example_path
    reference_implementation = SCRIPT_DIR / "reference.ts"
    if not example_file.is_file():
        raise FileNotFoundError("Configured example file is missing: " + str(example_file))
    if reference_implementation.read_bytes() != example_file.read_bytes():
        raise ValueError("work/R47-T016/reference.ts must match the configured reference")

    test_code = (EXERCISE_DIR / test_path).read_text()
    exercise_test_count = len(re.findall(r"\b(?:x?it|x?test)\s*\(", test_code))
    if exercise_test_count == 0:
        raise ValueError("No exercise tests were found in " + test_path)

    package = json.loads((EXERCISE_DIR / "package.json").read_text())
    if "test" not in package.get("scripts", {}):
        raise ValueError("The exercise package.json does not define a test script")

    env = os.environ.copy()
    env["CI"] = "true"
    env["FORCE_COLOR"] = "0"

    version_commands = {
        "Python": ["python3", "--version"],
        "Node.js": ["node", "--version"],
        "Corepack/Yarn": ["corepack", "yarn", "--version"],
    }
    versions = {name: version(command, env) for name, command in version_commands.items()}
    versions_ok = all(not value.startswith("unavailable (") for value in versions.values())
    implementations = [
        ("reference", reference_implementation),
        ("alternative", SCRIPT_DIR / "alternative.ts"),
    ]
    records: List[Dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="r47-t016-") as temp_name:
        temp_root = Path(temp_name)
        for label, implementation in implementations:
            if not implementation.is_file():
                raise FileNotFoundError("Missing implementation: " + str(implementation))
            print("[check] running " + label + " implementation")
            record = run_implementation(
                label,
                implementation,
                solution_path,
                test_path,
                exercise_test_count,
                temp_root,
                env,
            )
            records.append(record)
            print(
                "[check] "
                + label
                + ": "
                + str(record["passed"])
                + "/"
                + str(record["total"])
                + " tests passed"
            )

    evidence = [
        "# R47-T016 test evidence",
        "",
        "Both implementations ran from separate temporary copies of the tournament "
        "exercise. `shutil.copytree` copied the complete exercise, including hidden "
        "metadata directories; the configured solution and test paths came from "
        "`.meta/config.json`. Only the temporary solution/test files were changed.",
        "",
        "The original `xit` cases were enabled in each temporary copy. CI mode "
        "disabled Jest watch mode. Three additional contract examples checked "
        "empty input, a win, and the same win expressed as the opponent's loss.",
        "",
        "## Tool versions",
        "",
    ]
    evidence.extend("- " + name + ": " + value for name, value in versions.items())
    evidence.extend(
        [
            "",
            "## Expected and actual contract results",
            "",
            "| Input | Expected result | Actual result |",
            "| --- | --- | --- |",
            "| empty string | Header only | Captured in each Jest probe; compared with header |",
            "| `Allegoric Alaskans;Blithering Badgers;win` | Allegoric: 1 MP, 1 W, 0 L, 3 P; Blithering: 1 MP, 0 W, 1 L, 0 P | Captured in each Jest probe and asserted equal |",
            "| `Blithering Badgers;Allegoric Alaskans;loss` | Same standings as the win above | Captured in each Jest probe and asserted equal |",
            "",
            "The exact expected and returned tables are included in the successful "
            "Jest probe output below.",
            "",
        ]
    )
    evidence.extend(render_run(record) for record in records)

    evidence_path = SCRIPT_DIR / "evidence.md"
    evidence_path.write_text("\n".join(evidence))
    print("[check] evidence written to " + str(evidence_path))

    success = (
        versions_ok
        and len(records) == 2
        and all(record["success"] for record in records)
    )
    if success:
        print("[check] both implementations passed all tests")
        return 0
    print("[check] one or more implementations failed; see evidence.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())
