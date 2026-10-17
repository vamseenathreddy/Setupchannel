"""Daily beej mantra playlist, one per channel: SEO title and description, find-or-create, clean, and add-once.

Every beej/moola mantra Short of a channel belongs in ONE playlist. add_once checks the playlist's current
contents first, so a video can never be listed twice however often a run is retried. clean_playlist removes only
playlist ENTRIES that no longer show a video (deleted / private) and repeated entries; it never deletes a video.
"""
from __future__ import annotations

from channels.engine import upload

SPECS: dict[str, dict[str, str]] = {
    "mahanavi": {
        "title": "బీజ మంత్రాలు | Daily Beej Mantras in Telugu | Mahanavi Spirituals",
        "description": (
            "ప్రతి రోజు ఉదయం 6 గంటలకు ఒక దేవతా బీజ మంత్రం. గణపతి, శివ, విష్ణు, లక్ష్మి, సరస్వతి, దుర్గా, ఆంజనేయ "
            "మరియు మరిన్ని దేవతల బీజ మంత్రాలు, మూల మంత్రాలు. 108 సార్లు జపించండి.\n\n"
            "Daily beej (seed) mantra Shorts of Hindu deities in Telugu: Ganesha, Shiva, Vishnu, Lakshmi, Saraswati, "
            "Durga, Hanuman and more. A new mantra every morning at 6 AM.\n\n"
            "#BeejMantra #బీజమంత్రం #DailyMantra #Shorts #Telugu #Devotional"
        ),
        "language": "te",
    },
    "mantra_sangam": {
        "title": "बीज मंत्र | Daily Beej Mantra in Hindi | Divine Mantra Sangam",
        "description": (
            "हर सुबह 6 बजे एक देवता का बीज मंत्र। गणेश, शिव, विष्णु, लक्ष्मी, सरस्वती, दुर्गा, हनुमान और अन्य देवी-देवताओं "
            "के बीज मंत्र और मूल मंत्र। 108 बार जपें।\n\n"
            "Daily beej (seed) mantra Shorts of Hindu deities in Hindi. A new mantra every morning at 6 AM.\n\n"
            "#BeejMantra #बीजमंत्र #DailyMantra #Shorts #Hindi #Sanatan"
        ),
        "language": "hi",
    },
    "trance_beats": {
        "title": "बीज मंत्र | Daily Beej Mantra in Hindi | Devotional Trance Beats",
        "description": (
            "हर सुबह 6 बजे एक देवता का बीज मंत्र। गणेश, शिव, विष्णु, लक्ष्मी, सरस्वती, दुर्गा, हनुमान और अन्य देवी-देवताओं "
            "के बीज मंत्र और मूल मंत्र। 108 बार जपें।\n\n"
            "Daily beej (seed) mantra Shorts of Hindu deities in Hindi. A new mantra every morning at 6 AM.\n\n"
            "#BeejMantra #बीजमंत्र #DailyMantra #Shorts #Hindi #Devotional"
        ),
        "language": "hi",
    },
}

# A video is a beej-mantra Short when its title carries one of these (build() always writes one of them).
TITLE_MARKERS = ("beej mantra", "beeja mantra", "బీజ మంత్రం", "మూల మంత్రం", "बीज मंत्र", "मूल मंत्र")
DEAD_TITLES = {"deleted video", "private video"}


def is_beej_title(title: str) -> bool:
    low = title.lower()
    return any(m in low for m in TITLE_MARKERS)


def _pages(call):
    token = None
    while True:
        r = upload._retry(lambda: call(token).execute())  # noqa: SLF001
        yield from r.get("items", [])
        token = r.get("nextPageToken")
        if not token:
            return


def list_playlists(yt) -> list[tuple[str, str, int]]:
    return [(p["id"], p["snippet"]["title"], p["contentDetails"]["itemCount"]) for p in _pages(
        lambda t: yt.playlists().list(part="snippet,contentDetails", mine=True, maxResults=50, pageToken=t))]


def channel_beej_videos(yt) -> list[tuple[str, str, str]]:
    """[(video_id, title, privacy)] of this channel's public beej mantra uploads, oldest first."""
    uploads = upload._retry(lambda: yt.channels().list(part="contentDetails", mine=True).execute())  # noqa: SLF001
    uploads_id = uploads["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = [i["contentDetails"]["videoId"] for i in _pages(
        lambda t: yt.playlistItems().list(part="contentDetails", playlistId=uploads_id, maxResults=50, pageToken=t))]
    out = []
    for k in range(0, len(ids), 50):
        r = upload._retry(lambda: yt.videos().list(part="snippet,status", id=",".join(ids[k:k + 50])).execute())  # noqa: SLF001
        for v in r.get("items", []):
            if v["status"]["privacyStatus"] == "public" and is_beej_title(v["snippet"]["title"]):
                out.append((v["snippet"]["publishedAt"], v["id"], v["snippet"]["title"], v["status"]["privacyStatus"]))
    return [(vid, title, priv) for _, vid, title, priv in sorted(out)]


def ensure_playlist(yt, channel: str) -> str:
    spec = SPECS[channel]
    return upload.find_or_create_playlist(yt, spec["title"], spec["description"], spec["language"])


def playlist_video_ids(yt, playlist_id: str) -> set[str]:
    return {i["contentDetails"]["videoId"] for i in _pages(
        lambda t: yt.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=50, pageToken=t))}


def add_once(yt, video_id: str, playlist_id: str, present: set[str] | None = None) -> bool:
    present = playlist_video_ids(yt, playlist_id) if present is None else present
    if video_id in present:
        return False
    upload.add_to_playlist(yt, video_id, playlist_id)
    present.add(video_id)
    return True


def clean_playlist(yt, playlist_id: str) -> tuple[int, int]:
    """Remove dead entries and repeated entries. Returns (dead_removed, duplicates_removed)."""
    items = list(_pages(lambda t: yt.playlistItems().list(
        part="snippet,contentDetails", playlistId=playlist_id, maxResults=50, pageToken=t)))
    vids = [i["contentDetails"].get("videoId") for i in items]
    alive: set[str] = set()
    for k in range(0, len(vids), 50):
        chunk = [v for v in vids[k:k + 50] if v]
        if chunk:
            r = upload._retry(lambda: yt.videos().list(part="id", id=",".join(chunk)).execute())  # noqa: SLF001
            alive |= {v["id"] for v in r.get("items", [])}
    dead = dup = 0
    seen: set[str] = set()
    for it in items:
        vid = it["contentDetails"].get("videoId")
        title = it["snippet"].get("title", "").strip().lower()
        if not vid or vid not in alive or title in DEAD_TITLES:
            upload._retry(lambda: yt.playlistItems().delete(id=it["id"]).execute())  # noqa: SLF001
            dead += 1
        elif vid in seen:
            upload._retry(lambda: yt.playlistItems().delete(id=it["id"]).execute())  # noqa: SLF001
            dup += 1
        else:
            seen.add(vid)
    return dead, dup


def add_new_video(yt, channel: str, video_id: str) -> bool:
    """Called right after a daily upload: find-or-create the playlist and add the video once."""
    return add_once(yt, video_id, ensure_playlist(yt, channel))
