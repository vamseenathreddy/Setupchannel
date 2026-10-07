"""Pipeline entry point for Tollywood News. Run via:

  python -m channels.tollywood_news.scripts.post                 # real post for today (IST), unlisted
  python -m channels.tollywood_news.scripts.post --dry-run        # fetch + render + metadata only
  python -m channels.tollywood_news.scripts.post --public         # go public

Pattern B (fetch_row, not content_csv/rotation) -- see channels/engine/post.py and
channels/tollywood_news/metadata_config.py.
"""
import sys

from channels.engine.post import ChannelPipeline, run
from channels.tollywood_news import channel_config, metadata_config


def main():
    from mahanavi.config import get_settings

    settings = get_settings()
    pipeline = ChannelPipeline(
        channel_key="tollywood_news",
        render_cfg=channel_config.RENDER_CFG,
        fetch_row=metadata_config.fetch_row,
        metadata_bundle=metadata_config.bundle,
        metadata_captions=metadata_config.captions,
        youtube_token_file=settings.tollywood_news_youtube_token_file,
        blogger_blog_id=settings.tollywood_news_blogger_blog_id,
    )
    return run(pipeline)


if __name__ == "__main__":
    sys.exit(main())
