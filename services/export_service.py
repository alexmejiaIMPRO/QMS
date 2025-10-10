"""
Export service for data export functionality
"""
import io
import csv
import json
from datetime import datetime
from typing import List, Dict
from fastapi.responses import StreamingResponse


class ExportService:
    """Service for exporting data in various formats"""
    
    @staticmethod
    def export_json(items: List[Dict], entity: str) -> StreamingResponse:
        """Export items as JSON"""
        clean_items = []
        for item in items:
            clean_item = {k: v for k, v in item.items() if k != "is_active"}
            clean_items.append(clean_item)
        
        json_str = json.dumps(clean_items, indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(json_str.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={entity}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            },
        )
    
    @staticmethod
    def export_csv(items: List[Dict], entity: str) -> StreamingResponse:
        """Export items as CSV"""
        clean_items = []
        for item in items:
            clean_item = {k: v for k, v in item.items() if k != "is_active"}
            clean_items.append(clean_item)
        
        output = io.StringIO()
        if clean_items:
            writer = csv.DictWriter(output, fieldnames=clean_items[0].keys())
            writer.writeheader()
            writer.writerows(clean_items)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={entity}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )
