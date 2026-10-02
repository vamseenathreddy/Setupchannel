"""
SEO content for the long-form Puranam reading videos (scrolling Telugu
text over a rotating deity background image) -- genuinely different
format and audience-reach goal from the Shorts (content/alert_seo.py):
these are landscape, 8+ minute videos meant to carry mid-roll ads, so
title/description conventions differ (full ~100-char title budget
usable, no "first 3 hashtags show above the title" Shorts-specific
behavior to design around).

BILINGUAL SPLIT (per explicit request): title and description roughly
half Telugu / half English, so both language audiences can discover
this via search. The on-screen SCROLLING TEXT ITSELF stays 100% Telugu
per the same explicit request -- this module only covers the metadata
around the video, never the narrated content.

BENEFIT-LED TITLE (per explicit request): the title highlights the
specific benefit ("phala shruti") of listening to the story, not just
the deity's name -- e.g. "the story that removes fear of snakes",
matching what the story itself traditionally states.
"""

from __future__ import annotations

from dataclasses import dataclass

_CHANNEL_FOOTER_TE = """
మా ఛానల్‌లో మరిన్ని భక్తి వీడియోలు చూడండి:
🎬 వీడియోలు: https://www.youtube.com/@MahanaviSpirituals/videos
📱 షార్ట్స్: https://www.youtube.com/@MahanaviSpirituals/shorts

మహానవి స్పిరిచువల్స్ - తెలుగు భక్తి ఛానల్. ప్రతిరోజు పంచాంగం, పురాణ కథలు, మంత్రాలు మరియు భక్తి సమాచారం అందిస్తాము.

ప్రతిరోజు పురాణ కథల కోసం సబ్‌స్క్రైబ్ చేయండి.""".strip()

_CHANNEL_FOOTER_EN = """
Watch more devotional videos on our channel:
🎬 Videos: https://www.youtube.com/@MahanaviSpirituals/videos
📱 Shorts: https://www.youtube.com/@MahanaviSpirituals/shorts

Mahanavi Spirituals is a Telugu devotional channel. We bring you daily Panchangam, Puranam stories, mantras, and devotional content.

Subscribe for daily Puranam stories.""".strip()


@dataclass(frozen=True, slots=True)
class PuranaVideoSeoContent:
    title: str
    description: str
    hashtags: list[str]

    def full_caption(self) -> str:
        return f"{self.description}\n\n{' '.join(self.hashtags)}"


def build_purana_video_seo(
    story_title_te: str,
    benefit_te: str,
    benefit_en: str,
    purana_name_te: str,
    purana_name_en: str,
    story_summary_te: str,
    story_summary_en: str,
    hashtags: list[str],
    next_purana_name_te: str | None = None,
    next_purana_name_en: str | None = None,
) -> PuranaVideoSeoContent:
    """General builder for any episode's SEO content. story_title_te is
    just the story's own name (e.g. "మనసాదేవి కథ") -- the title itself
    is assembled here, led by the benefit rather than just the name."""
    title = f"{benefit_te} - {benefit_en} | {purana_name_en}"

    description_te = f"{story_summary_te} ఈ కథ అష్టాదశ పురాణాలలో ఒకటైన {purana_name_te} నుండి తీసుకోబడింది."
    description_en = f"{story_summary_en} This story is from {purana_name_en}, one of the 18 Puranas."

    if next_purana_name_te and next_purana_name_en:
        description_te += f" మా తదుపరి వీడియో {next_purana_name_te} నుండి ఉంటుంది."
        description_en += f" Our next video will be from {next_purana_name_en}."

    description = f"{description_te}\n\n{_CHANNEL_FOOTER_TE}\n\n---\n\n{description_en}\n\n{_CHANNEL_FOOTER_EN}"

    return PuranaVideoSeoContent(title=title, description=description, hashtags=hashtags)


