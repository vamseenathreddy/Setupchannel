"""One playlist per (niche, language), created on first use. A video is never listed twice."""
import time

from googleapiclient.errors import HttpError

from channels.engine import upload
from channels.trending import config as cfg

SETTLE_TRIES, SETTLE_WAIT = 6, 8  # a freshly created playlist answers 404 (listing) or 409 (adding) for a few seconds


def _settled(fn, empty=None):
    """Run fn, retrying while YouTube says the new playlist is not there yet (404/409). After the last try return
    `empty` if given (an empty new playlist has nothing in it), else raise."""
    for i in range(SETTLE_TRIES):
        try:
            return fn()
        except HttpError as exc:
            if exc.resp.status not in (404, 409):
                raise
            if i == SETTLE_TRIES - 1:
                if empty is not None:
                    return empty
                raise
            time.sleep(SETTLE_WAIT)


def video_ids(yt, playlist_id: str) -> set[str]:
    ids, token = set(), None
    while True:
        r = _settled(lambda: upload._retry(lambda: yt.playlistItems().list(
            part="contentDetails", playlistId=playlist_id, maxResults=50, pageToken=token).execute()),
            empty={"items": []})
        ids |= {i["contentDetails"]["videoId"] for i in r.get("items", [])}
        token = r.get("nextPageToken")
        if not token:
            return ids


def add(yt, video_id: str, lang: str, niche: str) -> str:
    title, desc = cfg.playlist_for(lang, niche)
    pid = upload.find_or_create_playlist(yt, title, desc, lang)
    if video_id in video_ids(yt, pid):
        return f"already in playlist {title}"
    _settled(lambda: upload.add_to_playlist(yt, video_id, pid))
    return f"added to playlist {title}"
