from fastapi import APIRouter

from app.api import admin, auth, dashboard, manuals, profile, staff, tests, wiki

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(staff.router)
api_router.include_router(profile.router)
api_router.include_router(manuals.router)
api_router.include_router(dashboard.router)
api_router.include_router(tests.router)
api_router.include_router(wiki.router)
