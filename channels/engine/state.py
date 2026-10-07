"""Small JSON state file that survives between stateless CI runs (synced to Google Drive by
scripts/ci/drive_state_sync.py -- every Pattern-A channel's state file is added to that
script's STATE_FILES so it rides along with the existing pull/push, same as Ramana's).

{"posted": {"2026-10-07": {"row": "q001", "video_id": "abc", "at": "2026-10-07T05:12:00+05:30"}},
 "used_ids": ["q001"]}

Each channel sets the STATE_FILE env var to its own path (e.g. data/jesus_state.json) before
calling load()/save() with no path argument -- same convention as ramana/src/state.py.
"""
import json
import os
import tempfile
from pathlib import Path


def _default_path():
    return Path(os.environ.get("STATE_FILE", "state.json"))


def load(path=None):
    path = Path(path) if path else _default_path()
    if not path.exists():
        return {"posted": {}, "used_ids": []}
    data = json.loads(path.read_text(encoding="utf-8") or "{}")
    data.setdefault("posted", {})
    data.setdefault("used_ids", [])
    return data


def save(state, path=None):
    path = Path(path) if path else _default_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, path)


def mark_posted(state, date_iso, row_id, video_id, special_row, at_iso):
    state["posted"][date_iso] = {"row": row_id, "video_id": video_id, "at": at_iso}
    if not special_row and row_id not in state["used_ids"]:
        state["used_ids"].append(row_id)
    return state
