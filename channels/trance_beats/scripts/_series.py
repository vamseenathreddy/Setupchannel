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
_TAIL_HI = " रोज़ नए शॉर्ट्स के लिए चैनल को सब्सक्राइब करें।"
PLAYLISTS = {
    "gita": ("भगवद्गीता श्लोक | Bhagavad Gita Daily Shloka (Hindi)",
             "श्रीमद्भगवद्गीता के चुने हुए श्लोक, सरल हिंदी अर्थ के साथ। कर्मयोग, भक्ति, ज्ञान और शांति की सीख, हर दिन एक शॉर्ट में।"
             + _TAIL_HI + "\n\nBhagavad Gita shlokas with simple Hindi meaning, one short every day. Karma yoga, bhakti, "
             "knowledge and peace from the words of Shri Krishna. Subscribe to Devotional Trance Beats for a new Gita shloka daily.\n\n"
             "#BhagavadGita #GitaShloka #GeetaSaar #Krishna #HindiDevotional"),
    "bhagavatam": ("श्रीमद्भागवत कथा | Shrimad Bhagavatam Daily Stories (Hindi)",
                   "श्रीमद्भागवत महापुराण की कथाएँ सरल हिंदी में: प्रह्लाद, ध्रुव, गजेंद्र, कृष्ण लीला और भक्ति की सीख, हर दिन एक शॉर्ट में।"
                   + _TAIL_HI + "\n\nStories from the Shrimad Bhagavatam in simple Hindi: Prahlad, Dhruva, Gajendra, Krishna leela "
                   "and lessons of bhakti, one short every day. Subscribe to Devotional Trance Beats for a new Bhagavatam story daily.\n\n"
                   "#ShrimadBhagavatam #BhagavatKatha #KrishnaKatha #Krishna #HindiDevotional"),
    "mantra": ("कृष्ण मंत्र और भजन | Krishna Mantra and Bhajan of the Day",
               "हरे कृष्ण महामंत्र, कृष्ण मंत्र, भजन और कीर्तन, शांत संगीत के साथ। सुनें, जपें और मन को शांति दें।"
               + _TAIL_HI + "\n\nHare Krishna maha mantra, Krishna mantras, bhajans and kirtans with calm devotional music. "
               "Listen, chant along and find peace. Subscribe to Devotional Trance Beats for a new mantra or bhajan daily.\n\n"
               "#KrishnaMantra #HareKrishna #KrishnaBhajan #Krishna #HindiDevotional"),
}
SERIES = {
    "gita": ("trance_beats", "gita.csv", channel_config.ROTATION_GITA, "MAHANAVI_TRANCE_BEATS_PLAYLIST_ID"),
    "bhagavatam": ("trance_bhagavatam", "bhagavatam.csv", channel_config.ROTATION_BHAGAVATAM, "MAHANAVI_TRANCE_BHAGAVATAM_PLAYLIST_ID"),
    "mantra": ("trance_mantra", "mantra.csv", channel_config.ROTATION_MANTRA, "MAHANAVI_TRANCE_MANTRA_PLAYLIST_ID"),
}


def main(series: str):
    from mahanavi.config import get_settings

    key, csv_name, rotation, _ = SERIES[series]
    settings = get_settings()
    # Playlists are found (or created) by title on the channel, so no playlist secret is needed and
    # an old mixed playlist can never receive these series.
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
        playlist_id=None,
        playlist_title=PLAYLISTS[series][0],
        playlist_description=PLAYLISTS[series][1],
    )
    return run(pipeline)
