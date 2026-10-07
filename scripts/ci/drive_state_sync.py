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
  - data/last_rashi_index.txt                 (0-11, which rashi the Rashi Mantra series posts next)
  - data/last_run_date_rashi_mantra.txt       (IST date Rashi Mantra Short last posted)
  - data/last_purana_short_index.txt          (0-9, which story the Purana Story series posts next)
  - data/purana_short_episode_count.txt       (ever-incrementing "పురాణ కథ - N" display count, never wraps)
  - data/last_purana_concept_index.txt        (0-17, which concept entry the Purana Concept series posts next)
  - data/last_run_date_purana_concept.txt     (IST date Purana Concept Short last posted)
  - data/last_gita_sloka_index.txt            ("mode:index" -- e.g. "quiz:3" -- which verse the
                                                Gita Sloka series' alternating verse/quiz cadence is on)
  - data/last_run_date_gita_sloka.txt         (IST date Gita Sloka Short last posted)

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

*** CONFIRMED VIA A REAL FAILURE (2026-10-01) *** Google Drive service
accounts have ZERO storage quota of their own. update() on a file that
already exists works fine (its quota is charged to whoever actually
owns the file -- a real human Google account, here
vamseenathreddy@gmail.com), but create() for a brand-new file fails
outright with HttpError 403 "Service Accounts do not have storage
quota... storageQuotaExceeded". This is NOT fixable by adjusting code
here -- Shared Drives (which pool quota from the organization) require
Google Workspace, not a personal Gmail account, and OAuth domain-wide
delegation has the same requirement.

PRACTICAL CONSEQUENCE: every path in STATE_FILES must already exist as
a real file in the target Drive folder, created once by the human
account that owns it (not by this script), before this script can ever
successfully push() it. This bit us for real when the hourly-tick
redesign introduced per-Short marker files
(last_run_date_rahu_kalam.txt etc.) to replace the old combined
last_run_date.txt -- nobody pre-created the new marker files in Drive,
so the very first post under the new scheme failed at push(), which
(being a single straight-through script with no per-file error
handling) aborted before pushing any of the remaining STATE_FILES too,
silently skipping whatever Shorts were still queued behind it that
tick. Whenever a new entry is added to STATE_FILES, it must be created
once by hand (or via an authenticated human session, e.g. a connected
Drive account) in the target folder first. *** THIS APPLIES TO
last_rashi_index.txt, ADDED 2026-10-01 *** -- before the Rashi Mantra
series' first real run, create an empty (or containing just "0") text
file named exactly "last_rashi_index.txt" in the same Drive folder as
the other marker files, the same way the earlier Durmuhurtham bug had
to be fixed. Skipping this will NOT crash the run (pull() just won't
find it and the posting script defaults to index 0/Mesha locally), but
push() will then hit the exact same storageQuotaExceeded failure
documented above, and the rotation will silently reset to Mesha every
single run instead of advancing -- it just won't be obvious until
several runs in a row all post the same rashi.

*** THIS ALSO APPLIES TO last_purana_short_index.txt, ADDED 2026-10-02
*** -- same fix, same reason: before the Purana Story series' first
real run, create an empty (or containing just "0") text file named
exactly "last_purana_short_index.txt" in the same Drive folder. Skipping
it means every run silently reposts story 0 (Gajendra Moksham) instead
of advancing through the rotation.

*** AND TO last_run_date_purana_short.txt, ALSO ADDED 2026-10-02 *** --
same fix again: this is the "already posted today" marker
scripts/ci/purana_short_gate.py checks (same role as
last_run_date_rahu_kalam.txt etc. for the alert Shorts). Create an
empty text file named exactly "last_run_date_purana_short.txt" in the
same Drive folder before relying on the daily gate -- otherwise every
gate-passing call on a given day would see "not posted today" and the
series could post more than once in the same 5-6 PM window.

*** AND TO purana_short_episode_count.txt, ADDED 2026-10-02 *** -- same
fix again: this is the ever-incrementing "పురాణ కథ - N" display counter
(distinct from last_purana_short_index.txt's bounded 0-9 content
rotation -- see PuranaShortCard.episode_number's docstring). Create an
empty (or containing just "0") text file named exactly
"purana_short_episode_count.txt" in the same Drive folder before the
first real run -- otherwise push() will hit the same storageQuotaExceeded
failure documented above, and every run will silently restart the
displayed count at "1" instead of advancing, even though the content
rotation itself keeps advancing correctly.

*** AND TO last_purana_concept_index.txt / last_run_date_purana_concept.txt,
ADDED 2026-10-02 for the new Purana Concept Shorts series (11 AM-1 PM
IST window) *** -- same fix, same reason, one more time: before this
series' first real run, create two empty (or "0"-containing, for the
index file) text files named exactly "last_purana_concept_index.txt" and
"last_run_date_purana_concept.txt" in the same Drive folder. Skipping
this means the content rotation silently resets to entry 0 every run,
and/or the daily gate never finds a "posted today" marker and could post
more than once in the same window.

*** AND TO last_gita_sloka_index.txt / last_run_date_gita_sloka.txt,
ADDED 2026-10-02 for the new Bhagavad Gita Sloka Shorts series (3-4 PM
IST window) *** -- same fix, same reason: create two empty (or
"0"-containing, for the index file) text files named exactly
"last_gita_sloka_index.txt" and "last_run_date_gita_sloka.txt" in the
same Drive folder before this series' first real run.

*** AND TO last_run_date_rashi_mantra.txt, ADDED 2026-10-03 when the
Rashi Mantra series moved from manual-test-only to a recurring daily
gate (8-9 AM IST window, scripts/ci/rashi_mantra_gate.py) *** -- same
fix, same reason: this is the "already posted today" marker the gate
checks (last_rashi_index.txt itself already exists in Drive from the
earlier manual test run, so only this NEW marker file needs
pre-creating). Create an empty text file named exactly
"last_run_date_rashi_mantra.txt" in the same Drive folder before
relying on the daily gate -- otherwise every gate-passing call in the
window would see "not posted today" and the series could post more
than once in the same 8-9 AM window.

*** AND TO youtube_token_ramana.json / ramana_state.json, ADDED 2026-10
for the Ramana Maharshi TV channel (ramana/ at the repo root, a
second, separate YouTube channel/pipeline folded into this SAME Drive
folder and service account rather than standing up a second one) ***
-- same fix, same reason, one more time: before that pipeline's first
real run, create two files by hand in this same Drive folder: an empty
one named exactly "youtube_token_ramana.json" (overwritten for real
the first time `python scripts/ci/drive_state_sync.py push` runs after
a local `youtube_shorts_auth_setup.py --token-file
data/youtube_token_ramana.json`), and one named exactly
"ramana_state.json" containing just `{}` (ramana/src/state.py fills in
the real "posted"/"used_ids" structure itself on first save). Skipping
either means the first real push() hits the same storageQuotaExceeded
failure documented above.

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
    "last_rashi_index.txt",
    "last_purana_short_index.txt",
    "last_run_date_purana_short.txt",
    "purana_short_episode_count.txt",
    "last_purana_concept_index.txt",
    "last_run_date_purana_concept.txt",
    "last_gita_sloka_index.txt",
    "last_run_date_gita_sloka.txt",
    "last_run_date_rashi_mantra.txt",
    "youtube_token_ramana.json",  # Ramana Maharshi TV channel's own OAuth token (separate channel, see config.py)
    "ramana_state.json",          # Ramana Maharshi TV's "posted"/"used_ids" state (ramana/src/state.py)
    # --- The 7-channel expansion (channels/ at the repo root, added 2026-10) --- same pattern
    # as the Ramana pair above, one token + one state file per channel. *** EACH OF THESE 14
    # FILES MUST BE PRE-CREATED BY HAND IN THE SAME DRIVE FOLDER BEFORE THAT CHANNEL'S FIRST
    # REAL RUN *** -- same storageQuotaExceeded reason documented at length above: an empty
    # file for each "youtube_token_*.json" (overwritten for real the first time
    # drive_state_sync.py push runs after a local youtube_shorts_auth_setup.py --token-file
    # run for that channel), and a file containing just "{}" for each "*_state.json".
    "youtube_token_jesus.json",
    "jesus_state.json",
    "jesus_quiz_state.json",  # evening Bible Quiz Short (shares youtube_token_jesus.json); MUST be pre-created containing {}
    "youtube_token_infoshorts.json",
    "infoshorts_state.json",
    "youtube_token_mantra_sangam.json",
    "mantra_sangam_state.json",
    "youtube_token_trance_beats.json",
    "trance_beats_state.json",
    "trance_bhagavatam_state.json",
    "trance_mantra_state.json",
    "youtube_token_pulse_boosting.json",
    "pulse_boosting_state.json",
    "youtube_token_tollywood_news.json",
    "tollywood_news_state.json",
    "youtube_token_live_hyderabad.json",
    "live_hyderabad_state.json",
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
