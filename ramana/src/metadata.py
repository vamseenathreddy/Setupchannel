"""Everything YouTube sees besides the pixels: title, description, tags, captions, comment, localizations."""
import os as _os, sys as _sys  # noqa: E401
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "src"))  # noqa: E402
from ytcore.brandcfg import D_NAME  # noqa: E402
import os

CHANNEL = f"{D_NAME}"
CAT_WORD = {"quote": "Teachings", "qa": "Satsang", "life": "Life"}
CAT_TAGS = {
    "quote": ["#SpiritualQuotes", "#Advaita", "#SelfInquiry", "#WhoAmI"],
    "qa": ["#Satsang", "#Vichara", "#WhoAmI", "#SpiritualQuestions"],
    "life": ["#Arunachala", "#Tiruvannamalai", "#Saints", "#RamanaMaharshiLife"],
}
COMMON_TAGS = ["#Arunachala", "#Vedanta", "#Meditation", "#Spirituality", "#ఆధ్యాత్మికం", "#అరుణాచలం"]
CORE_TAGS = ["#RamanaMaharshi", "#శ్రీరమణమహర్షి", "#Shorts"]  # the first 3 show above the title
KEYWORDS = ["Ramana Maharshi", "Sri Ramana Maharshi", "Bhagavan Ramana Maharshi", "Ramana Maharshi quotes",
            "Ramana Maharshi teachings", "Who am I", "Self inquiry", "Atma vichara", "Advaita Vedanta", "Arunachala",
            "Tiruvannamalai", "Ramana Maharshi Telugu", "Telugu spiritual quotes", "spiritual shorts", "meditation",
            "రమణ మహర్షి", "శ్రీ రమణ మహర్షి", "అరుణాచలం", "ఆధ్యాత్మికం", "రమణ మహర్షి బోధనలు"]
EXTRA_KEYWORDS = {"quote": ["spiritual quotes", "Ramana Maharshi quotes in Telugu"],
                  "qa": ["satsang", "Ramana Maharshi Q&A", "Ramana Maharshi questions and answers"],
                  "life": ["Ramana Maharshi life story", "Ramana Maharshi biography"]}
COMMENTS = {
    "quote": "What does this teaching mean to you? Share your thoughts below. 🙏\nఈ బోధన మీకు ఏమి అనిపించింది? మీ ఆలోచనలను పంచుకోండి. 🙏",
    "qa": "Which question about Self-inquiry should we answer next? Tell us below. 🙏\nమీరు తర్వాత ఏ ప్రశ్న గురించి తెలుసుకోవాలనుకుంటున్నారు? 🙏",
    "life": "Which moment from Bhagavan's life would you like to see next? 🙏\nభగవాన్ జీవితంలో మీరు తర్వాత ఏ సంఘటన తెలుసుకోవాలనుకుంటున్నారు? 🙏",
}
DISCLOSURE = ("Visuals are digitally created devotional artwork inspired by Sri Ramana Maharshi and Arunachala. "
              "The Om chant music is an original composition.")
TAG_LIMIT = 500


def plain(row):
    """English text and Telugu text of the Short, each as one clean line."""
    en, te = row["english"], row["telugu"]
    if row["category"] == "qa" and "|" in en:
        q, a = en.split("|", 1)
        en = f"{q.replace('Q:', '').strip()} {a.replace('A:', '').strip()}"
    strip = str.maketrans({c: None for c in "\"“”"})
    return en.translate(strip).strip(), te.replace("|", " ").translate(strip).strip()


def title(row, special):
    """SEO title (max 100 chars): the Short's own text first, then channel keywords, then Telugu."""
    en, te = plain(row)
    word = CAT_WORD[row["category"]]
    if special:
        en = f"{special['label_en']}: {en}"
    for cand in (f"{en} | Ramana Maharshi {word} | {te}", f"{en} | Ramana Maharshi {word}", f"{en} | Ramana Maharshi"):
        if len(cand) <= 100:
            return cand
    tail = " | Ramana Maharshi"
    cut = en[: 100 - len(tail) - 1].rsplit(" ", 1)[0].rstrip(",.:;")
    return f"{cut}…{tail}"


def hashtags(row, special):
    calm = bool(special) and special.get("tone") == "calm"
    tags = CORE_TAGS + ["#Arunachala", "#అరుణాచలం"] if calm else CORE_TAGS + CAT_TAGS[row["category"]] + COMMON_TAGS
    seen, out = set(), []
    for h in tags:
        if h.lower() not in seen:
            seen.add(h.lower())
            out.append(h)
    return out[:15]  # YouTube ignores every hashtag when there are more than 15


def description(row, special, playlist_url=None, contact=None):
    playlist_url = playlist_url if playlist_url is not None else os.environ.get("PLAYLIST_URL", "")
    contact = contact if contact is not None else os.environ.get("CONTACT_EMAIL", "")
    en, te = plain(row)
    calm = bool(special) and special.get("tone") == "calm"
    out = []
    if special:
        out += [f"{special['label_te']} | {special['label_en']}", ""]
    out += [en, te, ""]
    if not calm:  # intro
        out += ["Sri Ramana Maharshi (Bhagavan Ramana) on Self-inquiry (Atma Vichara), Advaita and Arunachala. "
                "A new 5 second teaching every day in Telugu and English.", ""]
    out += [DISCLOSURE, "", f"Source: {row['source']}", ""]  # originality statement, then context
    if not calm:  # call to action, playlist
        out += [f"Like, share and subscribe to {CHANNEL} for a daily teaching. ప్రతిరోజూ శ్రీ రమణ మహర్షి బోధనలు."]
        if playlist_url:
            out += [f"Playlist: {playlist_url}"]
        out += [""]
    out += [f"Credits: Teaching by Sri Ramana Maharshi. Telugu and English text by {CHANNEL}.",
            f"© {CHANNEL}. Short quotations are used with attribution for devotional and educational purposes."]
    if contact:
        out += [f"Contact: {contact}"]
    out += ["", " ".join(hashtags(row, special))]
    return "\n".join(out)  # no chapters: a 5 second Short has no sections to chapter


def tag_cost(tag):
    return len(tag) + (2 if " " in tag else 0)  # YouTube counts tags with spaces as if quoted


def fit_tags(tags, limit=TAG_LIMIT):
    """Deduplicate and keep as many tags as fit in the exact 500 character budget (commas included)."""
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


def localizations(row, special):
    """Telugu title and description so Telugu viewers see Telugu in search and suggestions."""
    _, te = plain(row)
    label = f"{special['label_te']}: " if special else ""
    desc = "\n".join([te, "", "ప్రతిరోజూ శ్రీ రమణ మహర్షి బోధనలు.", "", " ".join(hashtags(row, special))])
    return {"te": {"title": f"{label}{te} | శ్రీ రమణ మహర్షి"[:100], "description": desc}}


def srt(text, seconds=5):
    """One caption cue spanning the whole Short, identical to the burned-in text."""
    lines = "\n".join(s.strip() for s in text.split("|"))
    return f"1\n00:00:00,000 --> 00:00:{seconds:02d},000\n{lines}\n"


def captions(row):
    return {"te": srt(row["telugu"].replace('"', "").replace("'", "")), "en": srt(row["english"])}


def seed_comment(row):
    return COMMENTS[row["category"]]


def bundle(row, special):
    return {"title": title(row, special), "description": description(row, special), "tags": tags(row, special),
            "localizations": localizations(row, special), "comment": seed_comment(row)}
