"""Тесты матчинга ключевых слов (smart / strict / loose)."""

from __future__ import annotations

import pytest

from core.keyword_match import (
    DEFAULT_MATCH_MODE,
    explain_keyword_match,
    find_all_matching_keyword_details,
    find_matching_keyword,
    keyword_matches,
    normalize_match_mode,
    normalize_text,
)


class TestNormalize:
    def test_yo_and_case(self):
        assert normalize_text("Ёлка VPN") == "елка vpn"

    def test_punctuation_to_spaces(self):
        assert normalize_text("VPN-клиент!") == "vpn клиент"

    def test_empty(self):
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""


class TestNormalizeMode:
    def test_default_and_aliases(self):
        assert normalize_match_mode(None) == DEFAULT_MATCH_MODE
        assert normalize_match_mode("SMART") == "smart"
        assert normalize_match_mode("nope") == DEFAULT_MATCH_MODE


@pytest.mark.parametrize(
    "keyword,text,expected",
    [
        ("лучший vpn", "лучший vpn для телефона", True),
        ("лучший vpn", "но одни из самых лучших)", False),
        ("vpn", "VPN-клиент", True),
        ("белые списки", "просто белые", False),
        ("белые списки", "чёрные списки", False),
        ("белые списки", "нужны белые списки для доступа", True),
        (
            "работает только вк",
            "Mail.ru удалили… VK… продолжают работать",
            False,
        ),
        ("работает только вк", "у меня работает только вк", True),
        ("вк", "пишу в VK каждый день", True),
        ("telegram", "напишите в тг", True),
    ],
)
def test_smart_cases_from_roadmap(keyword, text, expected):
    assert keyword_matches(text, keyword, mode="smart") is expected


class TestStrict:
    def test_exact_phrase_only(self):
        assert keyword_matches("это лучший vpn сервис", "лучший vpn", mode="strict")
        assert not keyword_matches("одних лучших vpn", "лучший vpn", mode="strict")

    def test_stem_not_enough(self):
        assert not keyword_matches("нужны белые списки", "белый список", mode="strict")


class TestLoose:
    def test_two_words_first_enough(self):
        assert keyword_matches("одних из самых лучших", "лучший vpn", mode="loose")

    def test_three_words_majority(self):
        # 2 of 3: работает + вк (без «только»)
        assert keyword_matches(
            "у меня работает вк нормально",
            "работает только вк",
            mode="loose",
        )


class TestExplain:
    def test_exact_reason(self):
        d = explain_keyword_match("это лучший vpn", "лучший vpn", mode="smart")
        assert d is not None
        assert d.reason == "exact"
        assert d.keyword == "лучший vpn"

    def test_tokens_reason(self):
        d = explain_keyword_match(
            "одних из самых лучших vpn сервисов",
            "лучший vpn",
            mode="smart",
        )
        assert d is not None
        assert d.reason == "tokens"
        assert "лучший" in d.hit_tokens
        assert "vpn" in d.hit_tokens

    def test_loose_partial(self):
        d = explain_keyword_match(
            "одних из самых лучших",
            "лучший vpn",
            mode="loose",
        )
        assert d is not None
        assert d.reason == "loose"
        assert d.hit_tokens == ("лучший",)
        assert d.miss_tokens == ("vpn",)

    def test_none(self):
        assert explain_keyword_match("просто текст", "лучший vpn", mode="smart") is None


class TestFind:
    def test_first_match(self):
        assert (
            find_matching_keyword(
                "нужен vpn срочно",
                ["белый список", "vpn", "прокси"],
                mode="smart",
            )
            == "vpn"
        )

    def test_all_matches(self):
        details = find_all_matching_keyword_details(
            "это лучший vpn сервис",
            ["лучший vpn", "vpn", "прокси"],
            mode="smart",
        )
        assert [d.keyword for d in details] == ["лучший vpn", "vpn"]
