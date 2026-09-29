"""
Abstract interfaces for the pluggable components still used by the
active pipelines (Alert Shorts, Purana videos).

Why this file matters: it's the contract that lets us swap implementations
without touching the callers.

    - Need to switch Panchang from a dummy provider to a real API?
      Write a new PanchangProvider subclass. Nothing else changes.
    - Want a different image-selection strategy?
      Implement ImageSelector.

Every concrete implementation lives in its own module/package
(mahanavi.panchang.*, mahanavi.images.*, etc.).

Note: this file used to also define ImageRenderer, ContentGenerator,
Uploader, and Notifier for the Daily Community Post pipeline (removed --
it never got engagement). Those ABCs had exactly one implementation each,
all in the Community Post's own modules, and nothing in the Alert Shorts
or Purana pipelines depended on them -- confirmed by grep before removal.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from mahanavi.core.models import PanchangData, SelectedImage


class PanchangProvider(ABC):
    """Source of daily Telugu Panchang data. Swappable: API today, scraper tomorrow."""

    @abstractmethod
    def fetch(self, for_date: date) -> PanchangData:
        """Return Panchang details for the given date, or raise PanchangFetchError."""
        raise NotImplementedError


class ImageSelector(ABC):
    """Chooses today's devotional image, respecting non-repetition rules."""

    @abstractmethod
    def select_for_date(self, for_date: date) -> SelectedImage:
        """Return the chosen image for the given date, or raise ImageSelectionError."""
        raise NotImplementedError
