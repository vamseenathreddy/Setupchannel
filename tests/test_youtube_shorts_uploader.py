from __future__ import annotations
from ytcore.brandcfg import A_NAME  # noqa: E402

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ytcore.config import Settings
from ytcore.content.alert_seo import ShortSeoContent
from ytcore.publishers.youtube_shorts_uploader import YouTubeShortsUploader


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    images_root = tmp_path / "Images"
    images_root.mkdir(parents=True, exist_ok=True)
    token_file = tmp_path / "youtube_token.json"
    token_file.write_text('{"token": "fake", "refresh_token": "fake"}', encoding="utf-8")
    return Settings(
        images_root=images_root,
        output_dir=tmp_path / "generated",
        database_path=tmp_path / "db.sqlite",
        log_dir=tmp_path / "logs",
        youtube_token_file=token_file,
    )


def _seo() -> ShortSeoContent:
    return ShortSeoContent(
        title="⚠️ ఈరోజు రాహు కాలం ఎప్పుడు?",
        description="ఈరోజు రాహు కాలం: 04:30 PM - 06:00 PM",
        hashtags=["#Shorts", "#రాహుకాలం", "#పంచాంగం"],
    )


def test_upload_returns_failure_when_video_missing(settings: Settings) -> None:
    uploader = YouTubeShortsUploader(settings)
    result = uploader.upload(Path("/does/not/exist.mp4"), _seo())
    assert result.success is False
    assert "does not exist" in result.error_message


def test_upload_returns_failure_when_token_missing(settings: Settings, tmp_path: Path) -> None:
    settings2 = settings.__class__(
        images_root=settings.images_root,
        output_dir=settings.output_dir,
        database_path=settings.database_path,
        log_dir=settings.log_dir,
        youtube_token_file=tmp_path / "does_not_exist_token.json",
    )
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake video bytes")

    uploader = YouTubeShortsUploader(settings2)
    result = uploader.upload(video_path, _seo())
    assert result.success is False
    assert "auth_setup" in result.error_message


def test_upload_succeeds_with_mocked_api(settings: Settings, tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake video bytes")

    fake_response = {"id": "abc123"}
    mock_insert = MagicMock()
    mock_insert.execute.return_value = fake_response
    mock_videos = MagicMock()
    mock_videos.insert.return_value = mock_insert
    mock_youtube = MagicMock()
    mock_youtube.videos.return_value = mock_videos

    uploader = YouTubeShortsUploader(settings)
    with patch.object(uploader, "_build_service", return_value=mock_youtube):
        result = uploader.upload(video_path, _seo())

    assert result.success is True
    assert result.post_url == "https://www.youtube.com/watch?v=abc123"
    # Confirm the actual request body shape sent to the API.
    _, kwargs = mock_videos.insert.call_args
    assert kwargs["body"]["snippet"]["title"].startswith(_seo().title) and kwargs["body"]["snippet"]["title"].endswith(f"{A_NAME}")
    assert kwargs["body"]["status"]["selfDeclaredMadeForKids"] is False
    assert kwargs["body"]["snippet"]["tags"][:3] == ["Shorts", "రాహుకాలం", "పంచాంగం"] and f"{A_NAME.lower()}" in kwargs["body"]["snippet"]["tags"]


def test_upload_handles_api_error_gracefully(settings: Settings, tmp_path: Path) -> None:
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake video bytes")

    mock_youtube = MagicMock()
    mock_youtube.videos.return_value.insert.side_effect = RuntimeError("quota exceeded")

    uploader = YouTubeShortsUploader(settings)
    with patch.object(uploader, "_build_service", return_value=mock_youtube):
        result = uploader.upload(video_path, _seo())

    assert result.success is False
    assert "quota exceeded" in result.error_message
