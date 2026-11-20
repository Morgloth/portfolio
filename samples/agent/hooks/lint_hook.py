#!/usr/bin/env python3
"""PostToolUse hook (Edit|Write): after the agent edits a Python file, run ruff with only the rules that catch real
bugs (undefined names, redefinitions, unused variables, syntax errors). On findings, exit 2: Claude Code feeds
stderr back to the agent, which fixes the bug in the same turn. Otherwise stay silent, so it costs no context."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

RULES = "F821,F811,F841,E9,PLE"

try:
    path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
except (ValueError, AttributeError):
    sys.exit(0)
ruff = shutil.which("ruff")
if not path or not ruff or not Path(path).is_file():
    sys.exit(0)
if not path.endswith(".py"):
    with open(path, "rb") as f:
        if b"python" not in f.readline(200):   # scripts without .py but with a python shebang count too
            sys.exit(0)

r = subprocess.run([ruff, "check", "--quiet", "--no-cache", "--select", RULES, "--output-format", "concise", path],
                   capture_output=True, text=True, timeout=20, check=False)
if r.returncode == 1 and r.stdout.strip():
    print(f"ruff found likely bugs in {path}:\n{r.stdout.strip()}", file=sys.stderr)
    sys.exit(2)
