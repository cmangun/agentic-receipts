#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
echo "=== Schema Validation ==="
for schema in "$REPO_ROOT"/schemas/*.schema.json; do
  if python3 -c "import json; json.load(open('$schema'))" 2>/dev/null; then
    echo "✓ $(basename "$schema")"
  else
    echo "✗ $(basename "$schema") — invalid JSON" && exit 1
  fi
done
echo "All validations passed."
