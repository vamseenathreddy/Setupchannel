"""Strict pre-upload duplicate ledger (one JSON per channel, kept in Drive via drive_state_sync).

Every upload is fingerprinted (title + start of description, normalised). Before any upload the fingerprint is
looked up in the channel's ledger; a hit means the identical Short is already on the channel, so nothing is
uploaded. After a successful upload the fingerprint is recorded. Nothing is ever deleted from YouTube.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")


class DuplicatePost(Exception):
    """The identical Short (same title and description) is already on this channel."""


def channel_name(token_file: str | Path) -> str:
    stem = Path(token_file).stem
    stem = stem.removeprefix("youtube_token").strip("_")
    return stem or "mahanavi"


def ledger_path(token_file: str | Path) -> Path:
    return DATA_DIR / f"posted_ledger_{channel_name(token_file)}.json"


def fingerprint(title: str, description: str = "") -> str:
    norm = lambda s: re.sub(r"[\W_]+", " ", s.casefold()).strip()  # noqa: E731
    return hashlib.sha1((norm(title) + "|" + norm(description)[:400]).encode("utf-8")).hexdigest()[:16]


def load(token_file: str | Path) -> dict:
    try:
        data = json.loads(ledger_path(token_file).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def check(token_file: str | Path, title: str, description: str = "") -> None:
    hit = load(token_file).get(fingerprint(title, description))
    if hit:
        raise DuplicatePost(f"already posted on {channel_name(token_file)}: '{title[:60]}' ({hit.get('id')})")


def record(token_file: str | Path, title: str, description: str, video_id: str) -> None:
    data = load(token_file)
    data[fingerprint(title, description)] = {
        "id": video_id, "title": title[:80], "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    path = ledger_path(token_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")


def merge_files(a: Path, b: Path) -> dict:
    """Union of two ledger files (used when pushing to Drive so concurrent runs never lose entries)."""
    out: dict = {}
    for p in (a, b):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                out.update(d)
        except (OSError, ValueError):
            pass
    return out
