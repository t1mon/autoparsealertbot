"""Умное совпадение ключевых слов / фраз в тексте сообщений.

Режимы:
- strict — только нормализованная фраза целиком (contains)
- smart (default) — стем/fuzzy для длинных токенов; все слова фразы; алиасы вк↔vk
- loose — как старый мягкий режим (2 слова → первое; 3+ → majority)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

MATCH_MODES = ("strict", "smart", "loose")
DEFAULT_MATCH_MODE = "smart"

# exact — нормализованная фраза целиком; tokens — все слова; loose — частичное
MATCH_REASONS = ("exact", "tokens", "loose")


@dataclass(frozen=True)
class MatchDetail:
    keyword: str
    mode: str
    reason: str  # exact | tokens | loose
    hit_tokens: tuple[str, ...] = ()
    miss_tokens: tuple[str, ...] = ()

_NON_WORD = re.compile(r"[^\w]+", re.UNICODE)
_WS = re.compile(r"\s+")

_MIN_SMART_LEN = 4
_FUZZY_RATIO = 0.82

_ALIAS_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"вк", "vk", "вконтакте"}),
    frozenset({"тг", "tg", "телеграм", "telegram"}),
    frozenset({"ютуб", "youtube", "yt"}),
)

_ALIASES: dict[str, frozenset[str]] = {}
for _group in _ALIAS_GROUPS:
    for _token in _group:
        _ALIASES[_token] = _group

_RU_SUFFIXES = (
    "иями",
    "ями",
    "ами",
    "ыми",
    "ими",
    "ого",
    "его",
    "ому",
    "ему",
    "ыми",
    "ими",
    "ая",
    "яя",
    "ое",
    "ее",
    "ые",
    "ие",
    "ый",
    "ий",
    "ой",
    "ых",
    "их",
    "ом",
    "ем",
    "ам",
    "ям",
    "ах",
    "ях",
    "ов",
    "ев",
    "ей",
    "ью",
    "ия",
    "ие",
    "ы",
    "и",
    "а",
    "я",
    "о",
    "е",
    "у",
    "ю",
)


def normalize_match_mode(mode: str | None) -> str:
    value = (mode or DEFAULT_MATCH_MODE).strip().lower()
    return value if value in MATCH_MODES else DEFAULT_MATCH_MODE


def normalize_text(text: str) -> str:
    """Нижний регистр, ё→е, пунктуация → пробел, схлопывание пробелов."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).lower().replace("ё", "е")
    text = _NON_WORD.sub(" ", text)
    return _WS.sub(" ", text).strip()


def _stem_ru(word: str) -> str:
    if len(word) < _MIN_SMART_LEN:
        return word
    for suf in _RU_SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            return word[: -len(suf)]
    return word


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def _alias_set(token: str) -> frozenset[str]:
    return _ALIASES.get(token, frozenset({token}))


def _token_matches(kw_token: str, msg_tokens: list[str], msg_stems: set[str]) -> bool:
    candidates = _alias_set(kw_token)

    msg_expanded: set[str] = set()
    for mt in msg_tokens:
        msg_expanded |= _alias_set(mt)
    if candidates & msg_expanded:
        return True
    if candidates & msg_stems:
        return True

    if len(kw_token) < _MIN_SMART_LEN:
        return False

    kw_stem = _stem_ru(kw_token)
    if kw_stem in msg_stems or kw_stem in msg_tokens:
        return True

    for mt in msg_tokens:
        if len(mt) < _MIN_SMART_LEN:
            continue
        if _stem_ru(mt) == kw_stem:
            return True
        if _similarity(kw_token, mt) >= _FUZZY_RATIO:
            return True
        if _similarity(kw_stem, _stem_ru(mt)) >= _FUZZY_RATIO:
            return True
    return False


def _needed_hits_loose(token_count: int) -> int:
    """Loose: для 3+ слов достаточно большинства."""
    if token_count <= 2:
        return token_count
    return (token_count + 1) // 2


def explain_keyword_match(
    message_text: str,
    keyword: str,
    mode: str = DEFAULT_MATCH_MODE,
) -> MatchDetail | None:
    """Детали совпадения (или None, если не совпало)."""
    mode = normalize_match_mode(mode)
    raw = str(keyword).strip()
    if not raw:
        return None

    kw = normalize_text(raw)
    if not kw:
        return None

    msg = normalize_text(message_text)
    if not msg:
        return None

    display_kw = raw.lower()

    if kw in msg:
        return MatchDetail(
            keyword=display_kw,
            mode=mode,
            reason="exact",
            hit_tokens=tuple(kw.split()),
        )

    if mode == "strict":
        return None

    kw_tokens = kw.split()
    msg_tokens = msg.split()
    if not kw_tokens or not msg_tokens:
        return None

    msg_stems = {_stem_ru(t) for t in msg_tokens}
    hits = [_token_matches(token, msg_tokens, msg_stems) for token in kw_tokens]
    hit_tokens = tuple(tok for tok, ok in zip(kw_tokens, hits) if ok)
    miss_tokens = tuple(tok for tok, ok in zip(kw_tokens, hits) if not ok)

    if mode == "smart":
        if all(hits):
            return MatchDetail(
                keyword=display_kw,
                mode=mode,
                reason="tokens",
                hit_tokens=hit_tokens,
            )
        return None

    # loose
    matched = False
    if all(hits):
        matched = True
    elif len(kw_tokens) == 1:
        matched = hits[0]
    elif len(kw_tokens) == 2:
        matched = hits[0]
    else:
        matched = sum(hits) >= _needed_hits_loose(len(kw_tokens))

    if not matched:
        return None

    reason = "tokens" if all(hits) else "loose"
    return MatchDetail(
        keyword=display_kw,
        mode=mode,
        reason=reason,
        hit_tokens=hit_tokens,
        miss_tokens=miss_tokens if reason == "loose" else (),
    )


def keyword_matches(message_text: str, keyword: str, mode: str = DEFAULT_MATCH_MODE) -> bool:
    """Проверяет, содержит ли сообщение ключевое слово или фразу."""
    return explain_keyword_match(message_text, keyword, mode=mode) is not None


def find_matching_keyword_detail(
    message_text: str,
    keywords: list[str],
    mode: str = DEFAULT_MATCH_MODE,
) -> MatchDetail | None:
    """Первое совпадение с причиной, или None."""
    mode = normalize_match_mode(mode)
    for keyword in keywords:
        if not keyword or not str(keyword).strip():
            continue
        detail = explain_keyword_match(message_text, str(keyword), mode=mode)
        if detail:
            return detail
    return None


def find_all_matching_keyword_details(
    message_text: str,
    keywords: list[str],
    mode: str = DEFAULT_MATCH_MODE,
) -> list[MatchDetail]:
    """Все совпавшие ключи с причинами (порядок как в списке ключей)."""
    mode = normalize_match_mode(mode)
    results: list[MatchDetail] = []
    for keyword in keywords:
        if not keyword or not str(keyword).strip():
            continue
        detail = explain_keyword_match(message_text, str(keyword), mode=mode)
        if detail:
            results.append(detail)
    return results


def find_matching_keyword(
    message_text: str,
    keywords: list[str],
    mode: str = DEFAULT_MATCH_MODE,
) -> str | None:
    """Первое совпавшее ключевое слово (lowercase), или None."""
    detail = find_matching_keyword_detail(message_text, keywords, mode=mode)
    return detail.keyword if detail else None
