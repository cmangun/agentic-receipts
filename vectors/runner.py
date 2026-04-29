#!/usr/bin/env python3
"""
Conformance vector runner.

Walks `vectors/` recursively, validates that each `.json` file contains a
parseable list of case objects with a `description` field, and reports
pass/fail per file. Exits non-zero on any parse or structure failure.

In v0.1 this validates structural integrity only. Actual case execution —
run `input` through canonicalizer / hasher / signer / redactor and compare
to `expected_*` — is a v0.1 expansion deliverable that lights up
automatically as cases include input/expected pairs implementing the
spec operations.
"""

import json
import sys
from pathlib import Path


def main() -> int:
    vectors_dir = Path(__file__).parent
    case_files = sorted(vectors_dir.rglob("*.json"))

    if not case_files:
        print("No vector files found. Skipping.")
        return 0

    total_cases = 0
    failures: list[str] = []

    for f in case_files:
        rel = f.relative_to(vectors_dir.parent)
        try:
            with f.open() as fh:
                data = json.load(fh)
        except json.JSONDecodeError as e:
            failures.append(f"{rel}: invalid JSON ({e})")
            continue

        if not isinstance(data, list):
            failures.append(f"{rel}: top-level must be a JSON array of cases")
            continue

        file_cases = 0
        for i, case in enumerate(data):
            if not isinstance(case, dict):
                failures.append(f"{rel}[{i}]: case must be an object")
                continue
            if "description" not in case:
                failures.append(f"{rel}[{i}]: missing 'description' field")
                continue
            file_cases += 1
            total_cases += 1

        print(f"  ok  {rel}  ({file_cases} cases)")

    if failures:
        print(f"\nFAIL  {len(failures)} structural failures:")
        for fail in failures:
            print(f"  {fail}")
        return 1

    print(f"\nPASS  {total_cases} cases structurally valid across {len(case_files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
