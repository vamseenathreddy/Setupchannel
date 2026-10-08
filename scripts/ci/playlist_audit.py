"""Audit every channel's playlists: list them with their item counts and find entries whose
video was deleted or is private (they show as blank "Deleted video" / "Private video" rows).

  python scripts/ci/playlist_audit.py            # read only
  python scripts/ci/playlist_audit.py --fix      # also remove those dead rows from the playlists

Runs against every data/youtube_token*.json restored from Drive.
"""
import glob
import sys
from pathlib import Path

from channels.engine import upload

DEAD_TITLES = {"deleted video", "private video"}


def audit(token_file, fix):
    yt = upload.service(Path(token_file))
    ch = yt.channels().list(part="snippet", mine=True).execute()["items"][0]
    print(f"\n=== {ch['snippet']['title']} ({ch['snippet'].get('customUrl', '-')})  [{Path(token_file).name}]")
    pls, tok = [], None
    while True:
        r = yt.playlists().list(part="snippet,contentDetails,status", mine=True, maxResults=50, pageToken=tok).execute()
        pls += r.get("items", [])
        tok = r.get("nextPageToken")
        if not tok:
            break
    if not pls:
        print("  (no playlists)")
    for p in pls:
        items, tok = [], None
        while True:
            r = yt.playlistItems().list(part="snippet,status,contentDetails", playlistId=p["id"], maxResults=50,
                                        pageToken=tok).execute()
            items += r.get("items", [])
            tok = r.get("nextPageToken")
            if not tok:
                break
        dead = [i for i in items if i["snippet"]["title"].strip().lower() in DEAD_TITLES]
        print(f"  [{p['status']['privacyStatus']}] {p['snippet']['title']}  id={p['id']}  items={len(items)}  dead={len(dead)}")
        for i in dead:
            vid = i["contentDetails"].get("videoId", "?")
            if fix:
                try:
                    yt.playlistItems().delete(id=i["id"]).execute()
                    print(f"      removed dead entry {vid}")
                except Exception as e:  # noqa: BLE001
                    print(f"      COULD NOT remove {vid}: {e}")
            else:
                print(f"      dead entry {vid} ({i['snippet']['title']})")


def main():
    fix = "--fix" in sys.argv
    for tf in sorted(glob.glob("data/youtube_token*.json")):
        try:
            audit(tf, fix)
        except SystemExit as e:
            print(f"\n=== {tf}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"\n=== {tf}: FAILED {str(e)[:300]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
