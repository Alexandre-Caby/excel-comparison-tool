import os
import tempfile
import pandas as pd
import xlsxwriter
from time import time
from datetime import datetime, date, time as dt_time
import re
from io import BytesIO
from reportlab.lib.utils import ImageReader

# Import for the pdf generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER

class ReportGenerator:
    """Generates reports in various formats."""
    
    @staticmethod
    def generate_excel_report_temp(report_data, session_data, temp_dir):
        """Generate an enhanced Excel report using temporary file"""
        comparison_mode = report_data.get("comparison_mode", "full")
        
        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.xlsx', dir=temp_dir)
        os.close(temp_fd)
        
        try:
            with xlsxwriter.Workbook(temp_path) as workbook:
                # Enhanced formatting
                title_format = workbook.add_format({
                    'bold': True,
                    'font_size': 18,
                    'align': 'center',
                    'valign': 'vcenter',
                    'bg_color': '#007147',
                    'font_color': 'white',
                    'border': 2
                })
                
                header_format = workbook.add_format({
                    'bold': True,
                    'font_size': 12,
                    'bg_color': '#4CA27E',
                    'font_color': 'white',
                    'border': 1,
                    'align': 'center'
                })
                
                info_label_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#E8F5E8',
                    'border': 1
                })
                
                info_value_format = workbook.add_format({
                    'border': 1,
                    'text_wrap': True
                })
                
                # Status-specific formatting
                added_format = workbook.add_format({
                    'bg_color': '#E8F5E8',
                    'border': 1
                })
                
                removed_format = workbook.add_format({
                    'bg_color': '#FFEBEE',
                    'border': 1
                })
                
                modified_format = workbook.add_format({
                    'bg_color': '#FFF8E1',
                    'border': 1
                })

                similar_format = workbook.add_format({
                    'bg_color': '#E1F5FE',
                    'border': 1
                })

                summary_ws = workbook.add_worksheet("📊 Résumé Exécutif")
                
                # Title
                summary_ws.merge_range('A1:H1', 'RAPPORT DE COMPARAISON EXCEL', title_format)
                summary_ws.set_row(0, 25)
                
                # Report information section
                summary_ws.write('A3', 'INFORMATIONS GÉNÉRALES', header_format)
                summary_ws.merge_range('B3:H3', '', header_format)
                
                report_info = [
                    ('📋 Rapport ID:', report_data["id"]),
                    ('📅 Date de génération:', report_data["date"]),
                    ('📁 Fichier de référence:', report_data["base_file"]),
                    ('📁 Fichier(s) comparé(s):', report_data["comparison_file"]),
                    ('⚠️ Total des différences:', str(report_data["differences"])),
                    ('🔄 Doublons identifiés:', str(report_data.get("duplicates", 0))),
                    ('📊 Niveau de correspondance:', report_data["match_rate"])
                ]
                
                for i, (label, value) in enumerate(report_info, start=4):
                    summary_ws.write(f'A{i}', label, info_label_format)
                    summary_ws.write(f'B{i}', value, info_value_format)
                
                # Statistics section
                if session_data and session_data.get('comparison_results'):
                    results = session_data['comparison_results']['results']
                    summary = session_data['comparison_results']['summary']
                    
                    # Calculate category counts
                    added_count = removed_count = modified_count = 0
                    for sheet_name, sheet_results in results.items():
                        for result in sheet_results:
                            diffs = result.get('differences', [])
                            if diffs:
                                added_count += sum(1 for d in diffs if d.get('Status') == 'Ajoutée')
                                removed_count += sum(1 for d in diffs if d.get('Status') == 'Supprimée')
                                modified_count += sum(1 for d in diffs if d.get('Status') == 'Modifiée')
                    
                    # Add statistics section
                    summary_ws.write('A12', 'STATISTIQUES DÉTAILLÉES', header_format)
                    summary_ws.merge_range('B12:H12', '', header_format)
                    
                    stats_info = [
                        ('📊 Feuilles comparées:', str(summary.get('total_sheets_compared', 0))),
                        ('➕ Entrées ajoutées:', str(added_count)),
                        ('➖ Entrées supprimées:', str(removed_count)),
                        ('✏️ Entrées modifiées:', str(modified_count)),
                        ('🔍 Cellules analysées:', f"{summary.get('total_cells_compared', 0):,}".replace(',', ' ')),
                        ('⏱️ Temps d\'exécution:', f"{summary.get('execution_time_seconds', 0):.2f} secondes")
                    ]
                    
                    for i, (label, value) in enumerate(stats_info, start=13):
                        summary_ws.write(f'A{i}', label, info_label_format)
                        summary_ws.write(f'B{i}', value, info_value_format)
                
                # Set column widths
                summary_ws.set_column('A:A', 25)
                summary_ws.set_column('B:B', 50)
                summary_ws.set_column('C:H', 15)

                comparison_results = session_data.get('comparison_results', {}).get('results', {})
                
                for sheet_name, sheet_results in comparison_results.items():
                    safe_sheet_name = sheet_name.replace('/', '_').replace('\\', '_')[:20]
                    
                    for result_idx, result in enumerate(sheet_results):
                        diffs = result.get('differences', [])
                        columns = result.get('differences_columns', [])
                        
                        # Create differences worksheet with enhanced formatting
                        if comparison_mode in ['full', 'differences-only'] and diffs and columns:
                            ws_name = f"🔍 {safe_sheet_name}_{result_idx+1}"[:31]
                            
                            try:
                                diff_ws = workbook.add_worksheet(ws_name)
                                
                                # Add title and summary
                                diff_ws.merge_range('A1:H1', f'DIFFÉRENCES - {sheet_name}', title_format)
                                diff_ws.set_row(0, 20)
                                
                                # Add summary stats
                                comp_filename = result.get('comparison_file', f'Fichier {result_idx+1}')
                                diff_ws.write('A3', f'Comparaison avec: {comp_filename}', info_label_format)
                                diff_ws.write('A4', f'Total des différences: {len(diffs)}', info_label_format)
                                
                                # Group differences by status for better organization
                                added = [d for d in diffs if d.get('Status') == 'Ajoutée']
                                removed = [d for d in diffs if d.get('Status') == 'Supprimée']
                                modified = [d for d in diffs if d.get('Status') == 'Modifiée']
                                similar = [d for d in diffs if d.get('Status') == 'Similaire']
                                
                                diff_ws.write('B3', f'➕ Ajoutées: {len(added)}', added_format)
                                diff_ws.write('C3', f'➖ Supprimées: {len(removed)}', removed_format)
                                diff_ws.write('D3', f'✏️ Modifiées: {len(modified)}', modified_format)
                                diff_ws.write('E3', f'≈ Similaires: {len(similar)}', similar_format)
                                
                                # Filter and reorder columns based on content
                                filtered_columns = ReportGenerator.filter_relevant_columns(columns, diffs)

                                # Write headers
                                for col_idx, col in enumerate(filtered_columns):
                                    diff_ws.write(5, col_idx, str(col), header_format)
                                
                                # Write data with status-based formatting and enhanced similarity handling
                                for row_idx, row in enumerate(diffs, start=6):                                    
                                    # Extract and add week number directly from dates - enhanced version
                                    if 'Semaine' not in row or not row.get('Semaine'):
                                        # Try multiple approaches to get week number
                                        week_number = None
                                        
                                        # Method 1: Direct date fields
                                        date_fields = ['Date programmation', 'Date sortie', 'Date Butee', 'Comparison Value', 'Base Value']
                                        for date_field in date_fields:
                                            if date_field in row and row[date_field]:
                                                date_str = str(row[date_field])
                                                if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                                                    try:
                                                        dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
                                                        week_number = str(dt.isocalendar()[1])
                                                        break
                                                    except Exception as e:
                                                        pass

                                        # Method 2: Extract from key pattern for similarities
                                        if not week_number:
                                            key = str(row.get('Key', ''))
                                            if key:
                                                # Try to extract dates from the key parts
                                                key_parts = key.split(' ≈ ')
                                                for part in key_parts:
                                                    # Look for date patterns in the key
                                                    if '2025-' in part or '2024-' in part:
                                                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', part)
                                                        if date_match:
                                                            try:
                                                                dt = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                                                                week_number = str(dt.isocalendar()[1])
                                                                break
                                                            except:
                                                                pass
                                        
                                        # Method 3: Check if there are nested values
                                        if not week_number:
                                            # Sometimes the values are nested in Base Value or Comparison Value
                                            for field in ['Base Value', 'Comparison Value']:
                                                if field in row:
                                                    value = row[field]
                                                    if isinstance(value, dict):
                                                        # If it's a dict, check for date fields
                                                        for sub_field in value:
                                                            if 'date' in sub_field.lower():
                                                                date_str = str(value[sub_field])
                                                                if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                                                                    try:
                                                                        dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
                                                                        week_number = str(dt.isocalendar()[1])
                                                                        break
                                                                    except:
                                                                        pass
                                                    elif isinstance(value, str) and re.match(r'\d{4}-\d{2}-\d{2}', value):
                                                        try:
                                                            dt = datetime.strptime(value[:10], '%Y-%m-%d')
                                                            week_number = str(dt.isocalendar()[1])
                                                            break
                                                        except:
                                                            pass
                                        
                                        if week_number:
                                            row['Semaine'] = week_number
                                        else:
                                            pass

                                    # Choose format based on status
                                    row_format = info_value_format
                                    status = row.get('Status', '')
                                    
                                    if status == 'Ajoutée':
                                        row_format = added_format
                                    elif status == 'Supprimée':
                                        row_format = removed_format
                                    elif status == 'Modifiée':
                                        row_format = modified_format
                                    elif status == 'Similaire':
                                        row_format = similar_format
                                    
                                    for col_idx, col in enumerate(filtered_columns):
                                        value = row.get(col, "")
                                        if pd.isna(value) or value is None:
                                            value = ""
                                        
                                        # Special handling for similarity values
                                        if col == 'Similarity' and value:
                                            value = f"{value}"
                                        
                                        diff_ws.write(row_idx, col_idx, str(value), row_format)
                                
                                # Auto-adjust column widths
                                for col_idx, col in enumerate(filtered_columns):
                                    if col == 'Key':
                                        diff_ws.set_column(col_idx, col_idx, 25)
                                    elif col in ['Base Value', 'Comparison Value']:
                                        diff_ws.set_column(col_idx, col_idx, 20)
                                    elif col == 'Semaine':
                                        diff_ws.set_column(col_idx, col_idx, 10)
                                    elif col == 'Similarity':
                                        diff_ws.set_column(col_idx, col_idx, 15)
                                    elif col in ['Base Row', 'Comp Row']:
                                        diff_ws.set_column(col_idx, col_idx, 12)
                                    else:
                                        diff_ws.set_column(col_idx, col_idx, 18)
                                    
                            except Exception as e:
                                print(f"Erreur lors de la création de la feuille {ws_name}: {e}")
                        
                        # Enhanced duplicates worksheet
                        duplicates = []
                        dup_columns = []
                        if result.get('duplicates_base') and len(result.get('duplicates_base', [])) > 0:
                            duplicates.extend(result['duplicates_base'])
                            dup_columns = result.get('duplicates_base_columns', [])
                        if result.get('duplicates_comp') and len(result.get('duplicates_comp', [])) > 0:
                            duplicates.extend(result['duplicates_comp'])
                            if not dup_columns and result.get('duplicates_comp_columns'):
                                dup_columns = result['duplicates_comp_columns']
                        
                        if comparison_mode == 'full' and duplicates and dup_columns:
                            # Filter out empty duplicates
                            valid_duplicates = []
                            for dup in duplicates:
                                # Check if duplicate has any non-empty, non-NAT values
                                has_valid_data = False
                                for key, value in dup.items():
                                    if (value and not pd.isna(value) and 
                                        str(value).lower() not in ['nat', 'nan', 'none', '']):
                                        has_valid_data = True
                                        break
                                
                                if has_valid_data:
                                    valid_duplicates.append(dup)
                            
                            if valid_duplicates:
                                ws_name = f"🔄 Doublons_{safe_sheet_name}_{result_idx+1}"[:31]
                                
                                try:
                                    dup_ws = workbook.add_worksheet(ws_name)
                                    
                                    # Add title
                                    dup_ws.merge_range('A1:H1', f'DOUBLONS - {sheet_name}', title_format)
                                    dup_ws.set_row(0, 20)
                                    
                                    # Add summary
                                    dup_ws.write('A3', f'Total des doublons: {len(valid_duplicates)}', info_label_format)
                                    
                                    # Use all available columns, but prioritize important ones
                                    important_cols = ['key', 'Site', 'Serie', 'Locomotive', 'Base Row', 'Comp Row']
                                    other_cols = [col for col in dup_columns if col not in important_cols]
                                    filtered_dup_columns = [col for col in important_cols if col in dup_columns] + other_cols
                                    
                                    # Add week column if we can extract it
                                    if 'Semaine' not in filtered_dup_columns:
                                        filtered_dup_columns.insert(1, 'Semaine')  # Add after key
                                    
                                    # Write headers
                                    for col_idx, col in enumerate(filtered_dup_columns):
                                        dup_ws.write(4, col_idx, str(col), header_format)

                                    # Write data
                                    for row_idx, row in enumerate(valid_duplicates, start=5):
                                        # Pre-process row to add week number
                                        if 'Semaine' not in row or not row.get('Semaine'):
                                            week_number = ReportGenerator.extract_week_number(row)
                                            if week_number:
                                                row['Semaine'] = week_number
                                        
                                        for col_idx, col in enumerate(filtered_dup_columns):
                                            value = row.get(col, "")
                                            
                                            # Clean up NAT values
                                            if pd.isna(value) or value is None or str(value).lower() in ['nat', 'nan', 'none']:
                                                value = ""
                                            
                                            # Special handling for key column
                                            if col == 'key' and not value:
                                                # Try to construct key from available data
                                                site = row.get('Site', '')
                                                serie = row.get('Serie', '')
                                                loco = row.get('Locomotive', '')
                                                if site and serie and loco:
                                                    value = f"{site}_{serie}_{loco}"
                                            
                                            dup_ws.write(row_idx, col_idx, str(value), info_value_format)
                                
                                except Exception as e:
                                    print(f"Erreur lors de la création de la feuille doublons {ws_name}: {e}")
                            else:
                                pass

            return temp_path
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e

    @staticmethod
    def generate_csv_report_temp(report_data, session_data, temp_dir):
        """Generate a simple CSV report with classic format"""
        
        temp_fd, temp_path = tempfile.mkstemp(suffix='.csv', dir=temp_dir)
        
        try:
            with os.fdopen(temp_fd, 'w', newline='', encoding='utf-8-sig') as temp_file:
                import csv
                writer = csv.writer(temp_file, delimiter=';')
                
                # Write enhanced header row
                writer.writerow(['Feuille', 'Fichier', 'Ligne', 'Statut', 'Key', 'Column', 'Base Value', 'Comparison Value', 'Semaine', 'Similarity'])
                
                if session_data and session_data.get('comparison_results'):
                    results = session_data['comparison_results']['results']
                    
                    for sheet_name, sheet_results in results.items():
                        for result_idx, result in enumerate(sheet_results):
                            diffs = result.get('differences', [])
                            
                            if diffs:
                                comp_filename = result.get('comparison_file', f'Fichier {result_idx+1}')
                                
                                # Limit to 100 rows per sheet
                                max_rows_per_sheet = 100
                                rows_written = 0
                                
                                for diff in diffs:
                                    if rows_written >= max_rows_per_sheet:
                                        break
                                    
                                    # Extract the key fields
                                    key = diff.get('Key', '')
                                    status = diff.get('Status', '')
                                    column = diff.get('Column', '')
                                    base_value = diff.get('Base Value', '')
                                    comp_value = diff.get('Comparison Value', '')
                                    similarity = diff.get('Similarity', '')
                                    
                                    # Extract week number
                                    week_number = ReportGenerator.extract_week_number(diff)
                                    
                                    # If week number not found, try to extract from the key or values
                                    if not week_number:
                                        # Try to get week from any date in the row
                                        for field in ['Base Value', 'Comparison Value']:
                                            date_str = str(diff.get(field, ''))
                                            if date_str and re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                                                try:
                                                    from datetime import datetime
                                                    dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
                                                    week_number = str(dt.isocalendar()[1])
                                                    break
                                                except:
                                                    pass
                                    
                                    # Clean up values
                                    if pd.isna(base_value) or base_value is None:
                                        base_value = ""
                                    if pd.isna(comp_value) or comp_value is None:
                                        comp_value = ""
                                    if pd.isna(similarity) or similarity is None:
                                        similarity = ""
                                    
                                    # Only include similarity for similar entries
                                    if status != 'Similaire':
                                        similarity = ""
                                    
                                    row_data = [
                                        sheet_name,
                                        comp_filename,
                                        diff.get('Base Row', rows_written + 1),  # Use actual row number
                                        status,
                                        key,
                                        column,
                                        base_value,
                                        comp_value,
                                        week_number or "",
                                        similarity
                                    ]
                                    
                                    writer.writerow(row_data)
                                    rows_written += 1

            return temp_path
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
    
    @staticmethod
    def generate_pdf_report_temp(report_data, session_data, temp_dir):
        """Generate a PDF report using temporary file"""
        comparison_mode = report_data.get("comparison_mode", "full")
        
        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', dir=temp_dir)
        os.close(temp_fd)
        
        try:
            def add_watermark(cnv, doc):
                cnv.saveState()
                cnv.setFillColor(colors.lightgrey)
                cnv.setFillAlpha(0.3)
                cnv.setFont("Helvetica-Bold", 60)
                width, height = A4
                cnv.translate(width / 2, height / 2)
                cnv.rotate(45)
                text = "CONFIDENTIEL - Technis"
                text_width = cnv.stringWidth(text, "Helvetica-Bold", 60)
                cnv.drawString(-text_width/2, 0, text)
                cnv.restoreState()

            doc = SimpleDocTemplate(
                temp_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=50,
            )

            elements = []
            styles = getSampleStyleSheet()
            
            # Enhanced styles for better readability
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=22,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#007147')
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor('#4CA27E')
            )
            
            subheading_style = ParagraphStyle(
                'CustomSubheading',
                parent=styles['Heading3'],
                fontSize=14,
                spaceAfter=10,
                textColor=colors.HexColor('#4C7E7E')
            )

            # Executive summary section
            elements.append(Paragraph("Rapport de Comparaison Excel", title_style))
            elements.append(Spacer(1, 12))

            info_data = [
                ['Rapport Référence:', report_data["id"]],
                ['Date de génération:', report_data["date"]],
                ['Fichier de référence:', report_data["base_file"]],
                ['Fichier(s) comparé(s):', report_data["comparison_file"]],
                ['Total des différences:', str(report_data["differences"])],
                ['Doublons identifiés:', str(report_data.get("duplicates", 0))],
                ['Niveau de correspondance:', report_data["match_rate"]]
            ]
            
            # Create a visually appealing info table
            info_table = Table(info_data, colWidths=[2.5*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#007147')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F5F5F5')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 20))
            
            # Add executive summary with key findings
            elements.append(Paragraph("Résumé Exécutif", heading_style))
            
            # Calculate match percentage for summary
            match_rate = report_data["match_rate"].replace('%', '')
            try:
                match_percent = float(match_rate)
                if match_percent > 95:
                    match_quality = "très bonne"
                elif match_percent > 85:
                    match_quality = "bonne"
                elif match_percent > 70:
                    match_quality = "acceptable"
                else:
                    match_quality = "faible"
            except ValueError:
                match_quality = "indéterminée"
            
            # Key findings summary paragraph
            elements.append(Paragraph(f"Cette comparaison montre une <b>{match_quality}</b> correspondance ({report_data['match_rate']}) entre les fichiers.", styles["Normal"]))
            elements.append(Paragraph(f"{report_data['differences']} différences ont été identifiées entre le fichier de référence et le(s) fichier(s) comparé(s).", styles["Normal"]))
            elements.append(Paragraph(f"{report_data.get('duplicates', 0)} doublons ont également été identifiés.", styles["Normal"]))
            
            elements.append(Spacer(1, 8))
            elements.append(Paragraph("Les principales catégories de différences sont :", styles["Normal"]))
            
            # Create bullet points as separate paragraphs with proper indentation
            bullet_style = ParagraphStyle(
                'BulletStyle',
                parent=styles['Normal'],
                leftIndent=20,
                firstLineIndent=0,
                spaceBefore=2,
                bulletIndent=0,
                bulletFontName='Helvetica',
                bulletFontSize=10
            )
            
            added_count = 0
            removed_count = 0
            modified_count = 0
            
            # Extract counts from the actual comparison results
            if session_data and session_data.get('comparison_results'):
                results = session_data['comparison_results']['results']
                
                for sheet_name, sheet_results in results.items():
                    for result in sheet_results:
                        diffs = result.get('differences', [])
                        if diffs:
                            # Count by status from the actual difference records
                            added_count += sum(1 for d in diffs if d.get('Status') == 'Ajoutée')
                            removed_count += sum(1 for d in diffs if d.get('Status') == 'Supprimée')
                            modified_count += sum(1 for d in diffs if d.get('Status') == 'Modifiée')
            
            # Add bullet points individually with proper bullet character
            elements.append(Paragraph(f"• Entrées ajoutées : {added_count}", bullet_style))
            elements.append(Paragraph(f"• Entrées supprimées : {removed_count}", bullet_style))
            elements.append(Paragraph(f"• Entrées modifiées : {modified_count}", bullet_style))
            
            elements.append(Spacer(1, 15))
            
            def format_cell_value(value):
                """Format cell values for better readability"""
                if value is None or value == '':
                    return '-'

                if isinstance(value, str):
                    # Check if value looks like a date
                    if re.match(r'\d{4}-\d{2}-\d{2}', value):
                        try:
                            dt = datetime.strptime(value[:10], '%Y-%m-%d')
                            return dt.strftime('%d/%m/%Y')
                        except:
                            pass
                return str(value)
                
            def add_difference_table(elements, diffs, diff_type):
                """Add a formatted table for a specific type of difference"""
                # Limit to reasonable number per page
                max_rows = min(10, len(diffs))

                if diff_type == 'modified':
                    headers = ['Clé', 'Champ', 'Valeur d\'origine', 'Nouvelle valeur', 'Semaine']
                    data = []
                    for d in diffs[:max_rows]:
                        # Extract week number for each row
                        week_number = ReportGenerator.extract_week_number(d)
                        if not week_number:
                            # Try to get from the row data if it has a Semaine key
                            week_number = d.get('Semaine', '')
                        
                        data.append([
                            d.get('Key', ''), 
                            d.get('Column', ''), 
                            format_cell_value(d.get('Base Value', '')),
                            format_cell_value(d.get('Comparison Value', '')),
                            week_number or ''
                        ])
                        
                elif diff_type == 'similar':
                    headers = ['Clé', 'Similarité', 'Semaine']
                    data = []
                    for d in diffs[:max_rows]:
                        key = d.get('Key', '')
                        similarity = d.get('Similarity', '')
                        
                        # Extract week number for each row
                        week_number = ''
                        # Try to get from date fields
                        for date_field in ['Date programmation', 'Date sortie', 'Date Butee', 'Comparison Value', 'Base Value']:
                            if date_field in d and d[date_field]:
                                date_str = str(d[date_field])
                                if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                                    try:
                                        dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
                                        week_number = str(dt.isocalendar()[1])
                                        break
                                    except:
                                        pass

                        if ' ≈ ' in key:
                            parts = key.split(' ≈ ')
                            if len(parts) == 2:
                                key_display = f"{parts[0][:10]}... ≈ {parts[1][:10]}..."
                            else:
                                key_display = key[:20] + "..." if len(key) > 20 else key
                        else:
                            key_display = key[:20] + "..." if len(key) > 20 else key
                        
                        data.append([key_display, similarity, week_number or ''])
                        
                else:
                    headers = ['Clé', 'Semaine', 'Ligne Base', 'Ligne Comp', 'Informations']
                    data = []
                    for d in diffs[:max_rows]:
                        key = d.get('Key', '')
                        base_row = d.get('Base Row', '')
                        comp_row = d.get('Comp Row', '')
                        
                        # Extract week number for each row
                        week_number = ReportGenerator.extract_week_number(d)
                        if not week_number:
                            # Try to get from the row data if it has a Semaine key
                            week_number = d.get('Semaine', '')
                        
                        # Truncate long keys
                        key_display = key[:30] + "..." if len(key) > 30 else key
                        
                        info = f"Statut: {d.get('Status', '')}"
                        
                        data.append([key_display, week_number or '', base_row, comp_row, info])
                
                # Add headers row
                table_data = [headers] + data
                
                # Create table with styling based on difference type
                bg_color = colors.HexColor('#E8F5E8')  # default green
                if diff_type == 'removed':
                    bg_color = colors.HexColor('#FFEBEE')  # light red
                elif diff_type == 'modified':
                    bg_color = colors.HexColor('#FFF8E1')  # light amber
                elif diff_type == 'similar':
                    bg_color = colors.HexColor('#E3F2FD')  # light blue
                
                # Adjust column widths based on content type
                if diff_type == 'similar':
                    col_widths = [2.5*inch, 0.8*inch, 0.7*inch, 3*inch]  # Key, Similarity, Week, Details
                elif diff_type == 'modified':
                    col_widths = [2*inch, 1.5*inch, 1.5*inch, 1.5*inch, 0.5*inch]  # Key, Field, Base, Comp, Week
                else:
                    col_widths = [2.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 1.4*inch]  # Key, Week, Base Row, Comp Row, Info
                
                t = Table(table_data, colWidths=col_widths, repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CA27E')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('BACKGROUND', (0, 1), (-1, -1), bg_color),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                # Special formatting for similar entries
                if diff_type == 'similar':
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E3F2FD')),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1565C0')),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))
                
                elements.append(t)
                
                # If there are more differences than shown in the table
                if len(diffs) > max_rows:
                    elements.append(Paragraph(f"... et {len(diffs) - max_rows} autres entrées", styles["Italic"]))
                
                elements.append(Spacer(1, 10))
            
            # Add visual summary if we have enough data points
            if session_data and session_data.get('comparison_results'):
                results = session_data['comparison_results']['results']
                summary = session_data['comparison_results']['summary']

                elements.append(Paragraph("Détails de la Comparaison", heading_style))
                
                # Enhanced summary table with better formatting
                summary_data = [
                    ['Métrique', 'Valeur'],
                    ['Feuilles comparées', str(summary.get('total_sheets_compared', 0))],
                    ['Différences trouvées', str(summary.get('total_differences', 0))],
                    ['Doublons identifiés', str(summary.get('total_duplicates', 0))],
                    ['Cellules analysées', f"{summary.get('total_cells_compared', 0):,}".replace(',', ' ')],
                    ['Temps d\'exécution', f"{summary.get('execution_time_seconds', 0):.2f} secondes"]
                ]
                
                summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#4CA27E')),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#E8F5F8')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(summary_table)
                elements.append(Spacer(1, 20))
                
                # Process detailed results with better presentation
                page_width = A4[0] - doc.leftMargin - doc.rightMargin
                
                for sheet_name, sheet_results in results.items():
                    if not sheet_results:
                        continue
                        
                    elements.append(Paragraph(f"Feuille: {sheet_name}", heading_style))
                    
                    for result_idx, result in enumerate(sheet_results):
                        comp_filename = result.get('comparison_file', f'Fichier {result_idx+1}')
                        elements.append(Paragraph(f"Comparaison avec: {comp_filename}", subheading_style))
                        elements.append(Spacer(1, 6))
                        
                        # Show file comparison summary
                        file_summary = [
                            ['', 'Fichier référence', 'Fichier comparé'],
                            ['Nombre de lignes', str(result.get('base_rows', 0)), str(result.get('comp_rows', 0))]
                        ]
                        
                        file_table = Table(file_summary, colWidths=[1.5*inch, 2*inch, 2*inch])
                        file_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CA27E')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))
                        elements.append(file_table)
                        elements.append(Spacer(1, 10))
                        
                        # Group differences by status
                        diffs = result.get('differences', [])
                        
                        if diffs:
                            # Group differences by status for easier understanding
                            added = [d for d in diffs if d.get('Status') == 'Ajoutée']
                            removed = [d for d in diffs if d.get('Status') == 'Supprimée']
                            modified = [d for d in diffs if d.get('Status') == 'Modifiée']
                            similar = [d for d in diffs if d.get('Status') == 'Similaire']
                            
                            if added:
                                elements.append(Paragraph(f"Entrées ajoutées ({len(added)})", subheading_style))
                                add_difference_table(elements, added, 'added')
                            
                            if removed:
                                elements.append(Paragraph(f"Entrées supprimées ({len(removed)})", subheading_style))
                                add_difference_table(elements, removed, 'removed')
                            
                            if modified:
                                elements.append(Paragraph(f"Entrées modifiées ({len(modified)})", subheading_style))
                                add_difference_table(elements, modified, 'modified')
                            
                            if similar:
                                elements.append(Paragraph(f"Entrées similaires ({len(similar)})", subheading_style))
                                
                                # Simplified table with fewer columns
                                headers = ['Clé', 'Similarité', 'Semaine']
                                data = []
                                
                                # Process at most 10 rows
                                for d in similar[:10]:
                                    key = d.get('Key', '')
                                    similarity = d.get('Similarity', '')

                                    week = ''
                                    # Try the extract_week_number function first
                                    week = ReportGenerator.extract_week_number(d)
                                    
                                    # If still no week, try manual extraction from key
                                    if not week and key:
                                        # For similarity keys, try to extract dates from key parts
                                        if ' ≈ ' in key:
                                            key_parts = key.split(' ≈ ')
                                            for part in key_parts:
                                                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', part)
                                                if date_match:
                                                    try:
                                                        dt = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                                                        week = str(dt.isocalendar()[1])
                                                        break
                                                    except:
                                                        pass
                                    
                                    # Keep key formatting simpler
                                    key_display = key[:30]
                                    if len(key) > 30:
                                        key_display = key[:30] + "..."
                                    
                                    data.append([key_display, similarity, week or ''])                               
                                # Create the table with simpler structure
                                table_data = [headers] + data
                                
                                # Use wider columns for better readability
                                t = Table(table_data, colWidths=[4*inch, 1*inch, 0.8*inch])
                                t.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E3F2FD')),
                                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1565C0')),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))
                                
                                elements.append(t)
                                
                                if len(similar) > 10:
                                    elements.append(Paragraph(f"... et {len(similar) - 10} autres entrées", styles["Italic"]))
                                
                                elements.append(Spacer(1, 10))
                        
                        elements.append(Spacer(1, 10))
                        elements.append(PageBreak())

            # Footer
            elements.append(Spacer(1, 5))
            footer_text = f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')} | Excel Comparison Tool"
            elements.append(Paragraph(footer_text, styles['Normal']))

            # Build PDF
            doc.build(
                elements,
                onFirstPage=add_watermark,
                onLaterPages=add_watermark
            )
            
            return temp_path
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
    
    @staticmethod
    def filter_relevant_columns(columns, diffs):
        """Filter columns to show only relevant ones for differences"""
        # Always include these core columns
        core_columns = ['Key', 'Status', 'Column', 'Base Value', 'Comparison Value', 'Base Row', 'Comp Row']
        
        # Add week column if we can extract week data
        has_week_data = any(ReportGenerator.extract_week_number(diff) for diff in diffs)
        if has_week_data:
            core_columns.append('Semaine')
        
        # Add similarity column only for similar entries
        has_similarities = any(diff.get('Status') == 'Similaire' for diff in diffs)
        if has_similarities:
            core_columns.append('Similarity')
        
        # Filter to only include columns that exist in the data
        available_columns = [col for col in core_columns if col in columns]
        
        # Remove only irrelevant columns
        irrelevant_columns = ['Method', 'Confidence']
        filtered_columns = [col for col in available_columns if col not in irrelevant_columns]
        
        return filtered_columns
    
    @staticmethod
    def filter_duplicate_columns(columns):
        """Filter columns for duplicates display"""
        irrelevant_columns = []
        filtered_columns = [col for col in columns if col not in irrelevant_columns]
        
        # Reorder to put key and week first
        ordered_columns = []
        if 'key' in filtered_columns:
            ordered_columns.append('key')
        if 'Semaine de programmation' in filtered_columns:
            ordered_columns.append('Semaine de programmation')
        if 'Base Row' in filtered_columns:
            ordered_columns.append('Base Row')
        if 'Comp Row' in filtered_columns:
            ordered_columns.append('Comp Row')
        
        # Add remaining columns
        for col in filtered_columns:
            if col not in ordered_columns:
                ordered_columns.append(col)
        
        return ordered_columns
    
    @staticmethod
    def clean_duplicate_data(duplicates):
        """Clean duplicate data and add week numbers"""
        cleaned = []
        
        for duplicate in duplicates:
            cleaned_row = {}
            
            # Clean each field
            for key, value in duplicate.items():
                if pd.isna(value) or str(value).lower() in ['nat', 'nan', 'none']:
                    cleaned_row[key] = ""
                else:
                    cleaned_row[key] = str(value)
            
            # Extract week number from key or semaine column
            week_number = ReportGenerator.extract_week_number(duplicate)
            if week_number:
                cleaned_row['Semaine'] = week_number
            
            cleaned.append(cleaned_row)
        
        return cleaned
    
    @staticmethod
    def extract_week_number(row):
        """Extract week number from row data"""
        # First check if we already have a week number
        if row.get('Semaine'):
            return str(row['Semaine'])
        
        # Method 1: Check all fields for date patterns
        for field_name, field_value in row.items():
            if not field_value or pd.isna(field_value):
                continue
                
            # Check if field contains date
            if 'date' in field_name.lower() or field_name in ['Base Value', 'Comparison Value']:
                date_str = str(field_value)
                
                # Handle nested data (if field_value is a dict)
                if isinstance(field_value, dict):
                    for sub_field, sub_value in field_value.items():
                        if 'date' in sub_field.lower():
                            date_str = str(sub_value)
                            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                                try:
                                    dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
                                    week_num = str(dt.isocalendar()[1])
                                    return week_num
                                except:
                                    pass
                
                # Check direct date string
                if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                    try:
                        dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
                        week_num = str(dt.isocalendar()[1])
                        return week_num
                    except:
                        pass
        
        # Method 2: Extract from key for similarities
        key = str(row.get('Key', ''))
        if key and '≈' in key:
            # For similarity keys, try to extract from both parts
            key_parts = key.split(' ≈ ')
            for part in key_parts:
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', part)
                if date_match:
                    try:
                        dt = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                        week_num = str(dt.isocalendar()[1])
                        return week_num
                    except:
                        pass
        return None