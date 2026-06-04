"""SessionMiddleware с настраиваемым HttpOnly (Starlette по умолчанию всегда httponly)."""

from __future__ import annotations

import typing

from starlette.middleware.sessions import SessionMiddleware

if typing.TYPE_CHECKING:
    from starlette.datastructures import Secret
    from starlette.types import ASGIApp


class AppSessionMiddleware(SessionMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        secret_key: str | Secret,
        *,
        httponly: bool = True,
        session_cookie: str = "session",
        max_age: int | None = 14 * 24 * 60 * 60,
        path: str = "/",
        same_site: typing.Literal["lax", "strict", "none"] = "lax",
        https_only: bool = False,
        domain: str | None = None,
    ) -> None:
        super().__init__(
            app,
            secret_key,
            session_cookie=session_cookie,
            max_age=max_age,
            path=path,
            same_site=same_site,
            https_only=https_only,
            domain=domain,
        )
        parts: list[str] = []
        if httponly:
            parts.append("httponly")
        parts.append(f"samesite={same_site}")
        if https_only:
            parts.append("secure")
        if domain is not None:
            parts.append(f"domain={domain}")
        self.security_flags = "; ".join(parts)
