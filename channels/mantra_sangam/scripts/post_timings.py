"""Pipeline entry for the three daily Hindi timing Shorts. TIMING_KIND env: rahu | shubh | durm.

  TIMING_KIND=rahu python -m channels.mantra_sangam.scripts.post_timings [--dry-run] [--public]
"""
import dataclasses
import os
import sys

from channels.engine.post import ChannelPipeline, run
from channels.mantra_sangam import channel_config, metadata_timings, timings

PLAYLIST_TITLE = "आज का पंचांग | Daily Panchang: Rahu Kaal, Shubh Muhurat, Durmuhurat (Hindi)"
PLAYLIST_DESC = ("हर दिन का राहु काल, शुभ मुहूर्त (अभिजीत और ब्रह्म मुहूर्त) और दुर्मुहूर्त, सरल हिंदी में एक शॉर्ट में। "
                 "रोज़ अपडेट के लिए Divine Mantra Sangam को सब्सक्राइब करें।\n\nDaily Rahu Kaal, Shubh Muhurat (Abhijit and "
                 "Brahma Muhurat) and Durmuhurat in simple Hindi, one short every day. Times are calculated for New Delhi.\n\n"
                 "#RahuKaal #ShubhMuhurat #Durmuhurat #Panchang #HindiDevotional")


def main():
    from mahanavi.config import get_settings

    kind = os.environ["TIMING_KIND"]
    settings = get_settings()
    pipeline = ChannelPipeline(
        channel_key={"rahu": "mantra_rahu", "shubh": "mantra_shubh", "durm": "mantra_durm"}[kind],
        expected_channel="Mantra Sangam",
        fetch_row=timings.fetch_row_for(kind),
        render_cfg=dataclasses.replace(channel_config.TIMING_CFG, music_offset={"rahu": 0, "shubh": 3, "durm": 5}[kind]),
        metadata_bundle=metadata_timings.bundle,
        metadata_captions=metadata_timings.captions,
        youtube_token_file=settings.mantra_sangam_youtube_token_file,
        blogger_blog_id=settings.mantra_sangam_blogger_blog_id,
        playlist_id=None,
        playlist_title=PLAYLIST_TITLE,
        playlist_description=PLAYLIST_DESC,
    )
    return run(pipeline)


if __name__ == "__main__":
    sys.exit(main())
