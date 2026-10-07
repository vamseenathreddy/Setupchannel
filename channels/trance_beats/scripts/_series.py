"""Shared builder for the three daily Krishna series on Devotional Trance Beats.

gita        -> key trance_beats        (data/gita.csv)        evening
bhagavatam  -> key trance_bhagavatam   (data/bhagavatam.csv)  morning
mantra      -> key trance_mantra       (data/mantra.csv)      midday
"""
import dataclasses
import os
from pathlib import Path

from channels.engine.post import ChannelPipeline, run
from channels.trance_beats import channel_config, metadata

DATA = Path(__file__).resolve().parents[1] / "data"
SERIES = {
    "gita": ("trance_beats", "gita.csv", channel_config.ROTATION_GITA, "MAHANAVI_TRANCE_BEATS_PLAYLIST_ID"),
    "bhagavatam": ("trance_bhagavatam", "bhagavatam.csv", channel_config.ROTATION_BHAGAVATAM, "MAHANAVI_TRANCE_BHAGAVATAM_PLAYLIST_ID"),
    "mantra": ("trance_mantra", "mantra.csv", channel_config.ROTATION_MANTRA, "MAHANAVI_TRANCE_MANTRA_PLAYLIST_ID"),
}


def main(series: str):
    from mahanavi.config import get_settings

    key, csv_name, rotation, playlist_env = SERIES[series]
    settings = get_settings()
    playlist = os.environ.get(playlist_env) or None
    if series == "gita":
        playlist = playlist or settings.trance_beats_playlist_id
    pipeline = ChannelPipeline(
        channel_key=key,
        expected_channel="Trance",
        content_csv=DATA / csv_name,
        special_csv=None,
        render_cfg=dataclasses.replace(channel_config.RENDER_CFG, cta_text=channel_config.CTA[series]),
        rotation=rotation,
        metadata_bundle=metadata.bundle,
        metadata_captions=metadata.captions,
        youtube_token_file=settings.trance_beats_youtube_token_file,
        blogger_blog_id=settings.trance_beats_blogger_blog_id,
        playlist_id=playlist,
    )
    return run(pipeline)
