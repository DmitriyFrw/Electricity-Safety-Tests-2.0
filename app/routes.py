"""
Архив: HTML-маршруты перенесены в app/legacy/html_routes.py.

Этот модуль оставлен для обратной совместимости импортов и mypy exclude.
Не подключайте router в app.main — единственный UI: React SPA.
"""

from app.legacy.html_routes import router

__all__ = ["router"]
