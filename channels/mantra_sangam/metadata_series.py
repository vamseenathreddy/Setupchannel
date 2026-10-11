"""YouTube metadata for the Hindi Purana / Rashi Shorts. Titles mix Hindi with the English name."""
from ytcore.brandcfg import B_NAME  # noqa: E402
import os

CHANNEL = f"{B_NAME}"
PREFIX = {"purana": "पुराण कथा | Purana Story", "rashi": "राशि मंत्र | Rashi Mantra"}
TAGS = {
    "purana": ["#PuranaStory", "#पुराणकथा", "#HinduMythology", "#KrishnaStory"],
    "rashi": ["#RashiMantra", "#राशिमंत्र", "#Rashifal", "#Navagraha"],
}
COMMON = ["#DivineMantraSangam", "#Shorts", "#HindiDevotional", "#सनातनधर्म", "#Hindu", "#Spirituality"]


def title(row):
    hi, en = row["title_hi"], row["title_en"]
    if row["category"] == "purana":
        for cand in (f"{hi} ({en}) | Purana Story", f"{hi} ({en})", f"पुराण कथा | {hi} ({en})"):
            if len(cand) <= 95:
                return cand
        return f"{hi} | Purana Story"[:100]
    for cand in (f"{hi} राशि मंत्र {en} Rashi Mantra", f"{hi} राशि {en} Mantra", f"{PREFIX['rashi']} | {hi} {en}"):
        if len(cand) <= 95:
            return cand
    return f"{hi} राशि | Rashi Mantra"


def hashtags(row):
    out, seen = [], set()
    for h in TAGS[row["category"]] + COMMON:
        if h.lower() not in seen:
            seen.add(h.lower()); out.append(h)
    return out[:15]


def description(row):
    k = row["category"]
    lines = []
    if k == "purana":
        lines += [f"{row['title_hi']} ({row['title_en']})", "", row["t_story"], "", f"सीख: {row['t_moral']}",
                  f"Moral: {row['moral_en']}", ""]
    else:
        lines += [f"{row['title_hi']} राशि ({row['title_en']}) का मंत्र", "", f"स्वामी ग्रह: {row['planet_hi']} ({row['planet_en']})",
                  f"मंत्र: {row['t_moral']}", f"{row['benefit_hi']}", row["t_invoke"], ""]
    lines += [f"रोज़ ऐसे शॉर्ट्स के लिए {CHANNEL} को सब्सक्राइब करें। इस वीडियो पर अपनी राय कमेंट करें।", ""]
    contact = os.environ.get("CONTACT_EMAIL", "")
    if contact:
        lines += [f"Contact: {contact}", ""]
    lines += [" ".join(hashtags(row))]
    return "\n".join(lines)


def tags(row):
    base = ["Purana story Hindi", "Hindu mythology", "पुराण कथा", CHANNEL, "Hindi devotional shorts"] if row["category"] == "purana" \
        else ["Rashi mantra", "राशि मंत्र", row["title_en"], row["title_hi"], "Navagraha mantra", CHANNEL, "Hindi devotional shorts"]
    out, total = [], 0
    for t in base:
        c = len(t) + (2 if " " in t else 0)
        if total + c <= 450:
            out.append(t); total += c
    return out


def bundle(row, special=None):
    cm = "इस कथा से आपने क्या सीखा? कमेंट करें" if row["category"] == "purana" else "आपकी राशि कौन सी है? कमेंट करें"
    return {"title": title(row), "description": description(row), "tags": tags(row), "localizations": None,
            "comment": cm + " \U0001F64F", "language": "hi"}


def captions(row):
    return {}
