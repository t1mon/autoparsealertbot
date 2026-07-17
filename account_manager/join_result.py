"""Результат попытки вступления в канал."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JoinResult:
    outcome: str  # joined | already | error
    reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.outcome in ("joined", "already")