def build_shiva_tandava_video_seo() -> PuranaVideoSeoContent:
    """SEO content for episode 2 (Shiva's Ananda Tandava and Vishwarupa,
    from Sri Kurma Puranam). No stated phalasruti in this specific
    passage (unlike Manasadevi), so the title leads with the story's
    own significance instead of a stated benefit."""
    return build_purana_video_seo(
        story_title_te="శివ తాండవం",
        benefit_te="శివ తాండవం - శివుడి విశ్వరూప దర్శనం",
        benefit_en="Shiva's Cosmic Dance & Universal Form",
        purana_name_te="శ్రీ కూర్మ పురాణం",
        purana_name_en="Sri Kurma Puranam",
        story_summary_te=(
            "యోగేశ్వరుడైన పరమశివుడు ఆనంద తన్మయత్వంతో చేసే దివ్యనృత్యమే ఆనంద తాండవం. ఈ వీడియోలో "
            "పరమేశ్వరుడు ఆకాశంలో చేసిన ఆనంద తాండవాన్ని, ఆ తరువాత మహర్షులకు ప్రత్యక్షమైన ఆయన అద్భుతమైన "
            "విశ్వరూపాన్ని తెలుసుకుందాం. వేయి శీర్షాలు, వేయి చేతులు, వేయి పాదాలు కలిగిన ఆ దివ్యరూపాన్ని "
            "వర్ణించే పవిత్ర శ్లోకాలు ఈ వీడియోలో వినవచ్చు. నిద్రను విడిచిపెట్టి, ప్రాణాయామాన్ని ఆచరించి, "
            "ఇంద్రియ నిగ్రహాన్ని పెంపొందించుకున్న భక్తులు మాత్రమే ఈ జ్యోతి స్వరూపుడైన మహాయోగీశ్వరుణ్ణి "
            "దర్శించగలరని పురాణం చెబుతోంది. ఈ విశ్వరూపాన్ని దర్శించిన సనత్కుమారుడు, సనకుడు, భృగువు, "
            "సనాతనుడు, సనందుడు, రుద్రుడు, అంగిరసుడు, వామదేవుడు, శుక్రుడు, అత్రి, కపిల, మరీచ్యాది "
            "మహర్షులందరూ పరిపూర్ణమైన ఆనందంతో పరమేశ్వరుడిని స్తుతిస్తూ 'మహర్షులు చేసిన శివుడి విశ్వరూప "
            "స్తుతి' అనే ఇరవై శ్లోకాల పవిత్ర స్తోత్రాన్ని ఆలపించారు. ఈ స్తుతిలో పరమేశ్వరుడిని సాక్షాత్తు "
            "పరబ్రహ్మంగా, సర్వేశ్వరుడిగా, యోగీశ్వరుడిగా, ఓంకార స్వరూపుడిగా, సకల వేదాలచే స్తుతించబడేవాడిగా "
            "కీర్తించారు. మహర్షుల స్తుతిని ఆలకించిన పరమేశ్వరుడు తన విశ్వరూపాన్ని ఉపసంహరించుకుని, తిరిగి "
            "యథారూపాన్ని ధరించి, తన యథార్థ ప్రభావాన్ని గురించి మహర్షులకు బోధించడం మొదలుపెట్టాడు. ఈ కథ, "
            "ఈ పవిత్ర స్తుతి శ్రీ కూర్మ మహాపురాణం నుండి తీసుకోబడింది. శివతత్వం, శివుడి విశ్వరూపం, "
            "శివస్తుతి, ఆనంద తాండవం, యోగశాస్త్రం, పరబ్రహ్మ స్వరూపం వంటి అంశాలపై ఆసక్తి ఉన్న శివభక్తులకు "
            "ఈ వీడియో ప్రత్యేకంగా ఉపయోగపడుతుంది. తెలుగు భక్తులకు పురాణ కథలను సులభంగా, ఆసక్తికరంగా, "
            "సరళమైన భాషలో అందించాలనే లక్ష్యంతో మహానవి స్పిరిచువల్స్ ఛానల్ ఈ వీడియోను రూపొందించింది. "
            "పురాణాలలో ఉన్న ఇలాంటి ఎన్నో కథలను, మంత్రాలను, స్తోత్రాలను ప్రతిరోజు మీకు అందించడమే మా లక్ష్యం."
        ),
        story_summary_en=(
            "Lord Shiva, the supreme yogi, performs a divine dance of pure bliss known as Ananda "
            "Tandava. In this video, we explore this cosmic dance performed in the sky, and the "
            "extraordinary universal form (Vishwarupa) that Lord Shiva revealed to the great sages "
            "afterward -- a form with a thousand heads, a thousand arms, and a thousand feet. This "
            "video includes the sacred verses describing this divine form. The Puranas say that only "
            "devotees who give up sleep, practice pranayama, and master control of the senses can "
            "behold this radiant, universal Yogeshwara. Witnessing this Vishwarupa, great sages "
            "including Sanatkumara, Sanaka, Bhrigu, Sanatana, Sananda, Rudra, Angirasa, Vamadeva, "
            "Shukra, Atri, Kapila, and Marichi were overwhelmed with bliss and sang a sacred "
            "twenty-verse hymn praising Parameshwara as the Supreme Brahman, Lord of all, the eternal "
            "Yogeshwara, the very embodiment of Om, and the one praised by all the Vedas themselves. "
            "After hearing this hymn of praise, Lord Shiva withdrew his cosmic form, resumed his "
            "familiar form, and began teaching the sages about his true, essential glory. This story "
            "and its sacred hymn are from Sri Kurma Mahapuranam. If you are interested in Shiva "
            "tattva, Lord Shiva's universal form, hymns of praise to Shiva, the Ananda Tandava, the "
            "philosophy of yoga, or the nature of the Supreme Brahman as described in the Puranas, "
            "this video is especially for you. Mahanavi Spirituals brings you these timeless Puranic "
            "stories in simple, engaging Telugu narration, with the goal of making ancient wisdom "
            "accessible to devotees everywhere. Our mission is to bring you one such story, mantra, "
            "or stotram from the Puranas every single day."
        ),
        hashtags=["#ShivaTandavam", "#శివతాండవం", "#విశ్వరూపం", "#Shiva", "#TeluguDevotional"],
        next_purana_name_te="వామన పురాణం",
        next_purana_name_en="Vamana Puranam",
    )


