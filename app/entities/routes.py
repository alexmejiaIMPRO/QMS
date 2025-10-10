from typing import Optional
from fastapi import APIRouter, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from config import EntityType, Config
from repositories import Repository
from services import ExportService
from services.csv_import_service import CSVImportService
from utils import get_entity_info

router = APIRouter()
templates = Jinja2Templates(directory="jinja_templates")


def render_toast(message: str, type: str = "success") -> str:
    colors = {"success": "green", "error": "red", "info": "blue"}
    color = colors.get(type, "blue")
    return templates.get_template("components/toast.html").render(message=message, color=color)


@router.get("/{entity}", response_class=HTMLResponse)
async def entity_page(entity: str, request: Request):
    """Render an entity management page"""
    repo = Repository(EntityType(entity))
    items, total = repo.get_all(page=1)
    info = get_entity_info(entity)
    
    total_pages = (total + Config.PAGE_SIZE - 1) // Config.PAGE_SIZE
    return templates.TemplateResponse("entity_page.html", {
        "request": request,
        "entity": entity,
        "items": items,
        "total": total,
        "info": info,
        "page": 1,
        "search": "",
        "total_pages": total_pages
    })


@router.get("/{entity}/items", response_class=HTMLResponse)
async def get_items(entity: str, request: Request, page: int = 1, search: str = ""):
    """Get paginated and filtered items"""
    repo = Repository(EntityType(entity))
    items, total = repo.get_all(page=page, search=search if search else None)
    info = get_entity_info(entity)
    
    total_pages = (total + Config.PAGE_SIZE - 1) // Config.PAGE_SIZE
    return templates.TemplateResponse("components/items_list.html", {
        "request": request,
        "items": items,
        "total": total,
        "entity": entity,
        "page": page,
        "search": search,
        "info": info,
        "total_pages": total_pages
    })


@router.post("/{entity}/create", response_class=HTMLResponse)
async def create_item(
    entity: str, 
    request: Request, 
    name: str = Form(...),
    employee_number: str = Form(None)
):
    """Create a new item"""
    repo = Repository(EntityType(entity))
    
    if entity == "employees" and employee_number:
        repo.create(name.strip(), employee_number=employee_number.strip())
    else:
        repo.create(name.strip())

    items, total = repo.get_all(page=1)
    info = get_entity_info(entity)
    
    total_pages = (total + Config.PAGE_SIZE - 1) // Config.PAGE_SIZE
    html = templates.get_template("components/items_list.html").render(
        request=request,
        items=items,
        total=total,
        entity=entity,
        page=1,
        search="",
        info=info,
        total_pages=total_pages
    )
    html += render_toast(f"{info['label']} created successfully!", "success")
    return html


@router.post("/{entity}/upload-csv", response_class=HTMLResponse)
async def upload_csv(
    entity: str,
    request: Request,
    file: UploadFile = File(...)
):
    """Upload and import CSV file"""
    # Validate file type
    if not file.filename.endswith('.csv'):
        return render_toast("Please upload a CSV file", "error")
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse CSV
        items, parse_errors = CSVImportService.parse_csv(content, entity)
        
        if parse_errors:
            error_msg = "<br>".join(parse_errors[:5])  # Show first 5 errors
            if len(parse_errors) > 5:
                error_msg += f"<br>...and {len(parse_errors) - 5} more errors"
            return render_toast(f"CSV parsing errors:<br>{error_msg}", "error")
        
        if not items:
            return render_toast("No valid items found in CSV", "error")
        
        # Import items
        success, skipped, import_errors = CSVImportService.import_items(items, entity)
        
        # Refresh items list
        repo = Repository(EntityType(entity))
        items_list, total = repo.get_all(page=1)
        info = get_entity_info(entity)
        
        total_pages = (total + Config.PAGE_SIZE - 1) // Config.PAGE_SIZE
        html = templates.get_template("components/items_list.html").render(
            request=request,
            items=items_list,
            total=total,
            entity=entity,
            page=1,
            search="",
            info=info,
            total_pages=total_pages
        )
        
        # Build success message
        msg = f"✓ Imported {success} items"
        if skipped > 0:
            msg += f", skipped {skipped} duplicates"
        if import_errors:
            msg += f"<br>⚠ {len(import_errors)} errors occurred"
        
        html += render_toast(msg, "success" if not import_errors else "info")
        return html
    
    except Exception as e:
        return render_toast(f"Upload failed: {str(e)}", "error")


