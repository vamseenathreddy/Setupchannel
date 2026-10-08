"""Everything YouTube sees besides the pixels for Jesus Worship Waves' two daily Shorts:
the morning Bible Quote and the evening Bible Quiz. English leads, Telugu follows."""
import os

CHANNEL = "Jesus Worship Waves"
COMMON_TAGS = ["#Jesus", "#JesusChrist", "#ChristianShorts", "#Faith", "#తెలుగుక్రైస్తవ", "#యేసుప్రభు"]
CORE_TAGS = ["#JesusWorshipWaves", "#Shorts", "#Christian"]
CAT_TAGS = {
    "quote": ["#BibleVerse", "#Scripture", "#WordOfGod", "#DailyVerse"],
    "quiz": ["#BibleQuiz", "#BibleTrivia", "#QuizTime", "#TeluguBibleQuiz"],
}
KEYWORDS = ["Jesus", "Jesus Christ", "Bible verse", "Christian shorts", "Gospel", "Christian faith Telugu",
            "యేసుక్రీస్తు", "బైబిల్ వచనం", "దేవుని వాక్యము"]
EXTRA_KEYWORDS = {
    "quote": ["bible verse of the day", "daily bible verse", "scripture reading", "verse of the day Telugu",
              "how Bible verses apply to life"],
    "quiz": ["bible quiz", "bible trivia", "bible quiz Telugu", "guess the bible verse", "బైబిల్ క్విజ్"],
}
COMMENTS = {
    "quote": "Which part of this verse speaks to you today? Share below. 🙏\nఈ వచనంలో మీ హృదయానికి తాకిన భాగం ఏది? పంచుకోండి. 🙏",
}
DISCLOSURE = ("Visuals are digitally created worship artwork. Background music is an original "
              "composition. Scripture English text is public-domain (KJV/WEB).")
TAG_LIMIT = 500


def _short(text, n):
    words = text.split()
    return " ".join(words[:n]) + ("…" if len(words) > n else "")


def title(row, special=None):
    if row["category"] == "quote":
        for cand in (f"{row['ref_en']} | {_short(row['verse_en'], 9)} | Bible Verse of the Day",
                     f"{row['ref_en']} | Bible Verse of the Day | {row['ref_te']}",
                     f"{row['ref_en']} | Bible Verse of the Day"):
            if len(cand) <= 100:
                return cand
    for cand in (f"Bible Quiz: {row['question_en']} | బైబిల్ క్విజ్",
                 f"Bible Quiz: {row['question_en']}",
                 "Bible Quiz | బైబిల్ క్విజ్"):
        if len(cand) <= 100:
            return cand
    return "Bible Quiz"


def hashtags(row, special=None):
    tags = CORE_TAGS + CAT_TAGS[row["category"]] + COMMON_TAGS
    seen, out = set(), []
    for h in tags:
        if h.lower() not in seen:
            seen.add(h.lower())
            out.append(h)
    return out[:15]


def description(row, special=None, playlist_url=None, contact=None):
    playlist_url = playlist_url if playlist_url is not None else os.environ.get("PLAYLIST_URL", "")
    contact = contact if contact is not None else os.environ.get("CONTACT_EMAIL", "")
    out = []
    if row["category"] == "quote":
        out += [row["text_primary"], row["text_secondary"], "", row["apply_en"], row["apply_te"], ""]
        out += [f"Source: {row['ref_en']} ({row['ref_te']})", ""]
    else:
        out += [row["question_en"], row["question_te"], "", "Comment A, B, C or D.", ""]
        out += [row["opt_a"], row["opt_b"], row["opt_c"], row["opt_d"], "",
                f"Answer: {row['correct_letter']}) {row['answer']} ({row['ref_en']}) - see the pinned comment.", ""]
    out += [DISCLOSURE, "", f"Like, share and subscribe to {CHANNEL}: a Bible quote every morning and a Bible quiz every evening."]
    if playlist_url:
        out += [f"Playlist: {playlist_url}"]
    out += ["", f"© {CHANNEL}."]
    if contact:
        out += [f"Contact: {contact}"]
    out += ["", " ".join(hashtags(row))]
    return "\n".join(out)


def fit_tags(tags, limit=TAG_LIMIT):
    out, total, seen = [], 0, set()
    for tg in tags:
        k = tg.lower()
        if k in seen:
            continue
        cost = len(tg) + (2 if " " in tg else 0) + (1 if out else 0)
        if total + cost > limit:
            continue
        seen.add(k)
        out.append(tg)
        total += cost
    return out


def tags(row, special=None):
    return fit_tags(KEYWORDS + EXTRA_KEYWORDS[row["category"]])


def localizations(row, special=None):
    if row["category"] == "quote":
        te_title = f"{row['ref_te']} | నేటి బైబిల్ వచనం | యేసు ఆరాధన"
        te_desc = "\n".join([row["text_secondary"], "", row["apply_te"], "", " ".join(hashtags(row))])
    else:
        te_title = f"బైబిల్ క్విజ్ | {row['question_te']} | యేసు ఆరాధన"
        te_desc = "\n".join([row["text_secondary"], "", row["question_te"], "", " ".join(hashtags(row))])
    return {"te": {"title": te_title[:100], "description": te_desc}}


def srt(text, seconds=5):
    lines = "\n".join(s.strip() for s in text.split("|"))
    return f"1\n00:00:00,000 --> 00:00:{seconds:02d},000\n{lines}\n"


def captions(row):
    return {"en": srt(row["text_primary"]), "te": srt(row["text_secondary"].replace('"', "").replace("'", ""))}


def comment(row):
    if row["category"] == "quote":
        return COMMENTS["quote"]
    return (f"Answer: {row['correct_letter']}) {row['answer']} ({row['ref_en']}). Did you get it right? Comment below! 🙏\n"
            f"సమాధానం: {row['correct_letter']}) {row['answer_te']} ({row['ref_te']}). మీరు సరిగ్గా చెప్పారా? 🙏")


def bundle(row, special=None):
    return {"title": title(row), "description": description(row), "tags": tags(row),
            "localizations": localizations(row), "comment": comment(row)}
