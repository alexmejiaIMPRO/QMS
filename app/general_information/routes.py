"""
General information routes
"""
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from auth.auth import get_current_user, UserRole

router = APIRouter()
templates = Jinja2Templates(directory="jinja_templates")


@router.get("/general-info", response_class=HTMLResponse)
async def general_info(request: Request):
    """Render the general information management page"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    if user["role"] != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    entities = [
        {"key": "employees", "label": "Employees", "icon": "👤", "color": "purple"},
        {"key": "levels", "label": "Levels", "icon": "📊", "color": "indigo"},
        {"key": "areas", "label": "Areas", "icon": "🏢", "color": "pink"},
        {"key": "partnumbers", "label": "Part Numbers", "icon": "🔧", "color": "orange"},
        {"key": "calibrations", "label": "Calibrations", "icon": "⚙️", "color": "teal"},
        {"key": "workcenters", "label": "Work Centers", "icon": "🏭", "color": "blue"},
        {"key": "customers", "label": "Customers", "icon": "🏢", "color": "green"},
        {"key": "inspection_items", "label": "Inspection Items", "icon": "🔍", "color": "yellow"},
        {"key": "prepared_by", "label": "Prepared By", "icon": "✍️", "color": "red"},
        {"key": "car_types", "label": "CAR Types", "icon": "📋", "color": "cyan"},
        {"key": "dispositions", "label": "Dispositions", "icon": "✅", "color": "lime"},
        {"key": "failure_codes", "label": "Failure Codes", "icon": "❌", "color": "rose"},
    ]
    
    return templates.TemplateResponse("general_info.html", {
        "request": request,
        "entities": entities
    })
