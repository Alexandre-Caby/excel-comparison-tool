import streamlit as st
import os
import base64
from pathlib import Path

def show():
    """Display the legal information page"""
    st.title("Mentions Légales")
    
    # Add a small description
    st.markdown("""
    Cette page regroupe toutes les informations légales concernant l'utilisation 
    de l'application ECT Technis. Veuillez consulter ces documents pour comprendre 
    vos droits et responsabilités lors de l'utilisation de cet outil.
    """)
    
    # Create tabs for different legal documents
    tab1, tab2, tab3 = st.tabs(["Licence", "Politique de Confidentialité", "Conditions d'Utilisation"])
    
    try:
        # Load legal documents content
        docs_folder = Path(__file__).parent.parent.parent / "docs" / "legal"
        
        with tab1:
            license_path = docs_folder / "licence.md"
            if license_path.exists():
                with open(license_path, "r", encoding="utf-8") as f:
                    license_content = f.read()
                st.markdown(license_content)
            else:
                st.error("Le fichier de licence est introuvable.")
            
        with tab2:
            privacy_path = docs_folder / "privacy_policy.md"
            if privacy_path.exists():
                with open(privacy_path, "r", encoding="utf-8") as f:
                    privacy_content = f.read()
                st.markdown(privacy_content)
            else:
                st.error("La politique de confidentialité est introuvable.")
            
        with tab3:
            terms_path = docs_folder / "terms_of_use.md"
            if terms_path.exists():
                with open(terms_path, "r", encoding="utf-8") as f:
                    terms_content = f.read()
                st.markdown(terms_content)
            else:
                st.error("Les conditions d'utilisation sont introuvables.")
                
    except Exception as e:
        st.error(f"Une erreur est survenue lors du chargement des documents légaux: {str(e)}")