"""Pipeline entry point for Divine Mantra Sangam. Run via:

  python -m channels.mantra_sangam.scripts.post
  python -m channels.mantra_sangam.scripts.post --dry-run
  python -m channels.mantra_sangam.scripts.post --public
"""
import sys
from pathlib import Path

from channels.engine.post import ChannelPipeline, run
from channels.mantra_sangam import channel_config, metadata

CHANNEL_DIR = Path(__file__).resolve().parents[1]


def main():
    from mahanavi.config import get_settings

    settings = get_settings()
    pipeline = ChannelPipeline(
        channel_key="mantra_sangam",
        expected_channel="Mantra Sangam",
        content_csv=CHANNEL_DIR / "data" / "content.csv",
        special_csv=None,
        render_cfg=channel_config.RENDER_CFG,
        rotation=channel_config.ROTATION,
        metadata_bundle=metadata.bundle,
        metadata_captions=metadata.captions,
        youtube_token_file=settings.mantra_sangam_youtube_token_file,
        blogger_blog_id=settings.mantra_sangam_blogger_blog_id,
        playlist_id=settings.mantra_sangam_playlist_id,
    )
    return run(pipeline)


if __name__ == "__main__":
    sys.exit(main())
