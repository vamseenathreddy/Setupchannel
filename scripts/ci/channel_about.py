"""Read or update each channel's YouTube "About" (description, keywords, country, default language)
and create the Pulse Boosting playlist.

  python scripts/ci/channel_about.py read  [channel|all]
  python scripts/ci/channel_about.py apply [channel|all]
  python scripts/ci/channel_about.py pulse-playlist

channels: mahanavi, ramana, jesus, pulse. Output goes to stdout (the workflow tees it to a Drive file).
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
        keywords=['"Telugu devotional"', '"Rahu Kalam today"', '"Durmuhurtham today"', '"Shubha Ghadiyalu"',
                  '"rashi mantra"', '"Bhagavad Gita Telugu"', '"Purana stories Telugu"', '"Telugu bhakti"',
                  '"daily panchangam"', '"Telugu Shorts"', "Mahanavi", "మహానవి"],
        description=(
            "Mahanavi Spirituals | మహానవి స్పిరిచువల్స్\n\n"
            "Daily Telugu devotional Shorts: today's Rahu Kalam, Durmuhurtham and Shubha Ghadiyalu, "
            "rashi (zodiac) mantras, Bhagavad Gita slokas with meaning, and stories and concepts from the Puranas.\n\n"
            "రోజూ తెలుగులో భక్తి షార్ట్స్: ఈరోజు రాహు కాలం, దుర్ముహూర్తం, శుభ ఘడియలు, రాశి మంత్రాలు, "
            "భగవద్గీత శ్లోకాలు అర్థంతో, పురాణ కథలు, పురాణ విషయాలు.\n\n"
            "Subscribe so you never miss a day's timings and mantra.\n"
            "ప్రతి రోజు తెలుసుకోవాలంటే సబ్‌స్క్రైబ్ చేయండి.\n\n"
            "Timings are shared for general guidance. For important events, please confirm with your family "
            "priest or local panchangam."
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
    "jesus": dict(
        token="youtube_token_jesus.json", expect="jesus", lang="en",
        keywords=['"Bible verse of the day"', '"Bible quiz"', '"Telugu Bible"', '"Telugu Christian"',
                  '"Jesus worship"', '"Christian Shorts"', '"daily Bible quote"', '"Bible verse Telugu"',
                  '"worship songs"', "బైబిల్"],
        description=(
            "Jesus Worship Waves | జీసస్ వర్షిప్ వేవ్స్\n\n"
            "Every morning: a Bible verse in English and Telugu, with a short thought on how it applies to our life.\n"
            "Every evening: a Bible quiz. Which book and chapter is today's verse from? Test yourself and "
            "answer in the comments.\n"
            "Plus Telugu and English worship songs.\n\n"
            "ప్రతి ఉదయం బైబిల్ వచనం ఇంగ్లీష్, తెలుగులో, అది మన జీవితానికి ఎలా వర్తిస్తుందో చిన్న ఆలోచనతో. "
            "ప్రతి సాయంత్రం బైబిల్ క్విజ్: ఈ వచనం ఏ పుస్తకం, ఏ అధ్యాయంలోనిది? కామెంట్‌లో మీ సమాధానం చెప్పండి. "
            "అలాగే తెలుగు, ఇంగ్లీష్ ఆరాధన పాటలు.\n\n"
            "Subscribe for a daily Bible quote and quiz.\n"
            "రోజూ బైబిల్ వచనం, క్విజ్ కోసం సబ్‌స్క్రైబ్ చేయండి."
        ),
    ),
    "pulse": dict(
        token="youtube_token_pulse_boosting.json", expect="pulse", lang="en",
        keywords=['"technology updates"', '"gadget reviews"', '"inspiring stories"', "creativity", "inspiring",
                  "latest", "trending", '"science news"', '"tech news"', '"new gadgets"', '"daily Shorts"'],
        description=(
            "Pulse Boosting\n\n"
            "Your daily boost of what's new: technology updates, gadget launches, science breakthroughs, "
            "inspiring stories and creative ideas. One fresh Short every day.\n\n"
            "Every Short is based on a real, recent headline, and we credit the publisher in each video. "
            "We never make up news.\n\n"
            "Subscribe for a daily pulse of what's trending."
        ),
    ),
}
COUNTRY = "IN"

PULSE_PLAYLIST = (
    "Pulse Boosting Daily | Tech, Gadgets, Science & Inspiring Stories",
    "A fresh Short every day from Pulse Boosting: technology updates, gadget launches and reviews, science "
    "breakthroughs, inspiring stories and creative ideas, all from real, recent headlines with the source "
    "credited in every video.\n\n"
    "Watch the latest tech news, new gadgets, science discoveries and motivation in under a minute.\n\n"
    "Subscribe to Pulse Boosting for a daily boost of what's new and trending.\n\n"
    "#PulseBoosting #TechUpdates #GadgetReviews #InspiringStories #Creativity #Trending #Shorts",
)


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
    kw = " ".join(c["keywords"])
    assert len(kw) <= 500, (key, len(kw))
    branding = r.get("brandingSettings", {})
    ch = branding.setdefault("channel", {})
    ch["description"], ch["keywords"], ch["country"], ch["defaultLanguage"] = c["description"], kw, COUNTRY, c["lang"]
    yt.channels().update(part="brandingSettings", body={"id": r["id"], "brandingSettings": branding}).execute()
    print(f"updated {key}: {title} (description {len(c['description'])} chars, keywords {len(kw)} chars)")
    return True


def pulse_playlist():
    yt = _yt("pulse")
    title, desc = PULSE_PLAYLIST
    existing = {i["snippet"]["title"]: i["id"] for i in
                yt.playlists().list(part="snippet", mine=True, maxResults=50).execute().get("items", [])}
    if title in existing:
        pid = existing[title]
        print("found pulse playlist:", pid)
    else:
        body = {"snippet": {"title": title, "description": desc, "defaultLanguage": "en"},
                "status": {"privacyStatus": "public"}}
        pid = yt.playlists().insert(part="snippet,status", body=body).execute()["id"]
        print("created pulse playlist:", pid)
    print("PULSE_PLAYLIST_ID", pid)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "read"
    which = sys.argv[2] if len(sys.argv) > 2 else "all"
    keys = list(CHANNELS) if which == "all" else [which]
    if mode == "pulse-playlist":
        pulse_playlist()
        return 0
    for k in keys:
        try:
            read(k) if mode == "read" else apply(k)
        except Exception as e:  # noqa: BLE001 -- one channel failing must not hide the others
            print(f"::error::{k}: {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
