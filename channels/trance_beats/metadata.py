"""Everything YouTube sees besides the pixels for Devotional Trance Beats. Hindi-only
content, Krishna/Radha bhajan-kirtan focus (vs Divine Mantra Sangam's mantra-chanting focus)."""
import os

CHANNEL = "Devotional Trance Beats"
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


def title(row, special):
    hi = plain(row)
    word = CAT_WORD[row["category"]]
    if special:
        hi = f"{special['label_primary']}: {hi}"
    for cand in (f"{hi} | {word} | {CHANNEL}", f"{hi} | {word}"):
        if len(cand) <= 100:
            return cand
    tail = f" | {CHANNEL}"
    cut = hi[: 100 - len(tail) - 1].rsplit(" ", 1)[0].rstrip(",.:;")
    return f"{cut}…{tail}"


def hashtags(row, special):
    tags = CORE_TAGS + CAT_TAGS[row["category"]] + COMMON_TAGS
    seen, out = set(), []
    for h in tags:
        if h.lower() not in seen:
            seen.add(h.lower())
            out.append(h)
    return out[:15]


def description(row, special, contact=None):
    contact = contact if contact is not None else os.environ.get("CONTACT_EMAIL", "")
    hi = plain(row)
    out = []
    if special:
        out += [special.get("label_primary", ""), ""]
    out += [hi, ""]
    out += [f"{CHANNEL} -- daily Krishna shorts in Hindi: Bhagavad Gita, Shrimad Bhagavatam, and a mantra or bhajan of the day.", ""]
    out += [DISCLOSURE, "", f"Source: {row['source']}", ""]
    out += [f"Like, share and subscribe to {CHANNEL} for a daily moment of bhakti.", ""]
    out += [f"© {CHANNEL}. Traditional bhajans/kirtans are shared with attribution for devotional purposes."]
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


def tags(row, special):
    return fit_tags(KEYWORDS + EXTRA_KEYWORDS[row["category"]])


def srt(text, seconds=5):
    lines = "\n".join(s.strip() for s in text.split("|"))
    return f"1\n00:00:00,000 --> 00:00:{seconds:02d},000\n{lines}\n"


def captions(row):
    return {"hi": srt(row["text_primary"].replace('"', "").replace("'", ""))}


def seed_comment(row):
    return COMMENTS[row["category"]]


def bundle(row, special):
    return {"title": title(row, special), "description": description(row, special), "tags": tags(row, special),
            "comment": seed_comment(row)}
