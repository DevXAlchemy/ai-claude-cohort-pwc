#!/usr/bin/env python3
"""PostToolUse hook: append 'timestamp | tool | relative path' to logs/dev_audit.log.

Reads only tool_name and tool_input.file_path from the stdin payload. File contents,
edit strings and report data are never logged. Never blocks (always exits 0).
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        tool = payload.get("tool_name", "unknown")
        file_path = (payload.get("tool_input") or {}).get("file_path", "")
        root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
        try:
            shown = str(Path(file_path).resolve().relative_to(root.resolve()))
        except ValueError:
            shown = "(outside project)"
        log = root / "logs" / "dev_audit.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} | {tool} | {shown}\n")
    except Exception:
        pass  # logging must never interrupt development


if __name__ == "__main__":
    main()
    sys.exit(0)
