"""One trending Short: choose language and niche from the running counter, pick a real unused story, render, upload,
add to the niche playlist, post the source as the pinned comment, save state.

State (data/trending_state.json via STATE_FILE): posted {date#slot: ...}, used_ids (story keys), seq (counter)."""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from channels.engine import render
from channels.engine import state as state_mod
from channels.trending import config as cfg
from channels.trending import metadata, playlists
from channels.trending.sources import Story, enrich, pick_story

IST = ZoneInfo("Asia/Kolkata")
USED_CAP = 2000
SAMPLE = Story("Sample headline: a trending story appears here with its source named underneath",
               "Example Publisher", "https://example.com/story", None, "news")


def choose(lang: str, niche: str, used: set, yt, fetch=pick_story):
    """The planned niche first, then the other niches in the same language so a quiet source never wastes a slot."""
    order = [niche] + [n for n in cfg.NICHES if n != niche]
    for n in order:
        story = fetch(n, lang, used, yt)
        if story:
            return n, story
    return niche, None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--lang")
    ap.add_argument("--niche")
    ap.add_argument("--dry-run", action="store_true", help="render only, no upload")
    ap.add_argument("--sample", action="store_true", help="use a built-in sample story (no network)")
    ap.add_argument("--public", action="store_true")
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)

    from mahanavi.config import get_settings

    settings = get_settings()
    now = dt.datetime.now(IST)
    date = dt.date.fromisoformat(args.date) if args.date else now.date()
    st = state_mod.load()
    st.setdefault("seq", 0)
    key = state_mod.slot_key(date.isoformat())
    if key in st["posted"] and not args.dry_run and os.environ.get("FORCE_POST") != "true":
        print(f"Already posted for {key}. Nothing to do.")
        return 0
    lang, niche = cfg.plan(st["seq"])
    lang, niche = args.lang or lang, args.niche or niche
    print(f"{key} | seq {st['seq']} | {lang} / {niche}")

    yt = None
    token = settings.trending_youtube_token_file
    if not args.sample and Path(token).exists():
        from channels.engine import upload
        yt = upload.service(token)
    used = set(st["used_ids"])
    if args.sample:
        niche, story = niche, SAMPLE
    else:
        niche, story = choose(lang, niche, used, yt)
    if story is None:
        print("No fresh unused story found in any niche for this language; skipping this slot.")
        return 0

    if not args.sample:
        story = enrich(story, lang)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    row = metadata.row_for(story, lang, niche)
    rcfg = dataclasses.replace(cfg.render_cfg(lang, niche), music_offset=st["seq"])  # a different clip each post
    info = render.render(row, str(out / "short.mp4"), date.isoformat(), rcfg, None, str(out), 4.9)
    meta = metadata.bundle(story, lang, niche)
    (out / "meta.json").write_text(json.dumps({**meta, "story": story.__dict__ | {"published": str(story.published)},
                                                "card": row}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Rendered", info, "| title:", meta["title"], f"({len(meta['title'])} chars)")
    if args.dry_run or args.sample:
        return 0

    from channels.engine import upload
    from mahanavi.publishers.post_ledger import DuplicatePost

    got = yt.channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"]
    if "pulse" not in got.lower():
        raise SystemExit(f"::error::NOT posting: the saved token acts as channel '{got}', not Pulse Boosting.")
    privacy = "public" if args.public else "unlisted"
    try:
        video_id = upload.upload_video(yt, str(out / "short.mp4"), meta["title"], meta["description"], meta["tags"],
                                       None, privacy_status=privacy, language=lang)
    except DuplicatePost as dup:
        print(f"::warning::DUPLICATE BLOCKED, nothing uploaded: {dup}")
        st["used_ids"] = (st["used_ids"] + [story.key])[-USED_CAP:]
        state_mod.save(st)
        return 0
    print(f"UPLOADED ({privacy}) {video_id}\nWatch: https://www.youtube.com/watch?v={video_id}")
    state_mod.mark_posted(st, date.isoformat(), story.key, video_id, False, now.isoformat(timespec="seconds"))
    st["used_ids"] = st["used_ids"][-USED_CAP:]
    st["seq"] += 1
    state_mod.save(st)  # saved before the optional extras so a failure there never causes a second post
    try:
        print(playlists.add(yt, video_id, lang, niche))
    except Exception as exc:  # noqa: BLE001
        print(f"::warning::playlist failed: {exc}")
    try:
        upload.add_comment(yt, video_id, meta["comment"])
        print("source comment posted")
    except Exception as exc:  # noqa: BLE001
        print(f"::warning::comment failed: {exc}")
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"video_id={video_id}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
