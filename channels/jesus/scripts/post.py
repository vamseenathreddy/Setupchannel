"""Pipeline entry point for Jesus Worship Waves. Run via:

  python -m channels.jesus.scripts.post                 # real post for today (IST), unlisted
  python -m channels.jesus.scripts.post --dry-run        # render + metadata only
  python -m channels.jesus.scripts.post --public         # go public

All real logic lives in channels/engine/post.py (shared by every Pattern-A channel) -- this
file just builds the ChannelPipeline describing Jesus Worship Waves' own content/render/
metadata/credentials.
"""
import sys
from pathlib import Path

from channels.engine.post import ChannelPipeline, run
from channels.jesus import channel_config, metadata

CHANNEL_DIR = Path(__file__).resolve().parents[1]


def main():
    from mahanavi.config import get_settings

    settings = get_settings()
    pipeline = ChannelPipeline(
        channel_key="jesus",
        content_csv=CHANNEL_DIR / "data" / "content.csv",
        special_csv=None,
        render_cfg=channel_config.RENDER_CFG,
        rotation=channel_config.ROTATION,
        metadata_bundle=metadata.bundle,
        metadata_captions=metadata.captions,
        youtube_token_file=settings.jesus_youtube_token_file,
        blogger_blog_id=settings.jesus_blogger_blog_id,
        playlist_id=settings.jesus_playlist_id,
    )
    return run(pipeline)


if __name__ == "__main__":
    sys.exit(main())
