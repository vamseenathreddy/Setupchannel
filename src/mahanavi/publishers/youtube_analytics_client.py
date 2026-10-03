"""
youtube_analytics_client.py: thin wrapper around the YouTube Analytics
API v2 (a DIFFERENT API from youtube_shorts_uploader.py's Data API v3)
-- added 2026-10-03 (pipeline health review suggestion #3, "no
performance feedback loop"). Used only by
scripts/weekly_performance_report.py.

REQUIRES THE yt-analytics.readonly SCOPE, which the existing saved
token does NOT have until a one-time re-auth (youtube_shorts_auth_setup.py
now requests it too -- see that script's SCOPES). Until that re-auth
happens, every call here fails with an HttpError naming the missing
scope; weekly_performance_report.py catches that and prints/alerts
clear instructions rather than crashing confusingly.

Deliberately NOT sharing YouTubeShortsUploader._build_service() --
that builds a "youtube" v3 service; this builds a DIFFERENT
"youtubeAnalytics" v2 service, so the credential-loading is
necessarily duplicated here (same house style as the small amount of
shared-but-not-factored-out code across this codebase's renderer
classes) rather than threading an API-name parameter through a method
whose whole point is Data API v3 uploads.
"""

from __future__ import annotations

from mahanavi.config import Settings
from mahanavi.exceptions import YouTubeUploadError


def build_analytics_service(settings: Settings) -> "object":  # googleapiclient's Resource type isn't meaningfully annotable
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise YouTubeUploadError(
            "Missing packages. Run: pip install google-api-python-client google-auth-oauthlib google-auth"
        ) from exc

    token_file = settings.youtube_token_file
    if not token_file.exists():
        raise YouTubeUploadError(
            f"No saved YouTube API token at {token_file}. "
            "Run `python -m mahanavi.scripts.youtube_shorts_auth_setup` once first."
        )

    # Same deliberate omission of an explicit `scopes=` argument as
    # YouTubeShortsUploader._build_service() -- see that method's long
    # comment for why. Falls back to whatever scopes the saved token
    # file itself carries.
    credentials = Credentials.from_authorized_user_file(str(token_file))
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_file.write_text(credentials.to_json(), encoding="utf-8")

    return build("youtubeAnalytics", "v2", credentials=credentials)


def fetch_video_stats(
    settings: Settings, video_ids: list[str], start_date: str, end_date: str,
) -> dict[str, dict[str, float]]:
    """Returns {video_id: {"views": ..., "likes": ..., "averageViewPercentage": ...}}
    for every video_id in `video_ids` that has data in [start_date, end_date]
    (YYYY-MM-DD strings). A video with zero views in the window simply
    doesn't appear in the result -- callers should treat a missing key
    as "no activity", not an error.

    Raises YouTubeUploadError (missing token/packages) or re-raises
    googleapiclient's HttpError (most commonly: missing
    yt-analytics.readonly scope) -- both are caught by the caller,
    which has the context to print a clear, actionable message."""
    if not video_ids:
        return {}

    service = build_analytics_service(settings)
    response = service.reports().query(  # type: ignore[attr-defined]
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics="views,likes,averageViewPercentage",
        dimensions="video",
        filters=f"video=={','.join(video_ids)}",
    ).execute()

    results: dict[str, dict[str, float]] = {}
    column_names = [h["name"] for h in response.get("columnHeaders", [])]
    for row in response.get("rows", []):
        row_dict = dict(zip(column_names, row))
        video_id = str(row_dict.get("video"))
        results[video_id] = {
            "views": float(row_dict.get("views", 0) or 0),
            "likes": float(row_dict.get("likes", 0) or 0),
            "averageViewPercentage": float(row_dict.get("averageViewPercentage", 0) or 0),
        }
    return results