def build_panini_charitra_video_seo() -> PuranaVideoSeoContent:
    """SEO content for episode 3 (Panini's story -- how the Maheshwara
    Sutras, the foundation of Sanskrit grammar, were revealed by Shiva's
    damaru -- from Sri Bhavishya Puranam). No stated phalasruti in this
    passage, so the title leads with the story's own significance."""
    return build_purana_video_seo(
        story_title_te="పాణిని చరిత్ర",
        benefit_te="పాణిని చరిత్ర",
        benefit_en="How Sanskrit Grammar Was Born from Shiva's Damaru",
        purana_name_te="శ్రీ భవిష్య పురాణం",
        purana_name_en="Sri Bhavishya Puranam",
        story_summary_te=(
            "సంస్కృత వ్యాకరణానికి పితామహుడైన పాణిని మహర్షి కథ ఈ వీడియోలో తెలుసుకుందాం. కణాదుడి "
            "శిష్యులతో జరిగిన శాస్త్రవాదంలో ఓడిపోయిన పాణిని, ఆ అవమానాన్ని భరించలేక తీర్థయాత్రకు "
            "బయలుదేరాడు. దారిలో అనేక పుణ్యక్షేత్రాలను దర్శిస్తూ చివరికి కేదారధామం చేరుకున్న ఆయన, "
            "పరమేశ్వరుడి కోసం ఇరవై ఎనిమిది రోజులు కఠోరమైన తపస్సు చేసాడు. ఆహారం, నీరు కూడా వదిలిన ఆ "
            "తపస్సుకు మెచ్చిన పరమశివుడు పార్వతీదేవితో సహా ప్రత్యక్షమై వరం కోరుకోమన్నాడు. "
            "పరమానందభరితుడైన పాణిని వ్యాకరణశాస్త్రాన్ని రచించే శక్తిని కోరగా, దయాసముద్రుడైన "
            "పరమేశ్వరుడు తన ఢమరుక నాదం ద్వారా అక్షరాల్ని వినిపించి, వాటిని సూత్రాల రూపంలో పాణినికి "
            "అందించాడు. ఇవే మాహేశ్వర సూత్రాలు — సంస్కృత భాషకు వ్యాకరణ పునాది. ఈ సూత్రాల ఆధారంగానే "
            "పాణిని మహర్షి అష్టాధ్యాయి అనే మహావ్యాకరణ గ్రంథాన్ని రచించాడు, తరువాత పతంజలి మహర్షి "
            "దీనికి మహాభాష్యాన్ని, వరరుచి వార్తికాలను రచించారు. వరం ఇచ్చిన తరువాత పరమేశ్వరుడు "
            "పాణినికి జ్ఞానం, రాగద్వేషాలు, మానసతీర్థం గురించి కూడా విలువైన బోధ చేసాడు. ఈ కథ శ్రీ "
            "భవిష్య పురాణం నుండి తీసుకోబడింది. సంస్కృత వ్యాకరణం, పాణిని మహర్షి చరిత్ర, మాహేశ్వర "
            "సూత్రాలు, అష్టాధ్యాయి, శివతపస్సు, కేదారధామం వంటి అంశాలపై ఆసక్తి ఉన్నవారికి ఈ వీడియో "
            "ప్రత్యేకంగా ఉపయోగపడుతుంది. కష్టపడి, పట్టుదలతో సాధన చేస్తే ఎంతటి అవమానాన్నైనా అధిగమించి "
            "గొప్ప విజయాన్ని సాధించవచ్చని ఈ కథ నేర్పుతుంది. తెలుగు భక్తులకు పురాణ కథలను సులభంగా, "
            "ఆసక్తికరంగా, సరళమైన భాషలో అందించాలనే లక్ష్యంతో మహానవి స్పిరిచువల్స్ ఛానల్ ఈ వీడియోను "
            "రూపొందించింది. పురాణాలలో ఉన్న ఇలాంటి ఎన్నో కథలను ప్రతిరోజు మీకు అందించడమే మా లక్ష్యం."
        ),
        story_summary_en=(
            "In this video, we explore the story of sage Panini, the father of Sanskrit grammar. "
            "After being defeated in a scholarly debate by the disciples of sage Kanada, Panini could "
            "not bear the humiliation and set out on a pilgrimage, visiting many sacred sites along "
            "the way and eventually reaching the sacred site of Kedar. There, he undertook "
            "twenty-eight days of intense penance for Lord Shiva, giving up food and eventually even "
            "water. Moved by this austerity, Lord Shiva appeared before him together with Goddess "
            "Parvati and offered a boon. Overwhelmed with joy, Panini asked for the power to compose "
            "a treatise on grammar. The compassionate Lord Shiva then sounded his damaru (drum), "
            "revealing sacred syllables in the form of sutras -- these became known as the Maheshwara "
            "Sutras, the very foundation of Sanskrit grammar. Using these sutras, sage Panini composed "
            "the Ashtadhyayi, the definitive treatise on Sanskrit grammar, upon which sage Patanjali "
            "later wrote his Mahabhashya commentary, and Vararuchi wrote the Varttikas. Before "
            "vanishing, Lord Shiva also shared valuable teachings with Panini about true knowledge and "
            "the inner pilgrimage of the mind. This story is from Sri Bhavishya Puranam. If you are "
            "interested in Sanskrit grammar, the life of sage Panini, the Maheshwara Sutras, the "
            "Ashtadhyayi, penance to Lord Shiva, or the sacred site of Kedar, this video is especially "
            "for you. This story teaches that with hard work and determination, even the deepest "
            "humiliation can be overcome to achieve greatness. Mahanavi Spirituals brings you these "
            "timeless Puranic stories in simple, engaging Telugu narration, with the goal of making "
            "ancient wisdom accessible to devotees everywhere. Our mission is to bring you one such "
            "story from the Puranas every single day."
        ),
        hashtags=["#Panini", "#పాణిని", "#మాహేశ్వరసూత్రాలు", "#SanskritGrammar", "#TeluguDevotional"],
        next_purana_name_te="నారద పురాణం",
        next_purana_name_en="Narada Puranam",
    )


