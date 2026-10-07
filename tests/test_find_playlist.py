from channels.engine import upload


class _Req:
    def __init__(self, v): self.v = v
    def execute(self): return self.v


class _PL:
    def __init__(self, items): self.items, self.inserted = items, []
    def list(self, **kw): return _Req({"items": self.items})
    def insert(self, part, body): self.inserted.append(body); return _Req({"id": "NEW"})


class _YT:
    def __init__(self, items): self.p = _PL(items)
    def playlists(self): return self.p


def test_finds_existing_playlist_by_title():
    yt = _YT([{"id": "A", "snippet": {"title": "Gita"}}])
    assert upload.find_or_create_playlist(yt, "Gita") == "A" and not yt.p.inserted


def test_creates_when_missing():
    yt = _YT([])
    assert upload.find_or_create_playlist(yt, "Gita", "d") == "NEW" and yt.p.inserted
