"""
DMT (Defective Material Tag) routes
"""
from typing import Optional
from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse
from config import EntityType
from database import get_db
from repositories import Repository
from services import ExportService
from templates import (
    render_dmt_page,
    render_dmt_list_page,
    render_dmt_form_page,
    render_dmt_records_list,
    render_toast,
)
import uuid
from datetime import datetime

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def dmt_dashboard():
    """Render the DMT analytics dashboard"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    # Get statistics for DMT-related entities
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
        c.execute(f"SELECT COUNT(*) as count FROM {entity.value} WHERE is_active = 1")
        stats[entity.value] = c.fetchone()[0]

    # Get DMT records statistics
    c.execute("SELECT COUNT(*) as count FROM dmt_records WHERE is_active = 1")
    stats["dmt_records"] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) as count FROM dmt_records WHERE status = 'open' AND is_active = 1")
    stats["open_dmts"] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) as count FROM dmt_records WHERE status = 'closed' AND is_active = 1")
    stats["closed_dmts"] = c.fetchone()[0]

    # Get recent DMT records
    c.execute("SELECT * FROM dmt_records WHERE is_active = 1 ORDER BY created_at DESC LIMIT 10")
    recent_dmts = [dict(row) for row in c.fetchall()]
    
    conn.close()

    return render_dmt_page(stats, recent_dmts)


@router.get("/records", response_class=HTMLResponse)
async def dmt_records_list(page: int = 1, search: str = ""):
    """List all DMT records with pagination and search"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    # Build search query
    where_clause = "WHERE is_active = 1"
    params = []
    
    if search:
        where_clause += " AND (id LIKE ? OR part_num LIKE ? OR shop_order LIKE ? OR status LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])

    # Get total count
    c.execute(f"SELECT COUNT(*) as count FROM dmt_records {where_clause}", params)
    total = c.fetchone()[0]

    # Get paginated records
    offset = (page - 1) * 20
    c.execute(
        f"SELECT * FROM dmt_records {where_clause} ORDER BY created_at DESC LIMIT 20 OFFSET ?",
        params + [offset]
    )
    records = [dict(row) for row in c.fetchall()]
    
    conn.close()

    return render_dmt_list_page(records, total, page, search)


@router.get("/records/items", response_class=HTMLResponse)
async def get_dmt_records_items(page: int = 1, search: str = ""):
    """Get paginated DMT records for HTMX updates"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    where_clause = "WHERE is_active = 1"
    params = []
    
    if search:
        where_clause += " AND (id LIKE ? OR part_num LIKE ? OR shop_order LIKE ? OR status LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])

    c.execute(f"SELECT COUNT(*) as count FROM dmt_records {where_clause}", params)
    total = c.fetchone()[0]

    offset = (page - 1) * 20
    c.execute(
        f"SELECT * FROM dmt_records {where_clause} ORDER BY created_at DESC LIMIT 20 OFFSET ?",
        params + [offset]
    )
    records = [dict(row) for row in c.fetchall()]
    
    conn.close()

    return render_dmt_records_list(records, total, page, search)


@router.get("/create", response_class=HTMLResponse)
async def dmt_create_form():
    """Render DMT creation form"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    # Get all selector options
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
    
    conn.close()

    return render_dmt_form_page(None, selectors)


