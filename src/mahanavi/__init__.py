"""Channel A — automated daily devotional content pipeline."""

__version__ = "0.1.0"


from mahanavi.content import card_text as _card_text  # noqa: E402

_card_text.install()
