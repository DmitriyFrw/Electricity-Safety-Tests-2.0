# Legacy server-rendered UI

Модули в этой папке — **архив** старого Jinja-интерфейса. Они **не монтируются** в `app.main` и не участвуют в production-потоке (React SPA + `/api/*`).

| Файл | Назначение |
|------|------------|
| `html_routes.py` | HTML-маршруты (форма логина, каталог, take test) |
| `web.py` | Jinja2 templates |

Для локальной отладки legacy (не рекомендуется):

```python
# в app/main.py, только dev:
# from app.legacy.html_routes import router as legacy_router
# app.include_router(legacy_router)
```

Новая функциональность — только `app/api/` + `frontend/`.
