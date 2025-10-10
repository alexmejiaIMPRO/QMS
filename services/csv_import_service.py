"""
CSV Import Service for bulk entity uploads
"""
import csv
import io
from typing import List, Dict, Tuple
from repositories import Repository
from config import EntityType


class CSVImportService:
    """Service for importing entities from CSV files"""
    
    @staticmethod
    def validate_csv_headers(headers: List[str], entity: str) -> Tuple[bool, str]:
        """Validate CSV headers match expected format"""
        if entity == "employees":
            required = ["name", "employee_number"]
        else:
            required = ["name"]
        
        # Check if all required headers are present
        for req in required:
            if req not in headers:
                return False, f"Missing required column: {req}"
        
        return True, ""
    
    @staticmethod
    def parse_csv(file_content: bytes, entity: str) -> Tuple[List[Dict], List[str]]:
        """
        Parse CSV file and return list of items and any errors
        Returns: (items, errors)
        """
        items = []
        errors = []
        
        try:
            # Decode file content
            content = file_content.decode('utf-8')
            csv_file = io.StringIO(content)
            reader = csv.DictReader(csv_file)
            
            # Validate headers
            if not reader.fieldnames:
                return [], ["CSV file is empty or has no headers"]
            
            valid, error = CSVImportService.validate_csv_headers(reader.fieldnames, entity)
            if not valid:
                return [], [error]
            
            # Parse rows
            for idx, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Validate required fields
                if not row.get('name', '').strip():
                    errors.append(f"Row {idx}: Name is required")
                    continue
                
                item = {'name': row['name'].strip()}
                
                # Add employee_number for employees
                if entity == "employees":
                    employee_number = row.get('employee_number', '').strip()
                    if not employee_number:
                        errors.append(f"Row {idx}: Employee number is required")
                        continue
                    item['employee_number'] = employee_number
                
                items.append(item)
        
        except UnicodeDecodeError:
            errors.append("File encoding error. Please ensure the file is UTF-8 encoded")
        except csv.Error as e:
            errors.append(f"CSV parsing error: {str(e)}")
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
        
        return items, errors
    
    @staticmethod
    def import_items(items: List[Dict], entity: str) -> Tuple[int, int, List[str]]:
        """
        Import items into database
        Returns: (success_count, skip_count, errors)
        """
        repo = Repository(EntityType(entity))
        success_count = 0
        skip_count = 0
        errors = []
        
        for item in items:
            try:
                # Check if item already exists by name
                existing_items, _ = repo.get_all(search=item['name'])
                if any(i['name'].lower() == item['name'].lower() for i in existing_items):
                    skip_count += 1
                    continue
                
                # Create the item
                if entity == "employees":
                    repo.create(item['name'], employee_number=item['employee_number'])
                else:
                    repo.create(item['name'])
                
                success_count += 1
            
            except Exception as e:
                errors.append(f"Error importing '{item['name']}': {str(e)}")
        
        return success_count, skip_count, errors
