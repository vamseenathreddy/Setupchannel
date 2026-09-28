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

from mahanavi.exceptions import ConfigError

# Project root = two levels up from this file (src/mahanavi/config.py -> project root)
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
    post_hour: int = Field(default=5, ge=0, le=23)
    post_minute: int = Field(default=0, ge=0, le=59)

    # --- Branding ---
    channel_name: str = Field(default="Mahanavi Spirituals")
    watermark_text: str = Field(default="Mahanavi Spirituals")
    # Primary font: needs BOTH Telugu and Latin glyph coverage, since the
    # Panchang panel mixes Telugu labels with content that's often in
    # English (tithi/nakshatram names, "AM"/"PM" in times) — Noto Sans
    # Telugu covers both; a Telugu-only display font would render tofu
    # boxes for any Latin content (confirmed via a real render test).
    telugu_font_path: Path = Field(default=PROJECT_ROOT / "assets" / "fonts" / "NotoSansTelugu-Variable.ttf")
    # Decorative font: used ONLY for elements that are guaranteed pure
    # Telugu with no mixed Latin content (the header date, the deity
    # banner) — Ponnala (SIL OFL, by Appaji Ambarisha Darbha / Silicon
    # Andhra), a bolder, more traditional/devotional-poster calligraphic
    # style than Noto. It has no Latin glyphs at all, so it must never be
    # used anywhere Latin text could appear (the Panchang panel's mixed
    # content, or the watermark, which defaults to the English channel
    # name).
    decorative_font_path: Path = Field(default=PROJECT_ROOT / "assets" / "fonts" / "Ponnala-Regular.ttf")
    logo_path: Path | None = Field(default=PROJECT_ROOT / "assets" / "logo" / "logo.png")

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
    # audio/mixer.py raises MahanaviError rather than silently shipping
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
    alert_short_duration_seconds: float = Field(default=10.0, gt=0)

    # fal.ai (AI-generated Purana scene visuals: FLUX.1 [dev] stills +
    # Kling 2.5 Turbo Pro image-to-video animation) -- get a key at
    # fal.ai/dashboard/keys. Pay-as-you-go, no plan to pick; add a
    # payment method on that same billing page before this will work.
    fal_api_key: str | None = Field(default=None)

    # --- Image rendering ---
    canvas_width: int = Field(default=1080, gt=0)
    canvas_height: int = Field(default=1350, gt=0)
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
    # Used only by the official Data API v3 Shorts uploader -- the
    # existing Community Post automation (youtube_playwright_uploader.py)
    # doesn't need this at all, since Community Posts have no API.
    youtube_client_secrets_file: Path | None = Field(default=PROJECT_ROOT / "client_secrets.json")
    youtube_token_file: Path = Field(default=PROJECT_ROOT / "data" / "youtube_token.json")
    youtube_channel_id: str | None = Field(default=None)
    youtube_community_post_method: str = Field(default="playwright")  # "api" | "playwright"
    youtube_session_state_file: Path = Field(default=PROJECT_ROOT / "data" / "yt_session_state.json")

    # --- Telegram ---
    telegram_bot_token: str | None = Field(default=None)
    telegram_channel_id: str | None = Field(default=None)   # e.g. "@mahanavispirituals"
    telegram_admin_chat_id: str | None = Field(default=None)  # for operator notifications

    # --- Facebook / Instagram (optional) ---
    facebook_page_id: str | None = Field(default=None)
    facebook_page_access_token: str | None = Field(default=None)
    instagram_business_account_id: str | None = Field(default=None)
    instagram_access_token: str | None = Field(default=None)
    instagram_image_public_base_url: str | None = Field(default=None)

    # --- Content / SEO ---
    seo_max_caption_length: int = Field(default=1500, gt=0)

    max_retries: int = Field(default=3, ge=0)
    retry_backoff_seconds: float = Field(default=5.0, ge=0)

    # --- Feature toggles ---
    enable_facebook: bool = Field(default=False)
    enable_instagram: bool = Field(default=False)

    @model_validator(mode="before")
    @classmethod
    def _blank_env_vars_mean_unset(cls, data: object) -> object:
        """Treat an empty-string env var as 'not set' rather than a real value.

        Without this, MAHANAVI_LOGO_PATH= (present but empty) coerces to
        Path('.') — the current directory — instead of None, and the
        renderer would then try to open the working directory as an image.
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
