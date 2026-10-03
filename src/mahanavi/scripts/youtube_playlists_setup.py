"""
youtube_playlists_setup.py: one-time script that creates the channel's
4 series playlists via the YouTube Data API v3 and prints their IDs --
added 2026-10-03 (pipeline health review suggestion #2, "no
playlists"). Grouping choice: ONE playlist covers both Gita Sloka modes
(verse days AND quiz days), since they're literally one alternating
series, not two -- matches post_gita_sloka_short.py's own framing.

IDEMPOTENT: if a playlist with the exact same title already exists on
the channel (checked via playlists().list(mine=True) first), it reuses
that playlist's ID instead of creating a duplicate, and re-syncs its
description to whatever's currently in PLAYLISTS_TO_CREATE below --
safe to re-run any time, including just to push an edited description
to an already-live playlist.

Usage (locally, after youtube_shorts_auth_setup.py has run once):
    python -m mahanavi.scripts.youtube_playlists_setup

Usage (from CI, via the one-off "Set Up YouTube Playlists" workflow,
workflow_dispatch -- this is the normal path, since this script needs
the REAL saved token, which only exists where data/youtube_token.json
has been restored from Drive):
    see .github/workflows/setup-playlists.yml

After it runs, copy the printed playlist IDs into these GitHub repo
secrets (Settings -> Secrets and variables -> Actions):
    MAHANAVI_PLAYLIST_ID_MUHURTAS
    MAHANAVI_PLAYLIST_ID_GITA_SLOKA
    MAHANAVI_PLAYLIST_ID_PURANAS
    MAHANAVI_PLAYLIST_ID_RASHI
    MAHANAVI_PLAYLIST_ID_NAVARATRI_SONGS   (added 2026-10-03)
Each posting workflow already passes these through as env vars (see
.github/workflows/*.yml) -- once the secrets exist, every future
upload gets added to its series playlist automatically, no further
action needed.
"""

from __future__ import annotations

import sys

from mahanavi.config import get_settings
from mahanavi.exceptions import YouTubeUploadError
from mahanavi.publishers.youtube_shorts_uploader import YouTubeShortsUploader

