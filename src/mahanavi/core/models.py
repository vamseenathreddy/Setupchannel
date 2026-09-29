"""Domain models shared across the pipeline. Plain dataclasses, no ORM coupling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum
from pathlib import Path


class Deity(str, Enum):
    SHIVA = "Shiva"
    HANUMAN = "Hanuman"
    GANESHA = "Ganesha"
    SAI = "Sai"
    LAKSHMI = "Lakshmi"
    VENKATESWARA = "Venkateswara"
    SURYA = "Surya"
    DATTATREYA = "Dattatreya"


@dataclass(frozen=True, slots=True)
class SelectedImage:
    """An image chosen for today's post."""
    path: Path
    folder_name: str          # e.g. "Monday_Shiva"
    filename: str              # e.g. "shiva_012.jpg"
    deity: Deity


@dataclass(frozen=True, slots=True)
class PanchangData:
    """Telugu Panchang details for a single day."""
    date_: date
    tithi: str
    nakshatram: str
    varjyam: str
    rahu_kalam: str
    yamagandam: str
    gulika_kalam: str
    durmuhurtham: str
    abhijit_muhurtham: str
    sunrise: time
    sunset: time
    # Added per explicit request for a richer Panchang breakdown — all
    # optional (default empty/None) so existing providers that don't
    # supply them keep working unchanged.
    karana: str = ""
    yoga: str = ""
    amrit_kaal: str = ""
    moonrise: time | None = None
    moonset: time | None = None
    festivals: list[str] = field(default_factory=list)
    marriage_muhurats: str = ""
    source: str = "unknown"   # which provider produced this (for auditing)


class PublishTarget(str, Enum):
    YOUTUBE = "youtube"
    TELEGRAM = "telegram"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


@dataclass(slots=True)
class UploadResult:
    """Result of attempting to publish to one target."""
    target: PublishTarget
    success: bool
    post_url: str | None = None
    error_message: str | None = None
    screenshot_path: Path | None = None
