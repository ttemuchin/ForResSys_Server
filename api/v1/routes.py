from fastapi import APIRouter
from .auth import router as auth_router
from .bases import router as bases_router
from .predictions import router as predictions_router
from .health import router as health_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(bases_router, prefix="/bases", tags=["bases"])
router.include_router(predictions_router, prefix="/predictions", tags=["predictions"])
router.include_router(health_router, prefix="/health", tags=["health"])