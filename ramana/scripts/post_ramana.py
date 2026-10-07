"""Pipeline for the Ramana Maharshi TV series: choose, render, upload, captions, seed comment,
Blogger post, update state.

Run only after the gate said "post" (scripts/ci/ramana_gate.py). State is written right after
the upload succeeds, so a failure in the optional extras (captions, playlist, comment, blog
post) never causes a second post.

  python ramana/scripts/post_ramana.py                         # real post for today (IST)
  python ramana/scripts/post_ramana.py --dry-run               # render and write metadata only
  python ramana/scripts/post_ramana.py --dry-run --date 2026-12-30 --row l010

This mirrors the structure of src/mahanavi/scripts/post_rashi_mantra_short.py and friends
(same Blogger step, same "non-fatal extras" pattern) but is otherwise a self-contained
pipeline using the Ramana-specific content bank/renderer under ramana/src/.
"""
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

RAMANA_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAMANA_ROOT))
from src import common, metadata, pick, render, state as state_mod  # noqa: E402

# So `mahanavi.config` / `mahanavi.publishers.blogger_publisher` are importable even when this
# script is invoked directly (python ramana/scripts/post_ramana.py) rather than via `-m`.
REPO_ROOT = RAMANA_ROOT.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
from mahanavi.config import get_settings  # noqa: E402
from mahanavi.publishers.blogger_publisher import post_to_blogger  # noqa: E402

IST = ZoneInfo("Asia/Kolkata")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (IST). Default: today")
    ap.add_argument("--row", help="force a content row id, e.g. q001 (used for the very first post)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--public", action="store_true",
        help=(
            "Upload as public instead of private/draft. Omit this until you've reviewed the "
            "result yourself in YouTube Studio and manually set it to Public (or Unlisted)."
        ),
    )
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    now = dt.datetime.now(IST)
    date = dt.date.fromisoformat(args.date) if args.date else now.date()
    st = state_mod.load()
    if date.isoformat() in st["posted"] and not args.dry_run:
        print(f"Already posted for {date}. Nothing to do.")
        return 0

    rows = common.load_rows()
    special = common.special_for(date)
    if args.row:
        row, reason = next((r for r in rows if r["id"] == args.row), None), "forced"
    else:
        row, reason = pick.choose_row(rows, date, st["used_ids"])
    if row is None:
        print("::error::Content bank is empty or the row id is unknown. Run the monthly refresh workflow.")
        return 1
    print(f"Date {date} | row {row['id']} ({row['category']}) | {reason} | special={special['label_en'] if special else '-'}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    info = render.render(row, str(out / "short.mp4"), date.isoformat(), special, workdir=str(out))
    meta = metadata.bundle(row, special)
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    caps = metadata.captions(row)
    for lang, text in caps.items():
        (out / f"captions_{lang}.srt").write_text(text, encoding="utf-8")
    print("Rendered", info, "| title:", meta["title"], f"({len(meta['title'])} chars)")
    if args.dry_run:
        return 0

    from src import upload  # imported late so dry runs need no Google credentials

    settings = get_settings()
    yt = upload.service(settings.ramana_youtube_token_file)
    # "private" (not "unlisted") by default -- added 2026-10-07 per owner's explicit request
    # to review every Ramana short in Studio before it's reachable by anyone at all, not just
    # before it's public. Pass --public once a short is reviewed and ready to go live.
    privacy_status = "public" if args.public else "private"
    if not args.public:
        print(
            "Uploading as PRIVATE (draft, default). Review it in YouTube Studio and switch it "
            "to Public (or Unlisted) yourself once you're happy, or pass --public to skip the draft step."
        )
    video_id = upload.upload_video(yt, str(out / "short.mp4"), meta["title"], meta["description"], meta["tags"],
                                    meta["localizations"], privacy_status=privacy_status)
    print(f"UPLOADED ({privacy_status}) {video_id}")
    print(f"Watch: https://www.youtube.com/watch?v={video_id}")
    state_mod.mark_posted(st, date.isoformat(), row["id"], video_id, bool(row["special"]), now.isoformat(timespec="seconds"))
    state_mod.save(st)  # marked done immediately, before the optional extras below

    for lang, label in (("te", "Telugu"), ("en", "English")):
        try:
            upload.add_caption(yt, video_id, lang, label, caps[lang])
            print(f"caption {lang} added")
        except Exception as e:  # noqa: BLE001
            print(f"::warning::caption {lang} failed: {e}")
    if settings.ramana_playlist_id:
        try:
            upload.add_to_playlist(yt, video_id, settings.ramana_playlist_id)
            print("added to playlist")
        except Exception as e:  # noqa: BLE001
            print(f"::warning::playlist failed: {e}")
    try:
        upload.add_comment(yt, video_id, meta["comment"])
        print("seed comment posted")
    except Exception as e:  # noqa: BLE001
        print(f"::warning::seed comment failed: {e}")

    # Same in-repo Blogger API v3 step as every other series in this repo (replaces the broken
    # IFTTT applet) -- see src/mahanavi/publishers/blogger_publisher.py's module docstring.
    if post_to_blogger(settings, video_id, meta["title"], meta["description"], blog_id=settings.ramana_blogger_blog_id):
        print("Posted to Blogger.")
    else:
        print("Note: could not post to Blogger (non-fatal).")

    left = len(pick.unused_pool(rows, st["used_ids"]))
    print(f"Unused rows left: {left}")
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"video_id={video_id}\nlow_stock={'true' if left < pick.LOW_STOCK else 'false'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
