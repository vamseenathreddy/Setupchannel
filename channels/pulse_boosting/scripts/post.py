"""Pipeline entry point for Pulse Boosting. Run via:

  python -m channels.pulse_boosting.scripts.post                 # real post for today (IST), unlisted
  python -m channels.pulse_boosting.scripts.post --dry-run        # fetch + render + metadata only
  python -m channels.pulse_boosting.scripts.post --public         # go public

Pattern B (fetch_row, not content_csv/rotation) -- see channels/engine/post.py and
channels/pulse_boosting/metadata_config.py.
"""
import sys

from channels.engine.post import ChannelPipeline, run
from channels.pulse_boosting import channel_config, metadata_config


def main():
    from mahanavi.config import get_settings

    settings = get_settings()
    pipeline = ChannelPipeline(
        channel_key="pulse_boosting",
        render_cfg=channel_config.RENDER_CFG,
        fetch_row=metadata_config.fetch_row,
        metadata_bundle=metadata_config.bundle,
        metadata_captions=metadata_config.captions,
        youtube_token_file=settings.pulse_boosting_youtube_token_file,
        blogger_blog_id=settings.pulse_boosting_blogger_blog_id,
        expected_channel="Pulse",
    )
    return run(pipeline)


if __name__ == "__main__":
    sys.exit(main())
