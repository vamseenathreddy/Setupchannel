"""Read or update each channel's YouTube "About" (description, keywords, country, default language)


  python scripts/ci/channel_about.py read  [channel|all]
  python scripts/ci/channel_about.py apply [channel|all]
  

channels: mahanavi, ramana. Output goes to stdout (the workflow tees it to a Drive file).
`apply` fetches the channel's CURRENT brandingSettings and changes only description, keywords, country
and defaultLanguage, so nothing else (banner, trailer, featured channels) is lost.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from channels.engine import upload  # noqa: E402

DATA = ROOT / "data"

CHANNELS = {
    "mahanavi": dict(
        token="youtube_token.json", expect="mahanavi", lang="te",
        keywords=['"Rahu Kalam today"', '"Durmuhurtham today"', '"Shubha Ghadiyalu"', '"rashi mantra"',
                  '"Bhagavad Gita Telugu"', '"Purana stories Telugu"', '"telugu devotional"', '"telugu bhakthi"',
                  '"daily mantra"', '"mahanavi spirituals"', '"vishnu songs"', '"shiva songs"', '"lakshmi mantra"',
                  '"krishna bhajan"', '"telugu stotra"', '"devotional chants"', '"bhakti songs"',
                  '"Ayyappa Songs"', '"karthika maasam songs"', '"Ammavari Songs"', '"powerful mantras"',
                  '"telugu spiritual channel"'],
        description=(
            "Welcome to Mahanavi Spirituals, your sacred space for Telugu devotional music and daily bhakti. "
            "| మహానవి స్పిరిచువల్స్\n\n"
            "Devotional songs, bhajans, mantras and stotras (Vishnu, Shiva, Lakshmi, Hanuman, Ayyappa, Durga, "
            "Venkateswara), plus daily Telugu Shorts: today's Rahu Kalam, Durmuhurtham and Shubha Ghadiyalu, "
            "rashi mantras, Bhagavad Gita slokas with meaning, and Purana stories.\n\n"
            "భక్తి పాటలు, భజనలు, మంత్రాలు, స్తోత్రాలు, అలాగే రోజూ తెలుగు షార్ట్స్: ఈరోజు రాహు కాలం, దుర్ముహూర్తం, "
            "శుభ ఘడియలు, రాశి మంత్రాలు, భగవద్గీత శ్లోకాలు అర్థంతో, పురాణ కథలు.\n\n"
            "Subscribe so you never miss a day's timings and mantra.\n"
            "ప్రతి రోజు తెలుసుకోవాలంటే సబ్‌స్క్రైబ్ చేయండి.\n\n"
            "Timings are for general guidance. For important events, please confirm with your family priest "
            "or local panchangam."
        ),
    ),
    "ramana": dict(
        token="youtube_token_ramana.json", expect="ramana", lang="te",
        keywords=['"Ramana Maharshi"', '"Who am I"', '"self inquiry"', "Advaita", '"Ramana Maharshi Telugu"',
                  '"Ramana Maharshi quotes"', "Arunachala", '"spiritual teachings"', '"Telugu spiritual"',
                  "రమణ మహర్షి"],
        description=(
            "Ramana Maharshi TV | రమణ మహర్షి TV\n\n"
            "One short, clear thought each day from Sri Ramana Maharshi, in Telugu and English: his teachings "
            "on self-inquiry (\"Who am I?\"), silence, surrender and the path of Advaita, his questions and "
            "answers, and moments from his life.\n\n"
            "శ్రీ రమణ మహర్షి బోధనలు ప్రతి రోజు తెలుగు, ఇంగ్లీష్‌లో: \"నేను ఎవరిని?\" ఆత్మ విచారణ, మౌనం, "
            "శరణాగతి, అద్వైత మార్గం, ప్రశ్నోత్తరాలు, ఆయన జీవిత విశేషాలు.\n\n"
            "Subscribe for a daily moment of stillness.\n"
            "రోజూ ప్రశాంతత కోసం సబ్‌స్క్రైబ్ చేయండి."
        ),
    ),
}
COUNTRY = "IN"



def _yt(key):
    return upload.service(DATA / CHANNELS[key]["token"])


def _mine(yt):
    r = yt.channels().list(part="snippet,brandingSettings", mine=True).execute()["items"][0]
    return r


def read(key):
    r = _mine(_yt(key))
    ch = r.get("brandingSettings", {}).get("channel", {})
    print(f"=== {key}: {r['snippet']['title']} ({r.get('snippet', {}).get('customUrl', '-')}) id={r['id']}")
    print("country:", ch.get("country"), "| defaultLanguage:", ch.get("defaultLanguage"))
    print("keywords:", ch.get("keywords"))
    print("description:", json.dumps(ch.get("description", ""), ensure_ascii=False))
    pl = _yt(key).playlists().list(part="snippet", mine=True, maxResults=50).execute().get("items", [])
    print("playlists:", [(p["id"], p["snippet"]["title"]) for p in pl])


def apply(key):
    c = CHANNELS[key]
    yt = _yt(key)
    r = _mine(yt)
    title = r["snippet"]["title"]
    if c["expect"] not in title.lower():
        print(f"::error::{key}: token acts as '{title}', expected a channel containing '{c['expect']}'. Skipped.")
        return False
    assert len(c["description"]) <= 1000, (key, len(c["description"]))
    kw = ""
    for k in c["keywords"]:                            # keep order (most important first), stop at YouTube's 500-char limit
        if len((kw + " " + k).strip()) <= 500:
            kw = (kw + " " + k).strip()
    branding = r.get("brandingSettings", {})
    ch = branding.setdefault("channel", {})
    ch["description"], ch["keywords"] = c["description"], kw
    ch.setdefault("country", COUNTRY)                  # keep what the channel already has
    ch.setdefault("defaultLanguage", c["lang"])
    yt.channels().update(part="brandingSettings", body={"id": r["id"], "brandingSettings": branding}).execute()
    print(f"updated {key}: {title} (description {len(c['description'])} chars, keywords {len(kw)} chars)")
    return True




def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "read"
    which = sys.argv[2] if len(sys.argv) > 2 else "all"
    keys = list(CHANNELS) if which == "all" else [which]
    for k in keys:
        try:
            read(k) if mode == "read" else apply(k)
        except Exception as e:  # noqa: BLE001 -- one channel failing must not hide the others
            print(f"::error::{k}: {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
