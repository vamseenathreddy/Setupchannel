"""Generic pipeline: choose, render, upload, captions, seed comment, Blogger post, update
state -- shared by every channel in this repo, Pattern A (static content bank) and Pattern B
(one live/trending story a day) alike. Each channel's own scripts/post.py builds a
ChannelPipeline (see below) describing either its content bank (content_csv + rotation) OR a
fetch_row callable (Pattern B), its render config, and metadata functions, then calls
run(pipeline). This is the same sequence as ramana/scripts/post_ramana.py (and
post_rashi_mantra_short.py and friends), generalized.
"""
import dataclasses
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from . import common, pick, render
from . import state as state_mod

IST = ZoneInfo("Asia/Kolkata")


@dataclasses.dataclass
class ChannelPipeline:
    channel_key: str
    render_cfg: "render.ChannelConfig"
    metadata_bundle: Callable       # (row, special) -> {"title","description","tags","localizations","comment"}
    metadata_captions: Callable     # (row) -> {"lang": srt_text}
    youtube_token_file: Path
    expected_channel: str = ""  # if set, refuse to upload unless the token's channel title contains this (case-insensitive)
    # Pattern A (static content bank): set content_csv + rotation.
    content_csv: Path | None = None
    rotation: dict | None = None
    special_csv: Path | None = None
    sensitive_words: tuple = ()
    warmup_days: int = 0
    # Pattern B (one live/trending story a day): set fetch_row instead of content_csv/rotation.
    # Called as fetch_row(used_ids) -> row dict (same shape as a content.csv row) or None if
    # nothing fresh was found today (the pipeline then exits cleanly, nothing posted).
    fetch_row: Callable | None = None
    blogger_blog_id: str | None = None
    playlist_id: str | None = None
    duration: float = 5.0


def run(ch: ChannelPipeline, argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (IST). Default: today")
    ap.add_argument("--row", help="force a content row id (used for the very first post)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--public", action="store_true",
                     help="Upload as public instead of unlisted. Omit until you've reviewed the result.")
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)

    now = dt.datetime.now(IST)
    date = dt.date.fromisoformat(args.date) if args.date else now.date()
    st = state_mod.load()
    if date.isoformat() in st["posted"] and not args.dry_run:
        print(f"Already posted for {date}. Nothing to do.")
        return 0

    rows = None
    special = None
    if ch.fetch_row is not None:
        # Pattern B: one live/trending story, no static bank. "Nothing fresh" is a clean,
        # non-error skip -- unlike Pattern A, an empty day is expected sometimes (no story
        # published in the last N hours), not a configuration bug.
        row, reason = ch.fetch_row(st["used_ids"]), "trending"
        if row is None:
            print("No fresh trending story found for today -- skipping, nothing posted.")
            return 0
    else:
        rows = common.load_rows(ch.content_csv)
        special = common.special_for(date, ch.special_csv)
        if args.row:
            row, reason = next((r for r in rows if r["id"] == args.row), None), "forced"
        else:
            row, reason = pick.choose_row(rows, date, st["used_ids"], ch.rotation, ch.sensitive_words, ch.warmup_days)
        if row is None:
            print("::error::Content bank is empty or the row id is unknown.")
            return 1
    print(f"Date {date} | row {row['id']} ({row['category']}) | {reason} | special={special.get('label_primary') if special else '-'}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    info = render.render(row, str(out / "short.mp4"), date.isoformat(), ch.render_cfg, special, str(out), ch.duration)
    meta = ch.metadata_bundle(row, special)
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    caps = ch.metadata_captions(row)
    for lang, text in caps.items():
        (out / f"captions_{lang}.srt").write_text(text, encoding="utf-8")
    print("Rendered", info, "| title:", meta["title"], f"({len(meta['title'])} chars)")
    if args.dry_run:
        return 0

    from . import upload
    from mahanavi.config import get_settings
    from mahanavi.publishers.blogger_publisher import post_to_blogger

    settings = get_settings()
    yt = upload.service(ch.youtube_token_file)
    if ch.expected_channel:
        got = yt.channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"]
        if ch.expected_channel.lower() not in got.lower():
            raise SystemExit(f"::error::NOT posting: the saved token acts as channel '{got}', not '{ch.expected_channel}'. "
                             "Re-run the one-time auth and pick the right channel at the Google consent screen.")
    privacy_status = "public" if args.public else "unlisted"
    if not args.public:
        print("Uploading as UNLISTED (default). Pass --public once you're happy with the result.")
    video_id = upload.upload_video(yt, str(out / "short.mp4"), meta["title"], meta["description"], meta["tags"],
                                    meta.get("localizations"), privacy_status=privacy_status)
    print(f"UPLOADED ({privacy_status}) {video_id}")
    print(f"Watch: https://www.youtube.com/watch?v={video_id}")
    state_mod.mark_posted(st, date.isoformat(), row["id"], video_id, bool(row["special"]), now.isoformat(timespec="seconds"))
    state_mod.save(st)  # marked done immediately, before the optional extras below

    for lang, text in caps.items():
        try:
            upload.add_caption(yt, video_id, lang, lang.upper(), text)
            print(f"caption {lang} added")
        except Exception as e:  # noqa: BLE001
            print(f"::warning::caption {lang} failed: {e}")
    if ch.playlist_id:
        try:
            upload.add_to_playlist(yt, video_id, ch.playlist_id)
            print("added to playlist")
        except Exception as e:  # noqa: BLE001
            print(f"::warning::playlist failed: {e}")
    if meta.get("comment"):
        try:
            upload.add_comment(yt, video_id, meta["comment"])
            print("seed comment posted")
        except Exception as e:  # noqa: BLE001
            print(f"::warning::seed comment failed: {e}")

    if post_to_blogger(settings, video_id, meta["title"], meta["description"], blog_id=ch.blogger_blog_id):
        print("Posted to Blogger.")
    else:
        print("Note: could not post to Blogger (non-fatal).")

    gh = os.environ.get("GITHUB_OUTPUT")
    if rows is not None:
        left = len(pick.unused_pool(rows, st["used_ids"]))
        print(f"Unused rows left: {left}")
        if gh:
            with open(gh, "a") as f:
                f.write(f"video_id={video_id}\nlow_stock={'true' if left < pick.LOW_STOCK else 'false'}\n")
    elif gh:
        with open(gh, "a") as f:
            f.write(f"video_id={video_id}\nlow_stock=false\n")
    return 0
