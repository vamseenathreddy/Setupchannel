"""Jesus Worship Waves -- EVENING Bible Quiz Short. Run via:

  python -m channels.jesus.scripts.post_quiz [--dry-run] [--public]

Asks about the SAME verse the morning Quote Short posted today (read from the quote state
file, data/jesus_state.json). If the morning Short did not post, nothing is posted. Uses its
own state file (STATE_FILE=data/jesus_quiz_state.json) and its own playlist.
"""
import datetime as dt
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from channels.engine import state as state_mod
from channels.engine.post import ChannelPipeline, run
from channels.jesus import bank, channel_config, metadata
from channels.jesus.scripts.post import approved_music

QUOTE_STATE = Path("data") / "jesus_state.json"
IST = ZoneInfo("Asia/Kolkata")


def fetch_row(_used_ids):
    today = dt.datetime.now(IST).date().isoformat()
    posted = state_mod.load(QUOTE_STATE)["posted"].get(today)
    if not posted:
        print("This morning's Bible Quote Short did not post -- no quiz today.")
        return None
    v = bank.by_id(posted["row"])
    return bank.quiz_row(v) if v else None


def main(argv=None):
    from mahanavi.config import get_settings

    if not approved_music() and "--dry-run" not in (argv or sys.argv[1:]):
        print("No approved BGM yet -- NOT posting.")
        return 0
    settings = get_settings()
    pipeline = ChannelPipeline(
        channel_key="jesus_quiz",
        fetch_row=fetch_row,
        render_cfg=channel_config.QUIZ_CFG,
        metadata_bundle=metadata.bundle,
        metadata_captions=metadata.captions,
        youtube_token_file=settings.jesus_youtube_token_file,
        expected_channel="Jesus",
        blogger_blog_id=settings.jesus_blogger_blog_id,
        playlist_id=bank.playlist_id("quiz", settings.jesus_quiz_playlist_id),
        duration=channel_config.SHORT_SECONDS,
    )
    return run(pipeline, argv)


if __name__ == "__main__":
    sys.exit(main())