@router.post("/create", response_class=HTMLResponse)
async def create_dmt_record(
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
):
    """Create a new DMT record"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    dmt_id = str(uuid.uuid4())[:8].upper()
    
    c.execute("""
        INSERT INTO dmt_records (
            id, work_center, part_num, operation, employee_name, qty, customer,
            shop_order, serial_number, inspection_item, date, prepared_by,
            description, car_type, car_cycle, car_second_cycle_date,
            process_description, analysis, analysis_by,
            disposition, disposition_date, engineer, failure_code, rework_hours,
            responsible_dept, material_scrap_cost, others_cost, engineering_remarks,
            repair_process, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
    """, (
        dmt_id, work_center, part_num, operation, employee_name, qty, customer,
        shop_order, serial_number, inspection_item, date, prepared_by,
        description, car_type, car_cycle, car_second_cycle_date,
        process_description, analysis, analysis_by,
        disposition, disposition_date, engineer, failure_code, rework_hours,
        responsible_dept, material_scrap_cost, others_cost, engineering_remarks,
        repair_process
    ))

    # Log audit
    c.execute(
        "INSERT INTO audit_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
        ("dmt_records", dmt_id, "CREATE")
    )

    conn.commit()
    conn.close()

    # Redirect to records list with success message
    html = f'<div hx-get="/dmt/records" hx-target="#main-content" hx-trigger="load"></div>'
    html += render_toast(f"DMT record {dmt_id} created successfully!", "success")
    return html


@router.get("/edit/{dmt_id}", response_class=HTMLResponse)
async def dmt_edit_form(dmt_id: str):
    """Render DMT edit form"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    # Get DMT record
    c.execute("SELECT * FROM dmt_records WHERE id = ? AND is_active = 1", (dmt_id,))
    record = c.fetchone()
    
    if not record:
        conn.close()
        return render_toast("DMT record not found", "error")

    record = dict(record)

    # Get all selector options
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
    
    conn.close()

    return render_dmt_form_page(record, selectors)


@router.put("/update/{dmt_id}", response_class=HTMLResponse)
async def update_dmt_record(
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
):
    """Update an existing DMT record"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    c.execute("""
        UPDATE dmt_records SET
            work_center = ?, part_num = ?, operation = ?, employee_name = ?, qty = ?,
            customer = ?, shop_order = ?, serial_number = ?, inspection_item = ?,
            date = ?, prepared_by = ?, description = ?, car_type = ?, car_cycle = ?,
            car_second_cycle_date = ?, process_description = ?, analysis = ?,
            analysis_by = ?, disposition = ?, disposition_date = ?, engineer = ?,
            failure_code = ?, rework_hours = ?, responsible_dept = ?,
            material_scrap_cost = ?, others_cost = ?, engineering_remarks = ?,
            repair_process = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND is_active = 1
    """, (
        work_center, part_num, operation, employee_name, qty, customer,
        shop_order, serial_number, inspection_item, date, prepared_by,
        description, car_type, car_cycle, car_second_cycle_date,
        process_description, analysis, analysis_by, disposition, disposition_date,
        engineer, failure_code, rework_hours, responsible_dept,
        material_scrap_cost, others_cost, engineering_remarks, repair_process,
        status, dmt_id
    ))

    # Log audit
    c.execute(
        "INSERT INTO audit_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
        ("dmt_records", dmt_id, "UPDATE")
    )

    conn.commit()
    conn.close()

    html = f'<div hx-get="/dmt/records" hx-target="#main-content" hx-trigger="load"></div>'
    html += render_toast(f"DMT record {dmt_id} updated successfully!", "success")
    return html


@router.delete("/delete/{dmt_id}", response_class=HTMLResponse)
async def delete_dmt_record(dmt_id: str):
    """Delete a DMT record (soft delete)"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    c.execute(
        "UPDATE dmt_records SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (dmt_id,)
    )

    # Log audit
    c.execute(
        "INSERT INTO audit_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
        ("dmt_records", dmt_id, "DELETE")
    )

    conn.commit()
    conn.close()

    # Return updated list
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) as count FROM dmt_records WHERE is_active = 1")
    total = c.fetchone()[0]
    
    c.execute("SELECT * FROM dmt_records WHERE is_active = 1 ORDER BY created_at DESC LIMIT 20")
    records = [dict(row) for row in c.fetchall()]
    
    conn.close()

    html = render_dmt_records_list(records, total, 1, "")
    html += render_toast(f"DMT record {dmt_id} deleted successfully!", "success")
    return html


@router.get("/export/{format}")
async def export_dmt_records(format: str, days: Optional[int] = None):
    """Export DMT records in JSON or CSV format"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    where_clause = "WHERE is_active = 1"
    params = []
    
    if days:
        where_clause += " AND created_at >= datetime('now', '-' || ? || ' days')"
        params.append(days)

    c.execute(f"SELECT * FROM dmt_records {where_clause} ORDER BY created_at DESC", params)
    records = [dict(row) for row in c.fetchall()]
    
    conn.close()

    if format == "csv":
        return ExportService.export_csv(records, "dmt_records")
    else:
        return ExportService.export_json(records, "dmt_records")
