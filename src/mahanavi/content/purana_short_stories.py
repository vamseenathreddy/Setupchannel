"""
Static content for the "Purana Story" Shorts series -- a NEW series,
distinct from both the existing long-form scrolling Puranam videos
(scripts/post_purana_video.py, content/purana_pdf_extractor.py) and the
Rashi Mantra Shorts.

FORMAT (per explicit request, 2026-10-02): a single STATIC frame -- the
whole story, condensed, held on screen for the Short's entire duration,
with NO scrolling and NO narration/voiceover. Exact words from the
request: "static page short with all text should adjust in same frame
not scrolling... no need of reading that text because its not hearing
natural" -- i.e. the user has found that TTS narration of devotional
Telugu text doesn't sound natural, so this series (like the Rashi
Mantra series before it) is a read-it-yourself card with music only,
not narration audio.

CONTENT UNIT: each entry here is a short, SELF-CONTAINED story already
condensed to fit a single vertical frame (roughly 60-110 Telugu words),
not a passage lifted from the long-form video's much longer paragraph
sets -- those are written for 8+ minutes of scrolling, not a single
still frame. Every story is well-known and explicitly cited to one of
the 18 Mahapuranas (content/purana_selector.py's ALL_PURANAS list) by
name, consistent with this channel's existing practice of never leaving
a story's source unstated. Written fresh for this channel in plain,
accessible modern Telugu -- not a verbatim reproduction of any specific
published translation.

AUTO-FIT TEXT (per explicit request, "if little big adjust text"):
images/purana_short_card_renderer.py shrinks the story's font size (down
to a floor) to fit whatever length a given entry happens to be, rather
than requiring every entry be exactly the same length -- so entries here
can vary somewhat in length; the renderer handles it.

INVOCATION LINE (per explicit request, 2026-10-02: "above purana katha
text there should be Om namah sivaya / om namo naaraayanaaya / sri
matre namaha etc as per that story"): each entry carries the salutation
mantra of the DEITY THAT STORY IS ABOUT, shown above the series label
on the card -- not one fixed mantra for every story. Picked per story's
actual protagonist deity: a Vishnu-avatar story (Gajendra, Dhruva,
Prahlada/Narasimha, Vamana, Matsya, Kurma, Varaha) gets "ఓం నమో
నారాయణాయ"; a Shiva-centered story (Markandeya) gets "ఓం నమః శివాయ";
Ganesha's own story gets his own mantra rather than his father Shiva's;
and the one story centered on the Goddess herself (Sati) gets "శ్రీ
మాత్రే నమః" -- the exact three examples given in the request, applied
by actual protagonist rather than defaulted to one for everything.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PuranaShortStory:
    title_te: str          # short story title, e.g. "గజేంద్ర మోక్షం"
    title_en: str           # transliterated/English title, for SEO
    invocation_te: str       # this story's deity salutation, e.g. "ఓం నమో నారాయణాయ"
    story_te: str            # the condensed story itself, one block of Telugu text
    # This story's single most-searched payoff/keyword -- distinct from
    # title_te, which names the EVENT ("ధ్రువుడి తపస్సు", Dhruva's
    # penance), while this names what people actually search for/talk
    # about afterward ("ధ్రువ నక్షత్రం", the Pole Star he became).
    # Explicit request (2026-10-04): "Today it posted about druva
    # Nakshatram. In comment also it should mention about
    # druvanakshatram like that" -- the category comment
    # (category_comments.py) now surfaces THIS per-story, not the
    # generic rotating pool text alone.
    search_keyword_te: str
    moral_te: str             # one-line moral/benefit, shown in gold on the card
    moral_en: str              # English gloss of the moral, for SEO
    purana_name_te: str        # exact source, e.g. "శ్రీ భాగవత పురాణం"
    purana_name_en: str        # e.g. "Srimad Bhagavatam (Bhagavata Purana)"
    # Story-bank fields (core stories leave these at their defaults).
    topic: str = ""            # unique slug, used for no-repeat checks
    date: str | None = None    # YYYY-MM-DD (IST): post ONLY on this date; skipped in normal rotation


_GAJENDRA_STORY = (
    "త్రికూట పర్వతం దగ్గర ఒక సరస్సులో స్నానం చేస్తున్న గజేంద్రుడనే ఏనుగు రాజు కాలిని ఒక "
    "మొసలి పట్టుకుంది. ఏనుగు బలమంతా ఉపయోగించి పోరాడినా మొసలి వదల్లేదు. వేల సంవత్సరాలు ఈ "
    "పోరాటం సాగింది. తన శక్తి సరిపోదని గ్రహించిన గజేంద్రుడు, తన తొండంతో ఒక పద్మపుష్పాన్ని "
    "పట్టుకుని 'ఆదిమూలమా!' అని శ్రీమహావిష్ణువును మనస్ఫూర్తిగా వేడుకున్నాడు. భక్తుడి మొర "
    "విన్న శ్రీహరి తన వాహనమైన గరుడుడిపై క్షణంలో అక్కడికి వచ్చి, సుదర్శన చక్రంతో మొసలిని "
    "సంహరించి గజేంద్రుడిని రక్షించాడు."
)

_DHRUVA_STORY = (
    "ఉత్తానపాదుడి కుమారుడైన బాలుడు ధ్రువుడు, సవతి తల్లి మాటలకు బాధపడి తండ్రి ఒడిలో కూర్చునే "
    "హక్కు కోల్పోయాడు. దుఃఖంతో అడవికి వెళ్ళి, నారదుడి ఉపదేశంతో శ్రీమహావిష్ణువు కోసం కఠోర "
    "తపస్సు ప్రారంభించాడు. కేవలం ఐదేళ్ళ బాలుడైనా అతని నిష్ఠకు మెచ్చిన శ్రీహరి ప్రత్యక్షమై "
    "దర్శనమిచ్చాడు. తండ్రి రాజ్యం కన్నా గొప్ప వరం కోరుకున్న ధ్రువుడికి, చిరకాలం చెక్కుచెదరని "
    "స్థానాన్ని -- ధ్రువ నక్షత్రపదవిని -- ప్రసాదించాడు."
)

_PRAHLADA_STORY = (
    "రాక్షస రాజు హిరణ్యకశిపుడు తనను తప్ప ఎవరినీ కొలవరాదని శాసించినా, అతని కుమారుడు ప్రహ్లాదుడు "
    "శ్రీహరిని నిత్యం ధ్యానించేవాడు. కోపోద్రిక్తుడైన తండ్రి అనేక విధాలుగా చంపే ప్రయత్నం చేసినా "
    "విష్ణు కృపతో బాలుడికి ఏమీ కాలేదు. 'నీ దేవుడు ఈ స్తంభంలో ఉన్నాడా?' అని హిరణ్యకశిపుడు "
    "ఒక స్తంభాన్ని బద్దలుకొట్టగానే, అందులోనుంచి సగం సింహం సగం నరరూపంలో నరసింహస్వామి "
    "ఉద్భవించి, రాక్షసుడిని సంహరించి తన భక్తుడిని కాపాడాడు."
)

_MARKANDEYA_STORY = (
    "మృకండు మహర్షికి పుట్టిన మార్కండేయుడికి పదహారేళ్ళే ఆయుష్షు అని జాతకం చెప్పింది. ఆ "
    "సత్యం తెలిసినా బాలుడు భయపడక శివలింగాన్ని నిత్యం పూజిస్తూనే ఉన్నాడు. నిర్ణీత రోజున "
    "యమధర్మరాజు స్వయంగా ప్రాణం తీసుకెళ్ళటానికి రాగా, మార్కండేయుడు శివలింగాన్ని వదలకుండా "
    "గట్టిగా కావలించుకున్నాడు. భక్తుడి నిష్ఠకు మెచ్చిన పరమశివుడు ప్రత్యక్షమై యముడిని "
    "నివారించి, మార్కండేయుడికి చిరంజీవిత్వాన్ని ప్రసాదించాడు."
)

_SATI_STORY = (
    "దక్ష ప్రజాపతి తన కుమార్తె సతీదేవి భర్త అయిన పరమశివుడిని అగౌరవపరుస్తూ ఒక మహాయాగం "
    "నిర్వహించి, శివుడిని ఆహ్వానించలేదు. పిలవకున్నా పుట్టింటికి వెళ్ళిన సతీదేవి, తన తండ్రి "
    "సభలో భర్తను అవమానించటం భరించలేక, ఆ యాగాగ్నిలోనే తన శరీరాన్ని దహించుకుంది. ఈ వార్త "
    "తెలిసిన పరమశివుడు దుఃఖోద్రిక్తుడై వీరభద్రుడిని సృష్టించి దక్షయజ్ఞాన్ని ధ్వంసం చేయించాడు. "
    "సతీదేవి శరీరభాగాలు పడిన స్థలాలే నేటి 51 శక్తిపీఠాలు."
)

_GANESHA_STORY = (
    "ఒకసారి పరశురాముడు కైలాసానికి వచ్చినప్పుడు, శివుడు విశ్రాంతిలో ఉండటంతో గణేశుడు ఆయనను "
    "లోపలికి అనుమతించలేదు. కోపించిన పరశురాముడు తన గండ్రగొడ్డలిని గణేశుడిపై ప్రయోగించాడు. "
    "తండ్రి ఇచ్చిన ఆయుధాన్ని గౌరవించి, గణేశుడు దానిని తప్పించుకోకుండా తన ఒక దంతంతో "
    "స్వీకరించాడు -- అలా ఆ దంతం విరిగిపోయింది. తండ్రి ఆయుధం పట్ల గౌరవం కోసం స్వయంగా బాధను "
    "స్వీకరించిన ఈ త్యాగమే గణేశుడిని 'ఏకదంతుడు' అనే పేరుతో పూజనీయుడిగా చేసింది."
)

_VAMANA_STORY = (
    "దానవ చక్రవర్తి బలి చక్రవర్తి తన దాతృత్వానికి పేరు పొంది, ముల్లోకాలను జయించాడు. "
    "దేవతల ప్రార్థనపై శ్రీమహావిష్ణువు పొట్టి బ్రాహ్మణ బాలుడైన వామనుడిగా అవతరించి, బలి వద్దకు "
    "వెళ్ళి మూడడుగుల నేల దానం కోరాడు. బలి ఒప్పుకోగానే వామనుడు త్రివిక్రముడిగా ఎదిగి, ఒక "
    "అడుగుతో భూమిని, మరో అడుగుతో ఆకాశాన్ని ఆక్రమించాడు. మూడో అడుగుకు స్థలం లేకపోవటంతో బలి "
    "తన తలను చూపించాడు. ఆ త్యాగానికి మెచ్చి విష్ణువు బలిని పాతాళలోక చక్రవర్తిగా చేశాడు."
)

_MATSYA_STORY = (
    "సత్యవ్రతుడనే రాజు నదిలో స్నానం చేస్తుండగా ఒక చిన్న చేప అతని దోసిట్లోకి వచ్చి రక్షించమని "
    "వేడుకుంది. దయతో ఆ చేపను ఇంటికి తీసుకెళ్ళిన రాజు, అది క్రమంగా పెరిగి సముద్రమంత పెద్దదైనా "
    "చూసి ఆశ్చర్యపోయాడు. అదే స్వయంగా శ్రీమహావిష్ణువు మత్స్యావతారమని గ్రహించాడు. త్వరలో "
    "ప్రళయం వచ్చి జగత్తునంతా ముంచేస్తుందని, అప్పుడు ఒక నావను సిద్ధం చేసుకోమని మత్స్యావతారుడు "
    "హెచ్చరించాడు. ప్రళయం వచ్చినప్పుడు, వేదాలను, సప్తర్షులను, విత్తనాలను ఆ నావలో ఉంచి, "
    "మత్స్యావతారుడు స్వయంగా దానిని ఈడ్చి సృష్టిని కాపాడాడు."
)

_KURMA_STORY = (
    "దుర్వాసుడి శాపంతో దేవతలు బలహీనులై రాక్షసుల చేతిలో ఓడిపోసాగారు. అమృతం కోసం దేవదానవులు "
    "కలిసి క్షీరసాగరాన్ని మథించాలని నిశ్చయించారు. మందర పర్వతాన్ని కవ్వంగా, వాసుకిని తాడుగా "
    "ఉపయోగించగా, పర్వతం సముద్రంలో మునిగిపోసాగింది. అప్పుడు శ్రీమహావిష్ణువు కూర్మావతారం "
    "ధరించి, తన వీపుపై ఆ పర్వతాన్ని మోశాడు. చివరికి అమృతంతో పాటు లక్ష్మీదేవి, ఐరావతం వంటి "
    "అనేక దివ్య వస్తువులు ఉద్భవించాయి, దేవతలు తిరిగి బలం పొందారు."
)

_VARAHA_STORY = (
    "హిరణ్యాక్షుడనే రాక్షసుడు భూదేవిని బలవంతంగా అపహరించి సముద్రగర్భంలో దాచాడు. భూమిని "
    "రక్షించటానికి శ్రీమహావిష్ణువు మహా వరాహరూపం ధరించి సముద్రంలోకి దూకి, హిరణ్యాక్షుడితో "
    "వెయ్యేళ్ళు భీకరంగా పోరాడి అతడిని సంహరించాడు. తరువాత తన కోరలపై భూదేవిని మెల్లగా పైకి "
    "లేపి, ఆమెను యథాస్థానంలో నిలిపాడు. అందుకే వరాహస్వామిని సృష్టి రక్షకుడిగా, భూదేవి "
    "పతిగా కొలుస్తారు."
)


# Order is fixed (not alphabetical/random) so the rotation has a sensible
# arc -- Vishnu avatar stories grouped loosely with devotee stories,
# roughly the order a newcomer to these tales would naturally meet them.
PURANA_SHORT_STORIES: list[PuranaShortStory] = [
    PuranaShortStory(
        title_te="గజేంద్ర మోక్షం",
        title_en="Gajendra Moksham",
        invocation_te="ఓం నమో నారాయణాయ",
        story_te=_GAJENDRA_STORY,
        search_keyword_te="గజేంద్ర మోక్షం",
        moral_te="నిస్వార్థ భక్తికి భగవంతుడు తక్షణమే స్పందిస్తాడు",
        moral_en="God answers a devotee's sincere, selfless call instantly",
        purana_name_te="శ్రీ భాగవత పురాణం",
        purana_name_en="Srimad Bhagavatam (Bhagavata Purana)",
    ),
    PuranaShortStory(
        title_te="ధ్రువుడి తపస్సు",
        title_en="Dhruva's Penance",
        invocation_te="ఓం నమో నారాయణాయ",
        story_te=_DHRUVA_STORY,
        search_keyword_te="ధ్రువ నక్షత్రం",
        moral_te="చిన్న వయసైనా దృఢసంకల్పం ముందు అసాధ్యం కూడా సాధ్యమే",
        moral_en="Unwavering determination makes even the impossible possible, at any age",
        purana_name_te="శ్రీ విష్ణు పురాణం",
        purana_name_en="Sri Vishnu Puranam",
    ),
    PuranaShortStory(
        title_te="ప్రహ్లాద నరసింహ లీల",
        title_en="Prahlada and Narasimha",
        invocation_te="ఓం నమో నారాయణాయ",
        story_te=_PRAHLADA_STORY,
        search_keyword_te="నరసింహావతారం",
        moral_te="నిశ్చలమైన భక్తిని ఏ శక్తీ అణచలేదు",
        moral_en="No power can suppress unwavering devotion",
        purana_name_te="శ్రీ భాగవత పురాణం",
        purana_name_en="Srimad Bhagavatam (Bhagavata Purana)",
    ),
    PuranaShortStory(
        title_te="మార్కండేయుడి వరం",
        title_en="Markandeya's Boon",
        invocation_te="ఓం నమః శివాయ",
        story_te=_MARKANDEYA_STORY,
        search_keyword_te="మార్కండేయ చిరంజీవి",
        moral_te="నిశ్చలభక్తి మృత్యువును కూడా జయిస్తుంది",
        moral_en="Steadfast devotion can conquer even death itself",
        purana_name_te="శ్రీ శివ పురాణం",
        purana_name_en="Sri Shiva Puranam",
    ),
    PuranaShortStory(
        title_te="సతీదేవి త్యాగం",
        title_en="Sati's Sacrifice",
        invocation_te="శ్రీ మాత్రే నమః",
        story_te=_SATI_STORY,
        search_keyword_te="దక్షయజ్ఞం",
        moral_te="గౌరవం లేని చోట ఉండటం కన్నా నిష్క్రమించటం ధర్మం",
        moral_en="Walking away with dignity is better than staying where none is given",
        purana_name_te="శ్రీ శివ పురాణం",
        purana_name_en="Sri Shiva Puranam",
    ),
    PuranaShortStory(
        title_te="గణేశుడి విరిగిన దంతం",
        title_en="Ganesha's Broken Tusk",
        invocation_te="ఓం గం గణపతయే నమః",
        story_te=_GANESHA_STORY,
        search_keyword_te="ఏకదంతుడు",
        moral_te="పెద్దల మాటకు, వారి వస్తువుకు ఇచ్చే గౌరవమే నిజమైన వినయం",
        moral_en="True humility is the respect shown to elders and what they value",
        purana_name_te="శ్రీ బ్రహ్మవైవర్త పురాణం",
        purana_name_en="Sri Brahmavaivarta Puranam",
    ),
    PuranaShortStory(
        title_te="వామనావతారం",
        title_en="Vamana Avatara",
        invocation_te="ఓం నమో నారాయణాయ",
        story_te=_VAMANA_STORY,
        search_keyword_te="త్రివిక్రముడు",
        moral_te="నిజమైన దాతృత్వానికి ఎదురుగా అహంకారం నిలవదు",
        moral_en="True generosity leaves no room for pride to stand",
        purana_name_te="శ్రీ వామన పురాణం",
        purana_name_en="Sri Vamana Puranam",
    ),
    PuranaShortStory(
        title_te="మత్స్యావతారం",
        title_en="Matsya Avatara",
        invocation_te="ఓం నమో నారాయణాయ",
        story_te=_MATSYA_STORY,
        search_keyword_te="మత్స్యావతారం",
        moral_te="చిన్న జీవి పట్ల చూపిన దయ కూడా గొప్ప రక్షణగా తిరిగొస్తుంది",
        moral_en="Compassion shown even to the smallest life can return as great protection",
        purana_name_te="శ్రీ మత్స్య పురాణం",
        purana_name_en="Sri Matsya Puranam",
    ),
    PuranaShortStory(
        title_te="కూర్మావతారం - క్షీరసాగర మథనం",
        title_en="Kurma Avatara and the Churning of the Ocean",
        invocation_te="ఓం నమో నారాయణాయ",
        story_te=_KURMA_STORY,
        search_keyword_te="క్షీరసాగర మథనం",
        moral_te="కష్టసమయంలో ఏకమైన ప్రయత్నానికి భగవంతుడి తోడు తప్పక ఉంటుంది",
        moral_en="United effort in hard times always finds divine support",
        purana_name_te="శ్రీ కూర్మ పురాణం",
        purana_name_en="Sri Kurma Puranam",
    ),
    PuranaShortStory(
        title_te="వరాహావతారం",
        title_en="Varaha Avatara",
        invocation_te="ఓం నమో నారాయణాయ",
        story_te=_VARAHA_STORY,
        search_keyword_te="భూదేవి రక్షణ",
        moral_te="ధర్మాన్ని కాపాడటానికి భగవంతుడు ఏ రూపమైనా ధరిస్తాడు",
        moral_en="God takes any form necessary to protect righteousness",
        purana_name_te="శ్రీ వరాహ పురాణం",
        purana_name_en="Sri Varaha Puranam",
    ),
]


def _load_story_bank() -> list[PuranaShortStory]:
    """Stories saved in purana_story_bank.json (converted from the retired
    devotional-content library). Appended after the core stories above;
    never re-posted because the rotation index never wraps."""
    path = Path(__file__).with_name("purana_story_bank.json")
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [PuranaShortStory(**entry) for entry in data["stories"]]


PURANA_SHORT_STORIES = PURANA_SHORT_STORIES + _load_story_bank()
