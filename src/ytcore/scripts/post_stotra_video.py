"""
post_stotra_video.py: renders and uploads one weekly stotra/mantra
long-form video. Content: src/ytcore/content/stotras/<slug>.json.
Audio and background image are fetched from the shared Drive folder
beforehand (names come from the spec's `audio` and `background`).

Usage:
    python -m ytcore.scripts.post_stotra_video kamakhya --privacy private
    python -m ytcore.scripts.post_stotra_video kamakhya --render-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ytcore.config import get_settings
from ytcore.exceptions import AppError
from ytcore.images.fonts import FontManager
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from ytcore.video.stotra_video import StotraSpec, build_seo, build_video, render_thumbnail

MUSIC_CATEGORY_ID = "10"
CONTENT_DIR = Path(__file__).resolve().parents[1] / "content" / "stotras"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug")
    ap.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    ap.add_argument("--render-only", action="store_true")
    ap.add_argument("--data-dir", default="data")
    args = ap.parse_args()

    settings = get_settings()
    data = Path(args.data_dir)
    try:
        spec = StotraSpec.load(CONTENT_DIR / f"{args.slug}.json")
    except (OSError, AppError, ValueError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    audio = data / spec.audio
    if not audio.exists():
        print(f"FAILED: audio not found at {audio} (put '{spec.audio}' in the Drive folder).", file=sys.stderr)
        return 1
    bg = data / spec.background
    bg_path = bg if bg.exists() else None
    if bg_path is None:
        print(f"Note: background '{spec.background}' not found, using the plain fallback background.")

    out_dir = data / "generated"
    video = out_dir / f"stotra_{spec.slug}.mp4"
    thumb = out_dir / f"stotra_{spec.slug}_thumb.jpg"
    try:
        build_video(spec, audio, bg_path, data / "stotra_work" / spec.slug, video)
        render_thumbnail(FontManager(settings.telugu_font_path), spec, bg_path, thumb)
    except AppError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"Rendered: {video} and {thumb}")
    if args.render_only:
        return 0

    playlist_id = settings.playlist_id_stotras
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}" if playlist_id else ""
    seo = build_seo(spec, playlist_url)
    uploader = YouTubeShortsUploader(settings, category_id=MUSIC_CATEGORY_ID)
    result = uploader.upload(video, seo, privacy_status=args.privacy)
    if not result.success or not result.video_id:
        print(f"FAILED to upload: {result.error_message}", file=sys.stderr)
        return 1
    print(f"Uploaded ({args.privacy}): {result.post_url}")

    try:
        from googleapiclient.http import MediaFileUpload
        yt = uploader._build_service()  # noqa: SLF001
        yt.thumbnails().set(videoId=result.video_id, media_body=MediaFileUpload(str(thumb))).execute()
        print("Custom thumbnail set.")
    except Exception as exc:  # noqa: BLE001 -- thumbnail is non-fatal
        print(f"Note: could not set thumbnail ({exc}).")

    if playlist_id:
        print("Added to Stotras playlist." if uploader.add_to_playlist(result.video_id, playlist_id)
              else "Note: could not add to playlist (non-fatal).")
    else:
        print("Note: MAHANAVI_PLAYLIST_ID_STOTRAS not set, skipped playlist add.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
