"""
post_panini_video.py: assembles and uploads episode 3 of the long-form
Puranam scrolling-text video series -- sage Panini's story (how the
Maheshwara Sutras were revealed by Shiva's damaru), from Sri Bhavishya
Puranam.

FIRST EPISODE WITH REAL VOICEOVER: unlike episodes 1-2, which used a
words-per-minute ESTIMATE to set the video's duration, this episode
generates real Telugu narration via Sarvam AI, mixes it with ducked
background music, and uses the ACTUAL SPOKEN LENGTH of that narration
to drive both the video duration and the scroll speed -- text and
voice now genuinely stay in sync, rather than approximately matching.

Content notes:
- No Sanskrit shlokas at all in this passage (unlike episodes 1-2),
  which made it a deliberately lower-risk choice for the first
  voiceover episode: plain Telugu narrative is far more reliable for
  TTS pronunciation than Sanskrit shloka meter.
- No stated phalasruti in this passage either, so the SEO title leads
  with the story's own significance.
- One transcription note: the source book prints the first revealed
  sutra as "ఇఉణ్", not the more widely documented Sanskrit tradition
  form "అఇఉణ్" (with an initial అ) -- transcribed exactly as printed,
  since the goal is accurately representing this specific source, not
  correcting it against outside tradition.

Usage:
    python -m ytcore.scripts.post_panini_video
    python -m ytcore.scripts.post_panini_video --public   # only once you're ready
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
from ytcore.content.purana_video_seo import build_panini_charitra_video_seo
from ytcore.database.db import DatabaseManager
from ytcore.database.repositories import ImageHistoryRepository
from ytcore.exceptions import AppError
from ytcore.images.purana_text_renderer import PuranaTextRenderer, TextSegment
from ytcore.images.selector import RandomImageSelector
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from ytcore.video.scroll_assembler import assemble_scroll_video

BACKGROUND_FOLDERS = ["Monday_Shiva", "Wednesday_Ganesha", "Saturday_Venkateswara"]

# The full Panini story, exactly as transcribed and verified against
# the source pages (1185-1186) -- no shlokas, no TextSegment emphasis
# needed since this passage is pure narrative prose. The final entry
# is the next-episode teaser, part of the video content itself.
PANINI_PARAGRAPHS: list[str | TextSegment] = [
    "పాణిని చరిత్ర",
    "పితృశర్మ మనమడు పాణిని. ఈయన సాముడి కుమారుడు. ఒకనాడు పాణిని కణాదుడి శిష్యులతో శాస్త్రవాదం చేసాడు. ఆ వాదంలో పాణిని వారి చేతిలో పరాజయం పొందాడు. దానితో అతడికి ఆ ఊరిలో ఉండటానికి అవమానం అనిపించింది. వెంటనే తీర్థయాత్ర చేయాలనే నెపంతో ఊరువిడిచి బయలుదేరాడు. దారిలో అన్ని తీర్థాలూ, క్షేత్రాలు దర్శిస్తూ చివరికి కేదారధామానికి చేరుకున్నాడు.",
    "కేదారభూమి పాణినికి నచ్చింది. అక్కడే స్థిరంగా ఏకాగ్రచిత్తంతో పరమేశ్వరుడి గురించి కఠోరమైన తపస్సు చేయటం ప్రారంభించాడు. ఆకలి అనిపిస్తే కేవలం ఆకుల్ని తింటూ కొంతకాలం, కేవలం నీళ్ళని తీసుకుంటూ కొంతకాలం, నీరుకూడా స్వీకరించకుండా మరికొంత కాలం సాధన చేసాడు. అలా ఇరవైఎనిమిది రోజులు గడిచిపోయాయి. చివరిరోజు పరమేశ్వరుడు సాక్షాత్కరించాడు. వరం కోరుకోమన్నాడు.",
    "శివుడి మాట వినగానే పాణిని శరీరం ఒక్కసారిగా ఆనందంతో జలదరించింది. కళ్ళు తెరిచాడు. ఎదురుగా పార్వతీపతి. ఆయన్ని చూసేసరికి ఆనందం పెల్లుబికింది పాణినిలో. ఆ తన్మయత్వంలో పరిపరివిధాలుగా పరమేశ్వరుణ్ణి స్తుతించాడు. \"పరమేశ్వరా! నాకు ఆదివిద్యని, అక్షరమాలని, వ్యాకరణశాస్త్రాన్ని రచించే శక్తిని ప్రసాదించండి\" అని కోరాడు. దయాసముద్రుడైన పరమేశ్వరుడు తన ఢమరుక నాదం ద్వారా అక్షరాల్ని వినిపించి వాటిని \"ఇఉణ్\" అనే సూత్రాల రూపంలో పాణినికి అందించాడు. అవే మాహేశ్వర సూత్రాలు. వీటి ద్వారానే పాణిని మహర్షి అష్టాధ్యాయి అనే మహావ్యాకరణ గ్రంథాన్ని రచించాడు. వరాన్నిచ్చిన తరువాత పరమేశ్వరుడు పాణినితో \"నాయనా! మానవుడు జ్ఞానం అనే సరోవరంలోకి దిగితే రాగం, ద్వేషం అనే మలినాలు తొలగిపోతాయి. ఈ మానస తీర్థం గురించి అవగాహన చేసుకున్నవాడే అన్ని తీర్థాల స్నానాలను, విద్యావిధానాలను అర్థంచేసుకోగలడు. విద్య ఉన్నవాడికి బ్రహ్మ సాక్షాత్కారం పొందే శక్తి లభిస్తుంది. కనుక నీకు మానసజ్ఞానం అనే ఉత్తమమైన తీర్థాన్ని ప్రసాదిస్తున్నాను\" అని వరాన్నిచ్చి అదృశ్యమయ్యాడు శివుడు.",
    "ఆవిధంగా పరమేశ్వరుడి అనుగ్రహాన్ని పొందిన పాణిని ఆనందంగా ఇంటికి చేరుకున్నాడు. వెంటనే సంస్కృత భాషకి పరమప్రామాణికమైన మహాగ్రంథాన్ని అష్టాధ్యాయి అనే పేరుతో రచించాడు. తరువాత ఆ గ్రంథానికి పతంజలి మహాభాష్యాన్ని రచించగా వరరుచి వార్తికాలని రచించాడు.",
    "మా తదుపరి వీడియోలో నారద పురాణం నుండి ఒక పవిత్రమైన కథను తెలుసుకుందాం. మా ఛానల్‌ను సబ్‌స్క్రైబ్ చేయండి - ప్రతిరోజు పురాణ కథల కోసం.",
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
            PANINI_PARAGRAPHS, settings.output_dir / f"{today.isoformat()}_panini_voiceover.wav", settings,
        )
        print(f"Voiceover generated: {voiceover_path}")

        print("Mixing voiceover with background music...")
        mixed_audio_path = mix_voiceover_with_music(
            voiceover_path=voiceover_path,
            music_path=settings.alert_short_music_path,
            output_path=settings.output_dir / f"{today.isoformat()}_panini_audio.mp3",
        )
        duration = get_audio_duration_seconds(mixed_audio_path)
        print(f"Final audio duration (drives video length): {duration:.1f}s ({duration / 60:.2f} min)")

        print("Rendering scrolling text image...")
        text_renderer = PuranaTextRenderer(settings)
        text_image_path, text_image_height = text_renderer.render(
            PANINI_PARAGRAPHS, settings.output_dir / f"{today.isoformat()}_panini_text.png",
        )
        print(f"Rendered: {text_image_path} (height {text_image_height}px)")

        print("Selecting background image...")
        background_path = _select_background(settings, today)
        print(f"Background: {background_path}")

        video_path = settings.output_dir / f"{today.isoformat()}_panini_video.mp4"
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

        seo = build_panini_charitra_video_seo()
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
