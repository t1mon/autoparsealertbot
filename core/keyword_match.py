"""Умное совпадение ключевых слов / фраз в тексте сообщений.

Учитывает:
- вхождение фразы / слова (contains) после нормализации;
- опечатки (нечёткое сравнение токенов);
- простые русские словоформы (белый / белые / белых);
- частичное совпадение многословной фразы (большинство значимых слов).
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

_NON_WORD = re.compile(r"[^\w]+", re.UNICODE)
_WS = re.compile(r"\s+")

# Короткие слова (vpn, вк) — только точное совпадение, без fuzzy/stem
_MIN_SMART_LEN = 4
_FUZZY_RATIO = 0.82

# Частые русские окончания (длинные первыми)
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


def normalize_text(text: str) -> str:
    """Нижний регистр, ё→е, пунктуация → пробел, схлопывание пробелов."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).lower().replace("ё", "е")
    text = _NON_WORD.sub(" ", text)
    return _WS.sub(" ", text).strip()


def _stem_ru(word: str) -> str:
    """Грубый стем для RU: срезаем типичные окончания, оставляя основу ≥ 3 символов."""
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


def _token_matches(kw_token: str, msg_tokens: list[str], msg_stems: set[str]) -> bool:
    """Одно слово ключа совпало с каким-то токеном сообщения."""
    if kw_token in msg_tokens or kw_token in msg_stems:
        return True

    kw_stem = _stem_ru(kw_token)
    if kw_stem in msg_stems or kw_stem in msg_tokens:
        return True

    if len(kw_token) < _MIN_SMART_LEN:
        return False

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


def _needed_hits(token_count: int) -> int:
    """Сколько слов фразы из 3+ достаточно (большинство)."""
    if token_count <= 2:
        return token_count
    return (token_count + 1) // 2


def keyword_matches(message_text: str, keyword: str) -> bool:
    """Проверяет, содержит ли сообщение ключевое слово или фразу."""
    kw = normalize_text(keyword)
    if not kw:
        return False

    msg = normalize_text(message_text)
    if not msg:
        return False

    # 1) Точная фраза / слово как подстрока
    if kw in msg:
        return True

    kw_tokens = kw.split()
    msg_tokens = msg.split()
    if not kw_tokens or not msg_tokens:
        return False

    msg_stems = {_stem_ru(t) for t in msg_tokens}
    hits = [_token_matches(token, msg_tokens, msg_stems) for token in kw_tokens]

    # 2) Все слова (с учётом опечаток / словоформ)
    if all(hits):
        return True

    # 3) Одно слово — уже проверено в hits[0]
    if len(kw_tokens) == 1:
        return hits[0]

    # 4) Фраза из 2 слов: достаточно первого слова («белые» из «белые списки»),
    #    чтобы не ловить чужие «... списки» без «белые».
    if len(kw_tokens) == 2:
        return hits[0]

    # 5) Фраза из 3+ слов — большинство слов
    return sum(hits) >= _needed_hits(len(kw_tokens))


def find_matching_keyword(message_text: str, keywords: list[str]) -> str | None:
    """Первое совпавшее ключевое слово (lowercase), или None."""
    for keyword in keywords:
        if not keyword or not str(keyword).strip():
            continue
        if keyword_matches(message_text, str(keyword)):
            return str(keyword).strip().lower()
    return None
