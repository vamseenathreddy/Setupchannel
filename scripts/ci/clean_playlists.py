"""Remove playlist entries that no longer show a video (deleted / private / unavailable) from every playlist of a
channel. Only the playlist ENTRY is removed, never a video. Dry run unless --apply.

Usage: python scripts/ci/clean_playlists.py [--apply] [token_file ...]  (default: every token in data/)"""
from __future__ import annotations

import sys
from pathlib import Path

DEAD_TITLES = {"deleted video", "private video"}


def clean(token_file: Path, apply: bool) -> None:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(token_file))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_file.write_text(creds.to_json(), encoding="utf-8")
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    name = yt.channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"]
    print(f"\n=== {name} ({token_file.name}) ===")
    pls, tok = [], None
    while True:
        r = yt.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=tok).execute()
        pls += [(p["id"], p["snippet"]["title"]) for p in r.get("items", [])]
        tok = r.get("nextPageToken")
        if not tok:
            break
    for pid, ptitle in pls:
        items, tok = [], None
        while True:
            r = yt.playlistItems().list(part="snippet,status", playlistId=pid, maxResults=50, pageToken=tok).execute()
            items += r.get("items", [])
            tok = r.get("nextPageToken")
            if not tok:
                break
        vids = [i["snippet"]["resourceId"].get("videoId") for i in items]
        alive: set[str] = set()
        for k in range(0, len(vids), 50):
            chunk = [v for v in vids[k:k + 50] if v]
            if chunk:
                alive |= {v["id"] for v in yt.videos().list(part="id", id=",".join(chunk)).execute().get("items", [])}
        seen: set[str] = set()
        dead = dup = 0
        for it in items:
            vid = it["snippet"]["resourceId"].get("videoId")
            title = it["snippet"].get("title", "").strip().lower()
            reason = None
            if not vid or vid not in alive or title in DEAD_TITLES:
                reason = "dead (deleted/unavailable)"
                dead += 1
            elif vid in seen:
                reason = "same video listed twice"
                dup += 1
            seen.add(vid or "")
            if reason:
                print(f"  [{ptitle}] {vid} {reason}")
                if apply:
                    yt.playlistItems().delete(id=it["id"]).execute()
        print(f"  {ptitle}: {len(items)} entries, {dead} dead, {dup} repeated -> {'removed' if apply else 'dry run'}")


def main() -> int:
    args = sys.argv[1:]
    apply = "--apply" in args
    files = [Path(a) for a in args if not a.startswith("--")] or sorted(Path("data").glob("youtube_token*.json"))
    for f in files:
        try:
            clean(f, apply)
        except Exception as exc:  # noqa: BLE001
            print(f"{f.name}: skipped ({type(exc).__name__}: {exc})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
