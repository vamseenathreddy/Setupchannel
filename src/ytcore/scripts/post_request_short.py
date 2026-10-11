"""
post_request_short.py: builds and uploads a viewer-request mantra Short (content/request_shorts.py).
Uploads PRIVATE by default so the owner can verify it in YouTube Studio and publish it by hand.

Usage:
    python -m ytcore.scripts.post_request_short --spec narasimha_mantras --dry-run
    python -m ytcore.scripts.post_request_short --spec narasimha_mantras            # uploads private
    python -m ytcore.scripts.post_request_short --spec narasimha_mantras --after-publish VIDEO_ID
        # once the Short is public: replies to the viewer's comment and posts the mantras as a first comment
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

from ytcore.brandcfg import A_SHORT
from ytcore.config import get_settings
from ytcore.content.alert_seo import _CHANNEL_FOOTER_EN
from ytcore.content.branding import brand_tags, brand_title
from ytcore.content.request_shorts import SPECS, RequestShort
from ytcore.exceptions import AppError, YouTubeUploadError
from ytcore.images.request_card_renderer import RequestCardRenderer
from ytcore.publishers.youtube_shorts_uploader import DEFAULT_CATEGORY_ID, YouTubeShortsUploader

FADE = 0.6   # seconds of dip-to-dark between slides (a plain cross-fade overlaps two different text layouts)
FPS = 30


def assemble(spec: RequestShort, images: list[Path], music: Path, out: Path) -> Path:
    """Cross-fade the slides (each slide's own seconds, transitions included) over looped music."""
    secs = [s.seconds for s in spec.slides]
    total = sum(secs)
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for i, img in enumerate(images):
        length = secs[i] + (FADE if i < len(images) - 1 else 0)
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{length:.2f}", "-i", str(img)]
    cmd += ["-stream_loop", "-1", "-i", str(music)]
    chain = [f"[{i}:v]scale=1080:1920,setsar=1,fps={FPS},format=yuv420p[v{i}]" for i in range(len(images))]
    prev, offset = "v0", 0.0
    for i in range(1, len(images)):
        offset += secs[i - 1]
        chain.append(f"[{prev}][v{i}]xfade=transition=fadeblack:duration={FADE}:offset={offset:.2f}[x{i}]")
        prev = f"x{i}"
    chain.append(f"[{len(images)}:a]afade=t=in:st=0:d=1,afade=t=out:st={total - 1.5:.2f}:d=1.5[a]")
    cmd += ["-filter_complex", ";".join(chain), "-map", f"[{prev}]", "-map", "[a]", "-t", f"{total:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out)]
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True)
    return out


def upload(youtube: Any, spec: RequestShort, video: Path, privacy: str, publish_at: str = "") -> str:
    from googleapiclient.http import MediaFileUpload

    mahanavi = A_SHORT.lower() in spec.expected_channel.lower()
    body = {
        "snippet": {
            "title": brand_title(spec.title) if mahanavi else spec.title, "description": spec.description(),
            "tags": brand_tags(spec.tags) if mahanavi else spec.tags,
            "categoryId": DEFAULT_CATEGORY_ID, "defaultLanguage": spec.lang, "defaultAudioLanguage": spec.lang,
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
        "localizations": {"en": {"title": spec.title_en,
                                 "description": f"{spec.description_en}\n\n{_CHANNEL_FOOTER_EN}\n\n{' '.join(spec.hashtags)}"}},
    }
    if publish_at:  # scheduled release: uploaded private, YouTube makes it public at that moment
        body["status"] = {"privacyStatus": "private", "publishAt": publish_at, "selfDeclaredMadeForKids": False}
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=-1, resumable=True)
    resp = youtube.videos().insert(part="snippet,status,localizations", body=body, media_body=media).execute()
    return str(resp["id"])


def after_publish(youtube: Any, spec: RequestShort, video_id: str) -> None:
    url = f"https://www.youtube.com/watch?v={video_id}"
    youtube.comments().insert(part="snippet", body={"snippet": {
        "parentId": spec.comment_id, "textOriginal": spec.reply_text(url)}}).execute()
    print(f"Replied to {spec.handle}'s comment.")
    youtube.commentThreads().insert(part="snippet", body={"snippet": {
        "videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": spec.first_comment()}}}}).execute()
    print("Posted the mantras as the first comment (pin it in Studio).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", default="narasimha_mantras", choices=sorted(SPECS))
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    parser.add_argument("--publish-at", default="", help="ISO time with offset, e.g. 2026-10-09T23:00:00+05:30: schedule the release.")
    parser.add_argument("--dry-run", action="store_true", help="Render slides + video only; no upload.")
    parser.add_argument("--after-publish", metavar="VIDEO_ID", help="Reply to the viewer + first comment on a public Short.")
    args = parser.parse_args(argv)

    spec = SPECS[args.spec]
    settings = get_settings()
    try:
        if args.after_publish:
            after_publish(YouTubeShortsUploader(settings)._build_service(), spec, args.after_publish)  # noqa: SLF001
            return 0

        out_dir = settings.output_dir / "request_shorts" / spec.slug
        slides = RequestCardRenderer(settings).render_all(spec, out_dir)
        music = settings.alert_short_music_path
        if music is None or not music.exists():
            raise AppError(f"Music file missing: {music}")
        video = assemble(spec, [s.path for s in slides], music, out_dir / f"{spec.slug}.mp4")
        print(f"Assembled: {video} ({spec.total_seconds:.1f}s, {len(slides)} slides)")
        if args.dry_run:
            return 0

        youtube = YouTubeShortsUploader(settings)._build_service()  # noqa: SLF001
        got = youtube.channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"]
        if spec.expected_channel.lower() not in got.lower():
            raise AppError(f"NOT posting: the token acts as channel '{got}', expected '{spec.expected_channel}'.")
        publish_at = ""
        if args.publish_at:
            import datetime as dt
            publish_at = dt.datetime.fromisoformat(args.publish_at).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        video_id = upload(youtube, spec, video, args.privacy, publish_at)
        print(f"Channel: {got}" + (f" | scheduled public at {args.publish_at}" if args.publish_at else ""))
        print(f"Uploaded ({args.privacy}): https://www.youtube.com/watch?v={video_id}")
        print(f"Studio: https://studio.youtube.com/video/{video_id}/edit")
        print(f"VIDEO_ID={video_id}")
        return 0
    except (AppError, YouTubeUploadError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # googleapiclient HttpError etc.: surface it in the log
        print(f"FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
