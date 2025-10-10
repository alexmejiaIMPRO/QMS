"""
Audit log routes
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from database import get_db
from templates import render_audit_page

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def audit_log():
    """Render the audit log page"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100")
    logs = [dict(row) for row in c.fetchall()]
    conn.close()

    return render_audit_page(logs)
