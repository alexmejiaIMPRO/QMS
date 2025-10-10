"""
Audit log routes
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import get_db
from auth.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="jinja_templates")


@router.get("", response_class=HTMLResponse)
async def audit_log(request: Request):
    """Render the audit log page"""
    try:
        user = get_current_user(request)
        if not user:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/auth/login", status_code=302)
        
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100")
        logs = [dict(row) for row in c.fetchall()]
        conn.close()

        return templates.TemplateResponse("audit_page.html", {
            "request": request,
            "logs": logs,
            "user": user
        })
    except Exception as e:
        print(f"Error loading audit log: {e}")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/auth/login", status_code=302)
