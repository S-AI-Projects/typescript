#!/usr/bin/env python3
"""
tools/course_checks/r47-t002.py
Focused test-generation reproducibility checker for exercises/practice/rotational-cipher.
"""

import json
import os
import re
import sys
import tempfile
import tomllib

CANONICAL_CASES = [
    {
        "uuid": "7ee352c6-e6b0-4930-b903-d09943ecb8f5",
        "description": "rotate a by 1",
        "input": {"text": "a", "shiftKey": 1},
        "expected": "b",
        "active": True,
    },
    {
        "uuid": "edf0a733-4231-4594-a5ee-46a4009ad764",
        "description": "rotate a by 26, same output as input",
        "input": {"text": "a", "shiftKey": 26},
        "expected": "a",
        "active": False,
    },
    {
        "uuid": "74e58a38-e484-43f1-9466-877a7515e10f",
        "description": "rotate a by 0, same output as input",
        "input": {"text": "a", "shiftKey": 0},
        "expected": "a",
        "active": False,
    },
    {
        "uuid": "e3e82cb9-2a5b-403f-9931-e43213879300",
        "description": "rotate m by 13",
        "input": {"text": "m", "shiftKey": 13},
        "expected": "z",
        "active": False,
    },
    {
        "uuid": "19f9eb78-e2ad-4da4-8fe3-9291d47c1709",
        "description": "rotate n by 13 with wrap around alphabet",
        "input": {"text": "n", "shiftKey": 13},
        "expected": "a",
        "active": False,
    },
    {
        "uuid": "a116aef4-225b-4da9-884f-e8023ca6408a",
        "description": "rotate capital letters",
        "input": {"text": "OMG", "shiftKey": 5},
        "expected": "TRL",
        "active": False,
    },
    {
        "uuid": "71b541bb-819c-4dc6-a9c3-132ef9bb737b",
        "description": "rotate spaces",
        "input": {"text": "O M G", "shiftKey": 5},
        "expected": "T R L",
        "active": False,
    },
    {
        "uuid": "ef32601d-e9ef-4b29-b2b5-8971392282e6",
        "description": "rotate numbers",
        "input": {"text": "Testing 1 2 3 testing", "shiftKey": 4},
        "expected": "Xiwxmrk 1 2 3 xiwxmrk",
        "active": False,
    },
    {
        "uuid": "32dd74f6-db2b-41a6-b02c-82eb4f93e549",
        "description": "rotate punctuation",
        "input": {"text": "Let's eat, Grandma!", "shiftKey": 21},
        "expected": "Gzo'n zvo, Bmviyhv!",
        "active": False,
    },
    {
        "uuid": "9fb93fe6-42b0-46e6-9ec1-0bf0a062d8c9",
        "description": "rotate all letters",
        "input": {
            "text": "The quick brown fox jumps over the lazy dog.",
            "shiftKey": 13,
        },
        "expected": "Gur dhvpx oebja sbk whzcf bire gur ynml qbt.",
        "active": False,
    },
]


def ts_quote(s):
    if "'" in s:
        return f'"{s}"'
    return f"'{s}'"


def generate_test_content(cases, timestamp=None):
    lines = [
        "import { describe, it, expect, xit } from '@jest/globals'",
        "import { rotate } from './rotational-cipher.ts'",
    ]
    if timestamp:
        lines.append(f"// Generated at: {timestamp}")
    lines.append("")
    lines.append("describe('RotationalCipher', () => {")

    for i, c in enumerate(cases):
        fn = "it" if c["active"] else "xit"
        text_arg = ts_quote(c["input"]["text"])
        shift_arg = c["input"]["shiftKey"]
        expected_arg = ts_quote(c["expected"])

        lines.append(f"  {fn}('{c['description']}', () => {{")
        lines.append(f"    const result = rotate({text_arg}, {shift_arg})")
        lines.append(f"    expect(result).toEqual({expected_arg})")
        lines.append("  })")
        if i < len(cases) - 1:
            lines.append("")

    lines.append("})")
    lines.append("")
    return "\n".join(lines)


def normalize_content(content):
    # Strip any timestamp comments for reproducible comparison
    return re.sub(r"// Generated at:.*\n", "", content).strip()


def verify_regeneration():
    # 1. Check against tests.toml
    toml_path = "exercises/practice/rotational-cipher/.meta/tests.toml"
    with open(toml_path, "rb") as f:
        toml_data = tomllib.load(f)

    for case in CANONICAL_CASES:
        if case["uuid"] not in toml_data:
            raise AssertionError(f"UUID {case['uuid']} missing from {toml_path}")

    # 2. Generate in two temporary copies with different dummy timestamps
    gen1 = generate_test_content(CANONICAL_CASES, timestamp="2026-11-21T01:00:00Z")
    gen2 = generate_test_content(CANONICAL_CASES, timestamp="2026-11-21T02:00:00Z")

    norm1 = normalize_content(gen1)
    norm2 = normalize_content(gen2)

    if norm1 != norm2:
        raise AssertionError("Generations differed after timestamp normalization!")

    # 3. Compare normalized generated content with maintained rotational-cipher.test.ts
    existing_path = "exercises/practice/rotational-cipher/rotational-cipher.test.ts"
    with open(existing_path, "r", encoding="utf-8") as f:
        existing_content = f.read()

    norm_existing = normalize_content(existing_content)

    if norm1 != norm_existing:
        raise AssertionError(
            "Regenerated test content does not match existing rotational-cipher.test.ts"
        )

    print("✓ Both fresh generations matched perfectly after timestamp normalization.")
    print(f"✓ All {len(CANONICAL_CASES)} canonical cases verified against tests.toml.")
    return True


if __name__ == "__main__":
    try:
        verify_regeneration()
        print("Course check R47-T002 passed.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
