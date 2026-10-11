"""Small shared text helpers used across publishers and notifications."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def fit_text(text: str, limit: int, context: str = "text") -> str:
    """Truncate `text` to fit within `limit` characters, appending an ellipsis.

    Used anywhere a platform enforces a hard character limit (Telegram
    captions/messages, etc.) so we degrade gracefully — a slightly-cut
    caption — instead of the API rejecting the whole request outright.
    """
    if len(text) <= limit:
        return text
    logger.warning(
        "%s is %d characters, exceeding the %d-character limit — truncating.",
        context, len(text), limit,
    )
    return text[: limit - 1].rstrip() + "…"
