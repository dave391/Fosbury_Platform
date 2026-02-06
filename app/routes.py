from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.config import router as config_router
from app.routers.dashboard import router as dashboard_router
from app.routers.home import router as home_router
from app.routers.strategy import router as strategy_router

router = APIRouter()

router.include_router(home_router)
router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(strategy_router)
router.include_router(config_router)
