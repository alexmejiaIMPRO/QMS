"""
Helper utility functions
"""
from typing import Dict


def get_entity_info(entity: str) -> Dict[str, str]:
    """Get display information for an entity type"""
    info = {
        "employees": {"label": "Employee", "icon": "👤", "color": "purple"},
        "levels": {"label": "Level", "icon": "📊", "color": "indigo"},
        "areas": {"label": "Area", "icon": "🏢", "color": "pink"},
        "partnumbers": {"label": "Part Number", "icon": "🔧", "color": "orange"},
        "calibrations": {"label": "Calibration", "icon": "⚙️", "color": "teal"},
        "workcenters": {"label": "Work Center", "icon": "🏭", "color": "blue"},
        "customers": {"label": "Customer", "icon": "🏢", "color": "green"},
        "inspection_items": {"label": "Inspection Item", "icon": "🔍", "color": "yellow"},
        "prepared_by": {"label": "Prepared By", "icon": "✍️", "color": "red"},
        "car_types": {"label": "CAR Type", "icon": "📋", "color": "cyan"},
        "dispositions": {"label": "Disposition", "icon": "✅", "color": "lime"},
        "failure_codes": {"label": "Failure Code", "icon": "❌", "color": "rose"},
    }
    return info.get(entity, {"label": entity, "icon": "📄", "color": "gray"})
