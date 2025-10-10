"""
Entity CRUD routes
"""
from typing import Optional
from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse
from config import EntityType
from repositories import Repository
from services import ExportService
from templates import (
    render_entity_page,
    render_items_list,
    render_edit_modal,
    render_toast,
)
from utils import get_entity_info

router = APIRouter()


@router.get("/{entity}", response_class=HTMLResponse)
async def entity_page(entity: str):
    """Render an entity management page"""
    repo = Repository(EntityType(entity))
    items, total = repo.get_all(page=1)
    return render_entity_page(entity, items, total)


@router.get("/{entity}/items", response_class=HTMLResponse)
async def get_items(entity: str, page: int = 1, search: str = ""):
    """Get paginated and filtered items"""
    repo = Repository(EntityType(entity))
    items, total = repo.get_all(page=page, search=search if search else None)
    return render_items_list(items, total, entity, page, search)


@router.post("/{entity}/create", response_class=HTMLResponse)
async def create_item(entity: str, name: str = Form(...)):
    """Create a new item"""
    repo = Repository(EntityType(entity))
    repo.create(name.strip())

    items, total = repo.get_all(page=1)
    html = render_items_list(items, total, entity, 1)
    html += render_toast(
        f"{get_entity_info(entity)['label']} created successfully!", "success"
    )
    return html


@router.get("/{entity}/edit/{item_id}", response_class=HTMLResponse)
async def edit_form(entity: str, item_id: str):
    """Render edit form for an item"""
    repo = Repository(EntityType(entity))
    item = repo.get_by_id(item_id)

    if not item:
        return render_toast("Item not found", "error")

    return render_edit_modal(entity, item_id, item)


@router.put("/{entity}/update/{item_id}", response_class=HTMLResponse)
async def update_item(entity: str, item_id: str, name: str = Form(...)):
    """Update an existing item"""
    repo = Repository(EntityType(entity))
    updated = repo.update(item_id, name.strip())

    if not updated:
        return render_toast("Item not found", "error")

    items, total = repo.get_all(page=1)
    html = render_items_list(items, total, entity, 1)
    html += render_toast(
        f"{get_entity_info(entity)['label']} updated successfully!", "success"
    )
    html += '<div hx-swap-oob="true" id="edit-modal"></div>'
    return html


@router.delete("/{entity}/delete/{item_id}", response_class=HTMLResponse)
async def delete_item(entity: str, item_id: str):
    """Delete an item"""
    repo = Repository(EntityType(entity))
    success = repo.delete(item_id)

    if not success:
        return render_toast("Item not found", "error")

    items, total = repo.get_all(page=1)
    html = render_items_list(items, total, entity, 1)
    html += render_toast(
        f"{get_entity_info(entity)['label']} deleted successfully!", "success"
    )
    return html


@router.get("/{entity}/export/{format}")
async def export_data(entity: str, format: str, days: Optional[int] = None):
    """Export entity data in JSON or CSV format"""
    repo = Repository(EntityType(entity))
    items, _ = repo.get_all(days=days, page=1)

    if format == "csv":
        return ExportService.export_csv(items, entity)
    else:
        return ExportService.export_json(items, entity)
