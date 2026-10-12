"""Duplicate guard: titles of the channel's recent uploads, so a rotation that has lost its place (a concurrent
run clobbered the index) can never post a story / concept that is already on the channel (the Gaya repeat)."""
from __future__ import annotations

from typing import Any


def recent_titles(youtube: Any, limit: int = 100) -> list[str]:
    """Titles of the channel's newest uploads. Returns [] on any API problem (guard is best-effort)."""
    try:
        ch = youtube.channels().list(part="contentDetails", mine=True).execute()
        playlist = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        titles: list[str] = []
        token = None
        while len(titles) < limit:
            resp = youtube.playlistItems().list(
                part="snippet", playlistId=playlist, maxResults=50, pageToken=token).execute()
            titles += [i["snippet"]["title"] for i in resp.get("items", [])]
            token = resp.get("nextPageToken")
            if not token:
                break
        return titles[:limit]
    except Exception as exc:  # noqa: BLE001
        print(f"Note: duplicate guard skipped (could not read recent uploads: {type(exc).__name__}).")
        return []


def is_posted(titles: list[str], *needles: str) -> bool:
    """True if any needle (non-empty) appears in any recent title."""
    return any(n and n in t for n in needles for t in titles)
