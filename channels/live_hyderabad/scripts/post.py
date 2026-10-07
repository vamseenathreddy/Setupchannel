"""Pipeline entry point for Live Hyderabad. Run via:

  python -m channels.live_hyderabad.scripts.post                 # real post for today (IST), unlisted
  python -m channels.live_hyderabad.scripts.post --dry-run        # fetch + render + metadata only
  python -m channels.live_hyderabad.scripts.post --public         # go public

Pattern B (fetch_row, not content_csv/rotation) -- see channels/engine/post.py and
channels/live_hyderabad/metadata_config.py.
"""
import sys

from channels.engine.post import ChannelPipeline, run
from channels.live_hyderabad import channel_config, metadata_config


def main():
    from mahanavi.config import get_settings

    settings = get_settings()
    pipeline = ChannelPipeline(
        channel_key="live_hyderabad",
        render_cfg=channel_config.RENDER_CFG,
        fetch_row=metadata_config.fetch_row,
        metadata_bundle=metadata_config.bundle,
        metadata_captions=metadata_config.captions,
        youtube_token_file=settings.live_hyderabad_youtube_token_file,
        blogger_blog_id=settings.live_hyderabad_blogger_blog_id,
    )
    return run(pipeline)


if __name__ == "__main__":
    sys.exit(main())
