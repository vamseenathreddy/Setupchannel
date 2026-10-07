"""Everything YouTube sees besides the pixels for Jesus Worship Waves: title, description,
tags, captions, comment, localizations. Same shape as ramana/src/metadata.py, adapted so the
PRIMARY (English) text leads, matching this channel's English-first render order."""
import os

CHANNEL = "Jesus Worship Waves"
CAT_WORD = {"verse": "Bible Verse", "teaching": "Teaching", "praise": "Worship"}
CAT_TAGS = {
    "verse": ["#BibleVerse", "#Scripture", "#WordOfGod", "#DailyVerse"],
    "teaching": ["#JesusTeaches", "#Gospel", "#ChristianFaith", "#Discipleship"],
    "praise": ["#Hallelujah", "#Worship", "#PraiseGod", "#JesusIsLord"],
}
COMMON_TAGS = ["#Jesus", "#JesusChrist", "#ChristianShorts", "#Faith", "#తెలుగుక్రైస్తవ", "#యేసుప్రభు"]
CORE_TAGS = ["#JesusWorshipWaves", "#Shorts", "#Christian"]
KEYWORDS = ["Jesus", "Jesus Christ", "Bible verse", "Bible verse of the day", "Christian shorts",
            "worship", "praise and worship", "Gospel", "Christian faith Telugu", "Telugu Christian songs",
            "యేసుక్రీస్తు", "బైబిల్ వచనం", "క్రైస్తవ కీర్తనలు", "దేవుని వాక్యము", "ఆరాధన", "స్తుతి"]
EXTRA_KEYWORDS = {
    "verse": ["daily bible verse", "scripture reading", "verse of the day Telugu"],
    "teaching": ["teachings of Jesus", "Jesus parables", "gospel teaching"],
    "praise": ["praise and worship songs", "hallelujah chorus", "worship Jesus"],
}
COMMENTS = {
    "verse": "Which verse spoke to your heart today? Share below. 🙏\nఈ వచనం మీ హృదయానికి ఏమి తెలియజేసింది? పంచుకోండి. 🙏",
    "teaching": "How will you live out this teaching today? 🙏\nఈ బోధనను ఈ రోజు ఎలా పాటిస్తారు? 🙏",
    "praise": "Say Hallelujah in the comments! 🙌\nకామెంట్లలో హల్లెలూయ చెప్పండి! 🙌",
}
DISCLOSURE = ("Visuals are digitally created worship artwork. Background music is an original/royalty-free "
              "composition. Scripture text follows public-domain/standard translations.")
TAG_LIMIT = 500


def plain(row):
    strip = str.maketrans({c: None for c in "\"“”"})
    return row["text_primary"].translate(strip).strip(), row["text_secondary"].translate(strip).strip()


def title(row, special):
    en, te = plain(row)
    word = CAT_WORD[row["category"]]
    if special:
        en = f"{special['label_primary']}: {en}"
    for cand in (f"{en} | {word} | {te}", f"{en} | {word}", f"{en} | Jesus Worship Waves"):
        if len(cand) <= 100:
            return cand
    tail = " | Jesus"
    cut = en[: 100 - len(tail) - 1].rsplit(" ", 1)[0].rstrip(",.:;")
    return f"{cut}…{tail}"


def hashtags(row, special):
    tags = CORE_TAGS + CAT_TAGS[row["category"]] + COMMON_TAGS
    seen, out = set(), []
    for h in tags:
        if h.lower() not in seen:
            seen.add(h.lower())
            out.append(h)
    return out[:15]


def description(row, special, playlist_url=None, contact=None):
    playlist_url = playlist_url if playlist_url is not None else os.environ.get("PLAYLIST_URL", "")
    contact = contact if contact is not None else os.environ.get("CONTACT_EMAIL", "")
    en, te = plain(row)
    out = []
    if special:
        out += [f"{special['label_primary']} | {special.get('label_secondary', '')}", ""]
    out += [en, te, ""]
    out += ["Jesus Worship Waves -- a daily 5 second Bible verse, teaching, or worship moment in "
            "English and Telugu.", ""]
    out += [DISCLOSURE, "", f"Source: {row['source']}", ""]
    out += [f"Like, share and subscribe to {CHANNEL} for a daily moment of worship."]
    if playlist_url:
        out += [f"Playlist: {playlist_url}"]
    out += [""]
    out += [f"Credits: Scripture/teaching content, English and Telugu text by {CHANNEL}.",
            f"© {CHANNEL}. Short quotations are used with attribution for devotional and educational purposes."]
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


def localizations(row, special):
    """Telugu title/description localization, same pattern as ramana's."""
    _, te = plain(row)
    label = f"{special['label_secondary']}: " if special else ""
    desc = "\n".join([te, "", "ప్రతిరోజూ యేసుప్రభువు వాక్యము, బోధన, ఆరాధన.", "", " ".join(hashtags(row, special))])
    return {"te": {"title": f"{label}{te} | యేసు ఆరాధన"[:100], "description": desc}}


def srt(text, seconds=5):
    lines = "\n".join(s.strip() for s in text.split("|"))
    return f"1\n00:00:00,000 --> 00:00:{seconds:02d},000\n{lines}\n"


def captions(row):
    return {"en": srt(row["text_primary"]), "te": srt(row["text_secondary"].replace('"', "").replace("'", ""))}


def seed_comment(row):
    return COMMENTS[row["category"]]


def bundle(row, special):
    return {"title": title(row, special), "description": description(row, special), "tags": tags(row, special),
            "localizations": localizations(row, special), "comment": seed_comment(row)}
