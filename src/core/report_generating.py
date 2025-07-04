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
                                diff_ws.merge_range('A1:F1', f'DIFFÉRENCES - {sheet_name}', title_format)
                                diff_ws.set_row(0, 20)
                                
                                # Add summary stats
                                comp_filename = result.get('comparison_file', f'Fichier {result_idx+1}')
                                diff_ws.write('A3', f'Comparaison avec: {comp_filename}', info_label_format)
                                diff_ws.write('A4', f'Total des différences: {len(diffs)}', info_label_format)
                                
                                # Group differences by status for better organization
                                added = [d for d in diffs if d.get('Status') == 'Ajoutée']
                                removed = [d for d in diffs if d.get('Status') == 'Supprimée']
                                modified = [d for d in diffs if d.get('Status') == 'Modifiée']
                                
                                diff_ws.write('B3', f'➕ Ajoutées: {len(added)}', added_format)
                                diff_ws.write('C3', f'➖ Supprimées: {len(removed)}', removed_format)
                                diff_ws.write('D3', f'✏️ Modifiées: {len(modified)}', modified_format)
                                
                                # Write headers
                                for col_idx, col in enumerate(columns):
                                    diff_ws.write(5, col_idx, str(col), header_format)
                                
                                # Write data with status-based formatting
                                for row_idx, row in enumerate(diffs, start=6):
                                    # Choose format based on status
                                    row_format = info_value_format
                                    status = row.get('Status', '')
                                    if status == 'Ajoutée':
                                        row_format = added_format
                                    elif status == 'Supprimée':
                                        row_format = removed_format
                                    elif status == 'Modifiée':
                                        row_format = modified_format
                                    
                                    for col_idx, col in enumerate(columns):
                                        value = row.get(col, "")
                                        if pd.isna(value) or value is None:
                                            value = ""
                                        diff_ws.write(row_idx, col_idx, str(value), row_format)
                                
                                # Auto-adjust column widths
                                for col_idx, col in enumerate(columns):
                                    max_length = max(len(str(col)), 15)
                                    diff_ws.set_column(col_idx, col_idx, min(max_length, 30))
                                    
                            except Exception as e:
                                print(f"Erreur lors de la création de la feuille {ws_name}: {e}")
                        
                        # Create duplicates worksheet
                        duplicates = []
                        dup_columns = []
                        if result.get('duplicates_base'):
                            duplicates.extend(result['duplicates_base'])
                            dup_columns = result.get('duplicates_base_columns', [])
                        if result.get('duplicates_comp'):
                            duplicates.extend(result['duplicates_comp'])
                            if not dup_columns and result.get('duplicates_comp_columns'):
                                dup_columns = result['duplicates_comp_columns']
                        
                        if comparison_mode == 'full' and duplicates and dup_columns:
                            ws_name = f"🔄 Doublons_{safe_sheet_name}_{result_idx+1}"[:31]
                            
                            try:
                                dup_ws = workbook.add_worksheet(ws_name)
                                
                                # Add title
                                dup_ws.merge_range('A1:F1', f'DOUBLONS - {sheet_name}', title_format)
                                dup_ws.set_row(0, 20)
                                
                                # Add summary
                                dup_ws.write('A3', f'Total des doublons: {len(duplicates)}', info_label_format)
                                
                                # Write headers
                                for col_idx, col in enumerate(dup_columns):
                                    dup_ws.write(4, col_idx, str(col), header_format)
                                
                                # Write data
                                for row_idx, row in enumerate(duplicates, start=5):
                                    for col_idx, col in enumerate(dup_columns):
                                        value = row.get(col, "")
                                        if pd.isna(value) or value is None:
                                            value = ""
                                        dup_ws.write(row_idx, col_idx, str(value), info_value_format)
                                
                                # Auto-adjust column widths
                                for col_idx, col in enumerate(dup_columns):
                                    max_length = max(len(str(col)), 15)
                                    dup_ws.set_column(col_idx, col_idx, min(max_length, 30))
                                    
                            except Exception as e:
                                print(f"Erreur lors de la création de la feuille doublons {ws_name}: {e}")

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
                
                # Write the fixed header row
                writer.writerow(['Feuille', 'Fichier', 'Ligne', 'Statut', 'Key', 'Column', 'Base Value', 'Comparison Value'])
                
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
                                    
                                    # Clean up values
                                    if pd.isna(base_value) or base_value is None:
                                        base_value = ""
                                    if pd.isna(comp_value) or comp_value is None:
                                        comp_value = ""
                                    
                                    row_data = [
                                        sheet_name,
                                        comp_filename,
                                        rows_written + 1,
                                        status,
                                        key,
                                        column,
                                        base_value,
                                        comp_value
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
                    headers = ['Clé', 'Champ', 'Valeur d\'origine', 'Nouvelle valeur']
                    data = [[d.get('Key', ''), d.get('Column', ''), 
                            format_cell_value(d.get('Base Value', '')),
                            format_cell_value(d.get('Comparison Value', ''))] 
                           for d in diffs[:max_rows]]
                else:
                    headers = ['Clé', 'Informations complémentaires']
                    data = [[d.get('Key', ''), 
                            f"Ligne {d.get('Base Row', '')} | {d.get('Comp Row', '')}"]
                           for d in diffs[:max_rows]]
                
                # Add headers row
                table_data = [headers] + data
                
                # Create table with styling based on difference type
                bg_color = colors.HexColor('#E8F5E8')  # default green
                if diff_type == 'removed':
                    bg_color = colors.HexColor('#FFEBEE')  # light red
                elif diff_type == 'modified':
                    bg_color = colors.HexColor('#FFF8E1')  # light amber
                
                col_widths = [2*inch] * len(headers)
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
                    ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#E8F5E8')),
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
                            ('FONTSIZE', (0, 0), (-1, -1), 9),
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
                            
                            if added:
                                elements.append(Paragraph(f"Entrées ajoutées ({len(added)})", subheading_style))
                                add_difference_table(elements, added, 'added')
                            
                            if removed:
                                elements.append(Paragraph(f"Entrées supprimées ({len(removed)})", subheading_style))
                                add_difference_table(elements, removed, 'removed')
                            
                            if modified:
                                elements.append(Paragraph(f"Entrées modifiées ({len(modified)})", subheading_style))
                                add_difference_table(elements, modified, 'modified')
                        else:
                            elements.append(Paragraph("Aucune différence détectée", styles["Normal"]))
                        
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