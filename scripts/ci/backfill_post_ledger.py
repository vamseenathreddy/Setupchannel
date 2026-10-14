"""Seed each channel's duplicate ledger with everything already on YouTube (title + description fingerprints).
Read-only on YouTube. Usage: python scripts/ci/backfill_post_ledger.py [token_file ...]  (default: every token in data/)"""
from __future__ import annotations

import sys
from pathlib import Path

from mahanavi.publishers import post_ledger


def seed(token_file: Path) -> int:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(token_file))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_file.write_text(creds.to_json(), encoding="utf-8")
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    uploads = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        token = r.get("nextPageToken")
        if not token:
            break
    data = post_ledger.load(token_file)
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="snippet", id=",".join(ids[i:i + 50])).execute().get("items", []):
            sn = v["snippet"]
            data.setdefault(post_ledger.fingerprint(sn["title"], sn.get("description", "")),
                            {"id": v["id"], "title": sn["title"][:80], "at": sn.get("publishedAt", "")})
    path = post_ledger.ledger_path(token_file)
    import json
    path.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{token_file.name}: {len(ids)} uploads -> ledger {path.name} now {len(data)} entries")
    return len(ids)


def main() -> int:
    files = [Path(a) for a in sys.argv[1:]] or sorted(Path("data").glob("youtube_token*.json"))
    for f in files:
        try:
            seed(f)
        except Exception as exc:  # noqa: BLE001 - one bad token must not block the others
            print(f"{f.name}: skipped ({type(exc).__name__}: {exc})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
