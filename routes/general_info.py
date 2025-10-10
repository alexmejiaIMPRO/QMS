"""
General information routes
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from templates import render_general_info_page

router = APIRouter()


@router.get("/general-info", response_class=HTMLResponse)
async def general_info():
    """Render the general information management page"""
    return render_general_info_page()
