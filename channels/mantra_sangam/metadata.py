"""Everything YouTube sees besides the pixels for Divine Mantra Sangam. Hindi-only content
(text_secondary is blank in every row) -- there is no English/localization block here, unlike
the bilingual channels in this repo."""
import os

CHANNEL = "Divine Mantra Sangam"
CAT_WORD = {"mantra": "Mantra", "quote": "Teaching", "aarti": "Aarti"}
CAT_TAGS = {
    "mantra": ["#Mantra", "#OmNamahShivaya", "#HinduMantra"],
    "quote": ["#SpiritualQuotes", "#HinduTeachings", "#BhagavadGita"],
    "aarti": ["#Aarti", "#HinduAarti", "#Bhakti"],
}
COMMON_TAGS = ["#HindiDevotional", "#भक्ति", "#आरती", "#मंत्र", "#सनातनधर्म", "#Spirituality"]
CORE_TAGS = ["#DivineMantraSangam", "#Shorts", "#Hindu"]
KEYWORDS = ["Hindi mantra", "Hindu mantra shorts", "daily mantra", "aarti shorts", "bhakti shorts",
            "Hindi devotional shorts", "spiritual shorts Hindi", "Om Namah Shivaya", "Hare Krishna mantra",
            "हिंदी मंत्र", "भक्ति शॉर्ट्स", "आरती", "सनातन धर्म"]
EXTRA_KEYWORDS = {
    "mantra": ["powerful mantra", "mantra chanting"],
    "quote": ["Bhagavad Gita quotes Hindi", "spiritual wisdom Hindi"],
    "aarti": ["popular aarti", "aarti lyrics"],
}
COMMENTS = {
    "mantra": "ॐ नमः शिवाय। कमेंट में जय श्री राम लिखें। \U0001F64F",
    "quote": "यह बात आपके दिल को छू गई? नीचे बताएं। \U0001F64F",
    "aarti": "आरती के साथ जय बोलो! \U0001F64F",
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
    out += [f"{CHANNEL} -- every day a mantra, teaching, or aarti moment, in Hindi.", ""]
    out += [DISCLOSURE, "", f"Source: {row['source']}", ""]
    out += [f"Like, share and subscribe to {CHANNEL} for a daily moment of bhakti.", ""]
    out += [f"© {CHANNEL}. Traditional mantras/aartis are shared with attribution for devotional purposes."]
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