# (settings field name suffix, playlist title, playlist description).
# Descriptions rewritten 2026-10-03 for actual long-form bilingual SEO
# copy (Telugu + English, each description several paragraphs, well
# over 4000 characters combined per playlist) -- the prior version was
# still only a short couple of sentences per language. main() keeps
# these in sync on every run, even for a playlist that already exists
# (see the "Already exists" branch below), so editing this list and
# re-running is how you update a live playlist's description going
# forward.
PLAYLISTS_TO_CREATE = [
    (
        "muhurtas",
        "Daily Muhurtams (Rahu Kalam, Shubha Ghadiyalu, Durmuhurtham)",
        'మన పెద్దలు ఏ శుభకార్యమైనా మంచి సమయం చూసి మాత్రమే ప్రారంభిస్తారు. ప్రతిరోజూ పంచాంగంలో రాహు కాలం, యమగండం, దుర్ముహూర్తం వంటి అశుభ సమయాలు, అలాగే శుభ ఘడియలు, అమృత ఘడియలు వంటి శుభ సమయాలు నిర్ణయించబడతాయి. సూర్యోదయం నుండి సూర్యాస్తమయం వరకు ఉన్న కాలాన్ని ఎనిమిది భాగాలుగా విభజించి, ఏ వారంలో ఏ భాగం రాహు కాలం అవుతుందో లెక్కిస్తారు -- ఇది ప్రతి ఊరిలో, ప్రతి రోజు సూర్యోదయ సమయాన్ని బట్టి మారుతుంది. ఈ ఛానల్\u200cలో మేము ప్రతిరోజూ ఉదయం ఖచ్చితమైన లెక్కలతో ఆ రోజు రాహు కాలం, శుభ ఘడియలు, దుర్ముహూర్తం సమయాలను ఒక్క షార్ట్ వీడియోలో అందిస్తాం.\n\nరాహు కాలంలో కొత్త పని మొదలుపెట్టడం, ప్రయాణాలు, డబ్బు లావాదేవీలు వంటివి మానుకోవాలని నమ్మకం. శుభ ఘడియలు అంటే ఏ పనైనా ప్రారంభించడానికి మంచి సమయం -- గృహప్రవేశం, వ్యాపార ప్రారంభం, పెళ్లి మాట్లాడటం వంటి ముఖ్యమైన సందర్భాలకు ఈ సమయాన్ని చూస్తారు. దుర్ముహూర్తం అనేది రోజుకి ఒకటో రెండో సార్లు వచ్చే మరో అశుభ కాలం, దీన్ని కూడా తప్పించుకోవడం మంచిది అని పెద్దలు చెబుతారు. ఈ మూడు సమయాలను ఒక్కచోటే, సులభంగా అర్థమయ్యేలా, ప్రతి వీడియోలో ఆ రోజుకి వర్తించే దేవత మంత్రంతో కలిపి మేము అందిస్తున్నాం -- సోమవారం శివుడు, మంగళవారం హనుమంతుడు/గణేశుడు, శుక్రవారం లక్ష్మీదేవి, శనివారం వెంకటేశ్వరుడు వంటి వారపు దేవతల మంత్రాలు ఇందులో భాగమే.\n\nపంచాంగం అంటే ఐదు అంగాలు కలిసిన శాస్త్రం -- తిథి, వారం, నక్షత్రం, యోగం, కరణం. ఈ ఐదు అంశాలను కలిపి చూస్తేనే ఏ రోజు ఎలాంటిదో, ఏ సమయం శుభమో పూర్తిగా అర్థమవుతుంది. తిథి అంటే చంద్రుడి కళను బట్టి నెలలో ఉన్న రోజు (పాడ్యమి, విదియ వంటివి), నక్షత్రం అంటే చంద్రుడు ఆ రోజు ఏ నక్షత్రంలో ఉన్నాడో, యోగం సూర్య-చంద్ర కలయిక ఆధారంగా వచ్చే ప్రత్యేక కాలం, కరణం అంటే తిథిలో సగభాగం. ఈ లెక్కలన్నీ మా వెనుక ఆటోమేటిగ్గా జరుగుతాయి, మీకు కేవలం తేలికగా అర్థమయ్యే ఫలితం మాత్రమే వీడియోలో చూపిస్తాం. బ్రాహ్మణులు, పురోహితులు, జ్యోతిష్కులు మాత్రమే కాకుండా సాధారణ గృహస్థులు కూడా తమ దినచర్యను ఈ సమయాల ఆధారంగా ప్లాన్ చేసుకోవడం మన సంప్రదాయంలో భాగం, దాన్ని సులభతరం చేయడమే మా లక్ష్యం.\n\nప్రతి రోజూ కొత్త వీడియో అప్\u200cలోడ్ అవుతుంది, కాబట్టి సబ్\u200cస్క్రైబ్ చేసుకుని నోటిఫికేషన్ బెల్ నొక్కితే ఉదయాన్నే ఆ రోజు ముహూర్తాలు మీకు అందుతాయి. మీ ఊరి సమయం కొంచెం వేరుగా ఉంటే కామెంట్\u200cలో తెలియజేయండి, తెలుగు పంచాంగం ప్రేమికుల కోసం మేము ఈ ప్లేలిస్ట్\u200cని ప్రతిరోజూ అప్\u200cడేట్ చేస్తూనే ఉంటాం. #పంచాంగం #రాహుకాలం #శుభఘడియలు #దుర్ముహూర్తం'
        "\n\n"
        "Our elders never start anything important without checking for an auspicious time first, and this playlist brings that daily Panchangam wisdom straight to your feed. Every single day the Telugu almanac marks out inauspicious windows -- Rahu Kalam, Yamagandam, Durmuhurtham -- alongside auspicious ones like Shubha Ghadiyalu and Amrita Ghadiyalu. Rahu Kalam is calculated by splitting the daylight hours between sunrise and sunset into eight equal parts, with a different part falling on each weekday, which is why the exact clock time shifts slightly from city to city and day to day. Every morning, this series posts a short video with the precise timings for that day's Rahu Kalam, Shubha Ghadiyalu and Durmuhurtham, calculated fresh and never copy-pasted from a generic chart.\n\nTraditionally, people avoid starting new work, travelling, or signing financial deals during Rahu Kalam. Shubha Ghadiyalu, on the other hand, is considered the best window to begin something meaningful -- a housewarming, launching a business, discussing a wedding, or any fresh start. Durmuhurtham is a second, shorter inauspicious slot that recurs once or sometimes twice a day and is best avoided for the same reasons as Rahu Kalam. Rather than just listing numbers, every video also carries that weekday's ruling deity mantra -- Lord Shiva on Monday, Hanuman and Ganesha on Tuesday, Goddess Lakshmi on Friday, Lord Venkateswara on Saturday, and so on -- so you get both the timing and a moment of devotion in the same thirty seconds.\n\nPanchangam literally means 'five limbs' -- Tithi, Vara, Nakshatra, Yoga and Karana -- and all five have to be read together to fully understand what kind of day it is and which hours are favorable. Tithi is the lunar day based on the Moon's phase, Nakshatra is the constellation the Moon occupies that day, Yoga is a special period derived from the combined longitude of the Sun and Moon, and Karana is half of a Tithi. All of that calculation happens behind the scenes for you -- what you see on screen is just the clear, usable result. This isn't knowledge reserved for priests and astrologers alone; ordinary households have planned their day around these timings for generations, and our only job here is to make that easy to check every single morning.\n\nA fresh video drops every morning without fail, so subscribing and turning on notifications means you'll have that day's muhurtams before you start your routine. If your city's sunrise time differs noticeably, drop a comment and we'll clarify the adjustment -- this playlist is maintained daily for everyone who still plans their day around the traditional Telugu Panchangam. #DailyPanchangam #RahuKalam #ShubhaGhadiyalu #Durmuhurtham #TeluguAstrology",
    ),
    (
        "gita_sloka",
        "Bhagavad Gita Sloka & Quiz",
        'భగవద్గీత అంటే కేవలం ఒక గ్రంథం కాదు, అది కురుక్షేత్ర యుద్ధభూమిలో శ్రీకృష్ణుడు అర్జునుడికి చెప్పిన జీవన మార్గదర్శిని. యుద్ధం చేయడానికి మనస్కరించని అర్జునుడికి కృష్ణుడు ధర్మం, కర్మ యోగం, భక్తి యోగం, జ్ఞాన యోగం అనే మార్గాల గురించి వివరిస్తాడు -- ఫలితాన్ని ఆశించకుండా తన కర్తవ్యాన్ని ఎలా నిర్వర్తించాలో, ఆత్మ శాశ్వతమైనదని, శరీరం మాత్రమే నశిస్తుందని బోధిస్తాడు. ఈ ప్లేలిస్ట్\u200cలో మేము రెండు రోజులకు ఒక్కసారి కొత్త శ్లోకాన్ని సంస్కృత పాఠంతో, తెలుగు అర్థంతో, ఏ అధ్యాయం ఏ శ్లోక సంఖ్య అనే వివరాలతో అందిస్తాం.\n\nశ్లోకం పోస్ట్ అయిన మర్నాడు, అదే శ్లోకంపై ఒక చిన్న క్విజ్ వీడియో వస్తుంది -- నాలుగు ఆప్షన్లలో సరైన సమాధానం ఎంచుకునే సరదా పద్ధతిలో మీ జ్ఞాపకశక్తిని పరీక్షించుకోవచ్చు. ఈ వేరియట్\u200cలో శ్రీకృష్ణుడి మరియు శ్రీమహావిష్ణువు మంత్రాలు, నామాలు రొటేట్ అయ్యి వస్తాయి, కాబట్టి ప్రతి వీడియోలో ఒక్కలాంటి మంత్రం రిపీట్ కాకుండా వైవిధ్యంగా ఉంటుంది. కర్మ యోగం (ఫలితం ఆశించకుండా పని చేయడం), భక్తి యోగం (శరణాగతి), స్థిత ప్రజ్ఞత (సుఖదుఃఖాల్లో సమతూకం) వంటి గీతా బోధనలు ఒక్కో శ్లోకం ద్వారా నెమ్మదిగా, స్పష్టంగా అర్థమయ్యేలా ఈ సిరీస్\u200cలో అందుతాయి.\n\nగీత 18 అధ్యాయాలుగా విభజించబడింది, ఒక్కో అధ్యాయం ఒక్కో యోగాన్ని వివరిస్తుంది -- మొదటి అధ్యాయం అర్జునుడి విషాద యోగంతో మొదలై, రెండవ అధ్యాయంలో సాంఖ్య యోగం ద్వారా ఆత్మ గురించిన జ్ఞానం అందుతుంది. మూడు, నాలుగు అధ్యాయాల్లో కర్మ యోగం, ఆరవ అధ్యాయంలో ధ్యాన యోగం, పదకొండవ అధ్యాయంలో విశ్వరూప సందర్శన యోగం -- కృష్ణుడు తన విరాట్ రూపాన్ని చూపించే అద్భుతమైన ఘట్టం -- ఉంటాయి. చివరి అధ్యాయంలో మోక్ష సన్యాస యోగం ద్వారా గీత సారాన్ని కృష్ణుడు ముగిస్తాడు. ఈ ప్లేలిస్ట్ ఈ అధ్యాయాల క్రమంలోనే వెళ్తుంది, కాబట్టి మొదటి నుండి చూస్తే గీత అంతా ఒక క్రమపద్ధతిలో అర్థమవుతుంది.\n\nఒక్క రోజులో పూర్తి గీత చదవడం కష్టం అనిపిస్తే, ఈ విధంగా రోజుకో శ్లోకం, మర్నాడు క్విజ్ అనే పద్ధతిలో నెమ్మదిగా 700 శ్లోకాలను చదివించి, అర్థం చేసుకునేలా చేయడమే మా లక్ష్యం. సబ్\u200cస్క్రైబ్ చేసి, కామెంట్\u200cలో మీ క్విజ్ సమాధానం షేర్ చేయండి, మీకు ఇష్టమైన శ్లోకం ఏదో కూడా చెప్పండి. #భగవద్గీత #కృష్ణుడు #గీతాసారం #ధర్మం'
        "\n\n"
        "The Bhagavad Gita is not just scripture -- it is the conversation Lord Krishna had with Arjuna on the battlefield of Kurukshetra, at the exact moment Arjuna lost the will to fight. Through 700 verses across 18 chapters, Krishna explains dharma, karma yoga, bhakti yoga and jnana yoga: how to act without being attached to the outcome, why the soul is eternal while only the body perishes, and how duty and devotion fit together. This playlist posts one new verse every other day, complete with the original Sanskrit chant, its Telugu meaning, and the exact chapter and verse reference so you can look it up yourself.\n\nThe day after each verse goes up, a short quiz video tests whether you remember it -- four multiple-choice options, one right answer, and a quick dopamine hit if you get it. Krishna and Vishnu mantras and namams rotate across these quiz videos too, so no two days feel identical even when the format repeats. Along the way you'll naturally encounter core Gita ideas -- karma yoga (acting without craving the result), bhakti yoga (surrender), and sthitapragyata (staying even-minded through pleasure and pain) -- introduced one verse at a time rather than all at once.\n\nThe Gita is organized into 18 chapters, each centered on a particular yoga. It opens with Arjuna's Vishada Yoga -- his despair at the thought of fighting his own relatives -- before Krishna answers with Sankhya Yoga's teaching on the eternal soul in chapter two. Chapters three and four cover Karma Yoga, chapter six covers Dhyana Yoga (meditation), and chapter eleven delivers one of the most dramatic moments in all of scripture: Vishwarupa Darshana Yoga, where Krishna reveals his cosmic, universal form to Arjuna. The final chapter, Moksha Sanyasa Yoga, is where Krishna draws everything together into his closing message. This playlist follows that same chapter order, so watching from the start gives you the Gita's full arc, not just isolated verses.\n\nReading the entire Gita in one sitting is hard for most people; this series is built for the opposite approach -- one verse, one quiz, repeated patiently until all 700 verses have passed through your feed. Subscribe, drop your quiz answer in the comments, and tell us which verse has stayed with you the most. #BhagavadGita #Krishna #GitaSloka #KarmaYoga #HinduPhilosophy",
    ),
    (
        "puranas",
        "Purana Stories & Concepts",
        'పురాణాలు అంటే కేవలం పాత కథలు కాదు, అవి ధర్మం, నీతి, భక్తి గురించి వేల సంవత్సరాల జ్ఞానాన్ని కథల రూపంలో అందించే గ్రంథాలు. హిందూ సంప్రదాయంలో 18 ప్రధాన పురాణాలు ఉన్నాయి -- విష్ణు పురాణం, శివ పురాణం, భాగవత పురాణం, మార్కండేయ పురాణం, బ్రహ్మ పురాణం, స్కంద పురాణం వంటివి. ఒక్కో పురాణంలో దేవతల లీలలు, రాక్షసుల కథలు, రుషుల బోధనలు, సృష్టి గురించిన వివరణలు ఉంటాయి. ఈ ప్లేలిస్ట్\u200cలో మేము ఈ పురాణాల నుండి ఎంచుకున్న కథలు, ముఖ్యమైన భావనలను ప్రతిరోజూ ఒక్క నిమిషం లోపు వీడియోగా అందిస్తాం -- పెద్ద గ్రంథాన్ని చదవలేని వారికి కూడా ఈ కథలు సులభంగా, ఆసక్తిగా అర్థమయ్యేలా చేస్తాం.\n\nకొన్నిసార్లు ఇది ఒక దేవత లీల కావచ్చు -- గణేశుడు జన్మించిన కథ, శివుడు హాలాహలం మింగిన కథ, నరసింహావతారం వెనుక కథ. కొన్నిసార్లు ఇది ఒక భావన కావచ్చు -- పాపం-పుణ్యం, కర్మ సిద్ధాంతం, మోక్షం అంటే ఏమిటి, యుగాల గురించి వివరణ. ప్రతి వీడియో చివర ఆ కథ లేదా భావన ఏ పురాణం నుండి తీసుకోబడిందో స్పష్టంగా చెప్పి, కామెంట్\u200cలో మరింత వివరణాత్మక కామెంట్ కూడా పోస్ట్ చేస్తాం, ఆసక్తి ఉన్నవారు పూర్తి కథ చదవగలిగేలా.\n\n18 మహాపురాణాలను మూడు గుంపులుగా విభజిస్తారు -- సత్త్విక పురాణాలు (విష్ణువును ప్రధానంగా చెప్పేవి, విష్ణు పురాణం, భాగవత పురాణం వంటివి), రాజస పురాణాలు (బ్రహ్మను ప్రధానంగా చెప్పేవి, బ్రహ్మ పురాణం, మార్కండేయ పురాణం వంటివి), తామస పురాణాలు (శివుడిని ప్రధానంగా చెప్పేవి, శివ పురాణం, లింగ పురాణం వంటివి). ఇవి కాకుండా అగ్ని పురాణం, గరుడ పురాణం, పద్మ పురాణం, వరాహ పురాణం, వామన పురాణం, కూర్మ పురాణం, మత్స్య పురాణం, భవిష్య పురాణం వంటి మరిన్ని పురాణాలు కూడా ఉన్నాయి. ఈ ప్లేలిస్ట్\u200cలో మేము వీలైనంత వరకూ అన్ని పురాణాల నుండి కథలను ఎంచుకుని, ఏ కథ ఏ సందర్భంలో, ఎందుకు చెప్పబడిందో వివరిస్తూ అందిస్తాం -- కేవలం కథనం మాత్రమే కాదు, దాని వెనుక ఉన్న నీతి కూడా స్పష్టంగా తెలియజేస్తాం.\n\nపిల్లలకు నీతి కథలు చెప్పాలనుకునే తల్లిదండ్రులకు, పురాణాల గురించి తెలుసుకోవాలనుకునే ప్రతి ఒక్కరికీ ఈ ప్లేలిస్ట్ ఉపయోగకరంగా ఉంటుంది. ప్రతిరోజూ కొత్త కథ వస్తుంది, సబ్\u200cస్క్రైబ్ చేసి మీకు నచ్చిన పురాణం లేదా కథ ఏదో కామెంట్\u200cలో తెలియజేయండి, మేము దాని గురించి మరింత లోతుగా చేయడానికి ప్రయత్నిస్తాం. #పురాణాలు #హిందూపురాణాలు #భక్తికథలు'
        "\n\n"
        "The Puranas are not simply old stories -- they are how thousands of years of teaching on dharma, ethics and devotion have survived in story form. Hindu tradition recognizes 18 major Puranas, including the Vishnu Purana, Shiva Purana, Bhagavata Purana, Markandeya Purana, Brahma Purana and Skanda Purana, each weaving together divine leelas, accounts of demons and sages, and explanations of creation itself. This playlist pulls individual stories and concepts from across these texts and turns each one into a video under a minute long -- built for anyone who will never sit down and read the full original scripture but still wants to actually understand it.\n\nSome days you'll get a specific divine leela -- how Ganesha came to be, the story of Shiva swallowing the Halahala poison to save the universe, or what led to the Narasimha avatar. Other days bring a concept instead -- what karma really means, the difference between sin and merit, what moksha is, or how the four yugas are described in scripture. Every video names exactly which Purana the story or idea comes from, and the comment section carries a longer written version for anyone who wants more detail than thirty seconds allows.\n\nTradition groups the 18 Mahapuranas into three sets: Sattvika Puranas centered on Vishnu (the Vishnu Purana and Bhagavata Purana among them), Rajasa Puranas centered on Brahma (the Brahma Purana and Markandeya Purana), and Tamasa Puranas centered on Shiva (the Shiva Purana and Linga Purana). Beyond these there are also the Agni Purana, Garuda Purana, Padma Purana, Varaha Purana, Vamana Purana, Kurma Purana, Matsya Purana and Bhavishya Purana, each covering its own set of stories and teachings. This playlist draws from as many of these texts as possible, and each video explains not just the story itself but the context it was told in and the moral lesson it was meant to carry.\n\nParents looking for moral stories to share with their kids, and anyone simply curious about Hindu mythology, will both find this playlist useful. A new story or concept is posted every day -- subscribe and tell us in the comments which Purana or story you'd like covered in more depth next. #PuranaStories #HinduMythology #BhagavataPurana #ShivaPurana #TeluguDevotional",
    ),
    (
        "rashi",
        "Rashi Mantras",
        'వేద జ్యోతిష్యంలో మొత్తం 12 రాశులు ఉంటాయి -- మేషం, వృషభం, మిథునం, కర్కాటకం, సింహం, కన్య, తుల, వృశ్చికం, ధనుస్సు, మకరం, కుంభం, మీనం. ఒక్కో రాశికి ఒక పాలక గ్రహం ఉంటుంది, ఆ గ్రహాన్ని శాంతపరచడానికి, శుభఫలితాలు పొందడానికి ఒక్కో రాశికి ఒక నిర్దిష్ట మంత్రం చెప్పబడింది -- ఉదాహరణకు కుజుడు మేష, వృశ్చిక రాశులకు, శుక్రుడు వృషభ, తుల రాశులకు, బుధుడు మిథున, కన్య రాశులకు పాలకులు. ఈ ప్లేలిస్ట్\u200cలో మేము ప్రతి వీడియోలో ఒక్కో రాశి మంత్రాన్ని, దాని పాలక గ్రహాన్ని, సరైన పఠన విధానాన్ని వివరిస్తాం, 12 రాశులను వరసగా రొటేట్ చేస్తూ.\n\nమంత్రాన్ని ఎంత సార్లు పఠించాలి, ఏ సమయంలో పఠించడం మంచిది, పఠించేటప్పుడు ఏ దిక్కుకు తిరిగి కూర్చోవాలి వంటి ప్రాక్టికల్ వివరాలు కూడా ప్రతి వీడియోలో భాగంగా ఉంటాయి. గ్రహ దోషాలు, శని దోషం, కుజ దోషం వంటివి ఉన్నవారు తమ రాశి మంత్రాన్ని నిత్యం పఠించడం ద్వారా ఉపశమనం పొందవచ్చని జ్యోతిష్య శాస్త్రం చెబుతుంది. మీ రాశి ఏదో తెలుసుకోవాలంటే మీ జన్మ నక్షత్రం లేదా చంద్ర రాశిని బట్టి నిర్ణయించాలి, పుట్టిన తేదీ ఆధారంగా సూర్య రాశిని కూడా చూడవచ్చు. పాశ్చాత్య జ్యోతిష్యంలో చెప్పే సూర్య రాశికి, వేద జ్యోతిష్యంలో చెప్పే చంద్ర రాశికి మధ్య కొంచెం తేడా ఉంటుంది, అందుకే చాలా మందికి తమ వేద రాశి ఏదో సరిగ్గా తెలియదు -- ఈ ప్లేలిస్ట్ ద్వారా అన్ని రాశుల గురించి తెలుసుకుంటే, మీ సరైన రాశి ఏదో కూడా స్పష్టంగా అర్థమవుతుంది.\n\n12 రాశులు, వాటి పాలక గ్రహాలు ఇలా ఉంటాయి -- మేషం, వృశ్చికం: కుజుడు; వృషభం, తుల: శుక్రుడు; మిథునం, కన్య: బుధుడు; కర్కాటకం: చంద్రుడు; సింహం: సూర్యుడు; ధనుస్సు, మీనం: గురుడు; మకరం, కుంభం: శని. ప్రతి రాశికి ఒక రంగు, ఒక రత్నం, ఒక అనుకూల దిక్కు కూడా సంప్రదాయంలో చెప్పబడింది, వీటిని కూడా వీడియోలలో ప్రస్తావిస్తాం. మీ రాశి మంత్రాన్ని ప్రతిరోజూ ఉదయం స్నానం చేసిన తర్వాత, ప్రశాంతమైన మనసుతో పఠించడం ఉత్తమం అని జ్యోతిష్య గ్రంథాలు సూచిస్తాయి.\n\nఈ ప్లేలిస్ట్ 12 రాశులను ఒక్కొక్కటిగా కవర్ చేస్తుంది, ఆపై మళ్లీ మొదటి నుండి రొటేట్ అవుతుంది, కాబట్టి మీ రాశి వీడియో కొన్ని రోజుల్లో మళ్లీ వస్తుంది. కామెంట్\u200cలో మీ రాశి ఏదో తెలియజేయండి, సబ్\u200cస్క్రైబ్ చేసి నోటిఫికేషన్ ఆన్ చేసుకుంటే మీ రాశి వీడియో వచ్చినప్పుడు మీకు తెలుస్తుంది. #రాశిమంత్రం #జ్యోతిష్యం #వేదఆస్ట్రాలజీ'
        "\n\n"
        "Vedic astrology recognizes 12 rashis (zodiac signs) -- Mesha, Vrishabha, Mithuna, Karkataka, Simha, Kanya, Tula, Vrishchika, Dhanassu, Makara, Kumbha and Meena -- and each one is ruled by a specific planet. Mars rules Mesha and Vrishchika, Venus rules Vrishabha and Tula, Mercury rules Mithuna and Kanya, and so on through all nine grahas. Every rashi has its own traditional mantra, chanted specifically to please that ruling planet and draw out its favorable effects. This playlist dedicates one video to each rashi in turn, explaining its ruling planet and the correct way to chant its mantra, cycling through all 12 signs one at a time.\n\nEach video also covers practical details often left out elsewhere -- how many times to repeat the mantra, the best time of day to chant it, and which direction to face while doing so. Classical astrology holds that people dealing with graha doshas -- Shani dosha, Kuja dosha and similar planetary afflictions -- can find relief through consistent chanting of their rashi's mantra. If you're unsure of your own rashi, it's determined by your Moon's position at birth (your janma nakshatra), though many people also informally go by their Sun sign based on birth date. There's a subtle but real difference between the Sun sign used in Western astrology and the Moon-based rashi used in the Vedic system, which is why many people actually don't know their correct Vedic rashi -- watching through this playlist is a simple way to learn all twelve and work out which one is genuinely yours.\n\nHere's the full rulership list: Mesha and Vrishchika are ruled by Mars, Vrishabha and Tula by Venus, Mithuna and Kanya by Mercury, Karkataka by the Moon, Simha by the Sun, Dhanassu and Meena by Jupiter, and Makara and Kumbha by Saturn. Tradition also assigns each rashi a color, a gemstone and a favorable direction, which we touch on in the videos too. Classical texts recommend chanting your rashi mantra every morning after a bath, with a calm, focused mind, for the best results.\n\nThe playlist works through all 12 rashis and then loops back to the start, so your sign's video returns roughly once every two weeks. Tell us your rashi in the comments, and subscribe with notifications on so you don't miss it when your turn comes around again. #RashiMantra #VedicAstrology #ZodiacSigns #PlanetaryMantras",
    ),
    # Added 2026-10-03: full-length devotional SONGS (not Shorts) --
    # the first AI-generated-visuals series on the channel, starting
    # with Dasara Navaratri 2026 Day 1.
    (
        "navaratri_songs",
        "Dussehra Navaratri Songs 2026 | దసరా నవరాత్రి పాటలు 2026",
        (
            "దసరా నవరాత్రుల సందర్భంగా అమ్మవారి తొమ్మిది రూపాలను స్తుతిస్తూ మేము అందిస్తున్న "
            "భక్తి గీతాల ప్లేలిస్ట్ ఇది. ప్రతి పాట స్వీయ రచన, స్వీయ స్వరకల్పనతో రూపొందించబడింది -- "
            "సాహిత్యం కొత్తగా రాయబడింది, గానం మా కుటుంబ సభ్యురాలి స్వంత స్వరంతో (AI-ఆధారిత సంగీత "
            "సాధనాల సహాయంతో రికార్డ్ చేయబడింది), దృశ్యాలు కూడా AI సాధనాలతో రూపొందించబడ్డాయి -- "
            "ప్రతి పాట పూర్తిగా మా స్వంత సృజనే.\n\n"
            "మొదటి పాట, 'స్వర్ణకవచధారిణి కనకదుర్గమ్మా', విజయవాడ ఇంద్రకీలాద్రిపై వెలసిన శ్రీ "
            "కనకదుర్గమ్మ తల్లిపై రచించబడింది -- నవరాత్రుల తొలి రోజు పూజకు అంకితం. ఈ తొమ్మిది రోజుల్లో "
            "ఒక్కో రోజుకు ఒక్కో అమ్మవారి రూపాన్ని స్తుతిస్తూ కొత్త పాట వస్తుంది కాబట్టి, భక్తి పూజా "
            "సమయంలో ప్లే చేసుకోవడానికి ఈ ప్లేలిస్ట్\u200cని అనుసరించండి.\n\n"
            "మా ఛానల్\u200cని సబ్‌స్క్రైబ్ చేసి బెల్ ఐకాన్ నొక్కండి -- ఈ నవరాత్రుల్లో రాబోయే ప్రతి "
            "కొత్త పాట వెంటనే మీకు తెలిసేలా.\n\n"
            "---\n\n"
            "Original devotional songs for Dasara Navaratri, each one celebrating a form of "
            "the Goddess across the nine nights. Every song here is an original composition -- "
            "freshly written lyrics, sung in the channel family's own voice (recorded with "
            "AI-assisted music production tools), with visuals created using AI generation "
            "tools. Each piece is wholly original work.\n\n"
            "The first song, 'Swarnakavachadharini Kanakadurgamma', honors Goddess Kanaka "
            "Durga enshrined atop Indrakeeladri hill in Vijayawada, released for Navaratri "
            "Day 1. A new song follows through the nine nights, one for each form of the "
            "Devi -- follow this playlist and play it during your daily puja.\n\n"
            "Subscribe with the bell on so you don't miss a day. #DasaraNavaratri2026 "
            "#NavaratriSongs #TeluguDevotionalSongs #DurgaDevi"
        ),
    ),
]


