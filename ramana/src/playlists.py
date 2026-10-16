"""The one Ramana Maharshi TV playlist that holds every Short, with SEO title and description.

find_or_create is idempotent by exact title, and add_once checks the playlist's current contents first, so
a video can never be listed twice no matter how many times a run is retried or the backfill is repeated."""
from src import upload

TITLE = "Ramana Maharshi Teachings, Quotes & Self Enquiry (Who Am I?) | రమణ మహర్షి బోధనలు | Ramana Maharshi TV"
DESCRIPTION = (
    "All Ramana Maharshi Shorts in one place: short teachings, Self-enquiry (Atma Vichara, Who Am I?), "
    "questions and answers (satsang), and moments from the life of Sri Ramana Maharshi of Arunachala, "
    "Tiruvannamalai. New Short every day, in Telugu and English.\n\n"
    "శ్రీ రమణ మహర్షి బోధనలు, ఆత్మ విచారణ (నేను ఎవరిని?), సత్సంగ ప్రశ్నలు సమాధానాలు మరియు భగవాన్ జీవిత విశేషాలు. "
    "ప్రతి రోజు ఒక కొత్త షార్ట్, తెలుగు మరియు ఇంగ్లీష్‌లో. అరుణాచలం, తిరువణ్ణామలై.\n\n"
    "Subscribe to Ramana Maharshi TV for daily Advaita Vedanta wisdom.\n\n"
    "#RamanaMaharshi #శ్రీరమణమహర్షి #Shorts #WhoAmI #SelfInquiry #Advaita #Arunachala #అరుణాచలం"
)


def ensure_playlist(yt) -> str:
    """Find the playlist by exact title or create it (public). Refreshes the description if it differs."""
    token = None
    while True:
        r = upload._retry(lambda: yt.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=token).execute())
        for it in r.get("items", []):
            if it["snippet"]["title"].strip() == TITLE.strip():
                return it["id"]
        token = r.get("nextPageToken")
        if not token:
            break
    body = {"snippet": {"title": TITLE, "description": DESCRIPTION, "defaultLanguage": "en"},
            "status": {"privacyStatus": "public"}}
    return upload._retry(lambda: yt.playlists().insert(part="snippet,status", body=body).execute())["id"]


def video_ids(yt, playlist_id: str) -> set[str]:
    ids, token = set(), None
    while True:
        r = upload._retry(lambda: yt.playlistItems().list(part="contentDetails", playlistId=playlist_id,
                                                        maxResults=50, pageToken=token).execute())
        ids |= {i["contentDetails"]["videoId"] for i in r.get("items", [])}
        token = r.get("nextPageToken")
        if not token:
            return ids


def add_once(yt, video_id: str, playlist_id: str, present: set[str] | None = None) -> bool:
    """Add the video unless it is already in the playlist. Returns True when it was added."""
    present = video_ids(yt, playlist_id) if present is None else present
    if video_id in present:
        return False
    upload.add_to_playlist(yt, video_id, playlist_id)
    present.add(video_id)
    return True
