from fastapi import APIRouter

from .admin import admin_router
from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .display import router as display_router
from .missions import router as missions_router
from .profile import router as profile_router
from .purchase import router as purchase_router
from .referral import router as referral_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(dashboard_router)
api_router.include_router(missions_router)
api_router.include_router(display_router)
api_router.include_router(purchase_router)
api_router.include_router(referral_router)
api_router.include_router(admin_router)
