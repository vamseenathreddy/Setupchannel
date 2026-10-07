"""Everything YouTube sees besides the pixels for InfoShorts Telugu: title, description,
tags, captions, comment. text_primary = Telugu (the fact itself), text_secondary = English
gloss. Same shape as channels/jesus/metadata.py, swapped primary/secondary language."""
import os

CHANNEL = "InfoShorts Telugu"
CAT_WORD = {"science": "Science Fact", "history": "History Fact", "nature": "Nature Fact",
            "space": "Space Fact", "india": "India Fact"}
CAT_TAGS = {
    "science": ["#ScienceFacts", "#DidYouKnow"],
    "history": ["#HistoryFacts", "#DidYouKnow"],
    "nature": ["#NatureFacts", "#DidYouKnow"],
    "space": ["#SpaceFacts", "#Astronomy"],
    "india": ["#IndiaFacts", "#IncredibleIndia"],
}
COMMON_TAGS = ["#TeluguFacts", "#InfoShorts", "#తెలుగు", "#విషయాలు", "#GK", "#AmazingFacts"]
CORE_TAGS = ["#InfoShortsTelugu", "#Shorts", "#Facts"]
KEYWORDS = ["Telugu facts", "amazing facts Telugu", "unknown facts Telugu", "GK facts Telugu",
            "science facts Telugu", "history facts Telugu", "space facts Telugu", "India facts Telugu",
            "తెలుగు విషయాలు", "ఆసక్తికర విషయాలు", "సైన్స్ facts", "చరిత్ర facts"]
EXTRA_KEYWORDS = {
    "science": ["science trivia", "science GK"],
    "history": ["history trivia", "world history facts"],
    "nature": ["nature trivia", "wildlife facts"],
    "space": ["space trivia", "astronomy facts"],
    "india": ["India trivia", "Indian history facts"],
}
COMMENTS = {
    "science": "Did you know this one? Drop a \U0001F9E0 if it's new to you!\nమీకు ఇది తెలుసా? కొత్తగా ఉంటే \U0001F9E0 కామెంట్ చేయండి!",
    "history": "History always surprises! Share a fact you know below.\nచరిత్ర ఎప్పుడూ ఆశ్చర్యపరుస్తుంది! మీకు తెలిసిన విషయం పంచుకోండి.",
    "nature": "Nature never stops amazing us! \U0001F33F\nప్రకృతి ఎప్పుడూ ఆశ్చర్యపరుస్తూనే ఉంటుంది! \U0001F33F",
    "space": "Space is full of surprises! \U0001F680\nఅంతరిక్షం ఆశ్చర్యాలతో నిండి ఉంది! \U0001F680",
    "india": "Proud fact about India! \U0001F1EE\U0001F1F3\nభారతదేశం గురించి గర్వకారణమైన విషయం! \U0001F1EE\U0001F1F3",
}
DISCLOSURE = "Visuals are digitally created background artwork. Background music is an original/royalty-free composition."
TAG_LIMIT = 500


def plain(row):
    strip = str.maketrans({c: None for c in "'\"‘’“”"})
    return row["text_primary"].translate(strip).strip(), row["text_secondary"].translate(strip).strip()


def title(row, special):
    te, en = plain(row)
    word = CAT_WORD[row["category"]]
    for cand in (f"{te} | {word} | {en}", f"{te} | {word}", f"{te} | InfoShorts Telugu"):
        if len(cand) <= 100:
            return cand
    tail = " | InfoShorts"
    cut = te[: 100 - len(tail) - 1].rsplit(" ", 1)[0].rstrip(",.:;")
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
    te, en = plain(row)
    out = [te, en, ""]
    out += ["InfoShorts Telugu -- one surprising fact every day, in Telugu with an English gloss.", ""]
    out += [DISCLOSURE, "", f"Source: {row['source']}", ""]
    out += [f"Like, share and subscribe to {CHANNEL} for a daily fact.", ""]
    out += [f"© {CHANNEL}."]
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
    return {"te": srt(row["text_primary"].replace('"', "").replace("'", "")), "en": srt(row["text_secondary"])}


def seed_comment(row):
    return COMMENTS[row["category"]]


def bundle(row, special):
    return {"title": title(row, special), "description": description(row, special), "tags": tags(row, special),
            "comment": seed_comment(row)}
