"""
post_samudrika_video.py: assembles and uploads a long-form video on
Samudrika Shastra (the traditional Indian science of reading a
person's nature through physical signs) -- attributed to sage Samudra
and referenced across Puranic literature including Sri Bhavishya
Puranam.

DELIBERATELY THE PLAIN SCROLLING-TEXT PIPELINE (per explicit request:
"this samudrika video we will upload as simple text for now, later we
will select best script to visualise best video") -- no fal.ai scene
generation, no per-scene cost, same as episodes 1-3 before the
heavy-tier AI visual pipeline was added. Uses the same rotating
background-image + scrolling-text + real Telugu voiceover flow as
post_panini_video.py (episode 3), NOT the AI-animated flow in
post_purana_video.py (episode 1, since it was upgraded).

CONTENT NOTE -- written to avoid controversy, per explicit request
("it should not make contreversal"): I could not locate any verbatim
Bhavishya Puranam shloka text for Samudrika Shastra anywhere in this
project's history to transcribe (the earlier chat history that
supposedly held it is no longer retrievable, and no source PDF page
was ever supplied/verified for this topic, unlike episodes 1-3 which
were each checked against specific source pages). Rather than invent
verses and falsely attribute them to scripture, this script presents
a general, honest, non-gendered overview of the tradition itself
(forehead, eyes, palm lines, fingers) framed explicitly as traditional
belief rather than definitive prediction -- deliberately leaving out
the specific claims most associated with controversy in this
tradition (gendered mole/body readings, marriage/wealth fortune-
telling, caste-linked claims). If a real verified source passage is
found or supplied later, replace SAMUDRIKA_PARAGRAPHS with the actual
text and update the SEO summary in content/purana_video_seo.py to
match, the same way episodes 1-3 quote their real source pages.

Usage:
    python -m ytcore.scripts.post_samudrika_video
    python -m ytcore.scripts.post_samudrika_video --public   # only once you're ready
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ytcore.audio.mixer import get_audio_duration_seconds, mix_voiceover_with_music
from ytcore.audio.telugu_voiceover import generate_voiceover
from ytcore.config import Settings, get_settings
from ytcore.content.purana_video_seo import build_samudrika_shastra_video_seo
from ytcore.database.db import DatabaseManager
from ytcore.database.repositories import ImageHistoryRepository
from ytcore.exceptions import AppError
from ytcore.images.purana_text_renderer import PuranaTextRenderer, TextSegment
from ytcore.images.selector import RandomImageSelector
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from ytcore.video.scroll_assembler import assemble_scroll_video

BACKGROUND_FOLDERS = ["Monday_Shiva", "Wednesday_Ganesha", "Saturday_Venkateswara"]

# General, non-gendered, non-fortune-telling overview of the tradition
# -- see the CONTENT NOTE above for why this is written this way
# instead of quoting specific scripture verses.
SAMUDRIKA_PARAGRAPHS: list[str | TextSegment] = [
    "సాముద్రిక శాస్త్రం",
    (
        "సాముద్రిక శాస్త్రం అనేది మానవ శరీర లక్షణాలను పరిశీలించి, వ్యక్తి స్వభావాన్ని, గుణగణాలను "
        "అర్థం చేసుకునే ఒక ప్రాచీన భారతీయ సంప్రదాయ విద్య. ఇది సముద్రుడు అనే మహర్షి ప్రవచించినదిగా "
        "చెప్పబడుతుంది, అందుకే దీనికి 'సాముద్రికం' అనే పేరు వచ్చింది. శ్రీ భవిష్య పురాణం వంటి "
        "పురాణాలలో శరీర లక్షణాల ప్రాధాన్యత గురించి ప్రస్తావించబడింది. మన పెద్దలు శరీర ఆకారం, "
        "ముఖకవళికలు, హస్తరేఖలు వంటి అంశాల ద్వారా వ్యక్తి స్వభావాన్ని అంచనా వేసేవారు."
    ),
    (
        "నుదురు విశాలంగా, నిగనిగలాడుతూ ఉంటే అది బుద్ధి కుశలత, నాయకత్వ లక్షణాలకు సూచనగా "
        "భావించేవారు. కళ్ళు స్థిరంగా, ప్రశాంతంగా ఉంటే మనఃస్థిరత్వానికి, స్పష్టమైన ఆలోచనలకు సూచనగా "
        "చెప్పేవారు. చిరునవ్వుతో కూడిన ముఖం సాత్విక స్వభావానికి, మంచి మనస్తత్వానికి సంకేతంగా "
        "భావించబడేది."
    ),
    (
        "హస్తరేఖా శాస్త్రం సాముద్రిక శాస్త్రంలో ఒక ముఖ్యమైన భాగం. అరచేతిలో ఉండే జీవరేఖ, మస్తకరేఖ, "
        "హృదయరేఖ అనే మూడు ముఖ్యమైన రేఖలను పరిశీలించి, ఆరోగ్యం, బుద్ధి, భావోద్వేగాల గురించి అంచనా "
        "వేసేవారు. వేళ్ళు నిడుపుగా, నిష్పత్తిగా ఉంటే కళాత్మక, సునిశిత బుద్ధికి సూచనగా చెప్పబడేది."
    ),
    (
        "సాముద్రిక శాస్త్రం అనేది మన సంస్కృతిలో వేల ఏండ్లుగా వస్తున్న ఒక సంప్రదాయ విద్య. ఇది "
        "వ్యక్తుల గురించి ఖచ్చితమైన నిర్ణయాలు తీసుకోడానికి కాదు, మన పూర్వీకుల పరిశీలనా నైపుణ్యాన్ని, "
        "జీవితం పట్ల వారి దృష్టికోణాన్ని అర్థం చేసుకోడానికి ఉపయోగపడుతుంది. ఏ శాస్త్రమైనా గౌరవంతో, "
        "విమర్శనాత్మక దృష్టితో అర్థం చేసుకోవడమే మంచిది."
    ),
    "మా తదుపరి వీడియోలో ఇంకో ఆసక్తికరమైన అంశాన్ని తెలుసుకుందాం. మా ఛానల్‌ను సబ్‌స్క్రైబ్ చేయండి - ప్రతిరోజు భక్తి, సంప్రదాయ విషయాల కోసం.",
]


def _select_background(settings: Settings, for_date: date) -> Path:
    db = DatabaseManager(settings.database_path)
    history_repo = ImageHistoryRepository(db)
    selector = RandomImageSelector(settings, history_repo)
    folder_name = BACKGROUND_FOLDERS[for_date.toordinal() % len(BACKGROUND_FOLDERS)]
    selected = selector.select_from_folder(folder_name, for_date)
    return selected.path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public", action="store_true",
        help="Upload as public instead of unlisted. Omit this until you've reviewed the result yourself.",
    )
    args = parser.parse_args()

    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).date()
    privacy_status = "public" if args.public else "unlisted"
    if not args.public:
        print("Uploading as UNLISTED (default). Pass --public once you're happy with the result.")

    try:
        print("Generating Telugu voiceover narration...")
        voiceover_path = generate_voiceover(
            SAMUDRIKA_PARAGRAPHS, settings.output_dir / f"{today.isoformat()}_samudrika_voiceover.wav", settings,
        )
        print(f"Voiceover generated: {voiceover_path}")

        print("Mixing voiceover with background music...")
        mixed_audio_path = mix_voiceover_with_music(
            voiceover_path=voiceover_path,
            music_path=settings.alert_short_music_path,
            output_path=settings.output_dir / f"{today.isoformat()}_samudrika_audio.mp3",
        )
        duration = get_audio_duration_seconds(mixed_audio_path)
        print(f"Final audio duration (drives video length): {duration:.1f}s ({duration / 60:.2f} min)")

        print("Rendering scrolling text image...")
        text_renderer = PuranaTextRenderer(settings)
        text_image_path, text_image_height = text_renderer.render(
            SAMUDRIKA_PARAGRAPHS, settings.output_dir / f"{today.isoformat()}_samudrika_text.png",
        )
        print(f"Rendered: {text_image_path} (height {text_image_height}px)")

        print("Selecting background image...")
        background_path = _select_background(settings, today)
        print(f"Background: {background_path}")

        video_path = settings.output_dir / f"{today.isoformat()}_samudrika_video.mp4"
        print("Assembling scroll video...")
        assemble_scroll_video(
            background_image_path=background_path,
            text_image_path=text_image_path,
            text_image_height=text_image_height,
            output_path=video_path,
            duration_seconds=duration,
            audio_path=mixed_audio_path,
            audio_volume=1.0,  # already mixed/ducked -- no further adjustment needed
        )
        print(f"Assembled: {video_path}")

        seo = build_samudrika_shastra_video_seo()
        uploader = YouTubeShortsUploader(settings)
        result = uploader.upload(video_path, seo, privacy_status=privacy_status)

        if result.success:
            print(f"Uploaded ({privacy_status}): {result.post_url}")
            return 0
        print(f"Upload FAILED: {result.error_message}", file=sys.stderr)
        return 1

    except AppError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
