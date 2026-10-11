"""
post_purana_video.py: assembles and uploads the long-form Puranam
scrolling-text video -- currently a single fixed episode (Manasadevi's
story from Sri Brahmavaivarta Puranam), since finding and verifying a
passage in this source PDF requires manual reading (see
content/purana_selector.py's docstring for why) rather than a fully
automated daily pick like the Panchang-based scripts.

Flow: build the full paragraph list (story + mantra + stotrams + a
next-episode teaser) -> render as one tall Telugu text image
(images/purana_text_renderer.py) -> pick today's background deity image
from a 3-way Vishnu/Shiva/Ganesha rotation (images/selector.py) ->
assemble the scrolling video with your music at 50% volume
(video/scroll_assembler.py) -> upload via the YouTube Data API.

SAFETY: uploads as "unlisted" by default, exactly like
post_alert_shorts.py -- review it yourself before passing --public.

Usage:
    python -m ytcore.scripts.post_purana_video
    python -m ytcore.scripts.post_purana_video --public   # only once you're ready
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ytcore.config import Settings, get_settings
from ytcore.content.purana_video_seo import build_manasadevi_video_seo
from ytcore.database.db import DatabaseManager
from ytcore.database.repositories import ImageHistoryRepository
from ytcore.exceptions import AppError
from ytcore.images.purana_text_renderer import PuranaTextRenderer, TextSegment
from ytcore.images.selector import RandomImageSelector
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from ytcore.video.scroll_assembler import assemble_scroll_video

# Rotates among these three specific deities for the background, per
# explicit request -- NOT the full 7-day weekday rotation used by the
# Community Post/Shorts (this cycles by episode count, not day-of-week).
BACKGROUND_FOLDERS = ["Monday_Shiva", "Wednesday_Ganesha", "Saturday_Venkateswara"]

# Comfortable, slightly slow reading pace for scrolling text meant to be
# read AND absorbed, not skimmed -- see the reading-pace discussion that
# led to this number. Sacred verses (the stotrams) traditionally get
# read even slower than this in practice, but one flat pace across the
# whole passage keeps the scroll speed visually consistent rather than
# jarringly changing partway through.
WORDS_PER_MINUTE = 100

# The full Manasadevi passage, exactly as transcribed and corrected --
# each entry is one paragraph in the scrolling text, in order. The
# final entry is the next-episode teaser, per explicit request that
# this closing line be part of the video content itself, not just the
# description metadata.
MANASADEVI_PARAGRAPHS: list[str | TextSegment] = [
    "మనసాదేవి వృత్తాంతం",
    "పూర్వం భూలోకంలో మానవులంతా సర్పాలచేత బాధలు పడుతుండేవారు. సర్పాలు మానవుల్ని కాటువేసి వారి మరణానికి కారకులయ్యేవి. అలా ఎంతోమంది సర్పాల వల్ల మరణించారు. వారిలో దివ్యశక్తి కలిగిన కొంతమంది మహర్షులు బ్రహ్మ దగ్గరకి వెళ్ళి సర్పాల బారి నుంచి మానవుల్ని రక్షించమని ప్రార్థించారు. అప్పుడాయన కశ్యపమహర్షిని పిలిచి మానవులుపడుతున్న బాధల్ని వివరించాడు. వెంటనే కశ్యపప్రజాపతి తన దివ్యశక్తితో నాగులకి నాగమంత్రాలకి అధిష్టాన దేవత అయిన మనసాదేవిని సృష్టించాడు.",
    "కశ్యపుడి మనస్సు నుంచి పుట్టింది కాబట్టి ఆమె మనసాదేవి అని విఖ్యాతి చెందింది. ఆమె జన్మించగానే కైలాస పర్వతానికి వెళ్ళి వంద సంవత్సరాలు మహాదేవుణ్ణి పూజించింది. ఆమె పూజకి సంతోషించిన పరమేశ్వరుడు మనసాదేవికి సామవేదాన్ని నేర్పి, దివ్యమైన శ్రీకృష్ణ అష్టాక్షర మంత్రాన్ని ఉపదేశించాడు.",
    "శ్రీం హ్రీం క్లీం కృష్ణాయనమః అనేది అష్టాక్షర మంత్రం. ఈ మంత్రంతో పాటు శ్రీకృష్ణ కవచాన్ని పూజావిధానాన్ని, ఆయన దివ్యస్తోత్రాన్ని కూడా ఉపదేశించి, అందరికీ అలభ్యమైన మృతసంజీవని విద్యనికూడా ఆమెకి ప్రసాదించాడు.",
    "శంకరుడి ద్వారా ఉపదేశం పొందిన శ్రీకృష్ణుడి మంత్రాన్ని, పుష్కరక్షేత్రానికి వెళ్ళి అక్కడ మూడు యుగాలు తపస్సు చేసింది మనసాదేవి. ఆమె చేసిన ఘోరమైన తపస్సుకి మెచ్చిన శ్రీకృష్ణుడు ప్రత్యక్షమై రాబోయేకాలంలో భూలోకంలో అందరిచేత పూజించబడతావు అని వరాన్నిచ్చాడు.",
    "ఆవిధంగా గొప్పతపశక్తితో వరాలు పొందిన మనసాదేవిని ఆమెతండ్రి కశ్యపుడు జరత్కారుమహర్షికిచ్చి వివాహం చేసాడు. వారిద్దరూ హాయిగా సంసారం చేస్తూ కాలం గడపసాగారు. ఒకనాడు జరత్కారుడు మనసాదేవి ఒడి తలపెట్టుకుని హాయిగా ఆదమరిచి నిద్రపోతున్నాడు. సాయంత్రమయ్యింది.",
    "ఆయన సంధ్యావిధి ఆచరించాల్సిన సమయం మించిపోతోంది. ఈవిషయాన్ని గ్రహించి మనసాదేవి, ధర్మలోపంజరగకూడదని భావించి, వెంటనే తన భర్తని నిద్రలేపింది. హఠాత్తుగా తనని నిద్రాభంగం కలిగించటంతో జరత్కారుమహర్షికి ఆగ్రహం కలిగి ఆమెని నిందించి, నువ్వు ఇప్పుడే వెళ్ళిపో, లేదా నేనే ఇక్కణ్ణించి వెళ్ళిపోయి తపస్సు చేసుకుంటాను అని కఠినంగా పలికాడు.",
    "భర్త మాటలువిన్న మనసాదేవి ఎంతోదుఃఖిస్తూ ప్రభూ! తమకు ధర్మలోపం కలగకూడదనే నేను తమర్ని నిద్రలేపాను. కావాలని మీకు నిద్రాభంగం చేయలేదు, దయచేసి నన్ను క్షమించండి అని ప్రాధేయపడింది. అయినా ఆ మహర్షి శాంతించలేదు. అప్పుడు మనసాదేవి భయంతో తన గురువైన శంకరాష్టిని, తండ్రి కశ్యపుణ్ణి, బ్రహ్మ విష్ణువుల్ని స్మరించింది. వెంటనే వారంతా అక్కడ ప్రత్యక్షమయ్యారు. వారంతా నచ్చచెప్పినా జరత్కారు వినలేదు. తాను ఆడిన మాట తప్పనన్నాడు. ఇకచేసేదిలేక బ్రహ్మదేవుడు ఆయనతో మహర్షీ! నీవు తపస్సుకు వెళ్ళేముందు నీభార్యకి ఒక కుమారుణ్ణి ప్రసాదించి వెళ్ళు! అది ధర్మం అని తెలియచెప్పాడు.",
    "అందుకంగీకరించిన జరత్కారుడు మనసాదేవి నాభిమీద చేయివేశాడు. ఆయన తపశక్తితో మనసాదేవి వెంటనే గర్భాన్ని ధరించింది. జరత్కారుడు ఆమెతో మనసా! నేను నిన్ను విడిచి వెళ్ళటం అనేది విధి నిర్ణయం — నీకు పుట్టబోయే బిడ్డ మహావిష్ణుభక్తుడై, గొప్ప తపస్విగా పేరు పొందుతాడు. వంశాన్ని ఉద్ధరిస్తాడు అని ఆమెతో ప్రేమగా చెప్పాడు.",
    "మనసాదేవి భర్తమాటలు విని జరిగిందంతా కర్మప్రారబ్ధమని గ్రహించి బాధను దిగమింగుకుంది. వెళ్ళిపోబోతున్న భర్తతో స్వామీ! తమరు నేను ఎప్పుడు తలుచుకుంటే అప్పుడు రావాలి. ఈ కోరికని మన్నించండి అని ప్రార్థించింది. జరత్కారువు అలాగే తప్పక వస్తానని మాట ఇచ్చి శ్రీకృష్ణ పరమాత్మను గురించి తపస్సుచేసుకోవటానికి వెళ్ళిపోయాడు.",
    "కొంతకాలానికి మనసాదేవి నారాయణాంశ సంభూతుడైన ఒక పుత్రుణ్ణి కన్నది. అతడికి ఆస్తీకుడు అన్నపేరు పెట్టింది. పరమేశ్వరుడు స్వయంగా ఆ పిల్లవాడికి అక్షరాభ్యాసంచేసి వేదాలు శాస్త్రాలు బోధించాడు. మృత్యువుని జయించే తత్వజ్ఞానాన్ని ఉపదేశించాడు. ఆస్తీకుడు శివుడి బోధలతో మహాజ్ఞానిగా మారిపోయాడు. శంకరుడి ఆజ్ఞతో ఆస్తీకుడు పుష్కర క్షేత్రానికి వెళ్ళి లక్షదివ్య సంవత్సరాలు శ్రీమహావిష్ణువు గురించి తపస్సుచేసాడు.",
    "ఇలా సకల శాస్త్రాలూ అభ్యసించి మహాతపస్విగా ఎన్నో సిద్ధశక్తులు సంపాదించిన ఆస్తీకుడు కాలాంతరంలో జనమేజయుడు చేస్తున్న సర్పయాగాన్ని ఆపించి, దేవతలకు సర్పజాతికి మహోపకారం చేసాడు. మనసాదేవి ఆజ్ఞతో ఆస్తీకుడు దేవతలని సర్పాలని రక్షించినందుకు కృతజ్ఞతగా దేవేంద్రుడు మనసాదేవిని షోడశోపచారాలతో పూజించి, ఆమె మంత్రాన్ని జపించి ఆ తరువాత ఘనంగాస్తుతించాడు.",
    TextSegment(text="మనసాదేవి మంత్రం", emphasized=True),
    TextSegment(text="ఓం హ్రీం శ్రీం మనసాదేవ్యై స్వాహా", emphasized=True),
    "మనసాదేవి ద్వాదశనామ స్తోత్రం",
    "జరత్కారురర్థగద్దేరి మనసా సిద్ధయోగినీ । వైష్ణవీ నాగభగినీ శైవీ నాగేశ్వరీ తథా ॥ జరత్కారు ప్రియా అస్తీకమాతా విషహోరీతి చ । మహాజ్ఞాన యుతాచైవ సాదేవీ విశ్వపూజతా ॥ ద్వాదశైతాని నామాని పూజాకాలేచయః పరేత్ । తస్యనాగ భయం నాస్తి తస్యవంశోద్భవస్యచ ॥ ఇదుస్తోత్రం పరిత్యాతు ముచ్యతే నాత్ర సంశయః । నాగభీతేచ శయనే నాగగ్రస్తేచ మందిరే ॥ నాగక్షేతే నాగదుర్గే నాగవేష్టిత విగ్రహే ॥",
    "1.జరత్కారు 2.జగద్ధరి 3.మనసా 4.సిద్ధయోగినీ 5.వైష్ణవీ 6.నాగభగినీ 7.శైవీ 8.నాగేశ్వరీ 9.జరత్కారుప్రియా 10.అస్తీకమాతా 11.విషహోరీ 12.మహాజ్ఞానయుతా — అనే ఈ పన్నిండు పేర్లు మనసాదేవి ఎవరైతే ఈ దివ్య నామాల్ని నిత్యం పరిస్తోరు వారికి సర్ప భయం అనేది వుండదు. అతని వంశంలో పుట్టబోయేవారికి కూడా సర్పభయం వుండదు.",
    "నిద్రలో పామకులాలోకి వస్తున్నా, తరచు ఇంటిలోని సర్పాలు వస్తున్నా, పాము కాటు వేయటానికి ప్రయత్నించేడప్పుడు, సర్పాల మధ్యలో చిక్కుకుపోయినప్పుడు — ఈ నామస్తోత్రాన్ని గాని నామాల్ని గాని పరిస్తే సర్పాలు దూరంగా వెళ్ళిపోతాయి. ఈ స్తోత్రాన్ని శ్రద్ధగా నిత్యం పారాయణ చేసేవాడిని చూస్తే పాములు భయపడి పారిపోతాయి. పదిలక్షల సార్లు ఈ స్తోత్రాన్ని జపిస్తే సిద్ధిస్తుంది. సిద్ధి పొందినవాడు పాములని ఆభరణాలుగా మెడలో ధరించగలడు.",
    "మనసాదేవి స్తోత్రం",
    "దయారూపా చ భగినీ క్షమారూపాయధా ప్రసూః । త్వయా మే రక్షితాః ప్రాణాః పుత్రదారాః సురేశ్వరి ॥ అహం కరోమి త్వాం పూజ్యాం మమప్రీతిశ్చ వర్ధతే । నిత్యం యద్యపి పూజ్యాత్వం భవేత్ర జగదంబికే ॥ తథాపి తవపూజాం వైవర్దయామి పునః పునః । యే త్వామాషాధ సంక్రాంత్యాం పూజయిష్యంతి భక్తితః ॥ పంచమ్యాం మనసాభ్యాయం మాసాంతేవ దినేదినే । పుత్రపౌత్రాదయః తేషాం వర్ధంతే చ ధనాని చ ॥ యశస్వినః కీర్తిమంతో విద్యావంతో గుణాన్వితాః । యే త్వాం న పూజయిష్యంతి నిందంత్యజ్ఞానతో జనాః ॥ లక్ష్మీ హీనా భవిష్యంతి తేషాం నాగభయం సదా । త్వం స్వర్గలక్ష్మీ స్వర్గే చ వైకుంతే కమలా కళా ॥ నారాయణాంశ భగవాన్ జరత్కారుర్నీశ్వరః । తపసా తేజసా త్వాం చ మనసా సప్రుజే పితా ॥ అస్మాకం రక్షణాయైవ తేన త్వం మనసాభిధా । మనసా దేవితం శక్తా చాత్మనా సిద్ధయోగినీ ॥ తేన త్వం మనసాదేవీ పూజితా వందితా భవే । యాం భక్త్యా మనసా దేవ పూజయంత్యనిశ భృశం ॥",
    "తేన త్వాం మనసాం దేవీం ప్రవదంతి పురావిదః । సత్త్వరూపా చ దేవీ త్వం శశ్వత్త్వ్య నిషేవయా ॥ యో హి యద్వావయేన్నిత్యం శతం ప్రాప్నోతి తత్పమ్ ॥",
    "ఈ విధంగా మహేంద్రుడు మనసాదేవిని స్తుతించి తన ప్రాణాలు కాపాడిన ఆసోదరిని స్వర్గలోకానికి తీసుకువెళ్ళాడు. యథోచితంగా ఆమెని సత్కరించాడు. మనసాదేవి ఇంద్రుడి కోరిక మేరకు కొన్నాళ్ళు అక్కడే వుండి దేవతలందరికి జ్ఞానోపదేశం చేసింది.",
    TextSegment(
        text="స్తోత్ర ఫలశ్రుతి: పుణ్యప్రదమైన మనసాదేవి స్తోత్రాన్ని, మంత్రాన్ని పఠించినవాడికి, వారి వంశంలోవారికి ఎప్పటికీ సర్పభయం వుండదు. ఈస్తోత్రం 5 లక్షల సార్లు పరిస్తే సిద్ధిస్తుంది. సిద్ధిపొందిన వాడికి పాము విషం అమృతమవుతుంది.",
        emphasized=True,
    ),
    "మా తదుపరి వీడియోలో కూర్మ పురాణం నుండి ఒక పవిత్రమైన కథను, దాని ప్రయోజనాన్ని తెలుసుకుందాం. మా ఛానల్‌ను సబ్‌స్క్రైబ్ చేయండి - ప్రతిరోజు పురాణ కథల కోసం.",
]


def _select_background(settings: Settings, for_date: date) -> Path:
    """3-way rotation among Vishnu/Shiva/Ganesha, cycling by ordinal day
    (not tied to the actual weekday) -- reuses the same non-repeating
    image-selection logic as the Community Post, just scoped to these
    three folders instead of the full weekday map."""
    db = DatabaseManager(settings.database_path)
    history_repo = ImageHistoryRepository(db)
    selector = RandomImageSelector(settings, history_repo)

    folder_name = BACKGROUND_FOLDERS[for_date.toordinal() % len(BACKGROUND_FOLDERS)]
    selected = selector.select_from_folder(folder_name, for_date)
    return selected.path


def _compute_duration(paragraphs: list[str | TextSegment]) -> float:
    """Duration driven purely by content length, per explicit request --
    if a passage is naturally short, the video is short; if it's long,
    the video runs long. No artificial padding either way."""
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

    try:
        print("Rendering scrolling text image...")
        text_renderer = PuranaTextRenderer(settings)
        text_image_path, text_image_height = text_renderer.render(
            MANASADEVI_PARAGRAPHS, settings.output_dir / f"{today.isoformat()}_manasadevi_text.png",
        )
        print(f"Rendered: {text_image_path} (height {text_image_height}px)")

        print("Selecting background image...")
        background_path = _select_background(settings, today)
        print(f"Background: {background_path}")

        duration = _compute_duration(MANASADEVI_PARAGRAPHS)
        print(f"Target duration: {duration:.1f}s ({duration / 60:.2f} min)")

        video_path = settings.output_dir / f"{today.isoformat()}_manasadevi_video.mp4"
        print("Assembling scroll video (this can take a while for a long video)...")
        assemble_scroll_video(
            background_image_path=background_path,
            text_image_path=text_image_path,
            text_image_height=text_image_height,
            output_path=video_path,
            duration_seconds=duration,
            audio_path=settings.alert_short_music_path,
            audio_volume=0.5,
        )
        print(f"Assembled: {video_path}")

        seo = build_manasadevi_video_seo()
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
