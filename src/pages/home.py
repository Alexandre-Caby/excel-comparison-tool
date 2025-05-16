import streamlit as st
from typing import Dict, Any
import os
import pandas as pd

def show():
    """Render the home page of the Excel Comparison Tool"""
    
    # Main header
    st.markdown("<h1 class='main-title'>ECT Technis</h1>", unsafe_allow_html=True)
    
    # Feature description in a card
    st.markdown("""
    <div class="card">
        <div class="card-header">Bienvenue sur ECT Technis</div>
        <p>Cet outil vous aide à comparer des fichiers Excel pour trouver des différences et des doublons entre eux.</p>        
        <h3>Fonctionnalités principales:</h3>
        <ul>
            <li>Comparer des fichiers Excel par feuilles et colonnes</li>
            <li>Identifier les différences entre les fichiers avec mise en évidence</li>
            <li>Trouver des données en double dans les feuilles de calcul</li>
            <li>Générer des rapports de comparaison détaillés</li>
            <li>Exporter les résultats dans différents formats</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # How to use section
    st.markdown("""
    <div class="card">
        <div class="card-header">Comment l'utiliser</div>
        <ol>
            <li>Accédez à la page <b>"Télécharger des fichiers"</b> pour importer vos fichiers Excel</li>
            <li>Configurez vos paramètres de comparaison</li>
            <li>Lancez la comparaison</li>
            <li>Visualisez et téléchargez les résultats</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Start Buttons
    st.subheader("Démarrage rapide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Apply the new button styling
        with st.container():
            st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
            if st.button("Nouvelle comparaison", key="new_comparison", use_container_width=True):
                st.session_state.current_page = "upload"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
            if st.button("Voir les rapports", key="view_reports", use_container_width=True):
                st.session_state.current_page = "reports"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show()