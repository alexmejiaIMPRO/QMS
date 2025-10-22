"""
DMT (Defective Material Tag) routes with workflow management
"""
from typing import Optional
from fastapi import APIRouter, Form, Request, status
from fastapi.responses import Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from config import EntityType
from database import get_db
from services import ExportService
from auth.auth import get_current_user, get_all_users, get_assignable_users
import uuid

router = APIRouter()
templates = Jinja2Templates(directory="jinja_templates")


def render_toast(message: str, type: str = "success") -> str:
    colors = {"success": "green", "error": "red", "info": "blue"}
    color = colors.get(type, "blue")
    return templates.get_template("components/toast.html").render(message=message, color=color)


def get_next_report_number() -> int:
    """Get the next report number and increment the counter"""
    try:
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT next_number FROM report_counter WHERE id = 1")
        result = c.fetchone()
        next_number = result[0] if result else 1000
        
        c.execute("UPDATE report_counter SET next_number = ? WHERE id = 1", (next_number + 1,))
        conn.commit()
        conn.close()
        
        return next_number
    except Exception as e:
        print(f"Error getting next report number: {e}")
        import time
        return 1000 + int(time.time() % 10000)


def get_workflow_permissions(user_role: str, workflow_status: str, record_status: str, created_by: str = None, current_user_id: str = None):
    """
    Determine which sections a user can edit based on role and workflow status
    Returns dict with section permissions
    
    Role permissions:
    - Admin/Inspector: Full access to all DMT sections
    - Engineer: Can edit all DMT form fields
    - Supervisor: Can edit only General Information and Defect Description
    - Others: Read-only based on assignment
    """
    if user_role in ["Admin", "Inspector"]:
        return {
            "general_info": True,
            "defect_description": True,
            "process_analysis": True,
            "engineering": True,
            "can_close": True,
            "can_reopen": True,
            "can_print": True
        }
    
    if record_status == "closed":
        return {
            "general_info": False,
            "defect_description": False,
            "process_analysis": False,
            "engineering": False,
            "can_close": False,
            "can_reopen": False,
            "can_print": True
        }
    
    permissions = {
        "general_info": False,
        "defect_description": False,
        "process_analysis": False,
        "engineering": False,
        "can_close": False,
        "can_reopen": False,
        "can_print": False
    }
    
    if user_role == "Supervisor":
        permissions["general_info"] = True
        permissions["defect_description"] = True
        permissions["can_print"] = True
    elif user_role == "Engineer":
        permissions["general_info"] = True
        permissions["defect_description"] = True
        permissions["process_analysis"] = True
        permissions["engineering"] = True
        permissions["can_close"] = True
        permissions["can_print"] = True
    
    return permissions


@router.get("", response_class=HTMLResponse)
async def dmt_dashboard(request: Request):
    """Render the DMT analytics dashboard"""
    try:
        user = get_current_user(request)
        if not user:
            return RedirectResponse(url="/auth/login", status_code=302)
        
        db = get_db()
        conn = db.get_connection()
        c = db.get_connection().cursor()

        stats = {}
        dmt_entities = [
            EntityType.WORKCENTERS,
            EntityType.CUSTOMERS,
            EntityType.INSPECTION_ITEMS,
            EntityType.PREPARED_BY,
            EntityType.CAR_TYPES,
            EntityType.DISPOSITIONS,
            EntityType.FAILURE_CODES,
        ]
        
        for entity in dmt_entities:
            try:
                c.execute(f"SELECT COUNT(*) as count FROM {entity.value} WHERE is_active = 1")
                stats[entity.value] = c.fetchone()[0]
            except Exception as e:
                print(f"Error getting stats for {entity.value}: {e}")
                stats[entity.value] = 0

        c.execute("SELECT COUNT(*) as count FROM dmt_records WHERE is_active = 1")
        stats["dmt_records"] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) as count FROM dmt_records WHERE status = 'open' AND is_active = 1")
        stats["open_dmts"] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) as count FROM dmt_records WHERE status = 'closed' AND is_active = 1")
        stats["closed_dmts"] = c.fetchone()[0]

        if user["role"] in ["Admin", "Inspector", "Supervisor"]:
            c.execute("SELECT * FROM dmt_records WHERE is_active = 1 ORDER BY created_at DESC LIMIT 10")
        else:
            c.execute("""
                SELECT * FROM dmt_records 
                WHERE is_active = 1 AND (created_by = ? OR assigned_to = ?)
                ORDER BY created_at DESC LIMIT 10
            """, (user["id"], user["id"]))
        
        recent_dmts = [dict(row) for row in c.fetchall()]
        
        conn.close()

        return templates.TemplateResponse("dmt/dashboard.html", {
            "request": request,
            "stats": stats,
            "recent_dmts": recent_dmts,
            "user": user
        })
    except Exception as e:
        print(f"Error in DMT dashboard: {e}")
        return RedirectResponse(url="/auth/login", status_code=302)


