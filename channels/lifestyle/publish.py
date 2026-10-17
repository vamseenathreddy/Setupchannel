"""Make a reviewed lifestyle video public, add it to the channel's playlist (once) and post its seed comment.

  python -m channels.lifestyle.publish --lang te --video-id <id>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from channels.engine import upload
from channels.lifestyle import post, topics


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lang", choices=sorted(post.CHANNELS), required=True)
    ap.add_argument("--video-id", required=True)
    args = ap.parse_args()
    ch = post.CHANNELS[args.lang]
    yt = upload.service(Path(ch["token"]))
    got = yt.channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"]
    if ch["name"].lower() not in got.lower():
        raise SystemExit(f"::error::token acts as channel '{got}', not '{ch['name']}'")
    items = yt.videos().list(part="status,snippet", id=args.video_id).execute().get("items", [])
    if not items:
        raise SystemExit(f"::error::video {args.video_id} not found on {got}")
    item = items[0]
    status = item["status"]
    status["privacyStatus"] = "public"
    status.pop("publishAt", None)
    yt.videos().update(part="status", body={"id": args.video_id, "status": status}).execute()
    print(f"::notice::{ch['name']}: '{item['snippet']['title']}' is now PUBLIC")
    yt._tags = item["snippet"].get("tags", [])
    try:
        pl = upload.find_or_create_playlist(yt, ch["playlist"], "", ch["language"])
        have = yt.playlistItems().list(part="snippet", playlistId=pl, maxResults=50).execute().get("items", [])
        if any(i["snippet"]["resourceId"].get("videoId") == args.video_id for i in have):
            print("::notice::already in playlist")
        else:
            upload.add_to_playlist(yt, args.video_id, pl)
            print("::notice::added to playlist")
    except Exception as exc:  # noqa: BLE001
        print(f"::warning::playlist failed: {exc}")
    try:
        upload.add_comment(yt, args.video_id, post.metadata(args.lang, topics.THEMES[0], [0] * 12)["comment"])
        print("::notice::seed comment posted")
    except Exception as exc:  # noqa: BLE001
        print(f"::warning::comment failed: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
