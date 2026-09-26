"""
fallback_provider.py: FallbackPanchangProvider tries a list of
PanchangProvider instances in order, moving to the next one whenever
the current one raises PanchangFetchError, instead of failing the
whole daily post outright.

Built per explicit request (2026-09-26): the Prokerala free tier's
5,000 credits/month runs out a few days before the month ends, so a
second Prokerala account (separate client_id/client_secret, separate
email) can pick up where the first one's quota stops. This class is
provider-agnostic though -- it works with ANY PanchangProvider
implementations, not just two Prokerala accounts.

COMPLIANCE NOTE: check Prokerala's own terms of service on multiple
accounts before relying on this for production traffic -- some API
providers explicitly prohibit creating extra accounts to get around a
rate limit or quota.
"""

from __future__ import annotations

import logging
from datetime import date

from mahanavi.core.interfaces import PanchangProvider
from mahanavi.core.models import PanchangData
from mahanavi.exceptions import PanchangFetchError

logger = logging.getLogger(__name__)


class FallbackPanchangProvider(PanchangProvider):
    """Tries each provider in order; returns the first successful
    result. Raises PanchangFetchError (listing every provider's error)
    only if ALL of them fail."""

    def __init__(self, providers: list[PanchangProvider]) -> None:
        if not providers:
            raise ValueError("FallbackPanchangProvider requires at least one provider.")
        self._providers = providers

    def fetch(self, for_date: date) -> PanchangData:
        errors: list[str] = []
        for i, provider in enumerate(self._providers):
            provider_label = f"{type(provider).__name__} (#{i + 1}/{len(self._providers)})"
            try:
                data = provider.fetch(for_date)
                if i > 0:
                    logger.warning(
                        "Panchang provider #%d failed for %s -- fell back to %s, which succeeded.",
                        i, for_date, provider_label,
                    )
                return data
            except PanchangFetchError as exc:
                logger.warning("Panchang provider %s failed for %s: %s", provider_label, for_date, exc)
                errors.append(f"{provider_label}: {exc}")

        raise PanchangFetchError(
            f"All {len(self._providers)} Panchang provider(s) failed for {for_date}:\n"
            + "\n".join(errors)
        )