def main() -> int:
    settings = get_settings()

    try:
        from googleapiclient.errors import HttpError
    except ImportError as exc:
        print(f"Missing packages: {exc}. Run: pip install google-api-python-client", file=sys.stderr)
        return 1

    uploader = YouTubeShortsUploader(settings)
    try:
        youtube = uploader._build_service()  # noqa: SLF001 -- deliberate reuse, this IS a setup script
    except YouTubeUploadError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    print("Fetching this channel's existing playlists...")
    existing_by_title: dict[str, str] = {}
    page_token = None
    while True:
        request = youtube.playlists().list(
            part="snippet", mine=True, maxResults=50, pageToken=page_token,
        )
        response = request.execute()
        for item in response.get("items", []):
            existing_by_title[item["snippet"]["title"]] = item["id"]
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    results: dict[str, str] = {}
    for key, title, description in PLAYLISTS_TO_CREATE:
        if title in existing_by_title:
            playlist_id = existing_by_title[title]
            try:
                youtube.playlists().update(
                    part="snippet",
                    body={
                        "id": playlist_id,
                        "snippet": {"title": title, "description": description},
                    },
                ).execute()
                print(f"Already exists, description synced: \"{title}\" -> {playlist_id}")
            except HttpError as exc:
                print(f"Already exists but FAILED to sync description for \"{title}\": {exc}", file=sys.stderr)
        else:
            try:
                response = youtube.playlists().insert(
                    part="snippet,status",
                    body={
                        "snippet": {"title": title, "description": description},
                        "status": {"privacyStatus": "public"},
                    },
                ).execute()
                playlist_id = response["id"]
                print(f"Created: \"{title}\" -> {playlist_id}")
            except HttpError as exc:
                print(f"FAILED to create \"{title}\": {exc}", file=sys.stderr)
                return 1
        results[key] = playlist_id

    print("\n=== Copy these into GitHub repo secrets (Settings -> Secrets and variables -> Actions) ===")
    for key, playlist_id in results.items():
        print(f"MAHANAVI_PLAYLIST_ID_{key.upper()}={playlist_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
