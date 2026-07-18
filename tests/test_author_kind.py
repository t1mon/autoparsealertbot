"""Unit tests for author_kind classification and filter modes."""

from __future__ import annotations

from types import SimpleNamespace

from core.author_kind import (
    author_kind_allowed,
    classify_author_kind,
    normalize_author_filter,
)


class _User:
    def __init__(self, *, bot: bool = False, first_name: str = "Ann"):
        self.bot = bot
        self.first_name = first_name
        self.last_name = None
        self.username = "ann"
        self.id = 1


class _Channel:
    def __init__(self, *, broadcast: bool = True):
        self.broadcast = broadcast
        self.megagroup = not broadcast
        self.title = "News"
        self.username = "news"
        self.id = 100


def test_normalize_author_filter():
    assert normalize_author_filter(None) == "humans"
    assert normalize_author_filter("all") == "all"
    assert normalize_author_filter("weird") == "humans"


def test_author_kind_allowed_humans():
    assert author_kind_allowed("humans", "user") is True
    assert author_kind_allowed("humans", "bot") is False
    assert author_kind_allowed("humans", "channel") is False
    assert author_kind_allowed("humans", "anonymous") is False
    assert author_kind_allowed("humans", "forward_channel") is False


def test_author_kind_allowed_humans_anon():
    assert author_kind_allowed("humans_anon", "user") is True
    assert author_kind_allowed("humans_anon", "anonymous") is True
    assert author_kind_allowed("humans_anon", "channel") is False


def test_author_kind_allowed_all():
    for kind in ("user", "bot", "channel", "anonymous", "forward_channel"):
        assert author_kind_allowed("all", kind) is True


def test_classify_user_and_bot():
    msg = SimpleNamespace(fwd_from=None, post_author=None, from_id=None)
    assert classify_author_kind(_User(), msg) == "user"
    assert classify_author_kind(_User(bot=True), msg) == "bot"


def test_classify_channel():
    msg = SimpleNamespace(fwd_from=None, post_author=None, from_id=None)
    assert classify_author_kind(_Channel(), msg) == "channel"


def test_classify_forward_channel():
    fwd = SimpleNamespace(from_id=SimpleNamespace(channel_id=55))
    msg = SimpleNamespace(fwd_from=fwd, post_author=None, from_id=None)
    assert classify_author_kind(_User(), msg) == "forward_channel"


def test_classify_anonymous():
    msg = SimpleNamespace(fwd_from=None, post_author=None, from_id=None)
    assert classify_author_kind(None, msg) == "anonymous"
