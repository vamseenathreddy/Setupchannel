#!/usr/bin/env python3
"""
add_navaratri_captions_and_comment.py: one-off utility that (1) builds
and uploads a Telugu subtitle/caption track for the live
"Swarnakavachadharini Kanakadurgamma" video, matching the exact burned-in
lyric timing from post_navaratri_song.py (SCENE_SEQUENCE weights x the
real song duration, lines evenly split within each section -- the same
math _make_pingpong_loop() uses for the on-screen captions), and (2)
posts a top-level comment with an excerpt of the lyrics and a share
prompt, from the channel's own account.

WHY: the only existing caption track on the live video was an
auto-generated English one (wrong language for a Telugu song -- see
audit_navaratri_video.py's findings, 2026-10-04). A real Telugu
subtitle track is a strong signal for YouTube's Telugu-audience
matching, on top of being genuinely useful to viewers watching with
sound off while scrolling.

NOTE on pinning: the YouTube Data API v3 has no endpoint to pin a
comment -- commentThreads/comments resources have no "pinned" field.
This script posts the comment; pinning it is a one-click manual step
in YouTube Studio (or on the video's own watch page) that only the
channel owner can do.

Usage (from CI, via the "Add Navaratri Captions and Comment" workflow):
    see .github/workflows/add-navaratri-captions.yml
"""

from __future__ import annotations

import sys
from pathlib import Path

from ytcore.config import get_settings
from ytcore.exceptions import YouTubeUploadError
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from ytcore.scripts.post_navaratri_song import (
    LYRIC_LINES,
    SCENE_SEQUENCE,
    SONG_FILENAME,
    _audio_duration_seconds,
)

TITLE_MATCH = "కనకదుర్గమ్మా"
SRT_OUT_PATH = Path("data") / "navaratri_song_telugu.srt"

COMMENT_TEXT = (
    "🙏 శరణు శరణు కనకదుర్గమ్మా 🙏\n\n"
    "\"స్వర్ణకవచధారిణి కనకదుర్గమ్మా\n"
    "శరణు శరణు అంటూ మొక్కేము తల్లీ\n"
    "చల్లని చూపులతో కాపాడవమ్మా\n"
    "వరములు కురిపించు కనకదుర్గమ్మా\"\n\n"
    "ఈ నవరాత్రుల్లో అమ్మవారి ఆశీస్సులు అందరికీ లభించాలని కోరుకుంటూ ఈ గీతాన్ని అందిస్తున్నాం. "
    "మీకు నచ్చితే మీ స్నేహితులు, బంధువులతో షేర్ చేయండి 🙏✨ #KanakaDurga #Navaratri2026"
)


def _srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis == 1000:
        millis = 0
        secs += 1
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _build_srt(total_duration: float, out_path: Path) -> int:
    """Mirrors _make_pingpong_loop()'s caption timing exactly: each
    SCENE_SEQUENCE entry gets total_duration * weight seconds, and that
    section's LYRIC_LINES are shown one at a time over an even split of
    that span."""
    entries: list[tuple[float, float, str]] = []
    t = 0.0
    for key, weight in SCENE_SEQUENCE:
        duration = total_duration * weight
        lines = [line.strip() for line in LYRIC_LINES.get(key, []) if line.strip()]
        if lines:
            slice_seconds = duration / len(lines)
            for i, line in enumerate(lines):
                start = t + i * slice_seconds
                end = t + duration if i == len(lines) - 1 else t + (i + 1) * slice_seconds
                entries.append((start, end, line))
        t += duration

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for idx, (start, end, text) in enumerate(entries, start=1):
            f.write(f"{idx}\n")
            f.write(f"{_srt_timestamp(start)} --> {_srt_timestamp(end)}\n")
            f.write(f"{text}\n\n")
    return len(entries)


def main() -> int:
    settings = get_settings()

    song_path = Path("data") / SONG_FILENAME
    if not song_path.exists():
        print(f"FAILED: song file not found at {song_path} -- did fetch_drive_asset.py run first?", file=sys.stderr)
        return 1
    total_duration = _audio_duration_seconds(song_path)
    print(f"Song duration: {total_duration:.1f}s")

    entry_count = _build_srt(total_duration, SRT_OUT_PATH)
    print(f"Built {SRT_OUT_PATH} with {entry_count} caption entries.")

    uploader = YouTubeShortsUploader(settings)
    try:
        youtube = uploader._build_service()  # noqa: SLF001
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    try:
        channels_resp = youtube.channels().list(part="contentDetails", mine=True).execute()
        uploads_playlist_id = channels_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        video_ids: list[str] = []
        page_token = None
        while len(video_ids) < 50:
            resp = youtube.playlistItems().list(
                part="contentDetails", playlistId=uploads_playlist_id,
                maxResults=50, pageToken=page_token,
            ).execute()
            video_ids.extend(item["contentDetails"]["videoId"] for item in resp.get("items", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        videos_resp = youtube.videos().list(part="snippet", id=",".join(video_ids)).execute()
        matches = [item for item in videos_resp.get("items", []) if TITLE_MATCH in item["snippet"]["title"]]
        if not matches:
            print(f"FAILED: no uploaded video found with '{TITLE_MATCH}' in its title.", file=sys.stderr)
            return 1
        matches.sort(key=lambda item: item["snippet"]["publishedAt"], reverse=True)
        target = matches[0]
        video_id = target["id"]
        print(f"Target video: {video_id} (published {target['snippet']['publishedAt']})")
        if len(matches) > 1:
            print(f"Note: {len(matches)} videos matched '{TITLE_MATCH}'; picked the most recently published one.")

        # --- Caption track ---
        caption_body = {
            "snippet": {
                "videoId": video_id,
                "language": "te",
                "name": "Telugu",
                "isDraft": False,
            }
        }
        media = MediaFileUpload(str(SRT_OUT_PATH), mimetype="application/octet-stream")
        caption_resp = youtube.captions().insert(part="snippet", body=caption_body, media_body=media).execute()
        print(f"SUCCESS: Telugu caption track uploaded (caption id {caption_resp.get('id')}).")

        # --- Pinned-worthy comment ---
        comment_body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {"snippet": {"textOriginal": COMMENT_TEXT}},
            }
        }
        comment_resp = youtube.commentThreads().insert(part="snippet", body=comment_body).execute()
        comment_id = comment_resp.get("id")
        print(f"SUCCESS: comment posted (thread id {comment_id}).")
        print(
            "NOTE: the YouTube Data API has no endpoint to pin a comment -- "
            "pin this one manually in YouTube Studio or on the video's watch "
            "page (channel owner only, one click)."
        )

    except HttpError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
