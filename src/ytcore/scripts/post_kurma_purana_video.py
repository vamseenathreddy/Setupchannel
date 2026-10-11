"""
post_kurma_purana_video.py: assembles and uploads episode 2 of the
long-form Puranam scrolling-text video series -- Shiva's Ananda
Tandava and Vishwarupa, from Sri Kurma Puranam. Same pipeline as
post_purana_video.py (episode 1, Manasadevi), just with this episode's
own content -- see that script's docstring for the full flow
explanation, which applies identically here.

Content notes:
- More shloka-dense than episode 1 (24 verses total vs. ~8-9), all
  individually proofread against the source pages -- OCR extraction
  followed by manual correction of every verse, per explicit request.
- No stated phalasruti in this specific 5-page passage (unlike
  Manasadevi's episode), so the SEO title leads with the story's own
  significance rather than a stated benefit -- see
  content/purana_video_seo.py's build_shiva_tandava_video_seo().

Usage:
    python -m ytcore.scripts.post_kurma_purana_video
    python -m ytcore.scripts.post_kurma_purana_video --public   # only once you're ready
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ytcore.config import Settings, get_settings
from ytcore.content.purana_video_seo import build_shiva_tandava_video_seo
from ytcore.database.db import DatabaseManager
from ytcore.database.repositories import ImageHistoryRepository
from ytcore.exceptions import AppError
from ytcore.images.purana_text_renderer import PuranaTextRenderer, TextSegment
from ytcore.images.selector import RandomImageSelector
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader
from ytcore.video.scroll_assembler import assemble_scroll_video

BACKGROUND_FOLDERS = ["Monday_Shiva", "Wednesday_Ganesha", "Saturday_Venkateswara"]
WORDS_PER_MINUTE = 100

# The Vishwarupa description (10 shlokas) as one block -- every verse
# individually proofread against pages 1933-1934 of the source PDF.
_VISHWARUPA_SHLOKAS = (
    "సహస్రశీర్షం దేవం సహస్రచరణాకృతిమ్ । సహస్రబాహుం జటిలం చంద్రార్ధకృతశేఖరమ్ ॥ 1 "
    "వసానం చర్మ వైయ్యాఘ్రం శూలాసక్తమహాకరమ్ । దండపాణిం త్రయీనేత్రం సూర్యసోమాగ్నిలోచనమ్ ॥ 2 "
    "బ్రహ్మాండం తేజసా స్వేన సర్వమావృత్య చ స్థితమ్ । దంష్ట్రాకరాళం దుర్ధర్షం సూర్యకోటి సమప్రభమ్ ॥ 3 "
    "అండస్థం చాండబాహ్యస్థం బ్రాహ్మ మభ్యంతరం పరమ్ । సృజంత మనలజ్వాలం దహంత మఖిలం జగత్ । "
    "నృత్యంతం దదృశుః దేవం విశ్వకర్మాణ మీశ్వరమ్ ॥ 4 "
    "మహాదేవం మహాయోగం దేవానామపి దైవతమ్ । పశూనాం పతి మీశానం జ్యోతిషాం జ్యోతి రవ్యయమ్ ॥ 5 "
    "పినాకినం విశాలాక్షం భేషజం భవరోగిణామ్ । కాలాత్మానం కాలకాలం దేవదేవం మహేశ్వరమ్ ॥ 6 "
    "ఉమాపతిం విరూపాక్షం యోగానందమయం పరమ్ । జ్ఞానవైరాగ్యనిలయం జ్ఞానయోగం సనాతనమ్ ॥ 7 "
    "శాశ్వతైశ్వర్యవిభవం ధర్మాధారం దురాసదమ్ । మహేంద్రోపేంద్రనమితం మహర్షిగణవందితమ్ ॥ 8 "
    "ఆధారం సర్వశక్తీనాం మహాయోగేశ్వరేశ్వరమ్ । యోగినాం పరమం బ్రహ్మ యోగినం యోగవస్థితమ్ । "
    "యోగినాం హృది తిష్ఠంతం యోగమాయాసమావృతమ్ ॥ 9 "
    "క్షణేన జగతో యోనిం నారాయణ మనామయమ్ । ఈశ్వరే ఐకతాపన్న మపశ్యన్ బ్రహ్మవాదినః ॥ 10"
)

# The sages' hymn of praise (20 shlokas) as one block -- every verse
# individually proofread against pages 1935-1937.
_STUTI_SHLOKAS = (
    "త్వా మేక మీశం పురుషం పురాణం ప్రాణేశ్వరం రుద్ర మనన్తయోగమ్ । "
    "నమామ సర్వే హృది సంనివిష్టం ప్రచేతసం బ్రహ్మమయం పవిత్రమ్ ॥ 1 "
    "త్వాం పశ్యంతి మునయో బ్రహ్మయోనిం దాన్తాః శాన్తాః విమలం రుక్మవర్ణమ్ । "
    "ధ్యాత్వాత్మస్థమచలం స్వే శరీరే కవిం పరేభ్యః పరమం తత్పరం చ ॥ 2 "
    "త్వత్తః ప్రసూతా జగతః ప్రసూతిః సర్వాత్మభూ స్త్వం పరమాణుభూతః । "
    "అణో రణీయాన్ మహతో మహీయాం స్త్వామేవ సర్వం ప్రవదన్తి సన్తః ॥ 3 "
    "హిరణ్యగర్భో జగదంతరాత్మా త్వత్తో అధి జాతః పురుషః పురాణః । "
    "సంజాయమానో భవతా విసృష్టో యథావిధానం సకలం ససర్జ ॥ 4 "
    "త్వత్తో వేదాః సకలాః సమ్ప్రసూతాః స్వయ్యే వాంతే సంస్థితిం తే లభంతే । "
    "పశ్యామ స్వాం జగతో హేతుభూతం నృత్యంతం స్వే హృదయే సంనివిష్టమ్ ॥ 5 "
    "త్వయై వేదం భ్రామ్యతే బ్రహ్మచక్రం మాయావీ త్వం జగతా మేకనాథః । "
    "నమామ స్వాం శరణం సంప్రపన్నా యోగాత్మానం పరమాకాశమధ్యే ॥ 6 "
    "నృత్యంతం తే మహిమానం స్మరామః సర్వాత్మానం బహుధా సంనివిష్టం । బ్రహ్మానంద మనుభూయానుభూయ ॥ 7 "
    "ఓంకార స్తే వాచకో ముక్తిబీజం త్వ మక్షరం ప్రకృతౌ గూఢరూపమ్ । "
    "తత్త్వం సత్యం ప్రవదంతీహ సంతః స్వయం ప్రభం భవతో యత్ప్రకాశం ॥ 8 "
    "స్తువంతి త్వాం సతతం సర్వవేదాః నమంతి త్వాం ఋషయః క్షీణదోషాః । "
    "శాంతాత్మానః సత్యసంధా వరిష్ఠం విశంతి త్వాం యతయో బ్రహ్మనిష్ఠాః ॥ 9 "
    "ఏకో వేదో బహుశాఖో హ్యనంతః త్వా మేవైకం బోధయంత్యేకరూపమ్ । "
    "వేద్యం త్వాం శరణం యే ప్రపన్నా స్తేషాం శాంతిః శాశ్వతీ నేతరేషామ్ ॥ 10 "
    "భవా నీశో అనాదిమాం స్తేజోరాశి ర్బ్రహ్మా విశ్వం పరమేష్ఠీ వరిష్ఠః । "
    "స్వాత్మానంద మనుభూయ అధిశేతే స్వయం జ్యోతి రచలో నిత్యముక్తః ॥ 11 "
    "ఏకో రుద్రస్త్వం కరోషీహ విశ్వం త్వం పాలయ స్యఖిలం విశ్వరూపః । "
    "త్వ మేవాంతే నిలయం విందతీదం నమామ స్త్వాం శరణం సంప్రపన్నాః ॥ 12 "
    "త్వా మేక మాహుః కవి మేకరుద్రం ప్రాణం బృహంతం హరి మగ్ని మీశం । "
    "ఇంద్రం మృత్యు మనిలం చేకితానం ధాతార మాదిత్య మనేకరూపమ్ ॥ 13 "
    "త్వ మక్షరం పరమం వేదితవ్యం త్వమస్య విశ్వస్య పరం నిధానమ్ । "
    "త్వ మవ్యయః శాశ్వతధర్మగోప్తా సనాతన స్త్వం పురుషోత్తమో అసి ॥ 14 "
    "త్వ మేవ విష్ణు శ్చతురానన స్త్వం త్వమేవ రుద్రో భగవా నధీశః । "
    "త్వం విశ్వనాభిః ప్రకృతిః ప్రతిష్ఠా సర్వేశ్వర స్త్వం పరమేశ్వరో అసి ॥ 15 "
    "త్వా మేక మాహుః పురుషం పురాణ మాదిత్యవర్ణం తమసః పరస్తాత్ । "
    "చిన్మాత్ర మవ్యక్త మచింత్యరూపమ్ ఖం బ్రహ్మశూన్యం ప్రకృతిం నిర్గుణం చ ॥ 16 "
    "యదంతరా సర్వమిదం విభాతి య దవ్యయం నిర్మల మేకరూపమ్ । "
    "కి మప్యచింత్యం తవ రూప మేతత్ తదన్తరా య త్ప్రతిభాతి తత్త్వమ్ ॥ 17 "
    "యోగేశ్వరం రుద్ర మనంతశక్తిం పరాయణం బహుతనుం పవిత్రమ్ । "
    "నమామ సర్వే శరణార్థిన స్త్వాం ప్రసీద భూతాధిపతే మహేశ ॥ 18 "
    "త్వత్పాదపద్మస్మరణా దశేషసంసారబీజం విలయం ప్రయాతి । "
    "మనో నియమ్య ప్రణిధాయ కాయం ప్రసాదయామో వయ మేక మీశమ్ ॥ 19 "
    "నమో భవాయాస్తు భవోద్భవాయ కాలాయ సర్వాయ హరాయ తుభ్యమ్ । "
    "నమోస్తు రుద్రాయ కపర్దినే తే నమోఽగ్నయే దేవ నమః శివాయ ॥ 20"
)

KURMA_TANDAVA_PARAGRAPHS: list[str | TextSegment] = [
    "శివ తాండవం",
    "యోగేశ్వరుడైన శంకరుడు తనతత్త్వాన్ని ఋషులకీ మునులకీ బోధించిన తరువాత, ఆనంద తన్మయత్వంతో తన విభూతిని ప్రదర్శిస్తూ నృత్యం చేసాడు. అదే ఆనందతాండవం. పరమేశ్వరుడు ఆ విధంగా ఆకాశంలో నృత్యం చేస్తుంటే శ్రీమహావిష్ణువుతో సహ దేవతలు, జితేంద్రియులైన యోగులు, సిద్ధులు ఎంతో ఆనందంతో ఆ నృత్యాన్ని దర్శించారు. ఈ సకల ప్రపంచం ఎవరి సంకల్పంతో ప్రవర్తిస్తుందో అలాంటి పరమేశ్వరుడు ఆ విధంగా ఆనందతాండవం చేస్తూ బ్రహ్మాది దేవతలకి దర్శనమిచ్చాడు. ఎవరి పాద పద్మాల్ని స్మరించటం ద్వారా సకల భూతాలూ అజ్ఞానం వల్ల కలిగే భయాల్ని పోగొట్టుకుంటారో అలాంటి సకలభూతేశ్వరుడు ఆనంద తాండవాన్ని వారంతా దర్శించగలిగారు.",
    "నిద్రను విడిచిపెట్టి, ప్రాణాయామాన్ని ఆచరించి, ఇంద్రియ నిగ్రహాన్ని పెంపొందించుకున్న భక్తులు మాత్రమే జ్యోతి స్వరూపుడైన మహాయోగీశ్వరుణ్ణి దర్శించగలరు. అలాంటి భక్తవత్సలుడైన శివుడు ప్రసన్నుడైతే జీవులందర్నీ అజ్ఞానం నుంచి బైటపడేస్తాడు. ఈ విషయాన్ని గ్రహించిన మునులు, ఋషులు, దేవతలు ఆనందతాండవం చేస్తూ పరమేశ్వరుడి విశ్వరూపాన్ని చూసారు. ఆ మహాదేవుడి దివ్యరూపం ఎలా ఉందంటే!",
    TextSegment(text="శివుడి విశ్వరూపం", emphasized=True),
    TextSegment(text=_VISHWARUPA_SHLOKAS, emphasized=True),
    "ఆ పరమ రుద్రుడు వేయి శిరస్సులు, వేయి చేతులు కలవాడు, జటాధారి. అర్ధచంద్రుని శిరమున ఆభరణముగా కలవాడు, వ్యాఘ్ర చర్మమును ధరించేవాడు. పొడవైన చేతిలో శూలము ధరించువాడు. దండపాణి, వేదత్రయమును నేత్రములుగా కలవాడు. సూర్య చంద్రాగ్నులు నేత్రములుగా కలవాడు. సకల బ్రహ్మాండమును తన తేజస్సుతో అధిష్టించి వున్నవాడు, దంష్ట్రలతో భయంకరమైన వక్త్రము గలవాడు. ఇతరులచే ఓడించబడనివాడు, కోటి సూర్యులతో సమానమైన కాంతిగలవాడు. అగ్ని జ్వాలలను సృష్టించి అఖిల జగత్తును దహించేవాడు. సకల జగత్తును సృజించేవాడైన ఈశ్వరుని నృత్యం చేస్తుండగా చూసారు. ఈ పరమేశ్వరుడు మహాదేవుడు, మహాయోగస్వరూపుడు, దేవతలకు కూడ దేవత, పశుపతి, నిఖిల జగచ్చాసకుడు, ఆనందరూపుడు, జ్యోతి స్వరూపుడు, నాశము లేనివాడు, ధనువును ధరించినవాడు, విశాలనేత్రుడు, సంసార వ్యాధిగ్రస్తులకు దివ్యౌషధము. కాలస్వరూపుడు, యమునికి యముడు, దేవదేవుడు, మహేశ్వరుడు, ఉమాపతి, యోగరూపుడు, పరమానందరూపుడు, జ్ఞాన వైరాగ్యనిలయుడు, జ్ఞానయోగమును శరీరముగా కలవాడు, సనాతనుడు. ఉత్పత్తి నాశములు లేని ఐశ్వర్య వైభవములు కలవాడు. ధర్మమునకు ఆధారభూతుడు. అందరానివాడు. మహేంద్ర ఉపేంద్రాదులతో, మహర్షి గణములతో నమస్కరించబడేవాడు. యోగుల హృదయాలలో నివసించేవాడు. యోగమాయచే ఆవరించబడి ఉన్నవాడు. జగత్కారణభూతుడు.",
    "అటువంటి మహాదేవుడి విశ్వరూపంలో ఆద్యంతాలు లేని శ్రీమహావిష్ణువు అందరూ చూస్తుండగా ఐక్యమైపోయాడు. ఆ విధంగా నారాయణుణ్ణి తనలో నింపుకున్న పరమేశ్వరుణ్ణి చూసి, బ్రహ్మవాదులంతా తమ జీవితాలు ఎంతో ధన్యమయ్యాయని భావించారు.",
    "సనత్కుమారుడు, సనకుడు, భృగువు, సనాతనుడు, సనందుడు, రుద్రుడు, అంగిరసుడు, వామదేవుడు, శుక్రుడు, అత్రి, కపిల, మరీచ్యాది మహర్షులందరూ నారాయణుణ్ణి ఎడమభాగంలో ధరించిన పరమేశ్వరుడికి శిరసు వంచి నమస్కరించి ఆయన దివ్యమంగళాకారాన్ని తమ మనసుల్లో నిలుపుకుని పరిపూర్ణమైన ఆనందంతో, వేదమయమైన వాక్కులతో ఇలా కీర్తించారు.",
    TextSegment(text="మహర్షులు చేసిన శివుడి విశ్వరూప స్తుతి", emphasized=True),
    TextSegment(text=_STUTI_SHLOKAS, emphasized=True),
    "\"పరమేశ్వరా! తమరొక్కరే ఈశ్వరులు — పురాణ పురుషులు, ప్రాణేశ్వరులు, అనంతయోగస్వరూపులు. సకల జగత్తుకీ చైతన్యం ప్రసాదించేవారు. అలాంటి మీకు నమస్కరిస్తున్నాం. సంసారరూపుడు, సంసారాన్ని సృష్టించేవాడు, సర్వరూపుడు, కాలస్వరూపుడు అయిన పరమేశ్వరుడికి నమస్కారం\" అని మునులు చేసిన స్తోత్రం విని జటాజూటధారి అయిన పరమేశ్వరుడు తన విశాల విశ్వరూపాన్ని ఉపసంహరించి తిరిగి యథారూపాన్ని ధరించాడు. అప్పుడు మహర్షులంతా ఆయనకి నమస్కరించి \"మహాదేవా! నీ వల్ల ఈశ్వర జ్ఞానాన్ని ఆత్మతత్వాన్ని తెలుసుకున్నాం. దయచేసి మాకు పరమేశ్వరుడవైన నీ యథార్థ ప్రభావాన్ని గురించి చెప్పు\" అని ప్రార్థించారు.",
    TextSegment(text="పరమేశ్వరుడి యథార్థ ప్రభావం", emphasized=True),
    "\"మహర్షులారా! ఇప్పుడు మీరంతా దర్శించిన నా విశ్వరూపం కేవలమైనది. నా మాయ ఎంతటిదో తెలియచేయటానికి దీన్ని మీకు చూపించాను. ఈ సృష్టిలోని అన్ని వస్తువుల్లో సర్వాంతర్యామిగా నేనుంటాను. ఈ జగత్తునంతా నేను ఒకే అంశతో సృష్టిస్తాను. తిరిగి దాన్ని ఒకే అంశంతో లయం చేస్తాను.\"",
    "మా తదుపరి వీడియోలో వామన పురాణం నుండి ఒక పవిత్రమైన కథను తెలుసుకుందాం. మా ఛానల్‌ను సబ్‌స్క్రైబ్ చేయండి - ప్రతిరోజు పురాణ కథల కోసం.",
]


def _select_background(settings: Settings, for_date: date) -> Path:
    db = DatabaseManager(settings.database_path)
    history_repo = ImageHistoryRepository(db)
    selector = RandomImageSelector(settings, history_repo)
    folder_name = BACKGROUND_FOLDERS[for_date.toordinal() % len(BACKGROUND_FOLDERS)]
    selected = selector.select_from_folder(folder_name, for_date)
    return selected.path


def _compute_duration(paragraphs: list[str | TextSegment]) -> float:
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
            KURMA_TANDAVA_PARAGRAPHS, settings.output_dir / f"{today.isoformat()}_shiva_tandava_text.png",
        )
        print(f"Rendered: {text_image_path} (height {text_image_height}px)")

        print("Selecting background image...")
        background_path = _select_background(settings, today)
        print(f"Background: {background_path}")

        duration = _compute_duration(KURMA_TANDAVA_PARAGRAPHS)
        print(f"Target duration: {duration:.1f}s ({duration / 60:.2f} min)")

        video_path = settings.output_dir / f"{today.isoformat()}_shiva_tandava_video.mp4"
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

        seo = build_shiva_tandava_video_seo()
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
