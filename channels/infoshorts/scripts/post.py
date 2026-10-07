"""Pipeline entry point for InfoShorts Telugu. Run via:

  python -m channels.infoshorts.scripts.post
  python -m channels.infoshorts.scripts.post --dry-run
  python -m channels.infoshorts.scripts.post --public
"""
import sys
from pathlib import Path

from channels.engine.post import ChannelPipeline, run
from channels.infoshorts import channel_config, metadata

CHANNEL_DIR = Path(__file__).resolve().parents[1]


def main():
    from mahanavi.config import get_settings

    settings = get_settings()
    pipeline = ChannelPipeline(
        channel_key="infoshorts",
        content_csv=CHANNEL_DIR / "data" / "content.csv",
        special_csv=None,
        render_cfg=channel_config.RENDER_CFG,
        rotation=channel_config.ROTATION,
        metadata_bundle=metadata.bundle,
        metadata_captions=metadata.captions,
        youtube_token_file=settings.infoshorts_youtube_token_file,
        blogger_blog_id=settings.infoshorts_blogger_blog_id,
        playlist_id=settings.infoshorts_playlist_id,
    )
    return run(pipeline)


if __name__ == "__main__":
    sys.exit(main())
