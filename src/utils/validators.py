import os
from typing import List, Dict, Any, Optional
import pandas as pd

def is_valid_excel_file(file_path: str) -> bool:
    """Check if the provided path is a valid Excel file"""
    if not os.path.exists(file_path):
        return False
    
    # Check file extension
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in ['.xlsx', '.xls']:
        return False
    
    # Try to open with pandas
    try:
        pd.ExcelFile(file_path)
        return True
    except Exception:
        return False

def validate_sheet_exists(file_path: str, sheet_name: str) -> bool:
    """Verify that a sheet exists in an Excel file"""
    if not is_valid_excel_file(file_path):
        return False
    
    try:
        xls = pd.ExcelFile(file_path)
        return sheet_name in xls.sheet_names
    except Exception:
        return False

def validate_column_exists(file_path: str, sheet_name: str, column_name: str) -> bool:
    """Verify that a column exists in a specific sheet"""
    if not validate_sheet_exists(file_path, sheet_name):
        return False
    
    try:
        df = pd.read_excel(file_path, sheet_name)
        return column_name in df.columns
    except Exception:
        return False

def validate_comparison_settings(base_file: str, comparison_file: str, 
                               sheets: List[str], columns: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Validate all comparison settings
    
    Returns a dict with:
    - valid: bool indicating if all settings are valid
    - errors: list of error messages if any
    """
    errors = []
    
    # Check files exist and are valid Excel
    if not is_valid_excel_file(base_file):
        errors.append(f"Base file is not a valid Excel file: {base_file}")
    
    if not is_valid_excel_file(comparison_file):
        errors.append(f"Comparison file is not a valid Excel file: {comparison_file}")
    
    # If files are invalid, don't proceed with further checks
    if errors:
        return {"valid": False, "errors": errors}
    
    # Check sheets exist in both files
    base_xls = pd.ExcelFile(base_file)
    comp_xls = pd.ExcelFile(comparison_file)
    
    for sheet in sheets:
        if sheet not in base_xls.sheet_names:
            errors.append(f"Sheet '{sheet}' not found in base file")
        
        if sheet not in comp_xls.sheet_names:
            errors.append(f"Sheet '{sheet}' not found in comparison file")
    
    # Check columns exist in sheets
    for sheet, cols in columns.items():
        # Skip if sheet was already found to be invalid
        if sheet not in base_xls.sheet_names or sheet not in comp_xls.sheet_names:
            continue
        
        base_df = pd.read_excel(base_file, sheet)
        comp_df = pd.read_excel(comparison_file, sheet)
        
        for col in cols:
            if col not in base_df.columns:
                errors.append(f"Column '{col}' not found in base file sheet '{sheet}'")
            
            if col not in comp_df.columns:
                errors.append(f"Column '{col}' not found in comparison file sheet '{sheet}'")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }