"""Pipeline entry for the Hindi Purana / Rashi Shorts. SERIES_KIND env: purana | rashi.

  SERIES_KIND=purana python -m channels.mantra_sangam.scripts.post_series [--dry-run] [--public]
"""
import dataclasses
import os
import sys

from channels.engine.post import ChannelPipeline, run
from channels.mantra_sangam import channel_config, metadata_series, series

PLAYLISTS = {
    "purana": ("पुराण कथाएँ | Purana Stories (Hindi)",
               "हर दिन एक पुराण कथा, सरल हिंदी में एक शॉर्ट में।\n\nOne Purana story every day in simple Hindi.\n\n#PuranaStory #HinduMythology #HindiDevotional"),
    "rashi": ("राशि मंत्र | Rashi Mantras (Hindi)",
              "बारह राशियों के मंत्र, सरल हिंदी में।\n\nThe mantra for each of the twelve rashis in Hindi.\n\n#RashiMantra #Navagraha #HindiDevotional"),
}


def main():
    from mahanavi.config import get_settings

    kind = os.environ["SERIES_KIND"]
    settings = get_settings()
    title, desc = PLAYLISTS[kind]
    pipeline = ChannelPipeline(
        channel_key=f"mantra_{kind}",
        expected_channel="Mantra Sangam",
        fetch_row=series.fetch_row_for(kind),
        render_cfg=dataclasses.replace(channel_config.SERIES_CFG, music_offset={"purana": 7, "rashi": 9}[kind]),
        metadata_bundle=metadata_series.bundle,
        metadata_captions=metadata_series.captions,
        youtube_token_file=settings.mantra_sangam_youtube_token_file,
        blogger_blog_id=settings.mantra_sangam_blogger_blog_id,
        playlist_id=None,
        playlist_title=title,
        playlist_description=desc,
        duration=12.0,
    )
    return run(pipeline)


if __name__ == "__main__":
    sys.exit(main())
