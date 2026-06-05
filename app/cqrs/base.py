from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Command:
    """Маркер команды (изменение состояния)."""


@dataclass(frozen=True, slots=True)
class Query:
    """Маркер запроса (чтение)."""