def build_manasadevi_video_seo() -> PuranaVideoSeoContent:
    """SEO content for this specific episode (Manasadevi's story, from
    Sri Brahmavaivarta Puranam). Kept as a fixed wrapper (rather than
    requiring the caller to know every field) since this episode's
    content is fixed and already verified."""
    return build_purana_video_seo(
        story_title_te="మనసాదేవి కథ",
        benefit_te="సర్పభయం పోగొట్టే మనసాదేవి కథ",
        benefit_en="Story That Removes Snake Fear",
        purana_name_te="శ్రీ బ్రహ్మవైవర్త పురాణం",
        purana_name_en="Sri Brahmavaivarta Puranam",
        story_summary_te=(
            "పూర్వకాలంలో సర్పాల వలన మానవులు పడుతున్న బాధలను చూసిన మహర్షులు బ్రహ్మదేవుడిని ప్రార్థించగా, "
            "కశ్యపప్రజాపతి తన దివ్యశక్తితో నాగదేవత మనసాదేవిని సృష్టించాడు. మనసాదేవి పరమశివుడిని పూజించి "
            "శ్రీకృష్ణ అష్టాక్షర మంత్రాన్ని పొందింది, అలాగే మృతసంజీవని విద్యను కూడా సాధించింది. తరువాత ఆమెకు "
            "జరత్కారు మహర్షితో వివాహం జరిగింది. ఒకనాడు జరత్కారుడు నిద్రలో ఉండగా, మనసాదేవి ఆయనను సంధ్యావందనం "
            "సమయం మించిపోతుందని నిద్రలేపడంతో, ఆగ్రహించిన మహర్షి ఆమెను విడిచి వెళ్ళిపోతానని పలికాడు. అయితే "
            "బ్రహ్మదేవుడి సూచనతో, వెళ్ళే ముందు ఆయన మనసాదేవికి ఒక కుమారుణ్ణి ప్రసాదించాడు. వారి కుమారుడే గొప్ప "
            "మహర్షి ఆస్తీకుడు. ఆస్తీక మహర్షి పరమేశ్వరుడి వద్ద వేదాలు, శాస్త్రాలు అభ్యసించి మహాజ్ఞానిగా మారాడు. "
            "కాలాంతరంలో జనమేజయ మహారాజు చేస్తున్న సర్పయాగాన్ని ఆపి, సర్పజాతిని సంపూర్ణ నాశనం నుండి రక్షించిన "
            "వృత్తాంతం ఈ కథలో ప్రధానాంశం. ఈ సేవకు కృతజ్ఞతగా దేవేంద్రుడు మనసాదేవిని పూజించి, ఆమె మంత్రాన్ని జపించి "
            "స్తుతించాడు. ఈ వీడియోలో మనసాదేవి ద్వాదశనామ స్తోత్రం, మనసాదేవి స్తోత్రం అనే రెండు పవిత్ర స్తోత్రాలను "
            "కూడా వినవచ్చు — వీటిని నిత్యం భక్తితో పఠించేవారికి, వారి వంశంలో పుట్టబోయేవారికి కూడా సర్పభయం "
            "శాశ్వతంగా తొలగిపోతుందని పురాణం చెబుతోంది. నాగదేవత మంత్రాలు, సర్ప దోష నివారణ మంత్రాలు, పాము కాటు "
            "నుండి రక్షణ కలిగించే స్తోత్రాలు, జరత్కారు మహర్షి వృత్తాంతం, ఆస్తీక మహర్షి కథ, సర్పయాగం, జనమేజయుడి "
            "కథ వంటి అంశాలపై ఆసక్తి ఉన్న భక్తులకు ఈ వీడియో ప్రత్యేకంగా ఉపయోగపడుతుంది. తెలుగు భక్తులకు పురాణ "
            "కథలను సులభంగా, ఆసక్తికరంగా, సరళమైన భాషలో అందించాలనే లక్ష్యంతో మహానవి స్పిరిచువల్స్ ఛానల్ ఈ "
            "వీడియోను రూపొందించింది. పురాణాలలో ఉన్న ఇలాంటి ఎన్నో కథలను, మంత్రాలను, స్తోత్రాలను ప్రతిరోజు "
            "మీకు అందించడమే మా లక్ష్యం."
        ),
        story_summary_en=(
            "Long ago, when humans suffered greatly from snakebites, sages prayed to Lord Brahma for "
            "protection. Sage Kashyapa then created the serpent goddess Manasadevi through his divine "
            "power. Manasadevi worshipped Lord Shiva and received the sacred Krishna Ashtakshara mantra, "
            "as well as the rare Mrita Sanjeevani vidya (knowledge of reviving the dead). She was later "
            "married to the great sage Jaratkaru. One evening, while Jaratkaru was sleeping, Manasadevi "
            "woke him so he would not miss his evening prayers -- but this angered him, and he declared "
            "he would leave her. On Lord Brahma's guidance, before leaving, he blessed her with a son. "
            "That son was the great sage Astika, who studied the Vedas and scriptures under Lord Shiva "
            "himself and became a man of immense wisdom. Years later, Astika intervened in King "
            "Janamejaya's snake sacrifice (Sarpa Yaga) and saved the entire serpent race from complete "
            "destruction -- the central turning point of this story. In gratitude, Indra, king of the "
            "devas, worshipped Manasadevi and recited her sacred mantra in praise. This video also "
            "includes two sacred hymns -- the Manasadevi Dwadasanama Stotram (twelve names of "
            "Manasadevi) and the Manasadevi Stotram -- both traditionally believed to permanently "
            "remove the fear of snakes, for the devotee and their entire lineage, when recited with "
            "devotion. If you are interested in serpent deity mantras, protection from snakebite, the "
            "story of sage Jaratkaru and Astika, the Sarpa Yaga of King Janamejaya, or sacred Puranic "
            "stotrams in general, this video is for you. Mahanavi Spirituals brings you these timeless "
            "Puranic stories in simple, engaging Telugu narration, with the goal of making ancient "
            "wisdom accessible to devotees everywhere. Our mission is to bring you one such story, "
            "mantra, or stotram from the Puranas every single day."
        ),
        hashtags=["#Puranam", "#మనసాదేవి", "#అష్టాదశపురాణాలు", "#Manasadevi", "#TeluguDevotional"],
        next_purana_name_te="కూర్మ పురాణం",
        next_purana_name_en="Kurma Puranam",
    )


