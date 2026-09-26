"""
Factory for constructing the configured PanchangProvider.

This is the single place that reads `settings.panchang_provider` and
decides which concrete class to instantiate. Everything downstream
(pipeline.py) just calls `get_panchang_provider(settings).fetch(today)`
and doesn't know or care which implementation is behind it.
"""

from __future__ import annotations

from mahanavi.config import Settings
from mahanavi.core.interfaces import PanchangProvider
from mahanavi.exceptions import ConfigError
from mahanavi.panchang.api_provider import ApiPanchangProvider
from mahanavi.panchang.dummy_provider import DummyPanchangProvider
from mahanavi.panchang.fallback_provider import FallbackPanchangProvider
from mahanavi.panchang.prokerala_provider import ProkeralaPanchangProvider
from mahanavi.panchang.scraper_provider import ScraperPanchangProvider

# Scraper selectors are deployment-specific (depend on which site you scrape).
# Override by constructing ScraperPanchangProvider directly with your own
# selector map if you go this route, rather than relying on this default.
_DEFAULT_SCRAPER_SELECTORS: dict[str, str] = {}


def get_panchang_provider(settings: Settings) -> PanchangProvider:
    provider_name = settings.panchang_provider.lower()

    if provider_name == "dummy":
        return DummyPanchangProvider()

    if provider_name == "api":
        if not settings.panchang_api_base_url:
            raise ConfigError(
                "MAHANAVI_PANCHANG_PROVIDER=api requires MAHANAVI_PANCHANG_API_BASE_URL."
            )
        return ApiPanchangProvider(
            base_url=settings.panchang_api_base_url,
            api_key=settings.panchang_api_key,
            latitude=settings.panchang_latitude,
            longitude=settings.panchang_longitude,
            max_retries=settings.max_retries,
            backoff_seconds=settings.retry_backoff_seconds,
        )

    if provider_name == "prokerala":
        if not settings.prokerala_client_id or not settings.prokerala_client_secret:
            raise ConfigError(
                "MAHANAVI_PANCHANG_PROVIDER=prokerala requires "
                "MAHANAVI_PROKERALA_CLIENT_ID and MAHANAVI_PROKERALA_CLIENT_SECRET."
            )
        primary = ProkeralaPanchangProvider(
            client_id=settings.prokerala_client_id,
            client_secret=settings.prokerala_client_secret,
            latitude=settings.panchang_latitude,
            longitude=settings.panchang_longitude,
            token_cache_path=settings.output_dir.parent / "prokerala_token.json",
        )
        if settings.prokerala_client_id_2 and settings.prokerala_client_secret_2:
            secondary = ProkeralaPanchangProvider(
                client_id=settings.prokerala_client_id_2,
                client_secret=settings.prokerala_client_secret_2,
                latitude=settings.panchang_latitude,
                longitude=settings.panchang_longitude,
                token_cache_path=settings.output_dir.parent / "prokerala_token_2.json",
            )
            return FallbackPanchangProvider([primary, secondary])
        return primary

    if provider_name == "scraper":
        if not _DEFAULT_SCRAPER_SELECTORS:
            raise ConfigError(
                "MAHANAVI_PANCHANG_PROVIDER=scraper requires a selector map. "
                "Construct ScraperPanchangProvider directly with your target "
                "site's URL template and CSS selectors — see scraper_provider.py."
            )
        return ScraperPanchangProvider(
            url_template="",  # supply your own
            selectors=_DEFAULT_SCRAPER_SELECTORS,
            max_retries=settings.max_retries,
            backoff_seconds=settings.retry_backoff_seconds,
        )

    raise ConfigError(
        f"Unknown MAHANAVI_PANCHANG_PROVIDER='{settings.panchang_provider}'. "
        "Expected one of: dummy, api, scraper, prokerala."
    )
