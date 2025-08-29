import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class AnalysisEngine:
    """PHP Analysis Engine for maintenance program analysis"""
    
    def __init__(self):
        self.php_columns = {
            'client': 'STF',
            'serie': 'SERIE', 
            'material_number': 'N° Matériel Roulant',
            'operation_code': 'Code Opération',
            'intervention_label': 'Libellé Intervention',
            'start_date': 'Date de Début',
            'start_time': 'Heure de Début',
            'end_date': 'Date de Fin',
            'end_time': 'Heure de Fin',
            'week_number': 'N° Semaine Ou Reliquat',
            'accepted': 'Acceptée'
        }

    def analyze_php_file(self, file_path, sheet_name, analysis_options=None):
        """Main PHP analysis method"""
        try:
            logger.info(f"Starting PHP analysis for {file_path}, sheet: {sheet_name}")
            
            # Import ExcelProcessor with proper handling for both dev and packaged modes
            if getattr(sys, 'frozen', False):
                # PyInstaller mode
                from excel_processor import ExcelProcessor
            else:
                # Development mode
                from src.core.excel_processor import ExcelProcessor
            
            processor = ExcelProcessor(file_path)
            if not processor.load_workbook():
                raise Exception("Failed to load Excel file")
            
            df = processor.get_sheet_data(sheet_name, is_base_file=True)
            if df.empty:
                raise Exception("No data found in the sheet")
            
            logger.info(f"Loaded {len(df)} rows of PHP data")
            
            if analysis_options is None:
                analysis_options = {
                    'weekly_planning': True,
                    'equipment_analysis': True,
                    'concatenation_analysis': True,
                    'conflict_detection': True
                }
            
            site = sheet_name
            week_filter = analysis_options.get('week_filter', 'all')
            
            df_clean = self.prepare_php_data(df, site)
            
            if week_filter and week_filter != 'all':
                df_clean = self.filter_by_week(df_clean, week_filter)
            
            results = {}
            
            if analysis_options.get('weekly_planning', True):
                results['weekly_planning'] = self.analyze_weekly_planning(df_clean, site)
            
            if analysis_options.get('equipment_analysis', True):
                results['equipment_analysis'] = self.analyze_equipment(df_clean, site)
            
            if analysis_options.get('concatenation_analysis', True):
                results['concatenated_data'] = self.create_concatenated_data(df_clean, site)
            
            if analysis_options.get('conflict_detection', True):
                results['conflicts'] = self.detect_conflicts(df_clean, site)
            
            results['summary'] = self.calculate_summary(results, site)
            results['metadata'] = {
                'file_path': file_path,
                'sheet_name': sheet_name,
                'site': site,
                'total_rows': len(df),
                'processed_rows': len(df_clean),
                'analysis_date': datetime.now().isoformat(),
                'week_filter': week_filter
            }
            
            logger.info("PHP analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in PHP analysis: {str(e)}")
            raise
    
    def convert_date_columns(self, df):
        """Convert date columns with better handling of invalid dates"""
        try:
            date_columns = ['Date de Début', 'Date de Fin']

            for col in date_columns:
                if col in df.columns:
                    logger.info(f"Processing column {col}")
                    
                    # First, try different date formats
                    df[col] = self.parse_dates_multiple_formats(df[col])
                    
                    # Count missing values
                    missing_count = df[col].isna().sum()
                    if missing_count > 0:
                        logger.info(f"Found {missing_count} invalid dates in {col}")
            
            # Combine with time columns, but don't use default dates
            if 'Date de Début' in df.columns and 'Heure de Début' in df.columns:
                df['DateTime de Début'] = df.apply(
                    lambda row: self.combine_date_time(
                        row['Date de Début'], 
                        row['Heure de Début']
                    ) if pd.notna(row['Date de Début']) else pd.NaT, 
                    axis=1
                )
            
            if 'Date de Fin' in df.columns and 'Heure de Fin' in df.columns:
                df['DateTime de Fin'] = df.apply(
                    lambda row: self.combine_date_time(
                        row['Date de Fin'], 
                        row['Heure de Fin']
                    ) if pd.notna(row['Date de Fin']) else pd.NaT, 
                    axis=1
                )
                
            # Fix inverted dates (when end date is before start date)
            date_col = 'DateTime de Début' if 'DateTime de Début' in df.columns else 'Date de Début'
            end_date_col = 'DateTime de Fin' if 'DateTime de Fin' in df.columns else 'Date de Fin'
            
            inverted_mask = (pd.notna(df[date_col]) & pd.notna(df[end_date_col]) & 
                            (df[end_date_col] < df[date_col]))
            
            if inverted_mask.sum() > 0:
                logger.info(f"Fixing {inverted_mask.sum()} inverted date ranges")
                # Swap start and end dates for inverted ranges
                df.loc[inverted_mask, [date_col, end_date_col]] = df.loc[inverted_mask, [end_date_col, date_col]].values
                
        except Exception as e:
            logger.error(f"Error in datetime processing: {str(e)}")
    
    def parse_dates_multiple_formats(self, date_series):
        """Try multiple date formats to parse dates correctly"""
        if date_series.empty:
            return date_series
        
        # If already parsed as datetime, return as is
        if pd.api.types.is_datetime64_any_dtype(date_series):
            return date_series
        
        # Try different date formats
        date_formats = [
            '%d/%m/%Y',     # 23/05/2025
            '%d-%m-%Y',     # 23-05-2025
            '%Y-%m-%d',     # 2025-05-23
            '%Y-%m-%d %H:%M:%S',  # 2025-05-23 14:30:00
            '%d.%m.%Y',     # 23.05.2025
            '%d/%m/%y',     # 23/05/25
            '%d-%m-%y',     # 23-05-25
        ]
        
        result = pd.Series(index=date_series.index, dtype='datetime64[ns]')
        parsed_formats = set()
        
        for idx, value in date_series.items():
            if pd.isna(value) or value == '':
                result[idx] = pd.NaT
                continue
                
            # Convert to string and clean
            date_str = str(value).strip()
            
            # Skip if empty after cleaning
            if not date_str or date_str.lower() in ['nan', 'none', 'null']:
                result[idx] = pd.NaT
                continue
            
            # Try each format
            parsed = False
            for fmt in date_formats:
                try:
                    result[idx] = pd.to_datetime(date_str, format=fmt)
                    parsed = True
                    parsed_formats.add(fmt)
                    break
                except:
                    continue
            
            # If no format worked, try pandas auto-detection
            if not parsed:
                try:
                    # For ISO format dates (YYYY-MM-DD), dayfirst should be False
                    if re.match(r'^\d{4}-\d{2}-\d{2}', date_str):
                        result[idx] = pd.to_datetime(date_str, dayfirst=False, errors='raise')
                    else:
                        result[idx] = pd.to_datetime(date_str, dayfirst=True, errors='raise')
                    parsed_formats.add('auto-detection')
                except:
                    result[idx] = pd.NaT
        
        # Log the formats that were successfully used
        if parsed_formats:
            logger.info(f"Successfully parsed dates using formats: {', '.join(parsed_formats)}")
            
        return result
    
    def combine_date_time(self, date_val, time_val):
        """Combine date and time values"""
        if pd.isna(date_val):
            return pd.NaT
        
        combined = date_val
        
        if not pd.isna(time_val):
            time_str = str(time_val).strip()
            try:
                if ':' in time_str:
                    time_parts = time_str.split(':')
                    if len(time_parts) >= 2:
                        hour, minute = int(time_parts[0]), int(time_parts[1])
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            combined = combined.replace(hour=hour, minute=minute)
                else:
                    time_float = float(time_str)
                    hour = int(time_float)
                    minute = int((time_float - hour) * 60)
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        combined = combined.replace(hour=hour, minute=minute)
            except Exception:
                pass
        
        return combined
    
    def prepare_php_data(self, df, site):
        """Clean and prepare PHP data for analysis - keep all rows but flag invalid ones"""
        df_clean = df.copy()
        df_clean['Site'] = site
        df_clean = df_clean.fillna('')
        
        # Convert date columns with enhanced validation
        self.convert_date_columns(df_clean)
        
        # Clean text columns
        text_columns = ['STF', 'SERIE', 'N° Matériel Roulant', 'Code Opération', 'Libellé Intervention']
        for col in text_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.strip()
        
        # Add validation flags - don't remove any rows
        date_col = 'DateTime de Début' if 'DateTime de Début' in df_clean.columns else 'Date de Début'
        end_date_col = 'DateTime de Fin' if 'DateTime de Fin' in df_clean.columns else 'Date de Fin'
        
        # Flag rows with missing or invalid dates
        df_clean['has_valid_start_date'] = pd.notna(df_clean[date_col])
        df_clean['has_valid_end_date'] = pd.notna(df_clean[end_date_col])
        df_clean['has_valid_dates'] = df_clean['has_valid_start_date'] & df_clean['has_valid_end_date']
        
        # Flag excessive durations (only for valid dates)
        df_clean['excessive_duration'] = False
        valid_dates_mask = df_clean['has_valid_dates']
        
        if valid_dates_mask.sum() > 0:
            duration_days = (df_clean.loc[valid_dates_mask, end_date_col] - 
                            df_clean.loc[valid_dates_mask, date_col]).dt.days
            # Locomotives can be immobilized for more than a year
            excessive_mask = duration_days > 1000  # ~3 years should be a more reasonable limit
            df_clean.loc[valid_dates_mask, 'excessive_duration'] = excessive_mask.fillna(False)
            logger.info(f"Found {excessive_mask.sum()} rows with excessive durations (>1000 days)")
        
        # Log statistics
        total_rows = len(df_clean)
        valid_rows = df_clean['has_valid_dates'].sum()
        invalid_start = (~df_clean['has_valid_start_date']).sum()
        invalid_end = (~df_clean['has_valid_end_date']).sum()
        
        logger.info(f"Data prepared: {total_rows} total rows")
        logger.info(f"  - {valid_rows} rows with valid dates")
        logger.info(f"  - {invalid_start} rows with invalid start dates")
        logger.info(f"  - {invalid_end} rows with invalid end dates")
        
        return df_clean
    
    def filter_by_week(self, df, week_filter):
        """Filter data by week"""
        if week_filter == 'all':
            return df
        
        try:
            week_column = 'N° Semaine Ou Reliquat'
            
            if week_column not in df.columns:
                return df
            
            if week_filter == 'RELIQUAT':
                mask = df[week_column].astype(str).str.upper() == 'RELIQUAT'
            elif week_filter.upper().startswith('S'):
                week_num = week_filter[1:]
                mask = (df[week_column].astype(str).str.upper() == week_filter.upper()) | \
                       (df[week_column].astype(str) == week_num)
            else:
                mask = df[week_column].astype(str) == str(week_filter)
            
            filtered_df = df[mask]
            logger.info(f"Week filter '{week_filter}': {len(filtered_df)} rows from {len(df)} total")
            return filtered_df
            
        except Exception as e:
            logger.warning(f"Error filtering by week {week_filter}: {str(e)}")
            return df
        
    def analyze_weekly_planning(self, df, site):
        """Analyze weekly planning - only use rows with valid dates"""
        weekly_data = defaultdict(lambda: {
            'rdv_count': 0,
            'valid_rdv_count': 0,
            'invalid_rdv_count': 0,
            'site': site,
            'equipment': set(),
            'clients': set(),
            'immobilization_days': set(),
        })
        
        date_col = 'DateTime de Début' if 'DateTime de Début' in df.columns else 'Date de Début'
        end_date_col = 'DateTime de Fin' if 'DateTime de Fin' in df.columns else 'Date de Fin'
        
        for _, row in df.iterrows():
            week_value = row.get('N° Semaine Ou Reliquat', '')
            
            # Standardize week format
            if pd.notna(week_value) and str(week_value).strip() != '':
                week_str = str(week_value).strip()
                
                if week_str.upper() == 'RELIQUAT':
                    week_key = 'RELIQUAT'
                else:
                    week_num = ''.join(filter(str.isdigit, week_str))
                    if week_num:
                        week_key = f"S{int(week_num):02d}"
                    else:
                        week_key = week_str
            else:
                week_key = 'UNDEFINED'
            
            # Count all RDV
            weekly_data[week_key]['rdv_count'] += 1
            
            # Check if dates are valid
            has_valid_dates = row.get('has_valid_dates', False)
            
            if has_valid_dates:
                weekly_data[week_key]['valid_rdv_count'] += 1
                
                # Add equipment and clients
                equipment = str(row.get('SERIE', '') or row.get('N° Matériel Roulant', '')).strip()
                if equipment:
                    weekly_data[week_key]['equipment'].add(equipment)
                
                client = str(row.get('STF', '')).strip()
                if client:
                    weekly_data[week_key]['clients'].add(client)
                
                # Track immobilization days (only for valid dates)
                start_date = row.get(date_col)
                end_date = row.get(end_date_col)
                
                if pd.notna(start_date) and pd.notna(end_date):
                    current_date = start_date.date()
                    end_day = end_date.date()
                    
                    while current_date <= end_day:
                        weekly_data[week_key]['immobilization_days'].add(current_date.isoformat())
                        current_date += timedelta(days=1)
            else:
                weekly_data[week_key]['invalid_rdv_count'] += 1
    
        # Convert to final format
        result = {}
        for week, data in weekly_data.items():
            immobilization_days = len(data['immobilization_days'])
            immobilization_hours = immobilization_days * 24
            valid_rdv_count = data['valid_rdv_count']
            
            result[week] = {
                'rdv_count': data['rdv_count'],
                'valid_rdv_count': valid_rdv_count,
                'invalid_rdv_count': data['invalid_rdv_count'],
                'site': site,
                'equipment': list(data['equipment']),
                'equipment_count': len(data['equipment']),
                'clients': list(data['clients']),
                'client_count': len(data['clients']),
                'total_hours': immobilization_hours,
                'immobilization_days': immobilization_days,
                'avg_rdv_duration_hours': round(immobilization_hours / valid_rdv_count, 1) if valid_rdv_count > 0 else 0
            }
        
        return result
    
    def calculate_rdv_hours(self, start_date, end_date, max_hours=8760):  # 365 days in hours
        """Calculate hours for a RDV (appointment) with consistent day-to-hour conversion"""
        if pd.isna(start_date) or pd.isna(end_date):
            return 24  # Default to 1 day (24h) for missing dates
        
        # Calculate days then convert to hours consistently
        try:
            # First get the days
            days = self.calculate_days_in_period(start_date, end_date)
            
            # Convert days to hours consistently (24h per day)
            hours = days * 24
            
            # Apply maximum cap
            if hours > max_hours:
                return max_hours
                
            return hours
        except:
            return 24  # Default to 1 day if calculation fails
    
    def calculate_days_in_period(self, start_date, end_date, max_days=365):
        """Calculate number of days in a period with a maximum cap"""
        if pd.isna(start_date) or pd.isna(end_date):
            return 1  # Default to 1 day for missing dates
        
        try:
            # Calculate days between dates (inclusive)
            start_day = start_date.date()
            end_day = end_date.date()
            
            days_diff = (end_day - start_day).days + 1  # +1 to include both start and end days
            
            # Handle invalid or extreme values
            if days_diff <= 0:
                return 1  # Default to 1 day for invalid ranges
            else:
                return days_diff
        except:
            return 1  # Default to 1 day if calculation fails
    
    def analyze_equipment(self, df, site):
        """Analyze equipment - only calculate for valid dates"""
        equipment_data = defaultdict(lambda: {
            'rdv_count': 0,
            'valid_rdv_count': 0,
            'invalid_rdv_count': 0,
            'operations': set(),
            'clients': set(),
            'first_rdv': None,
            'last_rdv': None,
            'immobilization_days': set()
        })
        
        date_col = 'DateTime de Début' if 'DateTime de Début' in df.columns else 'Date de Début'
        end_date_col = 'DateTime de Fin' if 'DateTime de Fin' in df.columns else 'Date de Fin'
        
        for _, row in df.iterrows():
            equipment = (str(row.get('SERIE', '')) or str(row.get('N° Matériel Roulant', ''))).strip()
            
            if equipment:
                equipment_key = f"{site}_{equipment}"
                equipment_data[equipment_key]['rdv_count'] += 1
                
                has_valid_dates = row.get('has_valid_dates', False)
                
                if has_valid_dates:
                    equipment_data[equipment_key]['valid_rdv_count'] += 1
                    
                    start_date = row.get(date_col)
                    end_date = row.get(end_date_col)
                    
                    if pd.notna(start_date) and pd.notna(end_date):
                        # Track unique days THIS locomotive is immobilized
                        current_date = start_date.date()
                        end_day = end_date.date()
                        
                        while current_date <= end_day:
                            equipment_data[equipment_key]['immobilization_days'].add(current_date.isoformat())
                            current_date += timedelta(days=1)
                        
                        # Track first and last RDV
                        if equipment_data[equipment_key]['first_rdv'] is None or start_date < equipment_data[equipment_key]['first_rdv']:
                            equipment_data[equipment_key]['first_rdv'] = start_date
                        
                        if equipment_data[equipment_key]['last_rdv'] is None or end_date > equipment_data[equipment_key]['last_rdv']:
                            equipment_data[equipment_key]['last_rdv'] = end_date
                else:
                    equipment_data[equipment_key]['invalid_rdv_count'] += 1
                
                # Always add operations and clients
                operation = str(row.get('Code Opération', ''))
                if operation:
                    equipment_data[equipment_key]['operations'].add(operation)
                
                client = str(row.get('STF', ''))
                if client:
                    equipment_data[equipment_key]['clients'].add(client)
        
        # Convert to final format
        result = {}
        for eq_key, data in equipment_data.items():
            equipment_name = eq_key.split('_', 1)[1] if '_' in eq_key else eq_key
            
            immobilization_days = len(data['immobilization_days'])
            immobilization_hours = immobilization_days * 24
            
            valid_rdv_count = max(data['valid_rdv_count'], 1)
            
            result[eq_key] = {
                'site': site,
                'equipment': equipment_name,
                'rdv_count': data['rdv_count'],
                'valid_rdv_count': data['valid_rdv_count'],
                'invalid_rdv_count': data['invalid_rdv_count'],
                'total_immobilization_days': immobilization_days,
                'total_immobilization_hours': immobilization_hours,
                'average_duration_days': round(immobilization_days / valid_rdv_count, 1) if data['valid_rdv_count'] > 0 else 0,
                'average_duration_hours': round(immobilization_hours / valid_rdv_count, 1) if data['valid_rdv_count'] > 0 else 0,
                'operations_count': len(data['operations']),
                'clients_count': len(data['clients']),
                'first_rdv': data['first_rdv'].isoformat() if data['first_rdv'] else None,
                'last_rdv': data['last_rdv'].isoformat() if data['last_rdv'] else None
            }
        
        return result
    
    def create_concatenated_data(self, df, site):
        """Create concatenated RDV data grouped by locomotive and date range"""
        
        date_col = 'DateTime de Début' if 'DateTime de Début' in df.columns else 'Date de Début'
        end_date_col = 'DateTime de Fin' if 'DateTime de Fin' in df.columns else 'Date de Fin'
        
        # Group by locomotive and overlapping date ranges
        locomotive_groups = defaultdict(list)
        
        for index, row in df.iterrows():
            client = str(row.get('STF', '')).strip()
            material_number = str(row.get('N° Matériel Roulant', '')).strip()
            
            if not material_number:
                continue
                
            start_date = row.get(date_col)
            end_date = row.get(end_date_col)
            operation = str(row.get('Code Opération', '')).strip()
            libelle = str(row.get('Libellé Intervention', '')).strip()
            acceptee_value = str(row.get('Acceptée', ''))
            
            # IMPORTANT: Preserve the week information from the original data
            week_number_raw = row.get('N° Semaine Ou Reliquat', '')
            week_number = None
            
            if pd.notna(week_number_raw) and str(week_number_raw).strip():
                week_str = str(week_number_raw).strip().upper()
                if 'RELIQUAT' in week_str:
                    week_number = 'RELIQUAT'
                else:
                    try:
                        week_num = int(week_str)
                        if 1 <= week_num <= 53:
                            week_number = week_num
                    except:
                        pass

            locomotive_groups[material_number].append({
                'index': index + 1,
                'client': client,
                'material_number': material_number,
                'start_date': start_date,
                'end_date': end_date,
                'operation': operation,
                'libelle': libelle,
                'acceptee': acceptee_value,
                'week_number': week_number,  # Add this
                'original_row': row
            })
        
        concatenated_data = []
        grouped_index = 1
        
        for material_number, operations in locomotive_groups.items():
            # Sort operations by start date
            operations.sort(key=lambda x: x['start_date'] if pd.notna(x['start_date']) else pd.Timestamp.min)
            
            # Group overlapping or consecutive operations
            grouped_operations = self._group_overlapping_operations(operations)
            
            for group in grouped_operations:
                # Find the earliest start date and latest end date in the group
                valid_start_dates = [op['start_date'] for op in group if pd.notna(op['start_date'])]
                valid_end_dates = [op['end_date'] for op in group if pd.notna(op['end_date'])]
                
                if valid_start_dates and valid_end_dates:
                    earliest_start = min(valid_start_dates)
                    latest_end = max(valid_end_dates)
                elif valid_start_dates:
                    earliest_start = min(valid_start_dates)
                    latest_end = earliest_start
                elif valid_end_dates:
                    latest_end = max(valid_end_dates)
                    earliest_start = latest_end
                else:
                    earliest_start = None
                    latest_end = None
                
                # Collect all operations, clients, and week information
                all_operations = []
                all_clients = set()
                all_acceptee_values = []
                group_week_numbers = []
                
                for op in group:
                    if op['operation']:
                        all_operations.append(op['operation'])
                    if op['client']:
                        all_clients.add(op['client'])
                    if op['acceptee'] is not None:
                        all_acceptee_values.append(op['acceptee'])
                    if op['week_number'] is not None:
                        group_week_numbers.append(op['week_number'])

                # Determine the week for this group
                group_week = None
                if group_week_numbers:
                    # If we have RELIQUAT in the group, use that
                    if 'RELIQUAT' in group_week_numbers:
                        group_week = 'RELIQUAT'
                    else:
                        # Use the most common week number
                        from collections import Counter
                        week_counts = Counter(group_week_numbers)
                        group_week = week_counts.most_common(1)[0][0]

                # Create technical and display formats
                date_debut_tech = earliest_start.strftime('%Y%m%d_%H%M') if pd.notna(earliest_start) else 'NODATE'
                date_fin_tech = latest_end.strftime('%Y%m%d_%H%M') if pd.notna(latest_end) else 'NODATE'
                
                date_debut_display = self.format_date_for_display(earliest_start)
                date_fin_display = self.format_date_for_display(latest_end)
                
                operations_summary = ', '.join(set(all_operations)) if all_operations else 'N/A'
                client_summary = ', '.join(sorted(all_clients)) if all_clients else 'N/A'
                
                concatenated_string = f"{site}_{client_summary}_{material_number}_{date_debut_tech}_{date_fin_tech}_{operations_summary}"
                concatenated_string = re.sub(r'_{2,}', '_', concatenated_string).strip('_')
                
                # Calculate days using consistent method
                days = self.calculate_days_in_period(earliest_start, latest_end)
                hours = days * 24
                
                concatenated_data.append({
                    'index': grouped_index,
                    'site': site,
                    'client': client_summary,
                    'material_number': material_number,
                    'engin': material_number,
                    'date_debut': date_debut_tech,
                    'date_fin': date_fin_tech,
                    'date_debut_display': date_debut_display,
                    'date_fin_display': date_fin_display,
                    'operation': operations_summary[:50] + '...' if len(operations_summary) > 50 else operations_summary,
                    'operations_summary': operations_summary,
                    'libelle': '; '.join([op['libelle'] for op in group if op['libelle']])[:100],
                    'concatenated': concatenated_string,
                    'duration_days': days,
                    'duration_hours': hours,
                    'operations_count': len(group),
                    'group_week': group_week,  # Add this for week information
                    'start_datetime': earliest_start if pd.notna(earliest_start) else None,
                    'end_datetime': latest_end if pd.notna(latest_end) else None,
                    'rdv_details': [
                        {
                            'operation': op['operation'],
                            'libelle': op['libelle'],
                            'start': op['start_date'].isoformat() if pd.notna(op['start_date']) else None,
                            'end': op['end_date'].isoformat() if pd.notna(op['end_date']) else None,
                            'start_display': self.format_date_for_display(op['start_date']),
                            'end_display': self.format_date_for_display(op['end_date']),
                            'acceptee': op['acceptee'],
                            'week_number': op['week_number']  # Add this
                        } for op in group
                    ]
                })
                
                grouped_index += 1
        
        return concatenated_data

    def _group_overlapping_operations(self, operations):
        """Group operations that overlap or are consecutive for the same locomotive"""
        if not operations:
            return []
        
        # Sort by start date
        operations.sort(key=lambda x: x['start_date'] if pd.notna(x['start_date']) else pd.Timestamp.min)
        
        groups = []
        current_group = [operations[0]]
        
        for i in range(1, len(operations)):
            current_op = operations[i]
            last_op_in_group = current_group[-1]
            
            # Check if operations overlap or are consecutive
            if self._operations_should_be_grouped(last_op_in_group, current_op):
                current_group.append(current_op)
            else:
                # Start a new group
                groups.append(current_group)
                current_group = [current_op]
        
        # Add the last group
        groups.append(current_group)
        
        return groups

    def _operations_should_be_grouped(self, op1, op2):
        """Determine if two operations should be grouped together"""
        # If either operation has missing dates, group them conservatively
        if (pd.isna(op1['start_date']) or pd.isna(op1['end_date']) or 
            pd.isna(op2['start_date']) or pd.isna(op2['end_date'])):
            return True
        
        # Check for overlap or if they're within 1 day of each other
        op1_end = op1['end_date'].date()
        op2_start = op2['start_date'].date()
        
        # Group if there's overlap or if they're consecutive/very close
        days_gap = (op2_start - op1_end).days
        
        # Group if:
        # 1. There's overlap (gap <= 0)
        # 2. They're consecutive or within 1 day (gap <= 1)
        return days_gap <= 1
    
    def format_date_for_display(self, date_val):
        """Format date for human-readable display in French format"""
        if pd.isna(date_val) or date_val is None:
            return 'Non défini'
        
        try:
            # Ensure we have a datetime object
            if isinstance(date_val, str):
                date_val = pd.to_datetime(date_val)
            
            # Format as DD/MM/YYYY HH:MM
            return date_val.strftime('%d/%m/%Y %H:%M')
        except:
            return 'Date invalide'
        
    def detect_conflicts(self, df, site):
        """Detect conflicts including date format issues and missing dates"""
        conflicts = []
        
        date_col = 'DateTime de Début' if 'DateTime de Début' in df.columns else 'Date de Début'
        end_date_col = 'DateTime de Fin' if 'DateTime de Fin' in df.columns else 'Date de Fin'
        
        conflict_groups = defaultdict(list)
        
        for index, row in df.iterrows():
            equipment = (str(row.get('SERIE', '')) or str(row.get('N° Matériel Roulant', ''))).strip()
            
            if not equipment:
                continue
                
            equipment_key = f"{site}_{equipment}"
            start_date = row.get(date_col)
            end_date = row.get(end_date_col)
            operation = str(row.get('Code Opération', ''))
            libelle = str(row.get('Libellé Intervention', ''))
            
            # Check for missing start date
            if pd.isna(start_date):
                group_key = f"missing_start_date_{equipment_key}"
                conflict_groups[group_key].append({
                    'type': 'missing_start_date',
                    'equipment': equipment_key,
                    'severity': 'medium',
                    'index': index + 1,
                    'description': "Date de début manquante - l'engin n'est peut-être pas encore sur site",
                    'operation': operation,
                    'libelle': libelle,
                    'original_start_date': str(row.get('Date de Début', '')),
                    'original_end_date': str(row.get('Date de Fin', ''))
                })
            
            # Check for missing end date
            if pd.isna(end_date):
                group_key = f"missing_end_date_{equipment_key}"
                conflict_groups[group_key].append({
                    'type': 'missing_end_date',
                    'equipment': equipment_key,
                    'severity': 'medium',
                    'index': index + 1,
                    'description': "Date de fin manquante - l'entretien n'est peut-être pas encore défini",
                    'operation': operation,
                    'libelle': libelle,
                    'original_start_date': str(row.get('Date de Début', '')),
                    'original_end_date': str(row.get('Date de Fin', ''))
                })
            
            # Check for date inversion (only if both dates are valid)
            if pd.notna(start_date) and pd.notna(end_date) and end_date < start_date:
                group_key = f"date_inversion_{equipment_key}"
                conflict_groups[group_key].append({
                    'type': 'date_inversion',
                    'equipment': equipment_key,
                    'severity': 'high',
                    'description': "La date de fin est antérieure à la date de début",
                    'operation': operation,
                    'libelle': libelle,
                    'rdv_info': {
                        'index': index + 1,
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                })
            
            # Check for excessive immobilization (only if both dates are valid)
            if pd.notna(start_date) and pd.notna(end_date):
                immobilization_days = (end_date - start_date).days + 1
                if immobilization_days > 1000:
                    group_key = f"excessive_immobilization_{equipment_key}"
                    conflict_groups[group_key].append({
                        'type': 'excessive_immobilization',
                        'equipment': equipment_key,
                        'severity': 'medium',
                        'days': immobilization_days,
                        'hours': immobilization_days * 24,
                        'description': f"Immobilisation excessive ({immobilization_days} jours)",
                        'operation': operation,
                        'libelle': libelle,
                        'client': str(row.get('STF', '')),
                        'rdv_info': {
                            'index': index + 1,
                            'start': start_date.isoformat(),
                            'end': end_date.isoformat()
                        }
                    })
        
        # Group similar conflicts
        for group_key, group_conflicts in conflict_groups.items():
            if len(group_conflicts) == 1:
                conflicts.append(group_conflicts[0])
            else:
                first_conflict = group_conflicts[0]
                conflicts.append({
                    'type': first_conflict['type'],
                    'equipment': first_conflict['equipment'],
                    'severity': first_conflict['severity'],
                    'description': f"{first_conflict['description']} (Répété {len(group_conflicts)} fois)",
                    'operation': first_conflict['operation'],
                    'libelle': first_conflict['libelle'],
                    'occurrence_count': len(group_conflicts),
                    'days': first_conflict.get('days', 0),
                    'hours': first_conflict.get('hours', 0),
                    'rdv_info': first_conflict.get('rdv_info'),
                    'sample_original_dates': {
                        'start': first_conflict.get('original_start_date', ''),
                        'end': first_conflict.get('original_end_date', '')
                    }
                })
        
        return sorted(conflicts, key=lambda x: (x['severity'] == 'high', x['severity'] == 'medium'), reverse=True)
    
    def calculate_summary(self, results, site):
        """Calculate summary with proper immobilization logic"""
        summary = {
            'site': site,
            'total_rdv': 0,
            'total_clients': 0,
            'total_series': 0,
            'total_hours': 0,
            'total_days_with_rdv': 0,
            'conflict_count': 0
        }
        
        # Get unique days when ANY equipment is on-site (global immobilization days)
        global_immobilization_days = set()
        
        # Process weekly planning
        all_clients = set()
        all_equipment = set()
        
        if 'weekly_planning' in results:
            weekly = results['weekly_planning']
            
            for week_data in weekly.values():
                summary['total_rdv'] += week_data.get('rdv_count', 0)
                all_clients.update(week_data.get('clients', []))
                all_equipment.update(week_data.get('equipment', []))
        
        # Process equipment analysis to get total site immobilization days
        if 'equipment_analysis' in results:
            equipment = results['equipment_analysis']
            
            # Sum individual locomotive immobilization hours
            total_locomotive_hours = 0
            
            for eq_data in equipment.values():
                # Add this locomotive's immobilization hours to total
                locomotive_hours = eq_data.get('total_immobilization_hours', 0)
                total_locomotive_hours += locomotive_hours

                eq_first_rdv = eq_data.get('first_rdv')
                eq_last_rdv = eq_data.get('last_rdv')
                
                if eq_first_rdv and eq_last_rdv:
                    try:
                        start_date = datetime.fromisoformat(eq_first_rdv).date()
                        end_date = datetime.fromisoformat(eq_last_rdv).date()
                        
                        current_date = start_date
                        while current_date <= end_date:
                            global_immobilization_days.add(current_date.isoformat())
                            current_date += timedelta(days=1)
                    except:
                        pass
            
            summary['total_hours'] = round(total_locomotive_hours, 2)
        
        # Process concatenated data if needed
        if 'concatenated_data' in results and summary['total_rdv'] == 0:
            summary['total_rdv'] = len(results['concatenated_data'])
        
        # Count conflicts
        if 'conflicts' in results:
            summary['conflict_count'] = len(results['conflicts'])
        
        # Set final values
        summary['total_clients'] = len(all_clients)
        summary['total_series'] = len(all_equipment)
        summary['total_days_with_rdv'] = len(global_immobilization_days)  # Days when site had ANY locomotive
        
        return summary