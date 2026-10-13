"""One-off: create (or find, by exact title) the two Jesus Worship Waves playlists with the
channel's own saved token, and write their IDs to data/jesus_playlist_ids.json (pushed to Drive
by the workflow, since job logs aren't readable from the dev sandbox):

  Bible Quotes - Jesus Worship Waves   (morning Bible Quote Shorts)
  Bible Quiz - Jesus Worship Waves     (evening Bible Quiz Shorts)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so `channels` resolves
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from channels.engine import upload  # noqa: E402

PLAYLISTS = {
    "quotes": ("Bible Quotes | బైబిల్ వచనాలు - Jesus Worship Waves",
               "A Bible quote every morning in English and Telugu, and how it applies to our life."),
    "quiz": ("Bible Quiz | బైబిల్ క్విజ్ - Jesus Worship Waves",
             "A Bible quiz every evening: guess the book and chapter of the day's verse."),
}


def main() -> int:
    from mahanavi.config import get_settings

    yt = upload.service(get_settings().jesus_youtube_token_file)
    existing, token = {}, None
    while True:
        r = yt.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=token).execute()
        for item in r.get("items", []):
            existing[item["snippet"]["title"]] = item["id"]
        token = r.get("nextPageToken")
        if not token:
            break
    ids = {}
    for key, (title, desc) in PLAYLISTS.items():
        if title in existing:
            ids[key] = existing[title]
            print(f"found {key}: {ids[key]}")
        else:
            body = {"snippet": {"title": title, "description": desc}, "status": {"privacyStatus": "public"}}
            ids[key] = yt.playlists().insert(part="snippet,status", body=body).execute()["id"]
            print(f"created {key}: {ids[key]}")
    out = Path("data/jesus_playlist_ids.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ids), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
