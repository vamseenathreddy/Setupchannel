"""Daily Hindi timing Shorts for Divine Mantra Sangam: Rahu Kaal, Shubh Muhurat, Durmuhurat.

Hindi version of Mahanavi Spirituals' three daily timing Shorts. The times are computed locally
with the Swiss Ephemeris (mahanavi.panchang.local_provider), so no Panchang API and no quota is
used. Location is New Delhi (the card says so); change LOCATION to use another city.
"""
from datetime import date, timedelta

from mahanavi.panchang.local_provider import DELHI, LocalPanchangProvider

LOCATION_NAME_HI, LOCATION_NAME_EN = "दिल्ली", "New Delhi"
LOCATION = DELHI

KINDS = ("rahu", "shubh", "durm")
WEEKDAY_HI = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
WEEKDAY_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_HI = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
# the day's deity and mantra (Mon Shiva ... Sun Surya)
DEITY_MANTRA = [
    ("शिव", "ॐ नमः शिवाय"),
    ("हनुमान", "ॐ हनुमते नमः"),
    ("गणेश", "ॐ गं गणपतये नमः"),
    ("विष्णु", "ॐ नमो भगवते वासुदेवाय"),
    ("लक्ष्मी", "ॐ श्रीं महालक्ष्म्यै नमः"),
    ("शनि", "ॐ शं शनैश्चराय नमः"),
    ("सूर्य", "ॐ घृणिः सूर्याय नमः"),
]
COMMENT_PROMPTS = {
    "rahu": ["आपके शहर में राहु काल कब है? शहर का नाम कमेंट करें",
             "आप राहु काल में कौन सा काम टालते हैं? कमेंट करें",
             "क्या आप राहु काल मानते हैं? हाँ या नहीं कमेंट करें"],
    "shubh": ["आज आप कौन सा शुभ काम शुरू कर रहे हैं? कमेंट करें",
              "आपका पसंदीदा शुभ मुहूर्त कौन सा है? कमेंट करें",
              "आज के दिन का अपना संकल्प कमेंट करें"],
    "durm": ["आज दुर्मुहूर्त में आप कौन सा काम टालेंगे? कमेंट करें",
             "क्या आप दुर्मुहूर्त का ध्यान रखते हैं? कमेंट करें",
             "अपने परिवार को यह समय ज़रूर बताएँ, कमेंट में 'जय श्री राम' लिखें"],
}
CTA = {"rahu": "रोज़ राहु काल जानने के लिए सब्सक्राइब करें",
       "shubh": "रोज़ शुभ मुहूर्त जानने के लिए सब्सक्राइब करें",
       "durm": "रोज़ दुर्मुहूर्त जानने के लिए सब्सक्राइब करें"}
OPINION = "इस वीडियो पर अपनी राय कमेंट करें"


def date_hi(d: date) -> str:
    return f"{d.day} {MONTH_HI[d.month - 1]} {d.year}, {WEEKDAY_HI[d.weekday()]}"


def _other(p) -> str:
    parts = [f"यमगंड: {p.yamagandam}", f"गुलिक काल: {p.gulika_kalam}", f"वर्ज्य: {p.varjyam}"]
    return "  |  ".join(x for x in parts if not x.endswith(": "))


def timing_row(kind: str, d: date) -> dict:
    """One engine content row for the given kind and (IST) date."""
    prov = LocalPanchangProvider(*LOCATION)
    p = prov.fetch(d)
    deity, mantra = DEITY_MANTRA[d.weekday()]
    pick = COMMENT_PROMPTS[kind][d.toordinal() % 3]
    row = {
        "id": f"{kind}-{d.isoformat()}", "category": kind, "special": "", "source": "Local Swiss Ephemeris panchang",
        "text_primary": "", "text_secondary": "",
        "t_date": date_hi(d), "t_place": f"({LOCATION_NAME_HI} के अनुसार)",
        "t_mantra_label": f"आज के देव: {deity}", "t_mantra": mantra,
        "t_comment": pick, "t_sub": CTA[kind], "t_opinion": OPINION,
        "weekday_en": WEEKDAY_EN[d.weekday()], "date_iso": d.isoformat(),
        "rahu": p.rahu_kalam, "durm_times": p.durmuhurtham, "abhijit": p.abhijit_muhurtham,
        "brahma": prov.brahma_muhurta(d), "yamagandam": p.yamagandam, "gulika": p.gulika_kalam, "varjyam": p.varjyam,
    }
    if kind == "rahu":
        row.update(t_title="आज का राहु काल", t_label="समय", t_time=p.rahu_kalam,
                   t_note="इस समय नया शुभ कार्य शुरू न करें", t_other=_other(p))
    elif kind == "shubh":
        if p.abhijit_muhurtham:
            row.update(t_title="आज के शुभ मुहूर्त", t_label="अभिजीत मुहूर्त", t_time=p.abhijit_muhurtham,
                       t_note=f"ब्रह्म मुहूर्त: {row['brahma']}", t_other="")
        else:
            row.update(t_title="आज के शुभ मुहूर्त", t_label="ब्रह्म मुहूर्त", t_time=row["brahma"],
                       t_note="आज बुधवार है, अभिजीत मुहूर्त नहीं माना जाता", t_other="")
    else:
        row.update(t_title="आज का दुर्मुहूर्त", t_label="समय", t_time=p.durmuhurtham.replace(", ", "\n"),
                   t_note="इस समय शुभ कार्य टालें", t_other=f"राहु काल: {p.rahu_kalam}  |  यमगंड: {p.yamagandam}")
    return row


def fetch_row_for(kind: str):
    """fetch_row(used_ids) for ChannelPipeline: today's row in IST, once per day."""
    import datetime as dt
    from zoneinfo import ZoneInfo

    def fetch(used_ids):
        today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()
        return timing_row(kind, today)
    return fetch
