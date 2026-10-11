"""
blogger_publisher.py: posts a short blog entry on Blogspot -- migrated
2026-10-06 off a broken IFTTT applet (YouTube new-video trigger ->
Blogger create-post action) whose thumbnail-URL formula was literal,
unresolved template syntax --
`https://i.ytimg.com/vi_webp/{{Url?split('v=')[1]}}/maxresdefault.webp`
-- landing in every single post's HTML instead of a real video ID
(confirmed via the blog's own RSS feed, 2026-10-06). IFTTT's `{{ }}`
action-field placeholders only resolve to literal ingredient names;
they do not evaluate an arbitrary JS-like expression like
`?split('v=')[1]` inside them, so that text was never going to render
as an image.

Uses the official Blogger API v3 instead, called right after a
successful YouTube upload from each post_*.py script -- the video_id
is already in hand at that point, so the thumbnail URL is built
directly from it: https://i.ytimg.com/vi/<id>/hqdefault.jpg, which
YouTube guarantees to exist for every uploaded video. (maxresdefault.jpg,
what the old IFTTT formula was reaching for, is NOT guaranteed to exist
for every video -- notably for some Shorts/vertical uploads -- which
would have caused the same "image sometimes missing" symptom even with
a correctly-evaluated formula.)

REQUIRES the https://www.googleapis.com/auth/blogger scope on the
saved token (added 2026-10-06 to youtube_shorts_auth_setup.py's
SCOPES). A token saved before this change does NOT have it until a
one-time LOCAL re-auth (this needs a real browser window, so it cannot
be done from CI): re-run
`python -m ytcore.scripts.youtube_shorts_auth_setup` once, then push
the refreshed data/youtube_token.json to Drive
(`python scripts/ci/drive_state_sync.py push`).

Same non-fatal, logs-a-warning-and-returns-False pattern as
YouTubeShortsUploader.post_comment() / add_to_playlist() -- a failed
blog post must never fail the whole posting pipeline, since the video
itself already uploaded successfully by the time this runs. Also
returns False (quietly, via logger.info not a warning) when
settings.blogger_blog_id isn't configured at all, so this is a no-op
until that's set up, not an error.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ytcore.config import Settings
from ytcore.exceptions import YouTubeUploadError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/blogger"]


def _build_service(settings: Settings, token_file: Path | None = None) -> "object":  # googleapiclient's Resource type isn't meaningfully annotable
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise YouTubeUploadError(
            "Missing packages. Run: pip install google-api-python-client google-auth-oauthlib google-auth"
        ) from exc

    token_file = token_file if token_file is not None else settings.youtube_token_file
    if not token_file.exists():
        raise YouTubeUploadError(
            f"No saved YouTube/Blogger API token at {token_file}. "
            "Run `python -m ytcore.scripts.youtube_shorts_auth_setup` once first."
        )

    # Same deliberate omission of an explicit `scopes=` argument as
    # YouTubeShortsUploader._build_service() -- see that method's long
    # comment for why. Falls back to whatever scopes the saved token
    # file itself carries.
    credentials = Credentials.from_authorized_user_file(str(token_file))
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_file.write_text(credentials.to_json(), encoding="utf-8")

    return build("blogger", "v3", credentials=credentials)


def post_to_blogger(
    settings: Settings,
    video_id: str,
    title: str,
    description: str,
    blog_id: str | None = None,
    token_file: Path | None = None,
) -> bool:
    """Creates a new Blogger post with a real thumbnail image, a short
    description, and an embedded player for `video_id`. Returns False
    (and logs a warning, or just an info line if blogging isn't
    configured) rather than raising on any failure -- see module
    docstring.

    blog_id: overrides settings.blogger_blog_id -- lets other channels in
    this repo (e.g. Channel D, settings.ramana_blogger_blog_id)
    reuse this same function to post to THEIR OWN separate Blogger blog,
    added 2026-10 when this repo grew beyond one channel/one blog.

    token_file: overrides settings.youtube_token_file -- only needed if a
    new channel's Google account differs from the main one (if it's the
    same Google account under a different brand-account channel, the
    default main token already has Blogger access to every blog that
    account owns, so this can usually be left unset)."""
    blog_id = blog_id if blog_id is not None else settings.blogger_blog_id
    if not blog_id:
        logger.info("No Blogger blog id configured for this video -- skipping Blogger post.")
        return False

    try:
        service = _build_service(settings, token_file)
    except YouTubeUploadError as exc:
        logger.warning("Could not post to Blogger for video %s (service build failed): %s", video_id, exc)
        return False

    try:
        from googleapiclient.errors import HttpError
    except ImportError as exc:
        logger.warning("Could not post to Blogger for video %s (missing package): %s", video_id, exc)
        return False

    # hqdefault.jpg, not maxresdefault.jpg -- see module docstring for
    # why maxresdefault isn't a safe universal choice.
    thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    content = (
        f'<p><a href="{watch_url}"><img src="{thumbnail_url}" alt="{title}" '
        f'style="max-width:100%;height:auto;"/></a></p>'
        f"<p>{description}</p>"
        f'<p><iframe width="560" height="315" '
        f'src="https://www.youtube.com/embed/{video_id}" title="{title}" '
        f'frameborder="0" allow="accelerometer; autoplay; clipboard-write; '
        f'encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></p>'
    )

    try:
        service.posts().insert(  # type: ignore[attr-defined]
            blogId=blog_id,
            body={"title": title, "content": content},
        ).execute()
        logger.info("Posted to Blogger for video %s", video_id)
        return True
    except HttpError as exc:
        logger.warning(
            "Could not post to Blogger for video %s -- likely needs a re-run of "
            "youtube_shorts_auth_setup.py for the blogger scope: %s", video_id, exc,
        )
        return False
    except Exception as exc:  # genuinely need to catch anything else the SDK can raise
        logger.warning("Unexpected error posting to Blogger for video %s: %s", video_id, exc)
        return False
