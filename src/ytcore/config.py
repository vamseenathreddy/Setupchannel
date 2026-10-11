"""
Application configuration.

All runtime configuration is centralized here and loaded from environment
variables (populated from a .env file in development, or real environment
variables in Docker/CI/production). Nothing else in the codebase should
call os.environ directly — import `get_settings()` instead.

Using pydantic-settings gives us:
- Fail-fast validation (a missing/malformed value raises at startup,
  not at 5 AM when the scheduled job runs).
- A single typed object (`Settings`) that's easy to mock in tests.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ytcore.exceptions import ConfigError

# Project root = two levels up from this file (src/ytcore/config.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

WEEKDAY_FOLDER_MAP: dict[int, str] = {
    0: "Monday_Shiva",
    1: "Tuesday_Hanuman",
    2: "Wednesday_Ganesha",
    3: "Thursday_Sai",
    4: "Friday_Lakshmi",
    5: "Saturday_Venkateswara",
    6: "Sunday_Surya",
}
# Note: Python's date.weekday() -> Monday=0 ... Sunday=6, matches the map above.


class Settings(BaseSettings):
    """Strongly-typed application settings, loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MAHANAVI_",
        extra="ignore",
    )

    # --- Paths ---
    images_root: Path = Field(default=PROJECT_ROOT / "Images")
    assets_dir: Path = Field(default=PROJECT_ROOT / "assets")
    output_dir: Path = Field(default=PROJECT_ROOT / "data" / "generated")
    database_path: Path = Field(default=PROJECT_ROOT / "data" / "mahanavi.db")
    log_dir: Path = Field(default=PROJECT_ROOT / "data" / "logs")

    # --- Scheduling ---
    timezone: str = Field(default="Asia/Kolkata")

    # --- Branding ---
    # Primary font is now Ponnala (bold synthesized; Latin falls back to Noto
    # Sans Telugu Bold -- see images/fonts.py). Original note: needs BOTH Telugu and Latin glyph coverage, since the
    # Panchang panel mixes Telugu labels with content that's often in
    # English (tithi/nakshatram names, "AM"/"PM" in times) — Noto Sans
    # Telugu covers both; a Telugu-only display font would render tofu
    # boxes for any Latin content (confirmed via a real render test).
    telugu_font_path: Path = Field(default=PROJECT_ROOT / "assets" / "fonts" / "Ponnala-Regular.ttf")

    # --- Alert Shorts (Rahu Kalam / Shubha Ghadiyalu) ---
    # Icons shown in a row at the top of each card, in this left-to-right
    # order: Lakshmi, Ganesha, Kubera. All optional -- a missing/unset
    # path just means that card renders without an icon row rather than
    # failing (see AlertCardRenderer._draw_icon_row).
    alert_icon_lakshmi_path: Path | None = Field(default=PROJECT_ROOT / "assets" / "icons" / "lakshmi.png")
    alert_icon_ganesha_path: Path | None = Field(default=PROJECT_ROOT / "assets" / "icons" / "ganesha.png")
    alert_icon_kubera_path: Path | None = Field(default=PROJECT_ROOT / "assets" / "icons" / "kubera.png")
    # Royalty-free background music baked into each Short. Committed to
    # the repo (assets/music/) rather than driven by an env var, since
    # it is not a secret -- this way it just works in CI with no extra
    # workflow wiring, and a real file has to exist here or
    # audio/mixer.py raises Channel AError rather than silently shipping
    # a silent-audio-track Short.
    alert_short_music_path: Path | None = Field(default=PROJECT_ROOT / "assets" / "music" / "alert_bgm.mp3")

    # Sarvam AI Telugu voiceover (long-form Puranam videos) -- get a key
    # at sarvam.ai/try/tts-api. "meera" is Sarvam's own recommended
    # voice for warm storytelling narration.
    sarvam_api_key: str | None = Field(default=None)
    # "priya" confirmed compatible with model bulbul:v3 specifically --
    # a real API call showed "anushka" (valid for OTHER Sarvam models)
    # is NOT in bulbul:v3's own speaker roster: aditya, ritu, ashutosh,
    # priya, neha, rahul, pooja, rohan, simran, kavya, amit, dev,
    # ishita, shreya, ratan, varun, manan, sumit, roopa, kabir, aayan,
    # shubh, advait, anand, tanya, tarun, sunny, mani, gokul, vijay,
    # shruti, suhani, mohit, kavitha, rehan, soham, rupali. Override
    # this if you prefer a different voice after previewing options.
    sarvam_voice: str = Field(default="priya")
    sarvam_pace: float = Field(default=0.92, ge=0.5, le=2.0)
    sarvam_temperature: float = Field(default=0.75, ge=0.01, le=2.0)
    sarvam_speech_sample_rate: int = Field(default=24000)
    # All series' durations standardized to 5 seconds (explicit request,
    # 2026-10-03: "I want them to make only 5 seconds. Because youtube
    # paying per short view not short length so if it's 5 seconds it's
    # fine") -- YouTube Shorts monetization/view-counting rewards view
    # count and completion/loop rate, not raw length, so there is no
    # benefit to a longer card, only more loops needed to re-count as a
    # fresh view. Was 10.0 before this change.
    alert_short_duration_seconds: float = Field(default=5.0, gt=0)
    # Deliberately shorter than a comfortable full read of a Rashi Mantra
    # card (5-6 text blocks, ~10-14s to read once) -- short enough that
    # most viewers loop 2-3x to finish reading, which YouTube Shorts
    # counts as fresh views and reads as a retention signal. Use this
    # together with video.assembler.LOOP_FRIENDLY_FADE_IN_SECONDS /
    # LOOP_FRIENDLY_FADE_OUT_SECONDS (both 0.0) so the loop has no
    # visible/audible seam -- it should read as one stable, continuous
    # view, not a video restarting. See video/assembler.py module
    # docstring (explicit request, 2026-10-01) for the full reasoning.
    # Standardized to 5 seconds along with every other series (explicit
    # request, 2026-10-03, see alert_short_duration_seconds above) -- was
    # 8.0 before this change.
    rashi_mantra_short_duration_seconds: float = Field(default=5.0, gt=0)

    # Purana Story Shorts (post_purana_short.py) -- same loop-friendly,
    # no-fade design as the Rashi Mantra Shorts above. Explicitly set to
    # 5 seconds per request (2026-10-02: "short should be 5 seconds
    # without fade") -- deliberately shorter than a comfortable read of
    # the full story, so viewers loop 2-3x to finish, with the loop
    # seam kept invisible (LOOP_FRIENDLY_FADE_*_SECONDS, both 0.0).
    purana_short_duration_seconds: float = Field(default=5.0, gt=0)

    # Purana Concept Shorts (post_concept_short.py) -- the sixth series,
    # 11 AM-1 PM IST window, rotating through 6 non-story concepts drawn
    # from all 18 Puranas (2026-10-02: "rotate above 6 concepts daily
    # from all 18 puranas in another short between 11 am to 1 pm"). Same
    # loop-friendly, no-fade, short-duration design as every other Short
    # on this channel.
    purana_concept_short_duration_seconds: float = Field(default=5.0, gt=0)

    # Bhagavad Gita Sloka Shorts (post_gita_sloka_short.py) -- the
    # seventh series, 3-4 PM IST window, one verse + Telugu meaning per
    # day (2026-10-02: "from bhagavadgeetha get daily one sloka and
    # meening shorts card at 3 to 4 pm daily"). Same loop-friendly,
    # no-fade, short-duration design as every other Short on this
    # channel. Standardized to 5 seconds along with every other series
    # (explicit request, 2026-10-03, see alert_short_duration_seconds
    # above) -- was 6.0 before this change.
    gita_sloka_short_duration_seconds: float = Field(default=5.0, gt=0)

    # Real Krishna-Arjuna chariot artwork (user-supplied, 2026-10-03),
    # replacing the abstract line-art chariot watermark as the Gita
    # Sloka/Quiz cards' actual background -- faded under a dark overlay
    # so the Sanskrit/Telugu text on top stays cleanly readable (see
    # images/gita_sloka_card_renderer.py's _build_background).
    gita_background_image_path: Path | None = Field(
        default=PROJECT_ROOT / "assets" / "images" / "gita_krishna_arjuna_bg.png"
    )

    # fal.ai (AI-generated Purana scene visuals: FLUX.1 [dev] stills +
    # Kling 2.5 Turbo Pro image-to-video animation) -- get a key at
    # fal.ai/dashboard/keys. Pay-as-you-go, no plan to pick; add a
    # payment method on that same billing page before this will work.
    fal_api_key: str | None = Field(default=None)

    # --- Image rendering ---
    image_output_format: str = Field(default="JPEG")
    image_output_quality: int = Field(default=95, ge=1, le=100)

    # --- Panchang provider ---
    panchang_provider: str = Field(default="dummy")  # "dummy" | "api" | "scraper" | "prokerala"
    panchang_api_base_url: str | None = Field(default=None)
    panchang_api_key: str | None = Field(default=None)
    panchang_latitude: float = Field(default=17.3850)   # Hyderabad default
    panchang_longitude: float = Field(default=78.4867)
    # Prokerala Astrology API (https://api.prokerala.com/) — real Panchang
    # data, forever-free tier. Get client_id/client_secret from your
    # Prokerala dashboard under Integration -> App IDs.
    prokerala_client_id: str | None = Field(default=None)
    prokerala_client_secret: str | None = Field(default=None)
    prokerala_client_id_2: str | None = Field(default=None)
    prokerala_client_secret_2: str | None = Field(default=None)

    # --- YouTube ---
    # client_secrets.json: downloaded from Google Cloud Console
    # (APIs & Services -> Credentials -> OAuth client ID -> Desktop app).
    # Used by the official Data API v3 Shorts uploader (Alert Shorts).
    youtube_client_secrets_file: Path | None = Field(default=PROJECT_ROOT / "client_secrets.json")
    youtube_token_file: Path = Field(default=PROJECT_ROOT / "data" / "youtube_token.json")

    # --- Blogger (migrated off a broken IFTTT applet, 2026-10-06 -- the
    # applet's thumbnail-URL formula was literal unresolved template
    # syntax, `{{Url?split('v=')[1]}}`, landing in every post instead of
    # a real video ID, so no image ever rendered -- see
    # publishers/blogger_publisher.py's module docstring). The numeric
    # blog ID (NOT the blog's URL) -- find it in Blogger's dashboard
    # under Settings, or in the address bar of the post-editor page.
    # Reuses youtube_token_file above (same Google account), so needs no
    # separate credentials file -- just the
    # https://www.googleapis.com/auth/blogger scope added to that token
    # (see youtube_shorts_auth_setup.py's SCOPES). Unset = blog posting
    # is silently skipped everywhere, never a hard failure.
    blogger_blog_id: str | None = Field(default=None)

    # --- Channel D (second YouTube channel, same repo, added
    # 2026-10) -- a fully separate channel/pipeline under ramana/ at the
    # repo root (its own content bank, renderer, gate), but it reuses
    # this repo's YouTube client_secrets.json (same Google Cloud OAuth
    # project, a SEPARATE token file since it's a different channel) and
    # the SAME Drive service account/folder for its tiny state file
    # (see scripts/ci/drive_state_sync.py's STATE_FILES). Create this
    # token once locally with `python -m
    # ytcore.scripts.youtube_shorts_auth_setup --token-file
    # data/youtube_token_ramana.json`, choosing the Channel D
    # channel at the Google consent screen. Blog id/playlist id follow
    # the same "unset = silently skipped" convention as the fields
    # above.
    ramana_youtube_token_file: Path = Field(default=PROJECT_ROOT / "data" / "youtube_token_ramana.json")
    ramana_blogger_blog_id: str | None = Field(default=None)
    ramana_playlist_id: str | None = Field(default=None)

    # --- The 7-channel expansion (channels/ at the repo root, added 2026-10) ---
    # Same pattern as ramana_* above for every field: a separate YouTube OAuth
    # token file (possibly a different Google account entirely -- "is all
    # this channels are my different gmail accounts but some might be in
    # same gmail account" -- each channel's own token is created
    # independently via `youtube_shorts_auth_setup.py --token-file ...`
    # regardless of which account it belongs to), an optional dedicated
    # Blogger blog, and an optional playlist. All unset = silently skipped,
    # same convention as every field above.
    mantra_sangam_youtube_token_file: Path = Field(default=PROJECT_ROOT / "data" / "youtube_token_mantra_sangam.json")
    mantra_sangam_blogger_blog_id: str | None = Field(default=None)
    mantra_sangam_playlist_id: str | None = Field(default=None)

    trance_beats_youtube_token_file: Path = Field(default=PROJECT_ROOT / "data" / "youtube_token_trance_beats.json")
    trance_beats_blogger_blog_id: str | None = Field(default=None)
    trance_beats_playlist_id: str | None = Field(default=None)


    # --- Telegram alerts (pipeline health review, 2026-10-03) ---
    # See notifications/telegram_alert.py's module docstring for the
    # one-time @BotFather setup. Both unset = alerts are silently
    # skipped everywhere (never a hard failure on their own).
    telegram_bot_token: str | None = Field(default=None)
    telegram_chat_id: str | None = Field(default=None)

    # --- YouTube playlists (pipeline health review, 2026-10-03) ---
    # One playlist per series, created once via
    # scripts/youtube_playlists_setup.py -- each posting script adds
    # its video to the matching playlist after a successful upload
    # (non-fatal if unset/missing, same pattern as comments). Grouping
    # the two Gita modes (verse + quiz) into ONE playlist since they're
    # literally one alternating series, not two.
    playlist_id_muhurtas: str | None = Field(default=None)
    playlist_id_gita_sloka: str | None = Field(default=None)
    playlist_id_puranas: str | None = Field(default=None)
    playlist_id_rashi: str | None = Field(default=None)
    # Added 2026-10-03 for the AI-generated devotional song series
    # (Navaratri 2026 onward) -- separate from the Shorts playlists
    # above since these are full-length songs, not Shorts.
    playlist_id_navaratri_songs: str | None = Field(default=None)
    playlist_id_stotras: str | None = Field(default=None)

    max_retries: int = Field(default=3, ge=0)
    retry_backoff_seconds: float = Field(default=5.0, ge=0)

    @model_validator(mode="before")
    @classmethod
    def _blank_env_vars_mean_unset(cls, data: object) -> object:
        """Treat an empty-string env var as 'not set' rather than a real value.

        Without this, MAHANAVI_FAL_API_KEY= (present but empty) coerces to
        an empty string instead of None, which then fails an API call with
        a confusing auth error instead of a clear "not configured" one.
        Any optional field left blank in .env should behave as if it were
        omitted entirely.
        """
        if isinstance(data, dict):
            return {k: (None if v == "" else v) for k, v in data.items()}
        return data

    @field_validator("images_root")
    @classmethod
    def _images_root_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ConfigError(
                f"images_root does not exist: {v}. "
                "Set MAHANAVI_IMAGES_ROOT or create the folder."
            )
        return v

    def weekday_folder(self, weekday: int) -> Path:
        """Return the image folder for a given Python weekday (Mon=0..Sun=6)."""
        try:
            folder_name = WEEKDAY_FOLDER_MAP[weekday]
        except KeyError as exc:
            raise ConfigError(f"Invalid weekday index: {weekday}") from exc
        return self.images_root / folder_name

    def ensure_runtime_dirs(self) -> None:
        """Create output/log/data directories if they don't exist yet."""
        for path in (self.output_dir, self.log_dir, self.database_path.parent):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, process-wide Settings instance."""
    settings = Settings()
    settings.ensure_runtime_dirs()
    return settings
