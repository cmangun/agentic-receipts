#!/usr/bin/env python3
"""
Conformance vector runner.

Walks `vectors/` recursively, validates that each `.json` file contains either
a single case object (one-per-case format) or a list of case objects (legacy
array format), each with at minimum a `description` field. Reports pass/fail
per file and exits non-zero on any parse or structure failure.

In v0.1 this validates structural integrity. Actual case execution — run
`input` through canonicalizer / hasher / signer / redactor and compare to
`expected_*` — is a v0.1 expansion deliverable that lights up automatically
as cases include input/expected pairs implementing the spec operations.
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

        # Accept either a single case object or an array of cases
        if isinstance(data, dict):
            cases = [data]
        elif isinstance(data, list):
            cases = data
        else:
            failures.append(f"{rel}: top-level must be a JSON object or array of cases")
            continue

        file_cases = 0
        for i, case in enumerate(cases):
            if not isinstance(case, dict):
                failures.append(f"{rel}[{i}]: case must be an object")
                continue
            if "description" not in case:
                failures.append(f"{rel}[{i}]: missing 'description' field")
                continue
            file_cases += 1
            total_cases += 1

        print(f"  ok  {rel}  ({file_cases} case{'s' if file_cases != 1 else ''})")

    if failures:
        print(f"\nFAIL  {len(failures)} structural failures:")
        for fail in failures:
            print(f"  {fail}")
        return 1

    print(f"\nPASS  {total_cases} cases structurally valid across {len(case_files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
