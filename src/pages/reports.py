import streamlit as st
from typing import Dict, Any
import pandas as pd
import os
import datetime
import io
import xlsxwriter
import base64

def generate_excel_report(report_data):
    """Generate an Excel report with the comparison results"""
    output = io.BytesIO()
    
    try:
        # Create a new Excel workbook
        with xlsxwriter.Workbook(output) as workbook:
            # Add a summary worksheet
            summary_ws = workbook.add_worksheet("Résumé")
            
            # Add a title with formatting
            title_format = workbook.add_format({
                'bold': True, 
                'font_size': 16,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#007147',  # Green RLE color
                'font_color': 'white'
            })
            summary_ws.merge_range('A1:G1', 'Rapport de Comparaison Excel', title_format)
            
            # Add report information
            header_format = workbook.add_format({
                'bold': True, 
                'font_size': 12,
                'bg_color': '#4CA27E',  # Light Green
                'font_color': 'white',
                'border': 1
            })
            
            cell_format = workbook.add_format({
                'border': 1
            })

            # Define formats for different statuses
            modified_format = workbook.add_format({
                'bg_color': '#FFFF00',  # Yellow for modified
                'border': 1
            })
            
            # Summary data
            summary_ws.write('A3', 'Rapport ID:', header_format)
            summary_ws.write('B3', report_data["id"], cell_format)
            
            summary_ws.write('A4', 'Date:', header_format)
            summary_ws.write('B4', report_data["date"], cell_format)
            
            summary_ws.write('A5', 'Fichier de base:', header_format)
            summary_ws.write('B5', report_data["base_file"], cell_format)
            
            summary_ws.write('A6', 'Fichiers de comparaison:', header_format)
            summary_ws.write('B6', report_data["comparison_file"], cell_format)
            
            summary_ws.write('A7', 'Différences trouvées:', header_format)
            summary_ws.write('B7', report_data["differences"], cell_format)
            
            summary_ws.write('A8', 'Taux de correspondance:', header_format)
            summary_ws.write('B8', report_data["match_rate"], cell_format)
            
            # Set column widths
            summary_ws.set_column('A:A', 20)
            summary_ws.set_column('B:B', 40)
            
            # If we have comparison results, add the detailed sheets
            if 'comparison_results' in st.session_state:
                results_data = st.session_state.comparison_results
                
                # Create a master sheet for all differences
                all_differences = []
                all_duplicates = []
                
                # Track how many sheets and differences were processed
                sheet_count = 0
                total_differences = 0
                
                # Add a differences worksheet for each sheet with differences
                for sheet_name, sheet_results in results_data["results"].items():
                    sheet_count += 1
                    
                    # Track differences for this sheet
                    sheet_differences = 0
                    
                    for result in sheet_results:
                        differences = result["differences"]
                                                
                        # Add site/sheet info to each difference row
                        if not differences.empty:
                            sheet_differences += len(differences)
                            
                            # Add file and sheet info to each row
                            differences_with_info = differences.copy()
                            differences_with_info['Sheet'] = sheet_name
                            differences_with_info['File'] = result["comparison_file"]
                            
                            # Add to master list
                            all_differences.append(differences_with_info)
                            
                            # Create a worksheet for this sheet's differences
                            diff_ws_name = f"{sheet_name[:25]}_diff"  # Keep name under 31 chars
                            
                            # Try to create the worksheet
                            try:
                                diff_ws = workbook.add_worksheet(diff_ws_name)
                                
                                # Add title
                                diff_ws.merge_range('A1:E1', f'Différences pour {sheet_name}', title_format)
                                
                                # Add file info
                                diff_ws.merge_range('A2:E2', f'Comparaison avec {result["comparison_file"]}', header_format)
                                
                                # Translate column headers
                                col_map = {
                                    'Key': 'Clé',
                                    'Column': 'Colonne',
                                    'Base Value': 'Valeur de base',
                                    'Comparison Value': 'Valeur de comparaison',
                                    'Status': 'Statut'
                                }
                                
                                # Write column headers
                                for col_idx, col_name in enumerate(differences.columns):
                                    fr_col_name = col_map.get(col_name, col_name)
                                    diff_ws.write(3, col_idx, fr_col_name, header_format)
                                
                                # Write data
                                for row_idx, row in differences.iterrows():
                                    status = str(row['Status']) if 'Status' in differences.columns else ''
                                    
                                    # Choose format based on status
                                    row_format = modified_format  # All rows are modifications
                                    
                                    # Write each cell in the row
                                    for col_idx, col_name in enumerate(differences.columns):
                                        # Make sure we have data for this column
                                        if col_name in row:
                                            diff_ws.write(row_idx + 4, col_idx, str(row[col_name]), row_format)
                                
                                # Add legend
                                legend_row = len(differences) + 6
                                diff_ws.write(legend_row, 0, "Légende:", workbook.add_format({'bold': True}))
                                diff_ws.write(legend_row + 1, 0, "Modifiée", modified_format)
                            except Exception as e:
                                print(f"  ERROR creating worksheet {diff_ws_name}: {str(e)}")

                        # Collect all duplicates with sheet info
                        duplicates = result.get("duplicates")
                        if duplicates is not None and not duplicates.empty:
                            duplicates_with_info = duplicates.copy()
                            duplicates_with_info['Sheet'] = sheet_name
                            duplicates_with_info['File'] = result["comparison_file"]
                            
                            # Add to master list
                            all_duplicates.append(duplicates_with_info)
                    
                    # Update total differences counter
                    total_differences += sheet_differences

                # Add master sheets with all differences and duplicates
                if all_differences:
                    try:
                        # Combine all difference DataFrames
                        all_diffs_df = pd.concat(all_differences, ignore_index=True)
                        
                        # Create the master differences sheet
                        master_diff_ws = workbook.add_worksheet("Toutes_différences")
                        
                        # Add title
                        master_diff_ws.merge_range('A1:G1', 'Toutes les différences', title_format)
                        
                        # Reorder columns to put Sheet and File first
                        cols = all_diffs_df.columns.tolist()
                        if 'Sheet' in cols and 'File' in cols:
                            new_cols = ['Sheet', 'File']
                            for col in cols:
                                if col not in new_cols:
                                    new_cols.append(col)
                            all_diffs_df = all_diffs_df[new_cols]
                        
                        # French translations for column headers
                        col_map = {
                            'Sheet': 'Feuille',
                            'File': 'Fichier',
                            'Key': 'Clé', 
                            'Column': 'Colonne',
                            'Base Value': 'Valeur de base',
                            'Comparison Value': 'Valeur de comparaison',
                            'Status': 'Statut'
                        }
                        
                        # Write column headers
                        for col_idx, col_name in enumerate(all_diffs_df.columns):
                            col_name_fr = col_map.get(col_name, col_name)
                            master_diff_ws.write(2, col_idx, col_name_fr, header_format)
                        
                        # Write data
                        for row_idx, row in all_diffs_df.iterrows():
                            # Determine format based on status
                            status = row.get('Status', '')
                            row_format = modified_format  # All rows are modifications
                            
                            # Write each column
                            for col_idx, col_name in enumerate(all_diffs_df.columns):
                                cell_value = str(row[col_name]) if col_name in row else ''
                                master_diff_ws.write(row_idx + 3, col_idx, cell_value, row_format)
                        
                        # Add legend
                        legend_row = len(all_diffs_df) + 5
                        master_diff_ws.write(legend_row, 0, "Légende:", workbook.add_format({'bold': True}))
                        master_diff_ws.write(legend_row + 1, 0, "Modifiée", modified_format)
                        
                    except Exception as e:
                        print(f"Error creating master differences sheet: {str(e)}")

                # Add master duplicates sheet
                if all_duplicates:
                    # ...existing code for duplicates...
                    pass
        
        # Reset pointer to start of file
        output.seek(0)
    except Exception as e:
        import traceback
        traceback.print_exc()
    
    return output

