from typing import List, Dict, Any, Optional, NamedTuple
from dataclasses import dataclass

@dataclass
class FileInfo:
    """Information about a file being processed"""
    file_path: str
    file_name: str
    sheet_count: int
    sheet_names: List[str]
    
    @classmethod
    def from_path(cls, file_path: str, sheet_names: List[str]):
        """Create FileInfo from a file path"""
        import os
        return cls(
            file_path=file_path,
            file_name=os.path.basename(file_path),
            sheet_count=len(sheet_names),
            sheet_names=sheet_names
        )

@dataclass
class ComparisonSettings:
    """Settings for a comparison operation"""
    base_file: FileInfo
    comparison_files: List[FileInfo]  # To handle multiple comparison files
    sheets_to_compare: List[str]
    site_mappings: Dict[str, str]  # Added for site to sheet mapping
    site_column: str  # Added for specifying site column in comparison files
    column_indices: List[int]  # Added for B-J selection by index

    ignore_case: bool = True
    ignore_whitespace: bool = True
    match_by_column_name: bool = False  # Defaulting to False as we use position for B-J
    match_by_column_position: bool = True

@dataclass
class DifferenceRecord:
    """A record of a difference between two cells"""
    sheet_name: str
    row_index: int
    column_name: str
    base_value: Any
    comparison_value: Any
    
    def __str__(self) -> str:
        return f"Sheet '{self.sheet_name}', Row {self.row_index}, Column '{self.column_name}': " \
               f"Base: '{self.base_value}' vs Comp: '{self.comparison_value}'"

# Using NamedTuple for ComparisonSummary for easy _asdict()
class ComparisonSummary(NamedTuple):
    """Summary statistics for a comparison"""
    total_sheets_compared: int
    total_rows_compared: int
    total_cells_compared: int
    total_differences: int
    total_duplicates: int
    execution_time_seconds: float