import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "log_edit.py"


def run_hook(tmp_path, payload):
    subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), text=True,
                   env={"CLAUDE_PROJECT_DIR": str(tmp_path)}, check=True)
    return (tmp_path / "logs" / "dev_audit.log").read_text().splitlines()


def test_hook_logs_only_tool_path_timestamp(tmp_path):
    lines = run_hook(tmp_path, {"tool_name": "Edit", "tool_input": {
        "file_path": str(tmp_path / "app.py"), "old_string": "SECRET-OLD", "new_string": "SECRET-NEW"}})
    assert len(lines) == 1 and "SECRET" not in lines[0]
    ts, tool, path = [p.strip() for p in lines[0].split("|")]
    assert (tool, path) == ("Edit", "app.py")


def test_hook_outside_project_path(tmp_path):
    lines = run_hook(tmp_path, {"tool_name": "Write", "tool_input": {"file_path": "/etc/hosts"}})
    assert lines[0].endswith("(outside project)")
