"""
Authentication routes
"""
from fastapi import APIRouter, Form, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from auth.auth import (
    authenticate_user,
    get_current_user,
    require_admin,
    create_user,
    get_all_users,
    get_user_by_id,
    update_user,
    delete_user,
    activate_user,
    UserRole
)

router = APIRouter()
templates = Jinja2Templates(directory="jinja_templates")


def render_toast(message: str, type: str = "success") -> str:
    colors = {"success": "green", "error": "red", "info": "blue"}
    color = colors.get(type, "blue")
    return templates.get_template("components/toast.html").render(message=message, color=color)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle login"""
    try:
        if not username or not password:
            return render_toast("Username and password are required", "error")
        
        user = authenticate_user(username, password)
        
        if user:
            request.session["user"] = user
            return '<div hx-get="/" hx-target="body" hx-push-url="true" hx-trigger="load"></div>'
        
        return render_toast("Invalid username or password", "error")
    except Exception as e:
        print(f"Login error: {e}")
        return render_toast("An error occurred during login. Please try again.", "error")


@router.post("/logout")
async def logout(request: Request):
    """Handle logout"""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request):
    """Render admin users management page"""
    try:
        require_admin(request)
    except:
        return RedirectResponse(url="/login", status_code=302)
    
    users = get_all_users()
    
    return templates.TemplateResponse("auth/admin_users.html", {
        "request": request,
        "users": users,
        "roles": [role.value for role in UserRole]
    })


@router.get("/admin/users/create", response_class=HTMLResponse)
async def create_user_form(request: Request):
    """Render create user form"""
    try:
        require_admin(request)
    except:
        return render_toast("Admin access required", "error")
    
    return templates.TemplateResponse("auth/user_form.html", {
        "request": request,
        "user": None,
        "roles": [role.value for role in UserRole]
    })


@router.post("/admin/users/create", response_class=HTMLResponse)
async def create_user_handler(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...)
):
    """Handle user creation"""
    try:
        require_admin(request)
    except HTTPException:
        return render_toast("Admin access required", "error")
    except Exception as e:
        print(f"Auth error: {e}")
        return render_toast("Authentication error", "error")
    
    try:
        if not username or not password or not role:
            return render_toast("All fields are required", "error")
        
        user = create_user(username, password, UserRole(role))
        html = '<div hx-get="/auth/admin/users" hx-target="#main-content" hx-trigger="load"></div>'
        html += render_toast(f"User {username} created successfully!", "success")
        return html
    except ValueError as e:
        return render_toast(str(e), "error")
    except Exception as e:
        print(f"Error creating user: {e}")
        return render_toast("Failed to create user. Please try again.", "error")


@router.get("/admin/users/edit/{user_id}", response_class=HTMLResponse)
async def edit_user_form(request: Request, user_id: str):
    """Render edit user form"""
    try:
        require_admin(request)
    except:
        return render_toast("Admin access required", "error")
    
    user = get_user_by_id(user_id)
    if not user:
        return render_toast("User not found", "error")
    
    return templates.TemplateResponse("auth/user_form.html", {
        "request": request,
        "user": user,
        "roles": [role.value for role in UserRole]
    })


@router.put("/admin/users/update/{user_id}", response_class=HTMLResponse)
async def update_user_handler(
    request: Request,
    user_id: str,
    username: str = Form(...),
    password: str = Form(None),
    role: str = Form(...)
):
    """Handle user update"""
    try:
        require_admin(request)
    except HTTPException:
        return render_toast("Admin access required", "error")
    except Exception as e:
        print(f"Auth error: {e}")
        return render_toast("Authentication error", "error")
    
    try:
        if not username or not role:
            return render_toast("Username and role are required", "error")
        
        success = update_user(
            user_id,
            username=username,
            password=password if password else None,
            role=UserRole(role)
        )
        
        if success:
            html = '<div hx-get="/auth/admin/users" hx-target="#main-content" hx-trigger="load"></div>'
            html += render_toast(f"User {username} updated successfully!", "success")
            return html
        else:
            return render_toast("Failed to update user", "error")
    except ValueError as e:
        return render_toast(str(e), "error")
    except Exception as e:
        print(f"Error updating user: {e}")
        return render_toast("Failed to update user. Please try again.", "error")


@router.delete("/admin/users/delete/{user_id}", response_class=HTMLResponse)
async def delete_user_handler(request: Request, user_id: str):
    """Handle user deletion"""
    try:
        require_admin(request)
    except:
        return render_toast("Admin access required", "error")
    
    success = delete_user(user_id)
    
    if success:
        users = get_all_users()
        html = templates.get_template("auth/users_list.html").render(
            request=request,
            users=users,
            roles=[role.value for role in UserRole]
        )
        html += render_toast("User deleted successfully!", "success")
        return html
    else:
        return render_toast("Failed to delete user", "error")


@router.post("/admin/users/activate/{user_id}", response_class=HTMLResponse)
async def activate_user_handler(request: Request, user_id: str):
    """Handle user activation"""
    try:
        require_admin(request)
    except:
        return render_toast("Admin access required", "error")
    
    success = activate_user(user_id)
    
    if success:
        users = get_all_users()
        html = templates.get_template("auth/users_list.html").render(
            request=request,
            users=users,
            roles=[role.value for role in UserRole]
        )
        html += render_toast("User activated successfully!", "success")
        return html
    else:
        return render_toast("Failed to activate user", "error")
