from __future__ import annotations

from functools import lru_cache

from app.cqrs.bus import CommandBus, QueryBus
from app.cqrs.registry import build_command_bus, build_query_bus


@lru_cache(maxsize=1)
def get_command_bus() -> CommandBus:
    return build_command_bus()


@lru_cache(maxsize=1)
def get_query_bus() -> QueryBus:
    return build_query_bus()
