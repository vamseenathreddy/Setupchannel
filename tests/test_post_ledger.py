import pytest

from mahanavi.publishers import post_ledger as pl


def test_blocks_identical_and_allows_new(tmp_path, monkeypatch):
    monkeypatch.setattr(pl, "DATA_DIR", tmp_path)
    tok = tmp_path / "youtube_token_jesus.json"
    pl.check(tok, "Matthew 28:20", "desc")  # empty ledger: allowed
    pl.record(tok, "Matthew 28:20", "desc", "vid1")
    with pytest.raises(pl.DuplicatePost):
        pl.check(tok, "  matthew 28:20 ", "DESC")  # case/spacing ignored
    pl.check(tok, "Matthew 28:19", "desc")  # different content: allowed


def test_channels_are_separate_and_name_derived(tmp_path, monkeypatch):
    monkeypatch.setattr(pl, "DATA_DIR", tmp_path)
    assert pl.channel_name("data/youtube_token.json") == "mahanavi"
    assert pl.channel_name("youtube_token_trance_beats.json") == "trance_beats"
    pl.record(tmp_path / "youtube_token_ramana.json", "t", "d", "v")
    pl.check(tmp_path / "youtube_token_jesus.json", "t", "d")  # other channel unaffected


def test_merge_keeps_both(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text('{"x": {"id": "1"}}')
    b.write_text('{"y": {"id": "2"}}')
    assert set(pl.merge_files(a, b)) == {"x", "y"}
