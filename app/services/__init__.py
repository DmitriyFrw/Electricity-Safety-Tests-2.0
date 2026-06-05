"""Сервисный слой (бизнес-логика). Ленивые импорты — без циклов с api.mappers."""

__all__ = [
    "AuthService",
    "DashboardService",
    "ExportService",
    "LoginRateLimiter",
    "ManualService",
    "ProfileService",
    "SecurityAuditService",
    "TestService",
]


def __getattr__(name: str) -> object:
    if name == "AuthService":
        from app.services.users.auth import AuthService

        return AuthService
    if name == "DashboardService":
        from app.services.dashboard_service import DashboardService

        return DashboardService
    if name == "ExportService":
        from app.services.exports import ExportService

        return ExportService
    if name == "LoginRateLimiter":
        from app.services.security import LoginRateLimiter

        return LoginRateLimiter
    if name == "ManualService":
        from app.services.manual_service import ManualService

        return ManualService
    if name == "ProfileService":
        from app.services.profile_service import ProfileService

        return ProfileService
    if name == "SecurityAuditService":
        from app.services.security import SecurityAuditService

        return SecurityAuditService
    if name == "TestService":
        from app.services.test_service import TestService

        return TestService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