@router.get("/{entity}/edit/{item_id}", response_class=HTMLResponse)
async def edit_form(entity: str, item_id: str, request: Request):
    """Render edit form for an item"""
    repo = Repository(EntityType(entity))
    item = repo.get_by_id(item_id)

    if not item:
        return render_toast("Item not found", "error")

    info = get_entity_info(entity)
    
    return templates.TemplateResponse("components/edit_modal.html", {
        "request": request,
        "entity": entity,
        "item_id": item_id,
        "item": item,
        "info": info
    })


@router.put("/{entity}/update/{item_id}", response_class=HTMLResponse)
async def update_item(
    entity: str, 
    item_id: str, 
    request: Request, 
    name: str = Form(...),
    employee_number: str = Form(None)
):
    """Update an existing item"""
    repo = Repository(EntityType(entity))
    
    if entity == "employees" and employee_number is not None:
        updated = repo.update(item_id, name.strip(), employee_number=employee_number.strip())
    else:
        updated = repo.update(item_id, name.strip())

    if not updated:
        return render_toast("Item not found", "error")

    items, total = repo.get_all(page=1)
    info = get_entity_info(entity)
    
    total_pages = (total + Config.PAGE_SIZE - 1) // Config.PAGE_SIZE
    html = templates.get_template("components/items_list.html").render(
        request=request,
        items=items,
        total=total,
        entity=entity,
        page=1,
        search="",
        info=info,
        total_pages=total_pages
    )
    html += render_toast(f"{info['label']} updated successfully!", "success")
    html += '<div hx-swap-oob="true" id="edit-modal"></div>'
    return html


@router.delete("/{entity}/delete/{item_id}", response_class=HTMLResponse)
async def delete_item(entity: str, item_id: str, request: Request):
    """Delete an item"""
    repo = Repository(EntityType(entity))
    success = repo.delete(item_id)

    if not success:
        return render_toast("Item not found", "error")

    items, total = repo.get_all(page=1)
    info = get_entity_info(entity)
    
    total_pages = (total + Config.PAGE_SIZE - 1) // Config.PAGE_SIZE
    html = templates.get_template("components/items_list.html").render(
        request=request,
        items=items,
        total=total,
        entity=entity,
        page=1,
        search="",
        info=info,
        total_pages=total_pages
    )
    html += render_toast(f"{info['label']} deleted successfully!", "success")
    return html


@router.get("/{entity}/export/{format}")
async def export_data(entity: str, format: str, days: Optional[int] = None):
    """Export entity data in JSON or CSV format"""
    repo = Repository(EntityType(entity))
    
    # Get all items without pagination when exporting
    if days:
        items, _ = repo.get_all(days=days, page=1)
        # Get all pages if there are more items
        total_items = []
        page = 1
        while True:
            page_items, total = repo.get_all(days=days, page=page)
            if not page_items:
                break
            total_items.extend(page_items)
            if len(total_items) >= total:
                break
            page += 1
        items = total_items
    else:
        # Get all items without date filter
        total_items = []
        page = 1
        while True:
            page_items, total = repo.get_all(page=page)
            if not page_items:
                break
            total_items.extend(page_items)
            if len(total_items) >= total:
                break
            page += 1
        items = total_items

    if format == "csv":
        return ExportService.export_csv(items, entity)
    else:
        return ExportService.export_json(items, entity)
