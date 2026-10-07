"""Pipeline entry point for Devotional Trance Beats. Run via:

  python -m channels.trance_beats.scripts.post
  python -m channels.trance_beats.scripts.post --dry-run
  python -m channels.trance_beats.scripts.post --public
"""
import sys
from pathlib import Path

from channels.engine.post import ChannelPipeline, run
from channels.trance_beats import channel_config, metadata

CHANNEL_DIR = Path(__file__).resolve().parents[1]


def main():
    from mahanavi.config import get_settings

    settings = get_settings()
    pipeline = ChannelPipeline(
        channel_key="trance_beats",
        expected_channel="Trance",
        content_csv=CHANNEL_DIR / "data" / "content.csv",
        special_csv=None,
        render_cfg=channel_config.RENDER_CFG,
        rotation=channel_config.ROTATION,
        metadata_bundle=metadata.bundle,
        metadata_captions=metadata.captions,
        youtube_token_file=settings.trance_beats_youtube_token_file,
        blogger_blog_id=settings.trance_beats_blogger_blog_id,
        playlist_id=settings.trance_beats_playlist_id,
    )
    return run(pipeline)


if __name__ == "__main__":
    sys.exit(main())