def build_samudrika_shastra_video_seo() -> PuranaVideoSeoContent:
    """SEO content for the Samudrika Shastra (physiognomy) episode.

    Deliberately NOT presented as a verbatim shloka-by-shloka reading
    (unlike episodes 1-3) -- per explicit request, this is a general,
    non-controversial overview of the tradition (attributed to sage
    Samudra and referenced across Puranic literature including Sri
    Bhavishya Puranam), kept gender-neutral and framed as traditional
    belief rather than definitive prediction, so it stays safe and
    respectful."""
    return build_purana_video_seo(
        story_title_te="సాముద్రిక శాస్త్రం",
        benefit_te="శరీర లక్షణాల ద్వారా స్వభావాన్ని తెలుసుకునే సాముద్రిక శాస్త్రం",
        benefit_en="The Ancient Science of Reading Character Through Body Signs",
        purana_name_te="శ్రీ భవిష్య పురాణం",
        purana_name_en="Sri Bhavishya Puranam",
        story_summary_te=(
            "సాముద్రిక శాస్త్రం అనేది మానవ శరీర లక్షణాలను పరిశీలించి వ్యక్తి స్వభావాన్ని, గుణగణాలను "
            "అర్థం చేసుకునే ఒక ప్రాచీన భారతీయ సంప్రదాయ విద్య. ఇది సముద్రుడు అనే మహర్షి ప్రవచించినదిగా "
            "చెప్పబడుతుంది, అందుకే దీనికి 'సాముద్రికం' అనే పేరు వచ్చింది. శ్రీ భవిష్య పురాణం వంటి "
            "పురాణాలలో శరీర లక్షణాల ప్రాధాన్యత గురించి ప్రస్తావించబడింది. ఈ వీడియోలో నుదురు, కళ్ళు, "
            "హస్తరేఖలు, వేళ్ళు వంటి అంశాలను సంప్రదాయం ఏ విధంగా చూసేదో తెలుసుకుందాం. ఇది వ్యక్తుల గురించి "
            "ఖచ్చితమైన నిర్ణయాలు తీసుకోడానికి కాదు, మన పూర్వీకుల పరిశీలనా దృష్టికోణాన్ని అర్థం "
            "చేసుకోడానికి ఉపయోగపడే ఒక సంప్రదాయ విద్యగా మేము దీన్ని అందిస్తున్నాం. హస్తరేఖా శాస్త్రం, "
            "ముఖలక్షణాలు, శరీర లక్షణాలు, భారతీయ సంప్రదాయ విద్యలు వంటి అంశాలపై ఆసక్తి ఉన్నవారికి ఈ వీడియో "
            "ప్రత్యేకంగా ఉపయోగపడుతుంది. తెలుగు భక్తులకు మన సంప్రదాయ విషయాలను సులభంగా, గౌరవప్రదంగా "
            "అందించాలనే లక్ష్యంతో మహానవి స్పిరిచువల్స్ ఛానల్ ఈ వీడియోను రూపొందించింది."
        ),
        story_summary_en=(
            "Samudrika Shastra is an ancient Indian tradition of reading a person's nature and "
            "character through physical signs -- traditionally attributed to sage Samudra, and "
            "referenced across Puranic literature including Sri Bhavishya Puranam. In this video, we "
            "look at how this tradition has historically viewed features like the forehead, the eyes, "
            "the lines of the palm, and the fingers. This is presented as a window into how our "
            "ancestors observed people and life, a traditional belief system, not a set of scientific "
            "or definitive claims about any individual. If you are interested in palmistry, "
            "physiognomy, facial features in tradition, or Indian traditional sciences in general, "
            "this video is for you. Mahanavi Spirituals brings you our traditions in simple, "
            "respectful Telugu narration, with the goal of making this heritage accessible to "
            "everyone."
        ),
        hashtags=["#SamudrikaShastra", "#సాముద్రికశాస్త్రం", "#Palmistry", "#భవిష్యపురాణం", "#TeluguDevotional"],
    )
