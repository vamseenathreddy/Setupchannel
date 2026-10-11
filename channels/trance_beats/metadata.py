"""Everything YouTube sees besides the pixels for Channel C. Hindi-only
content, Krishna/Radha bhajan-kirtan focus (vs Channel B's mantra-chanting focus)."""
from ytcore.brandcfg import C_NAME  # noqa: E402
import os
import re

CHANNEL = f"{C_NAME}"
CAT_WORD = {"bhajan": "Bhajan", "kirtan": "Kirtan", "quote": "Teaching", "gita": "Bhagavad Gita",
            "bhagavatam": "Shrimad Bhagavatam", "mantra": "Krishna Mantra"}
CAT_TAGS = {
    "bhajan": ["#Bhajan", "#KrishnaBhajan", "#RadheRadhe"],
    "kirtan": ["#Kirtan", "#HareKrishna", "#Sankirtan"],
    "quote": ["#SpiritualQuotes", "#BhagavadGita", "#KrishnaTeachings"],
    "gita": ["#BhagavadGita", "#GitaShloka", "#GeetaSaar"],
    "bhagavatam": ["#ShrimadBhagavatam", "#Bhagavatam", "#KrishnaKatha"],
    "mantra": ["#KrishnaMantra", "#HareKrishna", "#Mantra"],
}
COMMON_TAGS = ["#HindiDevotional", "#भक्ति", "#कृष्णभक्ति", "#राधाकृष्ण", "#सनातनधर्म", "#Spirituality"]
CORE_TAGS = ["#DevotionalTranceBeats", "#Shorts", "#Krishna"]
KEYWORDS = ["Krishna bhajan", "Radha Krishna bhajan", "Hindi kirtan shorts", "Hare Krishna mantra",
            "devotional trance", "bhakti shorts Hindi", "Krishna shorts", "Radhe Radhe",
            "कृष्ण भजन", "राधे राधे", "कीर्तन", "हिंदी भक्ति शॉर्ट्स"]
EXTRA_KEYWORDS = {
    "bhajan": ["popular Krishna bhajan", "bhajan lyrics Hindi"],
    "kirtan": ["Hare Krishna kirtan", "sankirtan chanting"],
    "quote": ["Bhagavad Gita Krishna quotes", "Krishna teachings Hindi"],
    "gita": ["Bhagavad Gita shloka", "Gita shlok Hindi arth", "Geeta saar"],
    "bhagavatam": ["Shrimad Bhagavatam shloka", "Bhagavat Katha shorts", "Bhagavatam Hindi"],
    "mantra": ["Krishna mantra", "Hare Krishna maha mantra", "daily mantra Hindi"],
}
COMMENTS = {
    "bhajan": "राधे राधे! \U0001F33A कमेंट में जय श्री कृष्णा लिखें।",
    "kirtan": "हरे कृष्ण! \U0001F64F साथ में कीर्तन गाओ।",
    "quote": "यह बात दिल को छू गई? नीचे बताएं। \U0001F64F",
    "gita": "जय श्री कृष्ण! \U0001F64F आज का श्लोक आपको कैसा लगा? कमेंट में बताएं।",
    "bhagavatam": "जय श्री कृष्ण! \U0001F33A आज की भागवत कथा पर अपने विचार कमेंट में लिखें।",
    "mantra": "हरे कृष्ण! \U0001F64F आज का मंत्र जपें और कमेंट में हरे कृष्ण लिखें।",
}
DISCLOSURE = "Visuals are digitally created devotional artwork. Background music is an original/royalty-free composition."
TAG_LIMIT = 500


def plain(row):
    strip = str.maketrans({c: None for c in "'\"‘’“”"})
    return row["text_primary"].translate(strip).strip()


TITLE_PREFIX = {"gita": "गीता श्लोक: ", "bhagavatam": "भागवत कथा: ", "mantra": "", "bhajan": "", "kirtan": "", "quote": ""}


def title(row, special):
    """Always carries the English series keyword (e.g. "Bhagavad Gita 2.47"); only the Hindi text
    is ever shortened to make it fit."""
    hi = plain(row)
    word = CAT_WORD[row["category"]]
    ref = verse_ref(row)
    if ref:
        word = f"{word} {ref[0]}.{ref[1]}"
    if special:
        hi = f"{special['label_primary']}: {hi}"
    pre = TITLE_PREFIX.get(row["category"], "")
    for cand in (f"{pre}{hi} | {word} | {CHANNEL}", f"{pre}{hi} | {word}", f"{hi} | {word}"):
        if len(cand) <= 100:
            return cand
    tail = f" | {word}"
    cut = hi[: 100 - len(tail) - 1].rsplit(" ", 1)[0].rstrip(",.:;")
    return f"{cut}…{tail}"


def hashtags(row, special):
    tags = CAT_TAGS[row["category"]][:2] + ["#Krishna", "#Shorts", "#DevotionalTranceBeats"] + CAT_TAGS[row["category"]][2:] + COMMON_TAGS
    seen, out = set(), []
    for h in tags:
        if h.lower() not in seen:
            seen.add(h.lower())
            out.append(h)
    return out[:15]


