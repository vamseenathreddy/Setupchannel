"""
post_kamakhya_short.py: assembles and uploads a vertical Shorts-format
scrolling-text video telling the Kamakhya Devi origin story, from a
fixed background image (Images/Kamakhya/kamakhya_devi_temple.png).

WHY A SEPARATE SCRIPT FROM post_purana_video.py: that script's pipeline
(images/purana_text_renderer.py + video/scroll_assembler.py) was built
landscape-only (1920x1080) by explicit design decision, for the 8+
minute long-form Puranam videos meant to carry mid-roll ads. This
episode is a vertical (9:16) Short instead, matching the channel's
proven-top-performing alert-Short format (see ALERT_CARD_WIDTH/HEIGHT
in images/alert_card_renderer.py, 1080x1920 -- reused here for visual
consistency with the rest of the channel's Shorts). Both
PuranaTextRenderer.render() and assemble_scroll_video() were
generalized to accept width/height parameters for this, defaulting to
the original landscape constants so the existing long-form scripts
(post_purana_video.py, post_kurma_purana_video.py) are unaffected.

SOURCING NOTE: unlike the 18-Purana rotation, this story's source is
the Kalika Purana, a Shakta Upapurana -- NOT one of the 18 Mahapuranas
this channel's source PDF (Astadasa_Puranalu.pdf) covers. See
content/purana_video_seo.py's build_kamakhya_video_seo() docstring for
the research that confirmed this. Framed honestly in the video's own
on-screen text and description rather than folded into the Ashtadasa
Purana numbering -- a devotional channel's credibility depends on this
kind of accuracy holding up under a knowledgeable viewer's scrutiny.

SAFETY: uploads as "unlisted" by default, exactly like
post_alert_shorts.py and post_purana_video.py -- review it yourself
before passing --public.

Usage:
    python -m mahanavi.scripts.post_kamakhya_short
    python -m mahanavi.scripts.post_kamakhya_short --public   # only once you're ready
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from mahanavi.config import get_settings
from mahanavi.content.purana_video_seo import build_kamakhya_video_seo
from mahanavi.exceptions import MahanaviError
from mahanavi.images.purana_text_renderer import PuranaTextRenderer, TextSegment
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from mahanavi.video.scroll_assembler import assemble_scroll_video

# Vertical Shorts canvas -- matches the channel's existing alert-Short
# format (images/alert_card_renderer.py's ALERT_CARD_WIDTH/HEIGHT)
# rather than the long-form scroll pipeline's landscape default.
SHORT_VIDEO_WIDTH = 1080
SHORT_VIDEO_HEIGHT = 1920

# Narrower than the long-form TEXT_COLUMN_WIDTH (1400), with margin on
# both sides so wrapped Telugu lines never touch the vertical frame's
# edges at 1080px wide.
SHORT_TEXT_COLUMN_WIDTH = 900

# Same reading pace as the long-form Puranam videos (post_purana_video.py)
# for consistency -- this passage is short by design, so duration comes
# out to roughly 55-65 seconds, a proper Short.
WORDS_PER_MINUTE = 100

BACKGROUND_IMAGE_RELATIVE_PATH = "Kamakhya/kamakhya_devi_temple.png"

# The Kamakhya Devi origin passage -- Sati/yoni legend at Kamarupa, one
# of the four oldest of the 51 Shakti Peethas, sourced from the Kalika
# Purana and explicitly NOT presented as one of the 18 Mahapuranas (see
# module docstring's SOURCING NOTE).
KAMAKHYA_PARAGRAPHS: list[str | TextSegment] = [
    "కామాఖ్య దేవి ఆవిర్భావం",
    "దక్ష మహారాజు చేసిన యజ్ఞంలో జరిగిన అవమానాన్ని భరించలేక సతీదేవి తన దేహాన్ని యోగాగ్నిలో త్యజించింది. "
    "కుమార్తె వియోగాన్ని తట్టుకోలేని పరమశివుడు ఆమె పార్థివ దేహాన్ని భుజాన మోస్తూ సంహార తాండవం చేయసాగాడు. "
    "సృష్టి విఘాతం కలగకుండా శ్రీమహావిష్ణువు తన సుదర్శన చక్రంతో సతీదేవి దేహాన్ని ఛేదించగా, ఆ దేహభాగాలు "
    "భూమిపై యాభైఒక్క పుణ్యస్థలాలలో పడ్డాయి -- ఇవే శక్తి పీఠాలుగా ప్రసిద్ధి చెందాయి.",
    "అస్సాంలోని కామరూప ప్రాంతంలో పడిన సతీదేవి గర్భస్థానమే నేటి కామాఖ్యా పీఠం. సృష్టికి మూలమైన స్త్రీశక్తికి "
    "ప్రతీకగా ఇక్కడ దేవిని విగ్రహరూపంలో కాక, ప్రకృతి సిద్ధమైన యోనిఆకార శిలగా, నిరంతరం స్రవించే జలధారతో "
    "పూజిస్తారు. యాభైఒక్క శక్తి పీఠాలలో అత్యంత ప్రాచీనమైన నాలుగింటిలో కామాఖ్యా పీఠం ఒకటిగా చెప్పబడుతుంది.",
    "సృష్టి, కామన, సంతానం వంటి కోరికలు తీరాలని కోరుకునే భక్తులు ఈ పీఠాన్ని దర్శించి దేవిని ఆరాధిస్తారు. "
    "ఈ గాథ కాళికా పురాణంలో వివరించబడింది -- ఇది అష్టాదశ మహాపురాణాలలో ఒకటి కాదు, ప్రత్యేకమైన శక్తి "
    "ఉపపురాణం, శాక్తేయ సంప్రదాయానికి ప్రధాన ఆధారగ్రంథం.",
    TextSegment(text="ఓం కామాఖ్యాయై నమః", emphasized=True),
    "మా ఛానల్‌లో ప్రతిరోజు ఇలాంటి పురాణ, శక్తి పీఠ గాథలు చూడండి. సబ్‌స్క్రైబ్ చేయండి.",
]


def _compute_duration(paragraphs: list[str | TextSegment]) -> float:
    """Same approach as post_purana_video.py's _compute_duration --
    driven purely by content length, no artificial padding."""
    total_words = sum(len((p.text if isinstance(p, TextSegment) else p).split()) for p in paragraphs)
    return (total_words / WORDS_PER_MINUTE) * 60.0


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

    background_path = settings.images_root / BACKGROUND_IMAGE_RELATIVE_PATH
    if not background_path.exists():
        print(f"FAILED: background image not found at {background_path}", file=sys.stderr)
        return 1

    try:
        print("Rendering scrolling text image (vertical Shorts canvas)...")
        text_renderer = PuranaTextRenderer(settings)
        text_image_path, text_image_height = text_renderer.render(
            KAMAKHYA_PARAGRAPHS,
            settings.output_dir / f"{today.isoformat()}_kamakhya_text.png",
            text_column_width=SHORT_TEXT_COLUMN_WIDTH,
        )
        print(f"Rendered: {text_image_path} (height {text_image_height}px)")

        duration = _compute_duration(KAMAKHYA_PARAGRAPHS)
        print(f"Target duration: {duration:.1f}s ({duration / 60:.2f} min)")

        video_path = settings.output_dir / f"{today.isoformat()}_kamakhya_video.mp4"
        print("Assembling vertical scroll video...")
        assemble_scroll_video(
            background_image_path=background_path,
            text_image_path=text_image_path,
            text_image_height=text_image_height,
            output_path=video_path,
            duration_seconds=duration,
            audio_path=settings.alert_short_music_path,
            audio_volume=0.5,
            video_width=SHORT_VIDEO_WIDTH,
            video_height=SHORT_VIDEO_HEIGHT,
        )
        print(f"Assembled: {video_path}")

        seo = build_kamakhya_video_seo()
        uploader = YouTubeShortsUploader(settings)
        result = uploader.upload(video_path, seo, privacy_status=privacy_status)

        if result.success:
            print(f"Uploaded ({privacy_status}): {result.post_url}")
            return 0
        print(f"Upload FAILED: {result.error_message}", file=sys.stderr)
        return 1

    except MahanaviError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
