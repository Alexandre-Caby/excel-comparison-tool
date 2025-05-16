import pandas as pd
from typing import Dict, List

class SiteMatcher:
    """Simple class to handle site code matching and filtering"""
    
    def __init__(self):
        # Default site mappings
        self.site_mappings = {
            "LE": "lens",
            "BGL": "bgl"
        }
    
    def set_site_mappings(self, mappings: Dict[str, str]) -> None:
        """Update the site code to sheet name mappings"""
        self.site_mappings = mappings
    
    def get_site_mappings(self) -> Dict[str, str]:
        """Get current site mappings"""
        return self.site_mappings
    
    def filter_by_site(self, df: pd.DataFrame, site_column: str, site_code: str) -> pd.DataFrame:
        """Filter dataframe by site code using contains (case-insensitive)"""
        if df.empty or site_column not in df.columns:
            return pd.DataFrame()
            
        # Use the same filtering approach as in the successful test script
        filtered = df[df[site_column].str.contains(site_code, case=False, na=False)]
        return filtered
    
    def prepare_comparison_data(self, 
                               comparison_df: pd.DataFrame, 
                               site_column: str, 
                               base_sheets_to_match: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Group comparison data by site and map to corresponding base sheets
        
        Returns a dictionary where keys are base sheet names and values are 
        filtered DataFrames from the comparison file that match that site.
        """
        result = {}
        
        # For each site mapping, filter the comparison data
        for site_code, sheet_name in self.site_mappings.items():
            # Skip if the sheet isn't in our target list
            if sheet_name not in base_sheets_to_match:
                continue
                
            # Apply site filtering (exactly like in test script)
            filtered_data = self.filter_by_site(comparison_df, site_column, site_code)
            
            if not filtered_data.empty:
                result[sheet_name] = filtered_data
        
        return result
