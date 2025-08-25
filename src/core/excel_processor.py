import pandas as pd
import os
import numpy as np
import re

class ExcelProcessor:
    """Enhanced Excel file processor with dynamic header detection and robust processing"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.sheet_names = []
        self.detected_headers = {}  # Store detected header rows by sheet
        
    def load_workbook(self):
        """Load Excel file and get sheet names"""
        try:
            self.workbook = pd.ExcelFile(self.file_path)
            self.sheet_names = self.workbook.sheet_names
            return True
        except Exception as e:
            print(f"Error loading {self.file_path}: {str(e)}")
            return False
    
    def get_sheet_preview(self, sheet_name, rows=15):
        """Get raw sheet data without processing"""
        try:
            return pd.read_excel(self.file_path, sheet_name=sheet_name, header=None, nrows=rows)
        except Exception as e:
            print(f"Error previewing sheet: {str(e)}")
            return pd.DataFrame()
    
    def detect_header_row(self, sheet_name, max_rows=20):
        """Automatically detect the header row in a sheet
        
        Uses heuristics to find the most likely header row:
        1. Looks for rows with a high percentage of string values
        2. Checks for patterns in data types
        3. Prefers rows that don't have many empty cells
        """
        try:
            # Get raw preview of first several rows
            preview = self.get_sheet_preview(sheet_name, rows=max_rows)
            if preview.empty:
                return 2  # Default to row 3 (index 2) if detection fails
            
            # Initialize scores for each row
            scores = {}
            
            # Check rows 0 through max_rows-1
            for i in range(min(max_rows, preview.shape[0])):
                row = preview.iloc[i]
                
                # Skip completely empty rows
                if row.isna().all():
                    continue
                
                # Calculate metrics
                non_empty = row.notna().sum()
                string_values = sum(1 for val in row if isinstance(val, str))
                numeric_values = sum(1 for val in row if isinstance(val, (int, float)))
                
                # Calculate score based on metrics
                # Higher score for rows with more strings (likely headers)
                # Lower score for rows with many numbers (likely data)
                if non_empty > 0:
                    string_ratio = string_values / non_empty
                    score = string_ratio * 10 + non_empty * 0.5 - numeric_values * 0.3
                    
                    # Bonus for rows with "typical" header text
                    header_keywords = ['date', 'code', 'id', 'name', 'type', 'status', 'commentaire', 
                                      'site', 'locomotive', 'serie', 'heure', 'sortie', 'programmation']
                    for val in row:
                        if isinstance(val, str) and any(kw in val.lower() for kw in header_keywords):
                            score += 3
                            
                    scores[i] = score
            
            # Return the row with the highest score, or default if no valid rows
            if scores:
                return max(scores.items(), key=lambda x: x[1])[0]
            
            # Default header rows based on file patterns
            if any('PREPA' in self.file_name.upper() or 'PHP' in self.file_name.upper()):
                return 2  # Row 3 (index 2) for PREPA PHP files
            else:
                return 7  # Row 8 (index 7) for other files
                
        except Exception as e:
            print(f"Error detecting header row: {str(e)}")
            return 2  # Default to row 3 (index 2) if detection fails
    
    def detect_column_types(self, columns):
        """Enhanced column detection for harmonizing different file formats"""
        result = [None] * len(columns)
        
        column_mappings = {
            'Site': [
                'site', 'stf', 'code site', 'etablissement', 'ets', 'loc', 'location', 
                'code site réalisateur', 'site réalisateur'
            ],
            'Serie': [
                'serie', 'series', 'type', 'model', 'modèle', 'série+ss série+variante',
                'série', 'ss série', 'variante'
            ],
            'Locomotive': [
                'locomotive', 'loco', 'engine', 'number', 'numéro', 'materiel', 
                'n° matériel roulant', 'matériel roulant', 'materiel roulant'
            ],
            'CodeOp': [
                'codeop', 'code', 'operation', 'opération', 'op', 'id', 
                'code opération', 'code operation'
            ],
            'Commentaire': [
                'commentaire', 'comment', 'description', 'desc', 'note', 'remarks', 
                'commentaires', 'libéllé intervention', 'libelle intervention', 
                'intervention', 'libéllé', 'libelle'
            ],
            'Date Butee': [
                'date butee', 'butee', 'deadline', 'échéance', 'echeance', 'limite', 'limit',
                'butée intervention', 'date de butée', 'date butée', 'butée'
            ],
            'Date programmation': [
                'date programmation', 'date prog', 'schedule date', 'planned date', 'date plan',
                'date de programmation', 'date de début', 'date debut', 'programmation'
            ],
            'Heure programmation': [
                'heure programmation', 'heure prog', 'schedule time', 'planned time',
                'heure de programmation', 'heure de début', 'heure de debut', 'heure début', 'heure de\ndébut'
            ],
            'Date sortie': [
                'date sortie', 'sortie', 'exit date', 'completion date', 'finished date',
                'date de sortie', 'date de fin', 'date fin', 'fin'
            ],
            'Heure sortie': [
                'heure sortie', 'exit time', 'completion time', 'finished time',
                'heure de sortie', 'heure de fin', 'heure fin', 'heure de\nfin'
            ],
            'Semaine de programmation': [
                'semaine de programmation', 'semaine prog', 'week', 'semaine', 'week number',
                'numéro semaine', 'numero semaine', 'semaine de prog', 'week programming',
                'programming week', 'semaine programmation'
            ]
        }
        # Check each column
        for i, col in enumerate(columns):
            if not isinstance(col, str):
                continue
                
            # Clean the column name: remove newlines, extra spaces, and convert to lowercase
            col_clean = str(col).lower().strip().replace('\n', ' ').replace('\r', ' ')
            # Remove multiple spaces
            col_clean = ' '.join(col_clean.split())
            
            # Check against each mapping
            for standard_name, keywords in column_mappings.items():
                if any(kw.lower() in col_clean for kw in keywords):
                    result[i] = standard_name
                    #print(f"Mapped '{col}' -> '{standard_name}'")
                    break
        
        #print(f"Column mapping results: {dict(zip(columns, result))}")
        return result

    def get_sheet_data(self, sheet_name, is_base_file=False, header_row=None, 
                  use_dynamic_detection=True, file_type=None):
        """Get processed sheet data
    
        Args:
            sheet_name: Name of the sheet to process
            is_base_file: Whether this is the base file (for backward compatibility)
            header_row: Manually specify header row (0-based index)
            use_dynamic_detection: Whether to attempt to detect headers
            file_type: Type of file ('base', 'comparison', or 'analysis')
        """
        try:
            skiprows = None            
            if header_row is not None:
                skiprows = header_row
            elif not use_dynamic_detection:
                if is_base_file or file_type == 'base':
                    skiprows = 2  # PREPA PHP files (row 3)
                else:
                    skiprows = 7  # Comparison files (row 8)
            else:
                # Try to get from cache first
                if sheet_name in self.detected_headers:
                    skiprows = self.detected_headers[sheet_name]
                else:
                    # Dynamically detect the header row
                    skiprows = self.detect_header_row(sheet_name)
                    # Cache the result
                    self.detected_headers[sheet_name] = skiprows
        
            # Read the sheet with the determined header row
            df = pd.read_excel(self.file_path, sheet_name=sheet_name, skiprows=skiprows)
            
            # Check if this is a PHP analysis file
            is_analysis_file = file_type == 'analysis' or (
                file_type is None and 
                any(col in str(c).upper() for c in df.columns 
                    for col in ['STF', 'N° MATERIEL', 'N° SEMAINE', 'EQUIPE'])
            )
            
            if is_analysis_file:
                return self._process_php_analysis_file(df)
            else:
                # Continue with standard comparison file processing
                # Ensure we have at least some columns
                if df.shape[1] < 2:
                    return pd.DataFrame()
                    
                # Extract columns A-K for comparison files
                col_limit = min(11, df.shape[1])
                df = df.iloc[:, :col_limit].copy()
                
                detected_mappings = self.detect_column_types(df.columns)

            standard_columns = ["Site", "Serie", "Locomotive", "CodeOp", "Commentaire", 
                               "Date Butee", "Date programmation", "Heure programmation", 
                               "Date sortie", "Heure sortie", "Semaine de programmation"]

            final_column_names = []
            seen_columns = {}
            
            for i in range(col_limit):
                col_name = None
                if i < len(detected_mappings) and detected_mappings[i]:
                    col_name = detected_mappings[i]
                elif i < len(standard_columns):
                    col_name = standard_columns[i]
                else:
                    col_name = f"Unknown_{i}"
                if col_name in seen_columns:
                    seen_columns[col_name] += 1
                    final_column_names.append(f"{col_name}_{seen_columns[col_name]}")
                else:
                    seen_columns[col_name] = 0
                    final_column_names.append(col_name)
            
            df.columns = final_column_names
            #print(f"Column names after handling duplicates: {df.columns.tolist()}")
            
            result_df = pd.DataFrame(columns=standard_columns)

            for std_col in standard_columns:
                if std_col in df.columns:
                    result_df[std_col] = df[std_col]
                else:
                    matching_cols = [col for col in df.columns if col.startswith(f"{std_col}_")]
                    if matching_cols:
                        result_df[std_col] = df[matching_cols[0]]
                    else:
                        result_df[std_col] = ''
            
            # Replace the original DataFrame with our standardized one
            df = result_df
            
            #print(f"Final standardized columns: {df.columns.tolist()}")

            for required_col in standard_columns:
                if required_col not in df.columns:
                    df[required_col] = ''
                    #print(f"Added missing column: {required_col}")

            df = df.reindex(columns=standard_columns, fill_value='')
            #print(f"Final standardized columns: {df.columns.tolist()}")

            column_mapping = {
                'codeop': 'CodeOp',
                'Codeop': 'CodeOp', 
                'date sortie': 'Date sortie',
                'Date Sortie': 'Date sortie'
            }
            df.columns = [column_mapping.get(col, col) for col in df.columns]
            df = df.loc[:, ~df.columns.duplicated()]
            
            for col in df.columns:
                df[col] = df[col].fillna('')
                if not pd.api.types.is_datetime64_any_dtype(df[col]):
                    try:
                        df[col] = df[col].astype(str).str.strip()
                    except:
                        df[col] = df[col].fillna('').astype(str)
                
                # Replace various null indicators
                df[col] = df[col].replace(['nan', 'NaT', 'None', 'NA', 'N/A'], '')
                
                # Try to convert date columns to datetime
                if any(date_word in col.lower() for date_word in ['date', 'butee', 'programmation', 'sortie']):
                    try:
                        # First check if column contains date-like strings
                        date_pattern = r'\d{1,4}[/-]\d{1,2}[/-]\d{1,4}'
                        has_dates = df[col].astype(str).str.contains(date_pattern, regex=True, na=False).any()
                        
                        if has_dates:
                            # Check format type (YYYY-MM-DD vs DD/MM/YYYY)
                            iso_pattern = r'\d{4}-\d{2}-\d{2}'
                            has_iso = df[col].astype(str).str.contains(iso_pattern, regex=True, na=False).any()
                            
                            if has_iso:
                                # ISO format - don't use dayfirst
                                df[col] = pd.to_datetime(df[col], errors='coerce')
                            else:
                                # Likely DD/MM/YYYY format
                                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                    except Exception as e:
                        print(f"Date conversion error for {col}: {e}")
            
            # Filter out rows that are completely empty or only contain NA values
            # Check if a row has any non-empty content in any column except Site
            value_cols = [col for col in df.columns if col != "Site"]
            
            def has_content(row):
                # Check if any column has meaningful content
                for col in value_cols:
                    value = str(row[col]).strip()
                    if value and value not in ('', 'nan', 'NaT', 'None', 'NA', 'N/A'):
                        return True
                return False
            
            # Filter to keep only rows that have content
            df_with_content = df[df.apply(has_content, axis=1)]
            
            return df_with_content
                
        except Exception as e:
            print(f"Error loading sheet data: {str(e)}")
            return pd.DataFrame()

    def _process_php_analysis_file(self, df):
        """Process PHP analysis file format with different column structure"""
        if df.empty:
            return df

        # Select desired columns (A-J and N and P) based on position
        if df.shape[1] >= 16:
            desired_cols = list(range(0, 10)) + [13, 15]  # Columns A-J (0-9), N (13), and P (15)
            df_copy = df.iloc[:, desired_cols].copy()
        else:
            df_copy = df.copy()

        # PHP analysis column mappings
        php_columns = {
            'STF': ['stf'],
            'SERIE': ['serie'],
            'N° Matériel Roulant': ['n° matériel roulant', 'matériel roulant'],
            'Code Opération': ['code opération'],
            'Libellé Intervention': ['libéllé intervention', 'libellé intervention'],
            'Butée Intervention': ['butée', 'butée intervention'],
            'Date de Début': ['date de début'],
            'Heure de Début': ['heure de début', 'heure de\ndébut'],
            'Date de Fin': ['date de fin'],
            'Heure de Fin': ['heure de fin', 'heure de\nfin'],
            'N° Semaine Ou Reliquat': ['n° semaine', 'semaine ou reliquat'],
            'Acceptée': ['acceptée','acceptee']
        }
        
        # Standardize column names using exact matching first, then fuzzy matching
        column_map = {}
        for i, col in enumerate(df_copy.columns):
            col_str = str(col).lower().strip().replace('\n', ' ').replace('\r', ' ')
            col_str = ' '.join(col_str.split())  # Remove multiple spaces
            
            # Try exact match first
            for std_col, keywords in php_columns.items():
                if col_str in [kw.lower() for kw in keywords]:
                    column_map[col] = std_col
                    break
            
            # If no exact match, try fuzzy matching
            if col not in column_map:
                for std_col, keywords in php_columns.items():
                    if any(kw.lower() in col_str for kw in keywords):
                        column_map[col] = std_col
                        break
        
        # Rename matched columns
        if column_map:
            df_copy = df_copy.rename(columns=column_map)
        
        # Handle duplicate column names by keeping the first occurrence and renaming others
        if df_copy.columns.duplicated().any():
            cols = df_copy.columns.tolist()
            seen = {}
            new_cols = []
            
            for col in cols:
                if col in seen:
                    seen[col] += 1
                    new_cols.append(f"{col}_{seen[col]}")
                else:
                    seen[col] = 0
                    new_cols.append(col)
            
            df_copy.columns = new_cols

        # Clean and standardize data
        for col in df_copy.columns:
            df_copy[col] = df_copy[col].fillna('')
            
            # Convert to string and clean, but preserve datetime columns
            if not pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                try:
                    df_copy[col] = df_copy[col].astype(str).str.strip()
                except:
                    df_copy[col] = df_copy[col].fillna('').astype(str)
            
            # Replace null indicators
            df_copy[col] = df_copy[col].replace(['nan', 'NaT', 'None', 'NA', 'N/A'], '')
        
        # Handle time columns that might contain full datetime values
        time_columns = ['Heure de Début', 'Heure de Fin']
        for time_col in time_columns:
            if time_col in df_copy.columns:
                sample_values = df_copy[time_col].dropna().head(3)
                
                for i, val in enumerate(sample_values):
                    # Check if this looks like a datetime string with 1900 date
                    if isinstance(val, str) and ('1900-' in val or 'T' in val):
                        # Extract time from datetime strings like "1900-01-25 12:00:00"
                        def extract_time_from_datetime_string(dt_str):
                            try:
                                if isinstance(dt_str, str) and dt_str.strip():
                                    # Parse as datetime and extract time
                                    parsed = pd.to_datetime(dt_str, errors='coerce')
                                    if pd.notna(parsed):
                                        return parsed.strftime('%H:%M:%S')
                                    else:
                                        if ' ' in dt_str:
                                            time_part = dt_str.split(' ')[-1]
                                            if ':' in time_part:
                                                return time_part
                                return dt_str
                            except:
                                return dt_str
                        
                        df_copy[time_col] = df_copy[time_col].apply(extract_time_from_datetime_string)
                        break

        date_columns = ['Date de Début', 'Date de Fin', 'Butée Intervention']
        for date_col in date_columns:
            if date_col in df_copy.columns:
                # Save original values in a separate column
                df_copy[f"{date_col}_Original"] = df_copy[date_col].copy()
                
                # Check if date column contains datetime values or strings
                sample_values = df_copy[date_col].dropna().head(3)
                is_iso_format = False
                
                # Try to detect ISO format
                for val in sample_values:
                    if isinstance(val, str) and re.match(r'^\d{4}-\d{2}-\d{2}', val):
                        is_iso_format = True
                        break
                
                # Use the appropriate dayfirst setting based on detected format
                try:
                    if is_iso_format:
                        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce', dayfirst=False)
                    else:
                        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce', dayfirst=True)
                except Exception as e:
                    print(f"Date conversion error for {date_col}: {e}")
        
        # Filter out empty rows
        if not df_copy.empty:
            has_content = df_copy.apply(
                lambda row: any(str(val).strip() not in ('', 'nan', 'NaT', 'None', 'NA', 'N/A') 
                            for val in row), 
                axis=1
            )
            df_copy = df_copy[has_content]
        
        return df_copy