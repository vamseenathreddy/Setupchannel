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

NOTIFY-ON-FALLBACK (added 2026-10-03, explicit request): this class
itself stays provider-agnostic and has no idea what Telegram or
Settings are -- it just accepts an optional `on_fallback` callback and
invokes it whenever the primary provider wasn't the one that
succeeded. factory.py is what wires that callback to an actual
Telegram alert (see get_panchang_provider's prokerala branch). This is
purely an FYI signal, not an error: the whole point of this class is
that falling back WORKED and the post went out fine -- the callback
just lets the channel owner know Key 1's monthly quota ran out without
having to dig through CI logs, so they're not surprised when Key 2
eventually also needs a fresh month. A callback failure must never
break the actual Panchang fetch it's just annotating, so it's wrapped
in its own try/except here.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Callable

from ytcore.core.interfaces import PanchangProvider
from ytcore.core.models import PanchangData
from ytcore.exceptions import PanchangFetchError

logger = logging.getLogger(__name__)


class FallbackPanchangProvider(PanchangProvider):
    """Tries each provider in order; returns the first successful
    result. Raises PanchangFetchError (listing every provider's error)
    only if ALL of them fail."""

    def __init__(
        self,
        providers: list[PanchangProvider],
        on_fallback: Callable[[int, str], None] | None = None,
    ) -> None:
        if not providers:
            raise ValueError("FallbackPanchangProvider requires at least one provider.")
        self._providers = providers
        self._on_fallback = on_fallback

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
                    if self._on_fallback is not None:
                        try:
                            self._on_fallback(i, provider_label)
                        except Exception as notify_exc:  # never let a notification failure break the real fetch
                            logger.warning("on_fallback callback itself failed: %s", notify_exc)
                return data
            except PanchangFetchError as exc:
                logger.warning("Panchang provider %s failed for %s: %s", provider_label, for_date, exc)
                errors.append(f"{provider_label}: {exc}")

        raise PanchangFetchError(
            f"All {len(self._providers)} Panchang provider(s) failed for {for_date}:\n"
            + "\n".join(errors)
        )