INTRO_HI = {
    "gita": "श्रीमद्भगवद्गीता का आज का श्लोक, सरल हिंदी अर्थ के साथ।",
    "bhagavatam": "श्रीमद्भागवत महापुराण की आज की कथा, सरल हिंदी में।",
    "mantra": "आज का कृष्ण मंत्र और भक्ति, शांत मन से सुनें और जपें।",
    "bhajan": "आज का कृष्ण भजन, भक्ति और शांति के लिए।",
    "kirtan": "आज का हरे कृष्ण कीर्तन, साथ मिलकर गाएँ।",
    "quote": "आज का कृष्ण वचन, जीवन के लिए एक सीख।",
}
INTRO_EN = {
    "gita": "Today's Bhagavad Gita shloka with a simple Hindi meaning.",
    "bhagavatam": "Today's Shrimad Bhagavatam story, told simply in Hindi.",
    "mantra": "Today's Krishna mantra for calm and devotion. Listen and chant along.",
    "bhajan": "Today's Krishna bhajan for devotion and peace.",
    "kirtan": "Today's Hare Krishna kirtan. Sing along.",
    "quote": "Today's teaching of Krishna, a lesson for life.",
}
SUBSCRIBE_HI = "रोज़ नया श्लोक, कथा और मंत्र पाने के लिए चैनल को सब्सक्राइब करें और घंटी का बटन दबाएँ।"
SERIES_HI = ("हर दिन तीन शॉर्ट्स: सुबह श्रीमद्भागवत कथा, दोपहर कृष्ण मंत्र या भजन, शाम को भगवद्गीता श्लोक।")


def description(row, special, contact=None):
    contact = contact if contact is not None else os.environ.get("CONTACT_EMAIL", "")
    cat = row["category"]
    hi, verse = plain(row), (row.get("text_secondary") or "").strip()
    out = []
    if special:
        out += [special.get("label_primary", ""), ""]
    out += [f"{hi}", f"{INTRO_HI[cat]}", ""]
    if verse:
        out += [verse, ""]
    out += [SUBSCRIBE_HI, SERIES_HI, ""]
    out += [f"{CHANNEL}: {INTRO_EN[cat]}", f"Source: {row['source']}", ""]
    out += [f"Subscribe to {CHANNEL} for a daily Krishna short in Hindi: Shrimad Bhagavatam, a mantra or bhajan, and the Bhagavad Gita.", ""]
    out += [DISCLOSURE, ""]
    out += [f"© {CHANNEL}. Traditional shlokas, bhajans and kirtans are shared with attribution for devotional purposes."]
    if contact:
        out += [f"Contact: {contact}"]
    out += ["", " ".join(hashtags(row, special))]
    return "\n".join(out)


def tag_cost(tag):
    return len(tag) + (2 if " " in tag else 0)


def fit_tags(tags, limit=TAG_LIMIT):
    out, total, seen = [], 0, set()
    for tg in tags:
        k = tg.lower()
        if k in seen:
            continue
        cost = tag_cost(tg) + (1 if out else 0)
        if total + cost > limit:
            continue
        seen.add(k)
        out.append(tg)
        total += cost
    return out


HI_KEYWORDS = {
    "gita": ["भगवद गीता श्लोक", "गीता सार", "श्रीमद्भगवद्गीता", "गीता के श्लोक अर्थ सहित"],
    "bhagavatam": ["श्रीमद्भागवत कथा", "भागवत पुराण", "भागवत कथा हिंदी", "कृष्ण लीला"],
    "mantra": ["कृष्ण मंत्र", "हरे कृष्ण महामंत्र", "मंत्र जाप", "आज का मंत्र"],
    "bhajan": ["कृष्ण भजन हिंदी", "राधा कृष्ण भजन"],
    "kirtan": ["हरे कृष्ण कीर्तन", "संकीर्तन"],
    "quote": ["कृष्ण वचन", "गीता ज्ञान"],
}


def verse_ref(row):
    m = re.search(r"गीता\s*(\d+)\.(\d+)", row.get("text_secondary", ""))
    return (m.group(1), m.group(2)) if m else None


def tags(row, special):
    extra = list(EXTRA_KEYWORDS[row["category"]])
    ref = verse_ref(row)
    if ref:
        extra = [f"Bhagavad Gita {ref[0]}.{ref[1]}", f"Gita chapter {ref[0]} verse {ref[1]}",
                 f"गीता {ref[0]}.{ref[1]}"] + extra
    return fit_tags(extra + HI_KEYWORDS.get(row["category"], []) + KEYWORDS)


def srt(text, seconds=5):
    lines = "\n".join(s.strip() for s in text.split("|"))
    return f"1\n00:00:00,000 --> 00:00:{seconds:02d},000\n{lines}\n"


def captions(row):
    return {"hi": srt(row["text_primary"].replace('"', "").replace("'", ""))}


def seed_comment(row):
    return COMMENTS[row["category"]]


def bundle(row, special):
    return {"title": title(row, special), "description": description(row, special), "tags": tags(row, special),
            "comment": seed_comment(row), "language": "hi"}
