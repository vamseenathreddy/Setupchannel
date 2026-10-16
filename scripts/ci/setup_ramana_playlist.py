"""Create (or find) the Ramana Maharshi TV playlist and add every Short already on the channel to it, oldest
first. Never lists a video twice, never deletes anything. Safe to re-run.
Usage: python scripts/ci/setup_ramana_playlist.py [token_file]  (default data/youtube_token_ramana.json)"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ramana"))
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from src import playlists, upload

    token = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/youtube_token_ramana.json")
    yt = upload.service(token)
    pid = playlists.ensure_playlist(yt)
    print(f"playlist: https://www.youtube.com/playlist?list={pid}")
    uploads = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        r = upload._retry(lambda: yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50,
                                                        pageToken=tok).execute())
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        tok = r.get("nextPageToken")
        if not tok:
            break
    alive: dict[str, str] = {}
    for k in range(0, len(ids), 50):
        for v in yt.videos().list(part="snippet", id=",".join(ids[k:k + 50])).execute().get("items", []):
            alive[v["id"]] = v["snippet"].get("publishedAt", "")
    present = playlists.video_ids(yt, pid)
    added = skipped = 0
    for vid in sorted(alive, key=alive.get):  # oldest first
        if playlists.add_once(yt, vid, pid, present):
            added += 1
            print(f"added {vid}")
        else:
            skipped += 1
    print(f"done: {len(alive)} Shorts on channel, {added} added, {skipped} already in playlist, "
          f"{len(present)} now in playlist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
