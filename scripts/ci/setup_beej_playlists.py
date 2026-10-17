"""Create/clean the daily beej mantra playlist of each channel and put every public beej Short into it once.

  python scripts/ci/setup_beej_playlists.py [--apply]    (without --apply nothing is changed, it only reports)

Never deletes a video. Removes only dead/duplicate playlist entries. Summary lines are ::notice:: annotations."""
from __future__ import annotations

import sys
from pathlib import Path

from channels.beej import playlists as bp
from channels.engine import upload
from mahanavi.content import beej_mantras


def main() -> int:
    apply = "--apply" in sys.argv
    rc = 0
    for key, cfg in beej_mantras.CHANNELS.items():
        token = Path("data") / cfg["token_file"]
        if not token.exists():
            print(f"::warning::{key}: token file {token} missing, skipped")
            rc = 1
            continue
        yt = upload.service(token)
        name = yt.channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"]
        if cfg["expected"].lower() not in name.lower():
            print(f"::error::{key}: token acts as '{name}', expected '{cfg['expected']}'. Skipped.")
            rc = 1
            continue
        existing = bp.list_playlists(yt)
        listing = "; ".join(f"{t} ({n})" for _, t, n in existing) or "none"
        videos = bp.channel_beej_videos(yt)
        if not apply:
            print(f"::notice::{key} [{name}] playlists: {listing} | public beej Shorts: {len(videos)}")
            continue
        pid = bp.ensure_playlist(yt, key)
        dead, dup = bp.clean_playlist(yt, pid)
        present = bp.playlist_video_ids(yt, pid)
        added = sum(1 for vid, _, _ in videos if bp.add_once(yt, vid, pid, present))
        print(f"::notice::{key} [{name}] playlist {pid}: removed {dead} dead + {dup} duplicate, "
              f"added {added}, now {len(present)} videos. Other playlists: {listing}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
