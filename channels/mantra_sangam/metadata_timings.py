"""YouTube metadata for the Hindi timing Shorts. Titles mix Hindi with the English term."""
import os

from channels.mantra_sangam import timings

CHANNEL = "Divine Mantra Sangam"
NAMES = {  # (hindi, english)
    "rahu": ("राहु काल", "Rahu Kaal"),
    "shubh": ("शुभ मुहूर्त", "Shubh Muhurat"),
    "durm": ("दुर्मुहूर्त", "Durmuhurat"),
}
TITLE_FMT = {
    "rahu": ["आज का राहु काल | Rahu Kaal Today {d}", "Rahu Kaal Today | आज राहु काल कब है? {d}",
             "राहु काल आज | Rahu Kalam Timing {d}"],
    "shubh": ["आज के शुभ मुहूर्त | Shubh Muhurat Today {d}", "Shubh Muhurat Today | अभिजीत मुहूर्त {d}",
              "आज का शुभ समय | Abhijit Muhurat {d}"],
    "durm": ["आज का दुर्मुहूर्त | Durmuhurat Today {d}", "Durmuhurat Today | आज कौन सा समय अशुभ? {d}",
             "दुर्मुहूर्त आज | Inauspicious Time {d}"],
}
TAGS = {
    "rahu": ["#RahuKaal", "#RahuKalam", "#राहुकाल", "#Panchang"],
    "shubh": ["#ShubhMuhurat", "#AbhijitMuhurat", "#शुभमुहूर्त", "#Panchang"],
    "durm": ["#Durmuhurat", "#दुर्मुहूर्त", "#Panchang", "#Hindu"],
}
COMMON = ["#DivineMantraSangam", "#Shorts", "#HindiDevotional", "#आजकापंचांग", "#Hindu", "#Spirituality"]


def _d(row):
    import datetime as dt
    d = dt.date.fromisoformat(row["date_iso"])
    return f"{d.day} {d.strftime('%b %Y')}"


def title(row):
    opts = TITLE_FMT[row["category"]]
    import datetime as dt
    i = dt.date.fromisoformat(row["date_iso"]).toordinal() % len(opts)
    t = opts[i].format(d=_d(row))
    return t if len(t) <= 100 else opts[0].format(d=_d(row))[:100]


def hashtags(row):
    out, seen = [], set()
    for h in TAGS[row["category"]] + COMMON:
        if h.lower() not in seen:
            seen.add(h.lower()); out.append(h)
    return out[:15]


def description(row):
    hi, en = NAMES[row["category"]]
    k = row["category"]
    lines = [f"{timings.date_hi(__import__('datetime').date.fromisoformat(row['date_iso']))} का {hi} ({timings.LOCATION_NAME_HI} के अनुसार)", ""]
    if k == "rahu":
        lines += [f"राहु काल: {row['rahu']}", f"यमगंड: {row['yamagandam']}", f"गुलिक काल: {row['gulika']}",
                  f"वर्ज्य: {row['varjyam']}", f"दुर्मुहूर्त: {row['durm_times']}"]
    elif k == "shubh":
        lines += [f"अभिजीत मुहूर्त: {row['abhijit'] or 'आज नहीं'}", f"ब्रह्म मुहूर्त: {row['brahma']}"]
    else:
        lines += [f"दुर्मुहूर्त: {row['durm_times']}", f"राहु काल: {row['rahu']}"]
    lines += ["", f"{row['t_mantra_label']}: {row['t_mantra']}", "",
              f"रोज़ {hi} जानने के लिए {CHANNEL} को सब्सक्राइब करें। इस वीडियो पर अपनी राय कमेंट करें।", "",
              f"{en} for {row['weekday_en']} {_d(row)} ({timings.LOCATION_NAME_EN}). Times are calculated for "
              f"{timings.LOCATION_NAME_EN}; they differ by a few minutes in other cities. Subscribe to {CHANNEL} for a new "
              "Hindu panchang timing every day, and share your opinion on this video in the comments.", ""]
    contact = os.environ.get("CONTACT_EMAIL", "")
    if contact:
        lines += [f"Contact: {contact}", ""]
    lines += [" ".join(hashtags(row))]
    return "\n".join(lines)


def tags(row):
    hi, en = NAMES[row["category"]]
    base = [f"{en} today", en, hi, "आज का पंचांग", "panchang today", "Hindi panchang", "Hindu panchang",
            "daily panchang", "आज का राहु काल", "shubh muhurat today", "Hindi devotional shorts", CHANNEL]
    out, total = [], 0
    for t in base:
        c = len(t) + (2 if " " in t else 0)
        if total + c <= 450:
            out.append(t); total += c
    return out


def bundle(row, special=None):
    return {"title": title(row), "description": description(row), "tags": tags(row), "localizations": None,
            "comment": row["t_comment"] + " \U0001F64F", "language": "hi"}


def captions(row):
    return {}