def get_download_link(buffer, filename, text):
    """Generate a download link for a file"""
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" class="download-button">{text}</a>'

def show():
    """Render the reports page of the Excel Comparison Tool"""
    
    # Initialize session state variables
    if 'export_success' not in st.session_state:
        st.session_state.export_success = False
    if 'download_link' not in st.session_state:
        st.session_state.download_link = ""
    # Initialize reports list if it doesn't exist
    if 'reports' not in st.session_state:
        st.session_state.reports = []
    
    st.title("Rapports de comparaison")
    
    st.markdown("""
    <div class="card">
        <div class="card-header">Visualiser et exporter les rapports de comparaison</div>
        <p>Cette page vous permet de visualiser, gérer et exporter les rapports de comparaison.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if there are any comparison results to display
    if 'comparison_results' not in st.session_state or not st.session_state.get('comparison_results'):
        st.info("Aucun résultat de comparaison disponible pour le moment. Veuillez d'abord effectuer une comparaison.")
        
        with st.container():
            st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
            if st.button("Aller à la page de téléchargement", use_container_width=True):
                st.session_state.current_page = "upload"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return
            
    # Display available reports
    st.subheader("Rapports disponibles")
    
    # Display reports in a table - now we know reports list exists
    if st.session_state.reports:
        # Create a clean DataFrame for display
        display_data = []
        for report in st.session_state.reports:
            display_data.append({
                "ID": report["id"],
                "Date": report["date"],
                "Fichier de base": report["base_file"],
                "Fichiers de comparaison": report.get("comparison_file", ", ".join(report.get("comparison_files", []))),
                "Différences": report["differences"],
                "Taux de correspondance": report["match_rate"]
            })
            
        reports_df = pd.DataFrame(display_data)
        st.dataframe(reports_df, use_container_width=True)
        
        # Select report to view/export
        selected_report = st.selectbox(
            "Sélectionnez un rapport à visualiser ou exporter:",
            options=[f"{r['id']} - {r['base_file']} vs {r.get('comparison_file', ', '.join(r.get('comparison_files', [])))}" 
                    for r in st.session_state.reports],
            key="report_selector"
        )
        
        if selected_report:
            st.subheader("Détails du rapport")
            
            # Get the selected report
            report_id = selected_report.split(" - ")[0]
            selected_report_data = next(
                (r for r in st.session_state.reports if r["id"] == report_id), 
                st.session_state.reports[0]
            )
            
            # Display report details
            st.markdown("### Résumé")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Différences trouvées", selected_report_data["differences"])
                st.metric("Taux de correspondance", selected_report_data["match_rate"])
            
            with col2:
                # Count number of comparison files
                comp_files = selected_report_data.get("comparison_files", [])
                if not comp_files and "comparison_file" in selected_report_data:
                    comp_files = selected_report_data["comparison_file"].split(", ")
                
                st.metric("Fichiers de comparaison", len(comp_files))
                st.metric("Généré le", selected_report_data["date"])
            
            # Export options
            st.subheader("Exporter le rapport")
            
            with st.container():
                # First row for export format selection
                export_format = st.radio(
                    "Format d'exportation:",
                    options=["Excel (.xlsx)", "CSV (.csv)"]
                )
            
                # Create HTML container for better alignment
                st.markdown('<div class="export-section">', unsafe_allow_html=True)
                
                # Create two columns for filename and button
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    filename = st.text_input(
                        "Nom du fichier:", 
                        value=f"ECT_Technis_Report_{report_id}_{datetime.datetime.now().strftime('%Y%m%d')}"
                    )
                    
                    if export_format == "Excel (.xlsx)" and not filename.endswith('.xlsx'):
                        filename += '.xlsx'
                    elif export_format == "CSV (.csv)" and not filename.endswith('.csv'):
                        filename += '.csv'
                
                # Add the custom class to the button column
                with col2:
                    st.markdown('<div class="button-align-with-input">', unsafe_allow_html=True)
                    if st.button("Exporter", type="primary", use_container_width=True):
                        if export_format == "Excel (.xlsx)":
                            excel_buffer = generate_excel_report(selected_report_data)
                            
                            # Create a download link
                            download_link = get_download_link(excel_buffer, filename, "Télécharger le rapport Excel")
                            st.markdown(download_link, unsafe_allow_html=True)
                            st.success(f"Rapport généré! Cliquez sur le lien pour télécharger.")
                            
                            # Set success state
                            st.session_state.export_success = True
                            st.session_state.download_link = download_link
                        
                        elif export_format == "CSV (.csv)":
                            # Generate CSV for each sheet with differences
                            if 'comparison_results' in st.session_state:
                                results = st.session_state.comparison_results["results"]
                                
                                # Find the first sheet with differences
                                for sheet_name, sheet_results in results.items():
                                    for result in sheet_results:
                                        differences = result["differences"]
                                        if not differences.empty:
                                            # Convert to CSV
                                            csv = differences.to_csv(index=False)
                                            
                                            # Create download link for CSV
                                            b64 = base64.b64encode(csv.encode()).decode()
                                            download_link = f'<a href="data:text/csv;base64,{b64}" download="{filename}" class="download-button">Télécharger le rapport CSV</a>'
                                            st.markdown(download_link, unsafe_allow_html=True)
                                            st.success(f"Rapport généré! Cliquez sur le lien pour télécharger.")
                                            
                                            # Set success state
                                            st.session_state.export_success = True
                                            st.session_state.download_link = download_link
                                            break
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

            # Only show this section if we need to generate another report
            if st.session_state.export_success:
                # Add button to clear success message and start over
                if st.button("Générer un autre rapport"):
                    st.session_state.export_success = False
                    st.session_state.download_link = ""
                    st.rerun()

    else:
        st.info("Aucun rapport disponible. Effectuez une comparaison pour générer des rapports.")

if __name__ == "__main__":
    show()