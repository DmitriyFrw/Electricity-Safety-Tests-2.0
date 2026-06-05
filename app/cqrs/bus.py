from __future__ import annotations

from typing import Any, TypeVar, cast

from app.cqrs.base import Command, Query
from app.cqrs.handler import CommandHandler, QueryHandler

C = TypeVar("C", bound=Command)
Q = TypeVar("Q", bound=Query)
T = TypeVar("T")
R = TypeVar("R")


class UnknownMessageError(LookupError):
    def __init__(self, message_type: type[object]) -> None:
        super().__init__(f"No handler registered for {message_type.__name__}")
        self.message_type = message_type


class CommandBus:
    def __init__(self) -> None:
        self._handlers: dict[type[Command], Any] = {}

    def register(self, command_type: type[C], handler: CommandHandler[C, R] | Any) -> None:
        self._handlers[command_type] = handler

    def dispatch(self, command: C) -> object:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise UnknownMessageError(type(command))
        return handler.handle(command)


class QueryBus:
    def __init__(self) -> None:
        self._handlers: dict[type[Query], Any] = {}

    def register(self, query_type: type[Q], handler: QueryHandler[Q, R] | Any) -> None:
        self._handlers[query_type] = handler

    def dispatch(self, query: Q) -> object:
        handler = self._handlers.get(type(query))
        if handler is None:
            raise UnknownMessageError(type(query))
        return handler.handle(query)


def dispatch_command(command: Command, result: type[T]) -> T:
    from app.cqrs.deps import get_command_bus

    return cast(T, get_command_bus().dispatch(command))


def dispatch_query(query: Query, result: type[T]) -> T:
    from app.cqrs.deps import get_query_bus

    return cast(T, get_query_bus().dispatch(query))
