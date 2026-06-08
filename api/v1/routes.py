from fastapi import APIRouter
from .user import router as user_router
from .lbase import router as lbase_router
from .training import router as training_router
from .prediction import router as prediction_router

router = APIRouter(prefix="/api/v1")
router.include_router(user_router, prefix="/auth", tags=["auth"])
router.include_router(lbase_router, prefix="/bases", tags=["bases"])
router.include_router(training_router, prefix="/training", tags=["training"])
router.include_router(prediction_router, prefix="/predictions", tags=["predictions"])
