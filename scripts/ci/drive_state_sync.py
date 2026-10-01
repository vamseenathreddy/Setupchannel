#!/usr/bin/env python3
"""
CI helper: sync Mahanavi Spirituals persistent state with Google Drive.

GitHub Actions runners are stateless -- every run starts from a clean
checkout. This script uses one Drive folder as the durable store for the
files that must survive between runs:

  - data/mahanavi.db                          (purana / image usage history)
  - data/youtube_token.json                   (OAuth refresh token)
  - data/last_run_date_rahu_kalam.txt         (IST date Rahu Kalam last posted)
  - data/last_run_date_shubha_ghadiyalu.txt   (IST date Shubha Ghadiyalu last posted)
  - data/last_run_date_durmuhurtham.txt       (IST date Durmuhurtham last posted)

The Shorts got separate marker files (replacing one combined
last_run_date.txt) when the workflow moved to hourly ticks with an
independent gate per Short (scripts/ci/scheduler_gate.py) -- each Short
can now post on a different tick, so a delay on one must never block or
skip the others.

BUG FIX (2026-10-01): last_run_date_durmuhurtham.txt was missing from
STATE_FILES entirely when Durmuhurtham was added as a third alert Short
-- mark-done durmuhurtham would write the marker locally, but push()
would never upload it (it only iterates STATE_FILES), so the marker
never survived to the next run. Confirmed via a real failed run
(2026-10-01, run 36773455308): the push step failed for an unrelated
reason, which happened to hide this bug before it could bite -- it
would otherwise have caused Durmuhurtham to repost on every tick in the
window, every single night, since pull() would never find a prior
marker on Drive to restore.

Auth: a Google Cloud SERVICE ACCOUNT (not the interactive OAuth app used
for the actual YouTube upload). Its JSON key is stored as the
GDRIVE_SA_KEY_JSON GitHub secret (the raw JSON key file content, pasted
as-is) and written to a temp file at the start of each run. The target Drive folder must be shared
with the service account's email as Editor, or nothing below will find it.

Usage:
    python scripts/ci/drive_state_sync.py pull                    # Drive -> ./data
    python scripts/ci/drive_state_sync.py push                     # ./data -> Drive
    python scripts/ci/drive_state_sync.py mark-done rahu_kalam       # writes today's IST date locally
    python scripts/ci/drive_state_sync.py mark-done shubha_ghadiyalu
"""

from __future__ import annotations

import io
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"]
DATA_DIR = Path("data")
STATE_FILES = [
    "mahanavi.db",
    "youtube_token.json",
    "last_run_date_rahu_kalam.txt",
    "last_run_date_shubha_ghadiyalu.txt",
    "last_run_date_durmuhurtham.txt",
]


def _drive_client():
    key_json = os.environ["GDRIVE_SA_KEY_JSON"]
    key_path = Path("/tmp/gdrive_sa_key.json")
    key_path.write_text(key_json, encoding="utf-8")
    creds = service_account.Credentials.from_service_account_file(
        str(key_path), scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _folder_id() -> str:
    return os.environ["GDRIVE_FOLDER_ID"]


def _find_file_id(drive, name: str) -> str | None:
    query = f"'{_folder_id()}' in parents and name = '{name}' and trashed = false"
    resp = drive.files().list(q=query, fields="files(id, name)").execute()
    files = resp.get("files", [])
    return files[0]["id"] if files else None


def pull() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    drive = _drive_client()
    for name in STATE_FILES:
        file_id = _find_file_id(drive, name)
        if not file_id:
            print(f"[drive-sync] {name}: not found in Drive yet, skipping restore")
            continue
        request = drive.files().get_media(fileId=file_id)
        target = DATA_DIR / name
        with io.FileIO(target, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        print(f"[drive-sync] restored {name} <- Drive")


def push() -> None:
    drive = _drive_client()
    for name in STATE_FILES:
        local_path = DATA_DIR / name
        if not local_path.exists():
            print(f"[drive-sync] {name}: no local file to push, skipping")
            continue
        media = MediaFileUpload(str(local_path), resumable=False)
        file_id = _find_file_id(drive, name)
        if file_id:
            drive.files().update(fileId=file_id, media_body=media).execute()
        else:
            metadata = {"name": name, "parents": [_folder_id()]}
            drive.files().create(body=metadata, media_body=media, fields="id").execute()
        print(f"[drive-sync] pushed {name} -> Drive")


def _today_ist() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()


def mark_done(which: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / f"last_run_date_{which}.txt").write_text(_today_ist())
    print(f"[drive-sync] marked {which} as done for {_today_ist()}")


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "pull":
        pull()
        return 0
    if len(sys.argv) == 2 and sys.argv[1] == "push":
        push()
        return 0
    if len(sys.argv) == 3 and sys.argv[1] == "mark-done":
        mark_done(sys.argv[2])
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
