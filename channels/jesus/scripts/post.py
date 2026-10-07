"""Jesus Worship Waves -- MORNING Bible Quote Short. Run via:

  python -m channels.jesus.scripts.post                 # real post for today (IST), unlisted
  python -m channels.jesus.scripts.post --dry-run       # render + metadata only
  python -m channels.jesus.scripts.post --public        # go public

Posts the next unused verse in data/verses.json (never repeats). Needs at least one APPROVED
BGM clip in assets/music/approved/ -- with none, nothing is posted (the owner validates every
sliced clip before it can be used).
"""
import glob
import sys
from pathlib import Path

from channels.engine.post import ChannelPipeline, run
from channels.jesus import bank, channel_config, metadata

CHANNEL_DIR = Path(__file__).resolve().parents[1]


def approved_music() -> list[str]:
    return sorted(glob.glob(str(channel_config.QUOTE_CFG.assets_dir / channel_config.QUOTE_CFG.music_glob)))


def fetch_row(used_ids):
    v = bank.next_unused(used_ids)
    if v is None:
        raise SystemExit("::error::Verse bank exhausted -- add more verses to channels/jesus/data/verses.json "
                         "(nothing is ever re-posted automatically).")
    return bank.quote_row(v)


def main(argv=None):
    from mahanavi.config import get_settings

    if not approved_music() and "--dry-run" not in (argv or sys.argv[1:]):
        print("No approved BGM in channels/jesus/assets/music/approved/ yet -- NOT posting. "
              "(Slice the song with scripts/dev/slice_bgm.py and approve the clips first.)")
        return 0
    settings = get_settings()
    pipeline = ChannelPipeline(
        channel_key="jesus",
        fetch_row=fetch_row,
        render_cfg=channel_config.QUOTE_CFG,
        metadata_bundle=metadata.bundle,
        metadata_captions=metadata.captions,
        youtube_token_file=settings.jesus_youtube_token_file,
        expected_channel="Jesus",
        blogger_blog_id=settings.jesus_blogger_blog_id,
        playlist_id=bank.playlist_id("quotes", settings.jesus_playlist_id),
        duration=channel_config.SHORT_SECONDS,
    )
    return run(pipeline, argv)


if __name__ == "__main__":
    sys.exit(main())
