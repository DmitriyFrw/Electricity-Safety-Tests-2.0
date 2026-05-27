"""Сервисный слой (бизнес-логика)."""

from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.manual_service import ManualService
from app.services.profile_service import ProfileService
from app.services.test_service import TestService

__all__ = [
    "AuthService",
    "DashboardService",
    "ManualService",
    "ProfileService",
    "TestService",
]
