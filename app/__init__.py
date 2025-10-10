"""
Application modules package
"""
from fastapi import APIRouter
from .general_information.routes import router as general_info_router
from .entities.routes import router as entities_router
from .dmt.routes import router as dmt_router
from .audit.routes import router as audit_router

# Create main API router
api_router = APIRouter()

api_router.include_router(general_info_router, tags=["general-info"])
api_router.include_router(entities_router, prefix="/entity", tags=["entities"])
api_router.include_router(dmt_router, prefix="/dmt", tags=["dmt"])
api_router.include_router(audit_router, prefix="/audit", tags=["audit"])

__all__ = ["api_router"]
