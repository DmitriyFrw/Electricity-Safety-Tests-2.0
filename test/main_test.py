
from fastapi.responses import HTMLResponse
from app.dashboard_stats import router as cabinet_router
from app.auth import router as auth_router

app.include_router(auth_router)  # добавит /api/auth/login
app.include_router(cabinet_router)  # роутер дашборда

@app.get("/cabinet", response_class=HTMLResponse)
async def serve_cabinet():
    html_path = BASE_DIR / "static" / "cabinet.html"  # или frontend/dist/cabinet.html
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))