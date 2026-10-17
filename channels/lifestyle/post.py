"""Render and upload the weekly lifestyle video for one language.

  python -m channels.lifestyle.post --lang te --privacy private          # Mahanavi Spirituals (Telugu)
  python -m channels.lifestyle.post --lang hi --privacy private          # Divine Mantra Sangam (Hindi)
  python -m channels.lifestyle.post --lang te --render-only
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

from channels.engine import state as state_mod
from channels.lifestyle import render as R
from channels.lifestyle import topics

REPO = Path(__file__).resolve().parents[2]
CHANNELS = {
    "te": {"name": "Mahanavi Spirituals", "token": "data/youtube_token.json", "language": "te", "lang": "te",
           "assets": REPO / "channels/mantra_sangam/assets", "bg_glob": "backgrounds/*.webp", "music_glob": "music/*.mp3",
           "playlist": "జీవన నియమాలు | Daily Life Rules from Puranas | Mahanavi Spirituals",
           "english": "Purana Life Rules in Telugu", "tag": "Telugu"},
    "hi": {"name": "Divine Mantra Sangam", "token": "data/youtube_token_mantra_sangam.json", "language": "hi", "lang": "hi",
           "assets": REPO / "channels/mantra_sangam/assets", "bg_glob": "backgrounds/*.webp", "music_glob": "music/*.mp3",
           "playlist": "जीवन नियम | Daily Life Rules from Puranas | Divine Mantra Sangam",
           "english": "Purana Life Rules in Hindi", "tag": "Hindi"},
    # Hindi again, on the Krishna-themed Trance Beats channel: its own backgrounds and approved music
    "tb": {"name": "Devotional Trance Beats", "token": "data/youtube_token_trance_beats.json", "language": "hi", "lang": "hi",
           "assets": REPO / "channels/trance_beats/assets", "bg_glob": "backgrounds/*.webp", "music_glob": "music/approved/*.mp3",
           "playlist": "जीवन नियम | Daily Life Rules from Puranas | Devotional Trance Beats",
           "english": "Purana Life Rules in Hindi", "tag": "Hindi"},
}


def _stamp(sec: int) -> str:
    return f"{sec // 60}:{sec % 60:02d}"


def metadata(key: str, theme: dict, chapters: list[int]) -> dict:
    ch = CHANNELS[key]
    lang = ch["lang"]
    data = theme[lang]
    title = f"{data['title']} | {ch['english']}"[:100]
    lines = [data["title"], "",
             {"te": "పురాణాలు, స్మృతుల ప్రకారం రోజువారీ జీవన నియమాలు. పాయింట్ల వారీగా చూడండి.",
              "hi": "पुराणों और स्मृतियों के अनुसार दैनिक जीवन के नियम। बिंदुवार देखें।"}[lang], "",
             "0:00 " + {"te": "పరిచయం", "hi": "परिचय"}[lang]]
    for sec, (ptitle, _body, _src) in zip(chapters, data["points"]):
        lines.append(f"{_stamp(max(sec, 10))} {ptitle}")
    lines += ["", topics.DISCLAIMER[lang], "", topics.CTA[lang], "",
              f"#{ch['tag']} #Puranas #Dinacharya #HinduTradition #LifeRules #{ch['name'].replace(' ', '')}"]
    # chapter stamps must be strictly increasing and >= 10 s apart
    tags = [ch["name"], "Puranas", "Dinacharya", "Hindu daily routine", "Garuda Purana", "Vishnu Purana", "Manusmriti",
            "bath rules", "nail cutting rules", ch["english"], f"{ch['tag']} spiritual"]
    return {"title": title, "description": "\n".join(lines), "tags": tags, "language": ch["language"],
            "comment": {"te": "ఈ నియమాల్లో మీ ఇంట్లో ఏవి పాటిస్తారు? కామెంట్ చేయండి.",
                        "hi": "इनमें से कौन से नियम आपके घर में माने जाते हैं? कमेंट करें।"}[lang]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lang", choices=sorted(CHANNELS), required=True)
    ap.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    ap.add_argument("--render-only", action="store_true")
    ap.add_argument("--date", help="ISO date to pick the week's theme for (default today, IST)")
    ap.add_argument("--out", default="data/generated")
    args = ap.parse_args()

    day = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()
    theme = topics.theme_for(day)
    key, ch = args.lang, CHANNELS[args.lang]
    lang = ch["lang"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    tops: list[int] = []
    strip = R.build_strip(lang, theme, tops)
    chapters = R.chapter_seconds(tops, strip.height)
    backs = sorted(ch["assets"].glob(ch["bg_glob"]))
    music = sorted(ch["assets"].glob(ch["music_glob"]))
    week = day.isocalendar()[1]
    mp4 = out / f"lifestyle_{key}_{day.isoformat()}.mp4"
    secs = R.render(lang, theme, backs[week % len(backs)], music[week % len(music)], mp4, out / f"lifestyle_{key}_work")
    print(f"::notice::rendered {mp4.name}: {secs:.0f} s, chapters {chapters}")
    meta = metadata(key, theme, chapters)
    if args.render_only:
        print(meta["title"])
        print(meta["description"])
        return 0

    from channels.engine import upload
    from mahanavi.publishers.post_ledger import DuplicatePost

    yt = upload.service(Path(ch["token"]))
    got = yt.channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"]
    if ch["name"].lower() not in got.lower():
        raise SystemExit(f"::error::token acts as channel '{got}', not '{ch['name']}'")
    try:
        video_id = upload.upload_video(yt, str(mp4), meta["title"], meta["description"], meta["tags"],
                                       privacy_status=args.privacy, language=meta["language"])
    except DuplicatePost as dup:
        print(f"::warning::DUPLICATE BLOCKED, nothing uploaded: {dup}")
        return 0
    print(f"::notice::UPLOADED ({args.privacy}) https://www.youtube.com/watch?v={video_id}")
    st = state_mod.load()
    state_mod.mark_posted(st, day.isoformat(), theme["slug"], video_id, False,
                          dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
    state_mod.save(st)
    try:
        pl = upload.find_or_create_playlist(yt, ch["playlist"], "", ch["language"])
        upload.add_to_playlist(yt, video_id, pl)
        print("::notice::added to playlist")
    except Exception as exc:  # noqa: BLE001
        print(f"::warning::playlist failed: {exc}")
    try:
        upload.add_comment(yt, video_id, meta["comment"])
    except Exception as exc:  # noqa: BLE001
        print(f"::warning::comment failed: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
