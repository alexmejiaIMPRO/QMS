from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from config import Config
from app import api_router
from auth.routes import router as auth_router
from auth.auth import create_default_admin, get_current_user
from database.connection import get_db
import secrets

templates = Jinja2Templates(directory="jinja_templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    try:
        print("🚀 Starting Quality Management System...")
        print(f"📊 Database: {Config.DATABASE_PATH}")
        print(f"📄 Page Size: {Config.PAGE_SIZE}")
        create_default_admin()
        yield
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        raise
    finally:
        print("👋 Shutting down...")


# Initialize FastAPI application
app = FastAPI(title=Config.APP_TITLE,
              version=Config.APP_VERSION, lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=secrets.token_urlsafe(32))

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass

try:
    app.mount("/docs", StaticFiles(directory="docs"), name="docs")
except:
    pass

app.include_router(auth_router, prefix="/auth", tags=["auth"])

# Include all API routes
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the main application page with role-based dashboard"""
    try:
        user = get_current_user(request)
        if not user:
            return RedirectResponse(url="/auth/login", status_code=302)

        # Get dashboard statistics
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()

        stats = {}

        if user["role"] == "Admin":
            # Admin dashboard statistics
            stats["total_users"] = c.execute(
                "SELECT COUNT(*) FROM users" 
            ).fetchone()[0]
            stats["total_reports"] = c.execute(
                "SELECT COUNT(*) FROM dmt_records WHERE is_active = 1"
            ).fetchone()[0]
            stats["open_reports"] = c.execute(
                "SELECT COUNT(*) FROM dmt_records WHERE status = 'open' AND is_active = 1"
            ).fetchone()[0]
            stats["recent_audits"] = c.execute(
                "SELECT COUNT(*) FROM audit_log WHERE date(timestamp) = date('now')"
            ).fetchone()[0]

            # Recent activity
            stats["recent_reports"] = c.execute("""
                SELECT report_number, part_num, status, created_at, created_by
                FROM dmt_records 
                WHERE is_active = 1
                ORDER BY created_at DESC 
                LIMIT 5
            """).fetchall()

            stats["recent_users"] = c.execute("""
                SELECT username, role, created_at
                FROM users 
                WHERE is_active = 1
                ORDER BY created_at DESC 
                LIMIT 5
            """).fetchall()
        else:
            # User dashboard statistics
            stats["my_reports"] = c.execute(
                """
                SELECT COUNT(*) FROM dmt_records 
                WHERE (created_by = ? OR assigned_to = ?) AND is_active = 1
            """,
                (user["username"], user["username"]),
            ).fetchone()[0]

            stats["my_open_reports"] = c.execute(
                """
                SELECT COUNT(*) FROM dmt_records 
                WHERE (created_by = ? OR assigned_to = ?) 
                AND status = 'open' AND is_active = 1
            """,
                (user["username"], user["username"]),
            ).fetchone()[0]

            stats["my_closed_reports"] = c.execute(
                """
                SELECT COUNT(*) FROM dmt_records 
                WHERE (created_by = ? OR assigned_to = ?) 
                AND status = 'closed' AND is_active = 1
            """,
                (user["username"], user["username"]),
            ).fetchone()[0]

            # Recent reports
            stats["recent_reports"] = c.execute(
                """
                SELECT report_number, part_num, status, created_at, assigned_to
                FROM dmt_records 
                WHERE (created_by = ? OR assigned_to = ?) AND is_active = 1
                ORDER BY created_at DESC 
                LIMIT 5
            """,
                (user["username"], user["username"]),
            ).fetchall()

        conn.close()

        return templates.TemplateResponse(
            "base.html", {"request": request, "user": user, "stats": stats}
        )
    except Exception as e:
        print(f"Error in root route: {e}")
        return RedirectResponse(url="/auth/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_redirect(request: Request):
    """Redirect to auth login"""
    return RedirectResponse(url="/auth/login", status_code=302)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
