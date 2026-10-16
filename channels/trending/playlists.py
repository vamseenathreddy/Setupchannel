"""One playlist per (niche, language), created on first use. A video is never listed twice."""
from channels.engine import upload
from channels.trending import config as cfg


def video_ids(yt, playlist_id: str) -> set[str]:
    ids, token = set(), None
    while True:
        r = upload._retry(lambda: yt.playlistItems().list(part="contentDetails", playlistId=playlist_id,
                                                        maxResults=50, pageToken=token).execute())
        ids |= {i["contentDetails"]["videoId"] for i in r.get("items", [])}
        token = r.get("nextPageToken")
        if not token:
            return ids


def add(yt, video_id: str, lang: str, niche: str) -> str:
    title, desc = cfg.playlist_for(lang, niche)
    pid = upload.find_or_create_playlist(yt, title, desc, lang)
    if video_id in video_ids(yt, pid):
        return f"already in playlist {title}"
    upload.add_to_playlist(yt, video_id, pid)
    return f"added to playlist {title}"
