"""Проверка стоп-слов (чёрный список) в тексте сообщения."""

from __future__ import annotations

from core.keyword_match import normalize_text


def find_stopword(message_text: str, stopwords: list[str]) -> str | None:
    """
    Возвращает первое стоп-слово, найденное в тексте.
    Одно слово — по токенам; фраза — как подстрока после нормализации.
    """
    msg = normalize_text(message_text)
    if not msg:
        return None
    msg_tokens = set(msg.split())

    for raw in stopwords:
        sw = normalize_text(str(raw or ""))
        if not sw:
            continue
        parts = sw.split()
        if len(parts) == 1:
            if parts[0] in msg_tokens:
                return str(raw).strip()
        elif sw in msg:
            return str(raw).strip()
    return None
