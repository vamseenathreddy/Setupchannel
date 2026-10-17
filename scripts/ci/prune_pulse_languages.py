"""Delete the Pulse Boosting Shorts that are not Telugu (the channel is Telugu-only since 2026-10-17).

  python scripts/ci/prune_pulse_languages.py [--apply]     (without --apply it only lists what it would delete)

Language = the video's own language tag (set at upload); if missing, the script of the title. Only this channel's token
is used and the channel name is checked first. Stops at the first quota error and says how many are left."""
from __future__ import annotations

import sys
from pathlib import Path

from googleapiclient.errors import HttpError

from channels.engine import upload
from channels.trending.sources import SCRIPT_RANGE, matches_language


def guess(sn: dict) -> str:
    tag = (sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "").split("-")[0].lower()
    if tag:
        return tag
    for lang in SCRIPT_RANGE:
        if matches_language(sn.get("title", ""), lang):
            return lang
    return "en"


def main() -> int:
    apply = "--apply" in sys.argv
    token = Path("data/youtube_token_pulse_boosting.json")
    yt = upload.service(token)
    name = yt.channels().list(part="snippet,contentDetails", mine=True).execute()["items"][0]
    if "pulse" not in name["snippet"]["title"].lower():
        print(f"::error::token acts as '{name['snippet']['title']}', not Pulse Boosting. Nothing done.")
        return 1
    uploads = name["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, page = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=page).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        page = r.get("nextPageToken")
        if not page:
            break
    vids = []
    for i in range(0, len(ids), 50):
        vids += yt.videos().list(part="snippet,status", id=",".join(ids[i:i + 50])).execute()["items"]
    keep = [v for v in vids if guess(v["snippet"]) == "te"]
    drop = [v for v in vids if guess(v["snippet"]) != "te"]
    print(f"::notice::{len(vids)} videos on the channel: keep {len(keep)} Telugu, {'deleting' if apply else 'would delete'} {len(drop)} others")
    for v in drop:
        print(f"::notice::DELETE {guess(v['snippet'])} {v['status']['privacyStatus']} {v['id']} {v['snippet']['title'][:70]}")
    for v in keep:
        print(f"::notice::KEEP {guess(v['snippet'])} {v['status']['privacyStatus']} {v['id']} {v['snippet']['title'][:70]}")
    if not apply:
        return 0
    done = 0
    for v in drop:
        try:
            yt.videos().delete(id=v["id"]).execute()
            done += 1
        except HttpError as exc:
            print(f"::error::stopped after {done} deletions: {exc.status_code} {str(exc)[:200]}. {len(drop) - done} left; run again after the quota reset.")
            return 1
    print(f"::notice::deleted {done} videos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