@router.get("/records", response_class=HTMLResponse)
async def dmt_records_list(request: Request, page: int = 1, search: str = ""):
    """List all DMT records with pagination and search"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    where_clause = "WHERE is_active = 1"
    params = []
    
    # Admin, Inspector, and Supervisor can see all uploaded DMTs
    if user["role"] in ["Admin", "Inspector", "Supervisor"]:
        where_clause += " AND (is_session = 0 OR (is_session = 1 AND created_by = ?))"
        params.append(user["id"])
    else:
        # Others can only see their own sessions and assigned/created uploaded DMTs
        where_clause += " AND ((is_session = 0 AND (created_by = ? OR assigned_to = ?)) OR (is_session = 1 AND created_by = ?))"
        params.extend([user["id"], user["id"], user["id"]])
    
    if search:
        where_clause += " AND (report_number LIKE ? OR part_num LIKE ? OR shop_order LIKE ? OR status LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])

    c.execute(f"SELECT COUNT(*) as count FROM dmt_records {where_clause}", params)
    total = c.fetchone()[0]

    offset = (page - 1) * 20
    c.execute(
        f"SELECT * FROM dmt_records {where_clause} ORDER BY report_number DESC LIMIT 20 OFFSET ?",
        params + [offset]
    )
    records = [dict(row) for row in c.fetchall()]
    
    conn.close()

    return templates.TemplateResponse("dmt/list.html", {
        "request": request,
        "records": records,
        "total": total,
        "page": page,
        "search": search,
        "user": user
    })


@router.get("/records/items", response_class=HTMLResponse)
async def get_dmt_records_items(request: Request, page: int = 1, search: str = ""):
    """Get paginated DMT records for HTMX updates"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    where_clause = "WHERE is_active = 1"
    params = []
    
    if user["role"] in ["Admin", "Inspector", "Supervisor"]:
        where_clause += " AND (is_session = 0 OR (is_session = 1 AND created_by = ?))"
        params.append(user["id"])
    else:
        where_clause += " AND ((is_session = 0 AND (created_by = ? OR assigned_to = ?)) OR (is_session = 1 AND created_by = ?))"
        params.extend([user["id"], user["id"], user["id"]])
    
    if search:
        where_clause += " AND (report_number LIKE ? OR part_num LIKE ? OR shop_order LIKE ? OR status LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])

    c.execute(f"SELECT COUNT(*) as count FROM dmt_records {where_clause}", params)
    total = c.fetchone()[0]

    offset = (page - 1) * 20
    c.execute(
        f"SELECT * FROM dmt_records {where_clause} ORDER BY report_number DESC LIMIT 20 OFFSET ?",
        params + [offset]
    )
    records = [dict(row) for row in c.fetchall()]
    
    conn.close()

    return templates.TemplateResponse("dmt/records_list.html", {
        "request": request,
        "records": records,
        "total": total,
        "page": page,
        "search": search,
        "user": user
    })


