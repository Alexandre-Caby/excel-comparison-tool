import pandas as pd
import re

class ComparisonEngine:
    """Simple engine to compare Excel data"""
    
    def prepare_data(self, df):
        """Clean data for comparison"""
        if df.empty:
            return df
            
        df_clean = df.copy()
        
        # Convert all columns to string and clean
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('').astype(str).str.strip()
        
        return df_clean
    
    def normalize_locomotive_id(self, id_str):
        """
        Normalize locomotive IDs to handle inconsistent formats:
        - Some have letters prefix (BB15030, Z23518)
        - Some are just numbers (872677153)
        - Some might have spaces or other characters
        """
        # Convert to string, make uppercase, and remove any whitespace
        id_str = str(id_str).upper().strip()
        
        if not id_str:
            return ''
            
        # Extract letter prefix if present (e.g., BB from BB15030)
        # This pattern matches any letters at the beginning of the string
        match = re.match(r'^([A-Z]+)(\d+)$', id_str)
        if match:
            prefix = match.group(1)  # The letter prefix (e.g., BB)
            numbers = match.group(2)  # The numeric part (e.g., 15030)
            
            # For consistency, keep the letter prefix
            return f"{prefix}{numbers}"
        else:
            # If it's just numbers or doesn't match pattern, return as is
            return id_str
    
    def create_composite_key(self, df, key_columns=None):
        """Create composite key from specified columns with locomotive ID normalization"""
        if key_columns is None:
            key_columns = ["Locomotive", "CodeOp"]  # Default keys
        
        df_with_key = df.copy()
        
        # Clean key columns first
        for col in key_columns:
            if col in df_with_key.columns:
                df_with_key[col] = df_with_key[col].fillna('').astype(str).str.strip()
        
        # Special handling for Locomotive column - normalize the IDs
        if key_columns[0] in df_with_key.columns:  # Typically "Locomotive"
            df_with_key[key_columns[0]] = df_with_key[key_columns[0]].apply(self.normalize_locomotive_id)
        
        # Create composite key with normalized locomotive IDs
        df_with_key['key'] = df_with_key[key_columns[0]].astype(str) + "_" + df_with_key[key_columns[1]].astype(str)
        return df_with_key
    
    def find_differences(self, base_df, comp_df, key_columns=None, value_columns=None):
        """
        Find only modifications between base and comparison DataFrames.
        Only reports differences for rows that exist in BOTH files.
        """
        if base_df.empty or comp_df.empty:
            return pd.DataFrame(columns=['Key', 'Column', 'Base Value', 'Comparison Value', 'Status'])
            
        # Clean data and create keys
        base = self.prepare_data(base_df)
        comp = self.prepare_data(comp_df)
        
        base = self.create_composite_key(base, key_columns)
        comp = self.create_composite_key(comp, key_columns)
        
        # Default value columns are columns E-J
        if value_columns is None:
            value_columns = ["Commentaire", "Date Butee", "Date programmation", "Heure programmation", "Date sortie", "Heure sortie"]
        
        # Only focus on common keys (rows that exist in BOTH files)
        common_keys = set(base['key']).intersection(set(comp['key']))
        
        # Build results - ONLY for modified rows
        results = []
        
        # Process only modified entries (rows that exist in both files but with different values)
        for key in common_keys:
            base_rows = base[base['key'] == key]
            comp_rows = comp[comp['key'] == key]
            
            # Take the first instance of each key for comparison
            base_row = base_rows.iloc[0]
            comp_row = comp_rows.iloc[0]
            
            # Track if this key has any modifications
            row_modified = False
            row_changes = []
            
            # Compare each value column
            for col in value_columns:
                if col in base_row and col in comp_row:
                    base_val = base_row[col]
                    comp_val = comp_row[col]
                    
                    if base_val != comp_val:
                        row_modified = True
                        row_changes.append({
                            'Key': key,
                            'Column': col,
                            'Base Value': base_val,
                            'Comparison Value': comp_val,
                            'Status': 'Modifiée'
                        })
            
            # If the row was modified, add all changes for this key
            if row_modified:
                results.extend(row_changes)
        
        # Return the results DataFrame - only contains modifications
        return pd.DataFrame(results)
    
    def find_duplicates(self, df, key_columns=None):
        """Find duplicate entries in a DataFrame"""
        if df.empty:
            return pd.DataFrame()
            
        # Make a clean copy of the dataframe
        df_clean = df.copy()
        
        # Default key columns
        if key_columns is None:
            key_columns = ["Locomotive", "CodeOp"]
            
        # Clean data and convert to strings
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('').astype(str).str.strip()
        
        # Filter out rows where all value columns (non-site columns) are empty
        # First determine which columns to check (all except Site and key if in a row)
        value_cols = [col for col in df_clean.columns if col != 'Site' and col != 'key']
        
        # Check if at least one value column has content
        def has_real_content(row):
            for col in value_cols:
                if col in row.index and row[col] and row[col].strip() != '':
                    return True
            return False
        
        # Filter to keep only rows with actual content
        df_with_content = df_clean[df_clean.apply(has_real_content, axis=1)]
        
        if df_with_content.empty:
            return pd.DataFrame()
        
        # Use all columns except 'key' for duplicate detection
        dupe_cols = [col for col in df_with_content.columns if col != 'key']
        
        # Find duplicates
        duplicates = df_with_content[df_with_content.duplicated(subset=dupe_cols, keep=False)]
        
        if not duplicates.empty and all(col in duplicates.columns for col in key_columns):
            duplicates = duplicates.sort_values(by=key_columns)
            
        return duplicates
