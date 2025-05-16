import streamlit as st
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime

# Import the necessary modules
from src.core.comparison_engine import ComparisonEngine
from src.core.excel_processor import ExcelProcessor
from src.core.site_matcher import SiteMatcher
from src.models.data_models import ComparisonSummary

# Helper function to ensure Arrow-compatible data
def clean_dataframe_for_display(df):
    """Clean a dataframe to make it compatible with Arrow/Streamlit display"""
    if df is None or df.empty:
        return pd.DataFrame() # Return empty DataFrame if None or empty
        
    # Convert all columns to strings to avoid Arrow serialization issues
    df_clean = df.copy()
    for col in df_clean.columns:
        df_clean[col] = df_clean[col].astype(str)
    
    return df_clean

def show():
    """Render the comparison page of the Excel Comparison Tool"""
    
    st.title("Comparer des fichiers Excel")
    
    # Check if comparison settings exist
    if 'comparison_settings' not in st.session_state:
        st.warning("Aucun paramètre de comparaison trouvé. Veuillez d'abord configurer votre comparaison.")
        
        with st.container():
            st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
            if st.button("Aller à la page de téléchargement", use_container_width=True):
                st.session_state.current_page = "upload"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Get settings from session state
    settings = st.session_state.comparison_settings
    
    # Create instances of required classes
    site_matcher = SiteMatcher()
    comparison_engine = ComparisonEngine()
    
    # Update site mappings
    site_matcher.set_site_mappings(settings["site_mappings"])
    
    # Display configuration summary
    st.subheader("Configuration de la comparaison")
    
    with st.expander("Voir les détails de la configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Fichier de base:**", settings["base_file"].file_name)
            st.write("**Feuilles à comparer:**", ", ".join(settings["selected_sheets"]))
            st.write("**Correspondances de codes de site:**")
            for code, sheet in settings["site_mappings"].items():
                st.write(f"- {code} → {sheet}")
        
        with col2:
            st.write(f"**Fichiers de comparaison:** {len(settings['comparison_files'])} fichier(s)")
            for i, file_info in enumerate(settings["comparison_files"]):
                st.write(f"- {file_info.file_name}")
            
            st.write("**Options:**")
            st.write(f"- Comparaison des colonnes: B-J (positions 2-10)")
    
    # Run comparison logic
    if 'comparison_results' not in st.session_state:
        with st.spinner("Comparaison en cours..."):
            try:
                all_results = {}
                start_time = time.time()
                total_differences_count = 0
                total_duplicates_count = 0
                total_comparable_cells = 0
                
                # Process each selected sheet in the base file
                for sheet_name_from_base_file in settings["selected_sheets"]:
                    sheet_specific_results_list = []
                    
                    # Load base file data for this sheet
                    base_processor = ExcelProcessor(settings["base_file"].file_path)
                    if not base_processor.load_workbook():
                        continue
                        
                    base_data = base_processor.get_sheet_data(sheet_name_from_base_file, is_base_file=True)
                    
                    if base_data.empty:
                        all_results[sheet_name_from_base_file] = []
                        continue
                    
                    # Find duplicates in base data
                    base_dupes = comparison_engine.find_duplicates(base_data, ["Locomotive", "CodeOp"])
                    total_duplicates_count += len(base_dupes)
                    
                    # Process each comparison file
                    for comp_file_info in settings["comparison_files"]:
                        comp_processor = ExcelProcessor(comp_file_info.file_path)
                        if not comp_processor.load_workbook():
                            continue
                            
                        # Use first sheet in comparison file
                        if not comp_processor.sheet_names:
                            continue
                            
                        comp_sheet_name = comp_processor.sheet_names[0]
                        comp_data = comp_processor.get_sheet_data(comp_sheet_name, is_base_file=False)
                        
                        if comp_data.empty:
                            continue
                            
                        # Filter comparison data by site
                        filtered_comp_data = comp_data[comp_data["Site"].str.contains(
                            list(settings["site_mappings"].keys())[0], case=False, na=False)]
                        
                        if filtered_comp_data.empty:
                            continue
                            
                        # Calculate comparable cells
                        value_cols = ["Commentaire", "Date Butee", "Date programmation", "Heure programmation", "Date sortie", "Heure sortie"]
                        total_comparable_cells += len(base_data) * len(value_cols)
                        
                        # Find differences - now focusing only on modifications to existing rows
                        differences = comparison_engine.find_differences(
                            base_data, 
                            filtered_comp_data,
                            key_columns=["Locomotive", "CodeOp"],
                            value_columns=value_cols
                        )
                        
                        # Now differences only contain modifications, not additions or deletions
                        # Store results and update metrics
                        file_specific_result = {
                            "comparison_file": comp_file_info.file_name,
                            "differences": differences,
                            "duplicates": base_dupes,
                            "base_rows": len(base_data),
                            "comp_rows": len(filtered_comp_data),
                            "base_df_preview": base_data.head(), 
                            "comp_df_preview": filtered_comp_data.head(),
                        }
                        
                        sheet_specific_results_list.append(file_specific_result)
                        total_differences_count += len(differences)
                    
                    all_results[sheet_name_from_base_file] = sheet_specific_results_list
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Create summary
                summary = ComparisonSummary(
                    total_sheets_compared=len(settings["selected_sheets"]),
                    total_rows_compared=0,
                    total_cells_compared=total_comparable_cells if total_comparable_cells > 0 else 1,
                    total_differences=total_differences_count,
                    total_duplicates=total_duplicates_count,
                    execution_time_seconds=execution_time
                )._asdict()
                
                # Store results in session state
                st.session_state.comparison_results = {
                    "results": all_results,
                    "summary": summary,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
            except Exception as e:
                st.error(f"Erreur pendant la comparaison: {str(e)}")
                st.exception(e)
    
    # Display results
    results_data = st.session_state.comparison_results
    summary = results_data["summary"]
    
    st.subheader("Résultats de la comparaison")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Feuilles comparées", summary.get("total_sheets_compared", 0))
    
    with col2:
        st.metric("Différences totales", summary.get("total_differences", 0))
    
    with col3:
        # Calculate match rate correctly
        cells_compared = summary.get("total_cells_compared", 1)
        if cells_compared == 0: cells_compared = 1 # Avoid division by zero
        
        diffs = summary.get("total_differences", 0)
        match_rate = max(0, 100 - ((diffs / cells_compared) * 100))
        
        st.metric("Taux de correspondance", f"{match_rate:.1f}%")
    
    with col4:
        st.metric("Temps de traitement", f"{summary.get('execution_time_seconds', 0):.2f}s")
    
    # Show detailed results by sheet
    st.subheader("Résultats détaillés")
    
    sheets = list(results_data["results"].keys())
    if sheets:
        selected_sheet = st.selectbox("Sélectionner une feuille à visualiser", options=sheets)
        
        sheet_results = results_data["results"][selected_sheet]
        
        # If we have results for this sheet
        if sheet_results:
            # Select comparison file if multiple
            if len(sheet_results) > 1:
                comp_files = [result["comparison_file"] for result in sheet_results]
                selected_file = st.selectbox("Sélectionner un fichier de comparaison", options=comp_files)
                
                # Find the selected file's results
                file_result = next(
                    (result for result in sheet_results if result["comparison_file"] == selected_file), 
                    sheet_results[0]
                )
            else:
                file_result = sheet_results[0]
            
            # Show differences
            st.subheader(f"Différences dans {selected_sheet}")
            differences = file_result["differences"]
            
            if not differences.empty:
                st.markdown(f"<p>Trouvé <b>{len(differences)}</b> différences</p>", unsafe_allow_html=True)
                # Translate column names
                differences_fr = differences.copy()
                if not differences_fr.empty and 'Status' in differences_fr.columns:
                    differences_fr = differences_fr.rename(columns={
                        'Key': 'Clé', 
                        'Column': 'Colonne', 
                        'Base Value': 'Valeur de base', 
                        'Comparison Value': 'Valeur de comparaison',
                        'Status': 'Statut'
                    })
                st.dataframe(clean_dataframe_for_display(differences_fr), use_container_width=True)
            else:
                st.success(f"Aucune différence trouvée dans la feuille '{selected_sheet}'")
            
            # Show duplicates
            st.subheader(f"Doublons dans {selected_sheet}")
            duplicates = file_result["duplicates"]
            
            if not duplicates.empty:
                st.markdown(f"<p>Trouvé <b>{len(duplicates)}</b> lignes en doublon</p>", unsafe_allow_html=True)
                st.dataframe(clean_dataframe_for_display(duplicates), use_container_width=True)
            else:
                st.success(f"Aucun doublon trouvé dans la feuille '{selected_sheet}'")
        else:
            st.info(f"Aucune donnée de comparaison disponible pour la feuille '{selected_sheet}'")
    
    # Actions
    st.subheader("Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("Enregistrer le rapport", use_container_width=True):
            # In a real app, this would save the report
            if 'reports' not in st.session_state:
                st.session_state.reports = []
                
            report_id = f"report_{len(st.session_state.reports) + 1:03d}"
            
            # Create list of comparison file names for the report
            comp_files = [f.file_name for f in settings["comparison_files"]]
            
            st.session_state.reports.append({
                "id": report_id,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "base_file": settings["base_file"].file_name,
                "comparison_files": comp_files,  # Store as list
                "comparison_file": ", ".join(comp_files),  # Also store as string for backwards compatibility
                "differences": summary["total_differences"],
                "match_rate": f"{match_rate:.1f}%"
            })
            
            st.success(f"Rapport enregistré avec ID: {report_id}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("Nouvelle comparaison", use_container_width=True):
            # Clear comparison results and go to upload page
            if 'comparison_results' in st.session_state:
                del st.session_state.comparison_results
            
            if 'comparison_settings' in st.session_state:
                del st.session_state.comparison_settings
            
            st.session_state.current_page = "upload"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show()