@router.get("/create", response_class=HTMLResponse)
async def dmt_create_form(request: Request):
    """Render DMT creation form"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    selectors = {}
    selector_entities = {
        "workcenters": EntityType.WORKCENTERS,
        "partnumbers": EntityType.PARTNUMBERS,
        "employees": EntityType.EMPLOYEES,
        "customers": EntityType.CUSTOMERS,
        "inspection_items": EntityType.INSPECTION_ITEMS,
        "prepared_by": EntityType.PREPARED_BY,
        "car_types": EntityType.CAR_TYPES,
        "dispositions": EntityType.DISPOSITIONS,
        "failure_codes": EntityType.FAILURE_CODES,
    }
    
    for key, entity in selector_entities.items():
        c.execute(f"SELECT id, name FROM {entity.value} WHERE is_active = 1 ORDER BY name")
        selectors[key] = [dict(row) for row in c.fetchall()]
    
    assignable_users = get_assignable_users(user["role"])
    
    conn.close()

    permissions = get_workflow_permissions(user["role"], "draft", "open")

    return templates.TemplateResponse("dmt/form.html", {
        "request": request,
        "record": None,
        "selectors": selectors,
        "user": user,
        "all_users": assignable_users,
        "permissions": permissions
    })

@router.post("/create", response_class=HTMLResponse)
async def create_dmt_record(
    request: Request,
    work_center: str = Form(""),
    part_num: str = Form(""),
    operation: str = Form(""),
    employee_name: str = Form(""),
    qty: str = Form(""),
    customer: str = Form(""),
    shop_order: str = Form(""),
    serial_number: str = Form(""),
    inspection_item: str = Form(""),
    date: str = Form(""),
    prepared_by: str = Form(""),
    description: str = Form(""),
    car_type: str = Form(""),
    car_cycle: str = Form(""),
    car_second_cycle_date: str = Form(""),
    process_description: str = Form(""),
    analysis: str = Form(""),
    analysis_by: str = Form(""),
    disposition: str = Form(""),
    disposition_date: str = Form(""),
    engineer: str = Form(""),
    failure_code: str = Form(""),
    rework_hours: str = Form(""),
    responsible_dept: str = Form(""),
    material_scrap_cost: str = Form(""),
    others_cost: str = Form(""),
    engineering_remarks: str = Form(""),
    repair_process: str = Form(""),
    assigned_to: str = Form(""),
    save_as_session: str = Form("false"),
):
    """Create a new DMT record"""
    try:
        user = get_current_user(request)
        if not user:
            return RedirectResponse(url="/auth/login", status_code=303)
        
        if save_as_session != "true":
            required_fields = {
                "work_center": work_center,
                "part_num": part_num,
                "operation": operation,
                "employee_name": employee_name,
                "qty": qty,
                "customer": customer,
                "shop_order": shop_order,
                "serial_number": serial_number,
                "inspection_item": inspection_item,
                "date": date,
                "prepared_by": prepared_by,
                "description": description,
                "car_type": car_type,
                "car_cycle": car_cycle,
                "car_second_cycle_date": car_second_cycle_date,
                "disposition": disposition,
                "disposition_date": disposition_date,
                "engineer": engineer,
                "failure_code": failure_code,
                "rework_hours": rework_hours,
                "responsible_dept": responsible_dept,
                "material_scrap_cost": material_scrap_cost,
                "others_cost": others_cost,
                "engineering_remarks": engineering_remarks,
                "repair_process": repair_process,
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                print(f"[v0] Missing required fields: {missing_fields}")
                return RedirectResponse(
                    url=f"/dmt/create?error=Required fields missing: {', '.join(missing_fields)}", 
                    status_code=303
                )
        
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()

        dmt_id = str(uuid.uuid4())[:8].upper()
        report_number = get_next_report_number()
        
        is_session = 1 if save_as_session == "true" else 0
        
        print(f"[v0] Creating DMT record: id={dmt_id}, report_number={report_number}, is_session={is_session}")
        
        c.execute("""
            INSERT INTO dmt_records (
                id, report_number, 
                work_center, part_num, operation, employee_name, qty, customer,
                shop_order, serial_number, inspection_item, date, prepared_by,
                description, car_type, car_cycle, car_second_cycle_date,
                process_description, analysis, analysis_by,
                disposition, disposition_date, engineer, failure_code, rework_hours,
                responsible_dept, material_scrap_cost, others_cost, engineering_remarks,
                repair_process, 
                status, workflow_status, 
                created_by, assigned_to, is_session
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dmt_id, report_number, 
            work_center, part_num, operation, employee_name, qty, customer,
            shop_order, serial_number, inspection_item, date, prepared_by,
            description, car_type, car_cycle, car_second_cycle_date,
            process_description, analysis, analysis_by,
            disposition, disposition_date, engineer, failure_code, rework_hours,
            responsible_dept, material_scrap_cost, others_cost, engineering_remarks,
            repair_process, 
            'open', 'draft', 
            user["id"], assigned_to, is_session
        ))

        c.execute(
            "INSERT INTO audit_log (entity_type, entity_id, action, user_id) VALUES (?, ?, ?, ?)",
            ("dmt_records", dmt_id, "CREATE", user["id"])
        )

        conn.commit()
        conn.close()

        print(f"[v0] DMT record created successfully")
        
        return RedirectResponse(url="/dmt/records", status_code=303)
    except Exception as e:
        print(f"[v0] Error creating DMT record: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url=f"/dmt/create?error={str(e)}", status_code=303)


@router.get("/edit/{dmt_id}", response_class=HTMLResponse)
async def dmt_edit_form(dmt_id: str, request: Request):
    """Render DMT edit form with workflow permissions"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM dmt_records WHERE id = ? AND is_active = 1", (dmt_id,))
    record = c.fetchone()
    
    if not record:
        conn.close()
        return render_toast("DMT record not found", "error")

    record = dict(record)

    selectors = {}
    selector_entities = {
        "workcenters": EntityType.WORKCENTERS,
        "partnumbers": EntityType.PARTNUMBERS,
        "employees": EntityType.EMPLOYEES,
        "customers": EntityType.CUSTOMERS,
        "inspection_items": EntityType.INSPECTION_ITEMS,
        "prepared_by": EntityType.PREPARED_BY,
        "car_types": EntityType.CAR_TYPES,
        "dispositions": EntityType.DISPOSITIONS,
        "failure_codes": EntityType.FAILURE_CODES,
    }
    
    for key, entity in selector_entities.items():
        c.execute(f"SELECT id, name FROM {entity.value} WHERE is_active = 1 ORDER BY name")
        selectors[key] = [dict(row) for row in c.fetchall()]
    
    assignable_users = get_assignable_users(user["role"])
    
    conn.close()

    permissions = get_workflow_permissions(
        user["role"], 
        record.get("workflow_status", "draft"),
        record.get("status", "open"),
        record.get("created_by"),
        user["id"]
    )

    return templates.TemplateResponse("dmt/form.html", {
        "request": request,
        "record": record,
        "selectors": selectors,
        "user": user,
        "all_users": assignable_users,
        "permissions": permissions
    })

@router.post("/update/{dmt_id}", response_class=HTMLResponse)
async def update_dmt_record(
    request: Request,
    dmt_id: str,
    work_center: str = Form(""),
    part_num: str = Form(""),
    operation: str = Form(""),
    employee_name: str = Form(""),
    qty: str = Form(""),
    customer: str = Form(""),
    shop_order: str = Form(""),
    serial_number: str = Form(""),
    inspection_item: str = Form(""),
    date: str = Form(""),
    prepared_by: str = Form(""),
    description: str = Form(""),
    car_type: str = Form(""),
    car_cycle: str = Form(""),
    car_second_cycle_date: str = Form(""),
    process_description: str = Form(""),
    analysis: str = Form(""),
    analysis_by: str = Form(""),
    disposition: str = Form(""),
    disposition_date: str = Form(""),
    engineer: str = Form(""),
    failure_code: str = Form(""),
    rework_hours: str = Form(""),
    responsible_dept: str = Form(""),
    material_scrap_cost: str = Form(""),
    others_cost: str = Form(""),
    engineering_remarks: str = Form(""),
    repair_process: str = Form(""),
    status: str = Form("open"),
    assigned_to: str = Form(""),
    save_as_session: str = Form("false"),
):
    """Update an existing DMT record"""
    try:
        user = get_current_user(request)
        if not user:
            return RedirectResponse(url="/auth/login", status_code=303)
        
        if assigned_to:
            assignable_users = get_assignable_users(user["role"])
            assignable_ids = [u["id"] for u in assignable_users]
            
            if assigned_to not in assignable_ids:
                return RedirectResponse(
                    url=f"/dmt/edit/{dmt_id}?error=You can only assign to users with equal or higher roles", 
                    status_code=303
                )
        
        if save_as_session != "true":
            required_fields = {
                "work_center": work_center,
                "part_num": part_num,
                "operation": operation,
                "employee_name": employee_name,
                "qty": qty,
                "customer": customer,
                "shop_order": shop_order,
                "serial_number": serial_number,
                "inspection_item": inspection_item,
                "date": date,
                "prepared_by": prepared_by,
                "description": description,
                "car_type": car_type,
                "car_cycle": car_cycle,
                "car_second_cycle_date": car_second_cycle_date,
                "disposition": disposition,
                "disposition_date": disposition_date,
                "engineer": engineer,
                "failure_code": failure_code,
                "rework_hours": rework_hours,
                "responsible_dept": responsible_dept,
                "material_scrap_cost": material_scrap_cost,
                "others_cost": others_cost,
                "engineering_remarks": engineering_remarks,
                "repair_process": repair_process,
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                print(f"[v0] Missing required fields: {missing_fields}")
                return RedirectResponse(
                    url=f"/dmt/edit/{dmt_id}?error=Required fields missing: {', '.join(missing_fields)}", 
                    status_code=303
                )
        
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()

        is_session = 1 if save_as_session == "true" else 0
        
        print(f"[v0] Updating DMT record: id={dmt_id}, is_session={is_session}")

        c.execute("""
            UPDATE dmt_records SET
                work_center = ?, part_num = ?, operation = ?, employee_name = ?, qty = ?,
                customer = ?, shop_order = ?, serial_number = ?, inspection_item = ?,
                date = ?, prepared_by = ?, description = ?, car_type = ?, car_cycle = ?,
                car_second_cycle_date = ?, process_description = ?, analysis = ?,
                analysis_by = ?, disposition = ?, disposition_date = ?, engineer = ?,
                failure_code = ?, rework_hours = ?, responsible_dept = ?,
                material_scrap_cost = ?, others_cost = ?, engineering_remarks = ?,
                repair_process = ?, status = ?, assigned_to = ?, is_session = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND is_active = 1
        """, (
            work_center, part_num, operation, employee_name, qty, customer,
            shop_order, serial_number, inspection_item, date, prepared_by,
            description, car_type, car_cycle, car_second_cycle_date,
            process_description, analysis, analysis_by,
            disposition, disposition_date, engineer, failure_code, rework_hours,
            responsible_dept, material_scrap_cost, others_cost, engineering_remarks,
            repair_process, status, assigned_to, is_session, dmt_id
        ))

        c.execute(
            "INSERT INTO audit_log (entity_type, entity_id, action, user_id) VALUES (?, ?, ?, ?)",
            ("dmt_records", dmt_id, "UPDATE", user["id"])
        )

        conn.commit()
        conn.close()

        print(f"[v0] DMT record updated successfully")
        
        return RedirectResponse(url="/dmt/records", status_code=303)
    except Exception as e:
        print(f"[v0] Error updating DMT record: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url=f"/dmt/edit/{dmt_id}?error={str(e)}", status_code=303)


@router.delete("/delete/{dmt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dmt_record(dmt_id: str, request: Request):
    """
    Soft deletes a DMT record. Returns an empty 200 OK response with an
    HX-Trigger header, which tells the list container on the frontend to reload itself.
    """
    user = get_current_user(request)
    
    # Security check to ensure only authorized users can delete
    if not user or user["role"] not in ["Admin", "Inspector", "Supervisor"]:
        return Response(status_code=status.HTTP_403_FORBIDDEN, content="Not authorized")
    
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    # Check if the record exists before trying to delete
    c.execute("SELECT id FROM dmt_records WHERE id = ? AND is_active = 1", (dmt_id,))
    record_exists = c.fetchone()
    
    if record_exists:
        c.execute(
            "UPDATE dmt_records SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (dmt_id,)
        )
        c.execute(
            "INSERT INTO audit_log (entity_type, entity_id, action, user_id) VALUES (?, ?, ?, ?)",
            ("dmt_records", dmt_id, "DELETE", user["id"])
        )
        conn.commit()

    conn.close()

    # Return an empty response but add the HX-Trigger header
    # This tells any element listening for 'dmtListChanged' to fire its trigger.
    return Response(
        status_code=200,
    headers={"HX-Trigger": "dmtListChanged"}
    )
@router.get("/export/{format}")
async def export_dmt_records(format: str, request: Request, days: Optional[int] = None):
    """Export DMT records in JSON or CSV format"""
    try:
        user = get_current_user(request)
        if not user:
            return render_toast("Please log in to export DMT records", "error")
        
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()

        where_clause = "WHERE is_active = 1"
        params = []
        
        # Filter by user role and session visibility
        if user["role"] not in ["Admin", "Inspector", "Supervisor"]:
            where_clause += " AND ((is_session = 0 AND (created_by = ? OR assigned_to = ?)) OR (is_session = 1 AND created_by = ?))"
            params.extend([user["id"], user["id"], user["id"]])
        else:
            where_clause += " AND (is_session = 0 OR (is_session = 1 AND created_by = ?))"
            params.append(user["id"])
        
        # Apply date filter if specified
        if days:
            where_clause += " AND created_at >= datetime('now', '-' || ? || ' days')"
            params.append(days)

        c.execute(f"SELECT * FROM dmt_records {where_clause} ORDER BY created_at DESC", params)
        records = [dict(row) for row in c.fetchall()]
        
        conn.close()

        print(f"[v0] Exporting {len(records)} DMT records (format: {format}, days: {days})")

        if format == "csv":
            return ExportService.export_csv(records, "dmt_records")
        else:
            return ExportService.export_json(records, "dmt_records")
    except Exception as e:
        print(f"[v0] Error exporting DMT records: {e}")
        import traceback
        traceback.print_exc()
        return render_toast(f"Failed to export records: {str(e)}", "error")


@router.post("/workflow/advance/{dmt_id}", response_class=HTMLResponse)
async def advance_workflow(dmt_id: str, request: Request):
    """Advance the workflow to the next stage"""
    try:
        user = get_current_user(request)
        if not user:
            return render_toast("Please log in", "error")
        
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute("SELECT workflow_status, status FROM dmt_records WHERE id = ? AND is_active = 1", (dmt_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return render_toast("DMT record not found", "error")
        
        current_workflow = result[0]
        current_status = result[1]
        
        if current_status == "closed":
            conn.close()
            return render_toast("Cannot advance closed record", "error")
        
        workflow_transitions = {
            "draft": ("supervisor_review", "supervisor_completed_at"),
            "supervisor_review": ("manager_review", "manager_completed_at"),
            "manager_review": ("engineer_review", None),
            "engineer_review": ("completed", "engineer_completed_at")
        }
        
        if current_workflow not in workflow_transitions:
            conn.close()
            return render_toast("Invalid workflow status", "error")
        
        next_workflow, timestamp_field = workflow_transitions[current_workflow]
        
        if timestamp_field:
            c.execute(
                f"UPDATE dmt_records SET workflow_status = ?, {timestamp_field} = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (next_workflow, dmt_id)
            )
        else:
            c.execute(
                "UPDATE dmt_records SET workflow_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (next_workflow, dmt_id)
            )
        
        c.execute(
            "INSERT INTO audit_log (entity_type, entity_id, action, user_id, changes) VALUES (?, ?, ?, ?, ?)",
            ("dmt_records", dmt_id, "WORKFLOW_ADVANCE", user["id"], f"Advanced from {current_workflow} to {next_workflow}")
        )
        
        conn.commit()
        conn.close()
        
        html = f'<div hx-get="/dmt/edit/{dmt_id}" hx-target="#main-content" hx-trigger="load"></div>'
        html += render_toast(f"Workflow advanced to {next_workflow.replace('_', ' ').title()}", "success")
        return html
    except Exception as e:
        print(f"Error advancing workflow: {e}")
        return render_toast(f"Failed to advance workflow: {str(e)}", "error")


@router.post("/close/{dmt_id}", response_class=HTMLResponse)
async def close_dmt(dmt_id: str, request: Request):
    """Close a DMT record (Engineer, Inspector, or Admin)"""
    try:
        user = get_current_user(request)
        if not user:
            return render_toast("Please log in", "error")
        
        if user["role"] not in ["Admin", "Inspector", "Engineer"]:
            return render_toast("Only Engineers, Inspectors, and Admins can close DMT records", "error")
        
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute(
            "UPDATE dmt_records SET status = 'closed', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND is_active = 1",
            (dmt_id,)
        )
        
        c.execute(
            "INSERT INTO audit_log (entity_type, entity_id, action, user_id) VALUES (?, ?, ?, ?)",
            ("dmt_records", dmt_id, "CLOSE", user["id"])
        )
        
        conn.commit()
        conn.close()
        
        return RedirectResponse(url="/dmt/records?success=DMT record closed successfully", status_code=303)
    except Exception as e:
        print(f"[v0] Error closing DMT: {e}")
        return RedirectResponse(url=f"/dmt/records?error={str(e)}", status_code=303)


@router.post("/reopen/{dmt_id}", response_class=HTMLResponse)
async def reopen_dmt(dmt_id: str, request: Request):
    """Reopen a closed DMT record (Admin or Inspector only)"""
    try:
        user = get_current_user(request)
        if not user:
            return render_toast("Please log in", "error")
        
        if user["role"] not in ["Admin", "Inspector"]:
            return render_toast("Only Admins and Inspectors can reopen DMT records", "error")
        
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        c.execute(
            "UPDATE dmt_records SET status = 'open', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND is_active = 1",
            (dmt_id,)
        )
        
        c.execute(
            "INSERT INTO audit_log (entity_type, entity_id, action, user_id) VALUES (?, ?, ?, ?)",
            ("dmt_records", dmt_id, "REOPEN", user["id"])
        )
        
        conn.commit()
        conn.close()
        
        return RedirectResponse(url=f"/dmt/edit/{dmt_id}?success=DMT record reopened successfully", status_code=303)
    except Exception as e:
        print(f"[v0] Error reopening DMT: {e}")
        return RedirectResponse(url=f"/dmt/edit/{dmt_id}?error={str(e)}", status_code=303)


@router.get("/search/employees", response_class=HTMLResponse)
async def search_employees(request: Request, q: str = ""):
    """Search employees by ID, name, or employee number"""
    try:
        user = get_current_user(request)
        if not user:
            return ""
        
        db = get_db()
        conn = db.get_connection()
        c = conn.cursor()
        
        search_param = f"%{q}%"
        c.execute("""
            SELECT id, name, employee_number 
            FROM employees 
            WHERE is_active = 1 
            AND (
                CAST(id AS TEXT) LIKE ? 
                OR name LIKE ? 
                OR employee_number LIKE ?
            )
            ORDER BY name 
            LIMIT 10
        """, (search_param, search_param, search_param))
        
        employees = [dict(row) for row in c.fetchall()]
        conn.close()
        
        if not employees:
            return '<div class="px-4 py-2 text-gray-500 text-sm">No employees found</div>'
        
        html = ""
        for emp in employees:
            emp_number = emp.get('employee_number', '')
            emp_display = f"{emp['name']}"
            if emp_number:
                emp_display += f" ({emp_number})"
            
            html += f'''
            <div class="px-4 py-2 hover:bg-blue-100 cursor-pointer employee-option" 
                 data-id="{emp['id']}" 
                 data-name="{emp['name']}">
                <div class="font-medium">{emp['name']}</div>
                {f'<div class="text-xs text-gray-500">ID: {emp["id"]} | {emp_number}</div>' if emp_number else f'<div class="text-xs text-gray-500">ID: {emp["id"]}</div>'}
            </div>
            '''
        
        return html
    except Exception as e:
        print(f"Error searching employees: {e}")
        return '<div class="px-4 py-2 text-red-500 text-sm">Error searching employees</div>'
