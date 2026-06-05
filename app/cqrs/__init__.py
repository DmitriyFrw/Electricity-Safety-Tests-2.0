"""CQRS: CommandBus / QueryBus и типизированные сообщения."""

from app.cqrs.base import Command, Query
from app.cqrs.bus import CommandBus, QueryBus, UnknownMessageError, dispatch_command, dispatch_query
from app.cqrs.deps import get_command_bus, get_query_bus

__all__ = [
    "Command",
    "Query",
    "CommandBus",
    "QueryBus",
    "UnknownMessageError",
    "get_command_bus",
    "get_query_bus",
    "dispatch_command",
    "dispatch_query",
]
