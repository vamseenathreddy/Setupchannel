"""YouTube Data API v3: upload, captions, playlist, seed comment.

Shared by every channel in this repo (originally written for Channel D,
see ramana/src/upload.py; copied here unchanged, byte-for-byte, so the
Pattern-A engine (channels/engine/) has its own copy to import without
depending on ramana/). Each channel is a separate YouTube channel, each with
its OWN saved token file (see ytcore.config.Settings' per-channel
*_youtube_token_file fields), but every one of them can reuse the SAME
Google Cloud OAuth project/client_secrets.json already used by this repo --
or a different Google account entirely if that channel lives there (any
Google account can consent to the same OAuth client). Create each channel's
token once by running `python -m ytcore.scripts.youtube_shorts_auth_setup
--token-file <path for this channel>` locally and choosing the right
channel/account at the Google consent screen.

Deliberately does NOT pass an explicit scopes= to Credentials.from_authorized_user_file
-- see YouTubeShortsUploader._build_service()'s long comment in
src/ytcore/publishers/youtube_shorts_uploader.py for why (a documented past
production incident, RefreshError: invalid_scope).
"""
from ytcore.brandcfg import D_NAME  # noqa: E402
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
            "`python -m ytcore.scripts.youtube_shorts_auth_setup --token-file "
            f"{token_file}` once first, choosing the {D_NAME} channel."
        )
    credentials = Credentials.from_authorized_user_file(str(token_file))
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        Path(token_file).write_text(credentials.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def _retry(fn, attempts=5):
    for i in range(attempts):
        try:
            return fn()
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and i < attempts - 1:
                time.sleep(2 ** (i + 1))
                continue
            raise


def upload_video(yt, path, title, description, tags, localizations=None, publish_at=None, privacy_status="public", language=None):
    """publish_at: aware UTC datetime for a scheduled release, or None to publish immediately.
    privacy_status: "public" or "unlisted" (added 2026-10 to match this repo's --public-by-default-off
    testing convention -- see post_rashi_mantra_short.py's --public flag). Ignored when publish_at is set
    (a scheduled release is always uploaded "private" until it goes live)."""
    status = {"selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}  # realistic AI artwork must be disclosed
    if publish_at:
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    else:
        status["privacyStatus"] = privacy_status
    body = {
        "snippet": {"title": title[:100], "description": description[:4900], "tags": tags,
                    "categoryId": "22", "defaultLanguage": language or "en"},
        "status": status,
    }
    if language:
        body["snippet"]["defaultAudioLanguage"] = language
    part = "snippet,status"
    if localizations:
        body["localizations"] = localizations
        part += ",localizations"
    media = MediaFileUpload(path, mimetype="video/mp4", chunksize=-1, resumable=True)
    req = yt.videos().insert(part=part, body=body, media_body=media)
    response = None
    while response is None:
        _, response = _retry(req.next_chunk)
    return response["id"]


def add_caption(yt, video_id, language, name, srt_text):
    media = MediaIoBaseUpload(io.BytesIO(srt_text.encode("utf-8")), mimetype="application/octet-stream")
    body = {"snippet": {"videoId": video_id, "language": language, "name": name, "isDraft": False}}
    return _retry(lambda: yt.captions().insert(part="snippet", body=body, media_body=media).execute())["id"]


def find_or_create_playlist(yt, title, description="", language="en"):
    """Return the id of this channel's playlist named `title`, creating it (public) if missing, so a
    new series needs no manual setup or secret."""
    token = None
    while True:
        r = _retry(lambda: yt.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=token).execute())
        for it in r.get("items", []):
            if it["snippet"]["title"].strip() == title.strip():
                return it["id"]
        token = r.get("nextPageToken")
        if not token:
            break
    body = {"snippet": {"title": title, "description": description, "defaultLanguage": language},
            "status": {"privacyStatus": "public"}}
    return _retry(lambda: yt.playlists().insert(part="snippet,status", body=body).execute())["id"]


def add_to_playlist(yt, video_id, playlist_id):
    body = {"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}
    return _retry(lambda: yt.playlistItems().insert(part="snippet", body=body).execute())["id"]


def add_comment(yt, video_id, text):
    body = {"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}}
    return _retry(lambda: yt.commentThreads().insert(part="snippet", body=body).execute())["id"]
