import streamlit as st
import pandas as pd
import os
from typing import List, Dict, Optional, Tuple

from src.models.data_models import FileInfo, ComparisonSettings
from src.core.excel_processor import ExcelProcessor
from src.core.site_matcher import SiteMatcher

def show():
    """Render the upload page for the Excel Comparison Tool"""
    
    st.title("Télécharger des fichiers Excel")
    
    st.markdown("""
    <div class="card">
        <div class="card-header">Télécharger des fichiers pour comparaison</div>
        <p>Téléchargez le fichier Excel de base (PREPA PHP) et le(s) fichier(s) Excel de comparaison.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create temp directory if it doesn't exist
    os.makedirs("temp", exist_ok=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Fichier de base (PREPA PHP)")
        base_file = st.file_uploader("Télécharger un fichier Excel de base", type=["xlsx", "xls"], key="base_file")
        
        if base_file:
            # Save the uploaded file temporarily
            with open(os.path.join("temp", base_file.name), "wb") as f:
                f.write(base_file.getbuffer())
            
            # Process the file to get sheet information
            base_processor = ExcelProcessor(os.path.join("temp", base_file.name))
            if base_processor.load_workbook():
                st.success(f"Fichier de base chargé: {base_file.name}")
                st.write(f"Feuilles trouvées: {len(base_processor.sheet_names)}")
                st.write("Feuilles:", ", ".join(base_processor.sheet_names))
                
                # Store in session state
                st.session_state.base_file_info = FileInfo.from_path(
                    os.path.join("temp", base_file.name),
                    base_processor.sheet_names
                )
                
                # Preview the first sheet
                if st.checkbox("Afficher l'aperçu du fichier de base"):
                    sheet_to_preview = st.selectbox(
                        "Sélectionner une feuille à prévisualiser",
                        options=base_processor.sheet_names
                    )
                    
                    # Show raw preview to see headers
                    st.write("**Aperçu brut (affichage des lignes d'en-tête) :**")
                    preview_df = base_processor.get_sheet_preview(sheet_to_preview)
                    st.dataframe(preview_df.head(10), use_container_width=True)
                    
                    st.info("**Remarque :** Pour PREPA PHP, les 2 premières lignes sont des en-têtes, et la ligne 3 contient les noms des colonnes")
                    
                    # Show processed data
                    st.write("**Données traitées (après gestion des en-têtes) :**")
                    df = base_processor.get_sheet_data(sheet_to_preview, is_base_file=True)
                    st.dataframe(df.head(5), use_container_width=True)
            else:
                st.error("Échec du traitement du fichier de base. Veuillez vérifier s'il s'agit d'un fichier Excel valide.")
    
    with col2:
        st.subheader("Fichier(s) de comparaison")
        comparison_files = st.file_uploader(
            "Télécharger un ou plusieurs fichiers Excel de comparaison", 
            type=["xlsx", "xls"], 
            accept_multiple_files=True,
            key="comparison_files"
        )
        
        if comparison_files:
            st.success(f"{len(comparison_files)} fichier(s) de comparaison téléchargé(s)")
            
            # Store all uploaded files
            st.session_state.comp_file_info = []
            
            # Process each file
            for i, comp_file in enumerate(comparison_files):
                # Save the uploaded file temporarily
                with open(os.path.join("temp", comp_file.name), "wb") as f:
                    f.write(comp_file.getbuffer())
                
                # Process the file
                comp_processor = ExcelProcessor(os.path.join("temp", comp_file.name))
                if comp_processor.load_workbook():
                    st.write(f"Fichier {i+1}: {comp_file.name} - {len(comp_processor.sheet_names)} feuille(s)")
                    
                    # Store in session state
                    st.session_state.comp_file_info.append(
                        FileInfo.from_path(
                            os.path.join("temp", comp_file.name),
                            comp_processor.sheet_names
                        )
                    )
                    
                    # Sample of the file to identify site column
                    if st.checkbox(f"Afficher l'aperçu pour {comp_file.name}", key=f"preview_{i}"):
                        if comp_processor.sheet_names:
                            sheet_name = comp_processor.sheet_names[0]
                            
                            # Show raw preview to see headers
                            st.write("**Aperçu brut (affichage des lignes d'en-tête) :**")
                            preview_df = comp_processor.get_sheet_preview(sheet_name)
                            st.dataframe(preview_df.head(10), use_container_width=True)
                            
                            st.info("**Remarque :** Pour les fichiers de comparaison, les 7 premières lignes sont des en-têtes, et la ligne 8 contient les noms des colonnes")
                            
                            # Show processed data
                            st.write("**Données traitées (après gestion des en-têtes) :**")
                            df = comp_processor.get_sheet_data(sheet_name, is_base_file=False)
                            st.dataframe(df.head(5), use_container_width=True)
                else:
                    st.error(f"Échec du traitement de {comp_file.name}. Veuillez vérifier s'il s'agit d'un fichier Excel valide.")
    
    # If both files are uploaded, show configuration options
    if 'base_file_info' in st.session_state and 'comp_file_info' in st.session_state:
        st.subheader("Configurer la comparaison")
        
        # Get sheets from base file
        base_sheets = st.session_state.base_file_info.sheet_names
        
        # Select sheets from base file to compare
        selected_sheets = st.multiselect(
            "Sélectionner les feuilles à comparer",
            options=base_sheets,
            default=None,
            placeholder="Sélectionner une ou plusieurs feuilles"
        )
        
        # Site mapping configuration
        st.subheader("Configuration des codes de site")
        st.markdown("""
        <div class="info-box">
            Configurez comment les codes de site dans les fichiers de comparaison (colonne A) correspondent aux feuilles du fichier de base.
            Par exemple: LE → Lens, BGL → BGL
        </div>
        """, unsafe_allow_html=True)
        
        # Default mappings
        if 'site_mappings' not in st.session_state:
            st.session_state.site_mappings = {
                "LE": "Lens", 
                "BGL": "BGL"
            }
        
        # UI to add/edit mappings
        with st.expander("Modifier les correspondances de codes de site", expanded=True):
            # Add new mapping
            col1, col2 = st.columns(2)
            with col1:
                new_code = st.text_input("Code de site", "", placeholder="Entrez le code de site présent dans le fichier comparé")
            with col2:
                new_sheet = st.selectbox("Correspond à la feuille", options=base_sheets)
            
            if st.button("Ajouter/Mettre à jour"):
                if new_code and new_sheet:
                    st.session_state.site_mappings[new_code.strip().upper()] = new_sheet
                    st.success(f"Correspondance ajoutée: {new_code} → {new_sheet}")
            
            # Display current mappings
            mapping_data = [
                {"Code de site": code, "Nom de feuille": sheet} 
                for code, sheet in st.session_state.site_mappings.items()
            ]
            
            st.write("Correspondances actuelles:")
            st.table(pd.DataFrame(mapping_data))
        
        if st.button("Démarrer la comparaison", type="primary"):
            if not selected_sheets:
                st.error("Veuillez sélectionner au moins une feuille à comparer.")
            else:
                # Create comparison settings
                column_indices = list(range(1, 10))  # Columns B-J (indices 1-9)
                
                # Store settings for the comparison page
                st.session_state.comparison_settings = {
                    "base_file": st.session_state.base_file_info,
                    "comparison_files": st.session_state.comp_file_info,
                    "selected_sheets": selected_sheets,
                    "site_mappings": st.session_state.site_mappings,
                    "site_column": "A",  # Default to column A for site codes
                    "column_indices": column_indices,
                }
                
                # Redirect to comparison page
                st.session_state.current_page = "comparison"
                st.rerun()

if __name__ == "__main__":
    show()