import streamlit as st
import os
import base64
from pathlib import Path

def show():
    """Display the user guide"""
    st.title("Guide de l'utilisateur")
    
    # Add a small description
    st.markdown("""
    Ce guide vous aidera à naviguer dans l'application ECT Technis et à utiliser ses fonctionnalités.
    Veuillez suivre les étapes ci-dessous pour une utilisation optimale de l'outil de comparaison Excel.
    """)

    try:
        # Load document content
        docs_folder = Path(__file__).parent.parent.parent / "docs"  
              
        user_guide_path = docs_folder / "user_guide.md"
        if user_guide_path.exists():
            with open(user_guide_path, "r", encoding="utf-8") as f:
                user_guide_content = f.read()
            st.markdown(user_guide_content)
        else:
            st.error("Le fichier de guide utilisateur est introuvable.")
    except Exception as e:
        st.error(f"Une erreur est survenue lors du chargement du guide utilisateur: {str(e)}")