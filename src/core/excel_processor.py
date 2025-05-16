import pandas as pd
import os

class ExcelProcessor:
    """Simple, reliable Excel file processor"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.sheet_names = []
    
    def load_workbook(self):
        """Load Excel file and get sheet names"""
        try:
            self.workbook = pd.ExcelFile(self.file_path)
            self.sheet_names = self.workbook.sheet_names
            return True
        except Exception as e:
            print(f"Error loading {self.file_path}: {str(e)}")
            return False
    
    def get_sheet_preview(self, sheet_name, rows=10):
        """Get raw sheet data without processing"""
        try:
            return pd.read_excel(self.file_path, sheet_name=sheet_name, header=None, nrows=rows)
        except Exception as e:
            print(f"Error previewing sheet: {str(e)}")
            return pd.DataFrame()
    
    def get_sheet_data(self, sheet_name, is_base_file=False):
        """Get processed sheet data"""
        try:
            # Different processing based on file type
            if is_base_file:
                # PREPA PHP files - use row 3 as header (after skipping 2 rows)
                df = pd.read_excel(self.file_path, sheet_name=sheet_name, skiprows=2)
            else:
                # Comparison files - skip 7 rows, header on row 8
                df = pd.read_excel(self.file_path, sheet_name=sheet_name, skiprows=7)
            
            # Ensure we have at least some columns
            if df.shape[1] < 2:
                return pd.DataFrame()
                
            # Extract columns A-J
            col_limit = min(10, df.shape[1])
            df = df.iloc[:, :col_limit].copy()
            
            # Give simple column names like in the test script
            column_names = ["Site", "Serie", "Locomotive", "CodeOp", "Commentaire", "Date Butee", "Date programmation", "Heure programmation", "Date sortie", "Heure sortie"]
            df.columns = column_names[:col_limit]
            
            # Clean data and convert to strings
            for col in df.columns:
                df[col] = df[col].fillna('').astype(str).str.strip().replace('nan', '').replace('NaT', '')
            
            # Filter out rows that are completely empty or only contain NA values
            # Check if a row has any non-empty content in any column except Site
            value_cols = [col for col in df.columns if col != "Site"]
            
            def has_content(row):
                # Check if any column has meaningful content
                for col in value_cols:
                    value = str(row[col]).strip()
                    if value and value not in ('', 'nan', 'NaT', 'None'):
                        return True
                return False
            
            # Filter to keep only rows that have content
            df_with_content = df[df.apply(has_content, axis=1)]
            
            return df_with_content
            
        except Exception as e:
            print(f"Error loading sheet data: {str(e)}")
            return pd.DataFrame()
