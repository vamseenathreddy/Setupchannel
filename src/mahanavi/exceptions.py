"""
Centralized exception hierarchy for Channel A.

Every module raises exceptions from this file (or subclasses of them)
rather than bare Exception / built-in errors, so the orchestration layer
(pipeline.py) can catch failures precisely, log them meaningfully, and
decide whether to retry.
"""

from __future__ import annotations


class MahanaviError(Exception):
    """Base class for all application-specific errors."""


# --- Configuration -----------------------------------------------------

class ConfigError(MahanaviError):
    """Raised when required configuration is missing or invalid."""


# --- Database ------------------------------------------------------------

class DatabaseError(MahanaviError):
    """Raised for any SQLite/database-layer failure."""


class RecordNotFoundError(DatabaseError):
    """Raised when an expected database record does not exist."""


# --- Image selection & rendering ---------------------------------------

class ImageSelectionError(MahanaviError):
    """Raised when no valid image can be selected for a given day."""


class ImageRenderError(MahanaviError):
    """Raised when Pillow-based composition of the final image fails."""

class VideoAssemblyError(MahanaviError):
    """Raised when ffmpeg-based video assembly (image + audio -> .mp4) fails."""
# --- Panchang ------------------------------------------------------------

class PanchangFetchError(MahanaviError):
    """Raised when panchang data cannot be retrieved from any provider."""


# --- Content / SEO -------------------------------------------------------

class ContentGenerationError(MahanaviError):
    """Raised when caption/SEO content generation fails."""


# --- Publishing ------------------------------------------------------------

class UploadError(MahanaviError):
    """Base class for all publishing-target failures."""


class YouTubeUploadError(UploadError):
    """Raised when YouTube Community Post publishing fails."""


class TelegramUploadError(UploadError):
    """Raised when Telegram channel publishing fails."""


class FacebookUploadError(UploadError):
    """Raised when Facebook Page publishing fails."""


class InstagramUploadError(UploadError):
    """Raised when Instagram publishing fails."""


# --- Notifications -------------------------------------------------------

class NotificationError(MahanaviError):
    """Raised when sending an operator notification fails."""


# --- Retry helper ----------------------------------------------------------

class RetryExhaustedError(MahanaviError):
    """Raised when an operation still fails after all retry attempts."""

    def __init__(self, message: str, last_error: Exception | None = None) -> None:
        super().__init__(message)
        self.last_error = last_error
