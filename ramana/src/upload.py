"""YouTube Data API v3: upload, captions, playlist, seed comment.

Adapted 2026-10 to reuse mahanavi's file-based OAuth token pattern instead of
three raw YT_CLIENT_ID/YT_CLIENT_SECRET/YT_REFRESH_TOKEN secrets (the zip's
original scheme) -- this channel (Channel D) is a separate YouTube
channel but lives under the SAME Google Cloud OAuth project/client_secrets.json
already used by the rest of this repo, just with its own saved token file
(see mahanavi.config.Settings.ramana_youtube_token_file), created once by
running `python -m mahanavi.scripts.youtube_shorts_auth_setup --token-file
data/youtube_token_ramana.json` locally and choosing the Channel D
channel at the Google consent screen.

Deliberately does NOT pass an explicit scopes= to Credentials.from_authorized_user_file
-- see YouTubeShortsUploader._build_service()'s long comment in
src/mahanavi/publishers/youtube_shorts_uploader.py for why (a documented past
production incident, RefreshError: invalid_scope).
"""
import io
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload


def service(token_file: Path):
    if not Path(token_file).exists():
        raise SystemExit(
            f"No saved YouTube token at {token_file}. Run "
            "`python -m mahanavi.scripts.youtube_shorts_auth_setup --token-file "
            f"{token_file}` once first, choosing the Ramana Maharshi TV channel."
        )
    credentials = Credentials.from_authorized_user_file(str(token_file))
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        Path(token_file).write_text(credentials.to_json(), encoding="utf-8")
    yt = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    yt._token_file = str(token_file)  # used by the duplicate ledger
    return yt


def _retry(fn, attempts=5):
    for i in range(attempts):
        try:
            return fn()
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and i < attempts - 1:
                time.sleep(2 ** (i + 1))
                continue
            raise


def upload_video(yt, path, title, description, tags, localizations=None, publish_at=None, privacy_status="public"):
    """publish_at: aware UTC datetime for a scheduled release, or None to publish immediately.
    privacy_status: "public" or "unlisted" (added 2026-10 to match this repo's --public-by-default-off
    testing convention -- see post_rashi_mantra_short.py's --public flag). Ignored when publish_at is set
    (a scheduled release is always uploaded "private" until it goes live)."""
    from mahanavi.content import card_text
    from mahanavi.publishers import post_ledger
    description = card_text.description(description)
    yt._tags = list(tags or [])
    tf = getattr(yt, "_token_file", None)
    if tf:
        post_ledger.check(tf, title, description)  # raises DuplicatePost
    status = {"selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}  # realistic AI artwork must be disclosed
    if publish_at:
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    else:
        status["privacyStatus"] = privacy_status
    body = {
        "snippet": {"title": title[:100], "description": description[:4900], "tags": tags,
                    "categoryId": "22", "defaultLanguage": "en"},
        "status": status,
    }
    part = "snippet,status"
    if localizations:
        body["localizations"] = localizations
        part += ",localizations"
    media = MediaFileUpload(path, mimetype="video/mp4", chunksize=-1, resumable=True)
    req = yt.videos().insert(part=part, body=body, media_body=media)
    response = None
    while response is None:
        _, response = _retry(req.next_chunk)
    if tf:
        post_ledger.record(tf, title, description, response["id"])
    return response["id"]


def add_caption(yt, video_id, language, name, srt_text):
    media = MediaIoBaseUpload(io.BytesIO(srt_text.encode("utf-8")), mimetype="application/octet-stream")
    body = {"snippet": {"videoId": video_id, "language": language, "name": name, "isDraft": False}}
    return _retry(lambda: yt.captions().insert(part="snippet", body=body, media_body=media).execute())["id"]


def add_to_playlist(yt, video_id, playlist_id):
    body = {"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}
    return _retry(lambda: yt.playlistItems().insert(part="snippet", body=body).execute())["id"]


def add_comment(yt, video_id, text):
    from mahanavi.content import card_text
    from mahanavi.publishers.post_ledger import channel_name
    text = card_text.comment(text, channel_name(getattr(yt, "_token_file", "")), card_text.related_from_tags(getattr(yt, "_tags", [])))
    body = {"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}}
    return _retry(lambda: yt.commentThreads().insert(part="snippet", body=body).execute())["id"]
