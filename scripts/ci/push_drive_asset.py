#!/usr/bin/env python3
"""
push_drive_asset.py: uploads ONE local file to the same Drive folder
drive_state_sync.py uses, as an existing-file UPDATE (never a create) --
the counterpart to fetch_drive_asset.py. Added 2026-10-03 so a one-off
script's result (e.g. the printed playlist IDs from
youtube_playlists_setup.py, which the channel owner needs copied into
GitHub secrets, but which this session has no way to read back out of
a GitHub Actions job log) can be handed off through Drive instead,
where it's readable via a normal Drive account.

IMPORTANT -- update only, never create: this re-uses the service
account creds (GDRIVE_SA_KEY_JSON / GDRIVE_FOLDER_ID), and per
drive_state_sync.py's module docstring, a Drive service account has
ZERO storage quota of its own -- create() for a brand-new file fails
outright with storageQuotaExceeded, but update() on a file that
ALREADY EXISTS works fine (the quota is charged to the human owner of
that existing file). So the destination file must already exist in
the Drive folder, created once by a real Google account (e.g. via the
Drive connector, or by hand) -- this script will refuse to create one.

Usage (from CI):
    python scripts/ci/push_drive_asset.py <local-path> <name-in-drive-folder>
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _drive_client():  # noqa: ANN201 -- not type-checked in CI; matches fetch_drive_asset.py's style
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
    if len(sys.argv) != 3:
        print("Usage: push_drive_asset.py <local-path> <name-in-drive-folder>", file=sys.stderr)
        return 1
    local_path = Path(sys.argv[1])
    drive_name = sys.argv[2]

    if not local_path.exists():
        print(f"FAILED: local file '{local_path}' does not exist, nothing to push", file=sys.stderr)
        return 1

    drive = _drive_client()
    file_id = _find_file_id(drive, drive_name)
    if not file_id:
        print(
            f"FAILED: '{drive_name}' does not exist yet in the Drive folder -- a service "
            "account can't create a brand-new file (storageQuotaExceeded), so it must be "
            "created once by hand or via a connected human Drive account first.",
            file=sys.stderr,
        )
        return 1

    media = MediaFileUpload(str(local_path), resumable=False)
    drive.files().update(fileId=file_id, media_body=media).execute()
    print(f"Pushed '{local_path}' -> Drive '{drive_name}' ({local_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
