#!/usr/bin/env python3
"""
fetch_drive_asset.py: downloads ONE named file from the same Drive
folder drive_state_sync.py uses, to data/<name> -- for one-off binary
assets (e.g. a song WAV the channel owner drops in manually) that don't
belong in STATE_FILES' recurring pull/push cycle (those are small text
markers rewritten every run; this is a large file written once by hand
and only ever read).

Reuses the exact same service-account auth and file-lookup approach as
drive_state_sync.py (same env vars: GDRIVE_SA_KEY_JSON, GDRIVE_FOLDER_ID)
-- see that script's module docstring for the full auth/quota story.
The file must already exist in the Drive folder (same
storageQuotaExceeded constraint: this script can only download an
existing file, never create one), placed there by the human account
that owns the folder.

Usage (from CI):
    python scripts/ci/fetch_drive_asset.py <filename-in-drive-folder>

Exits non-zero (without crashing the whole workflow on its own -- the
caller's `if:` step should check this) if the named file isn't found.
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"]
DATA_DIR = Path("data")


def _drive_client():
    key_json = os.environ["GDRIVE_SA_KEY_JSON"]
    key_path = Path("/tmp/gdrive_sa_key.json")
    key_path.write_text(key_json, encoding="utf-8")
    creds = service_account.Credentials.from_service_account_file(str(key_path), scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _folder_id() -> str:
    return os.environ["GDRIVE_FOLDER_ID"]


def _find_file_id(drive, name: str) -> str | None:
    query = f"'{_folder_id()}' in parents and name = '{name}' and trashed = false"
    resp = drive.files().list(q=query, fields="files(id, name)").execute()
    files = resp.get("files", [])
    return files[0]["id"] if files else None


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: fetch_drive_asset.py <filename-in-drive-folder>", file=sys.stderr)
        return 1
    name = sys.argv[1]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    drive = _drive_client()
    file_id = _find_file_id(drive, name)
    if not file_id:
        print(f"FAILED: '{name}' not found in the Drive folder -- has it been uploaded there yet?", file=sys.stderr)
        return 1

    target = DATA_DIR / name
    request = drive.files().get_media(fileId=file_id)
    with io.FileIO(target, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    print(f"Downloaded '{name}' -> {target} ({target.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
