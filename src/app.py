import streamlit as st
import os
import sys
import time
import base64

def get_icon_base64():
    """Get the app icon as base64 string"""
    try:
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "static", "images", "icon_excel_comparison.ico")
        if os.path.exists(icon_path):
            with open(icon_path, 'rb') as f:
                icon_data = f.read()
            return f"data:image/x-icon;base64,{base64.b64encode(icon_data).decode()}"
    except:
        pass
    return "📊"

def run_app():
    """Run the Excel Comparison Tool application"""
    # Configure page settings
    st.set_page_config(
        page_title="ECT Technis",
        page_icon=get_icon_base64(),
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Load CSS
    load_css()
    
    # Create necessary directories
    os.makedirs("temp", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "home"
    
    # Sidebar with toggle functionality
    render_sidebar()
    
    # Render the current page
    try:
        if st.session_state.current_page == "home":
            from src.pages import home
            home.show()
        elif st.session_state.current_page == "upload":
            from src.pages import upload
            upload.show()
        elif st.session_state.current_page == "comparison":
            from src.pages import comparison
            comparison.show()
        elif st.session_state.current_page == "reports":
            from src.pages import reports
            reports.show()
        elif st.session_state.current_page == "legal":
            from src.pages import legal
            legal.show()
        elif st.session_state.current_page == "help":
            from src.pages import help
            help.show()
        else:
            st.error(f"Page '{st.session_state.current_page}' introuvable!")
            st.session_state.current_page = "home"
    except Exception as e:
        st.error(f"Une erreur est survenue: {str(e)}")
        st.exception(e)
    
    # Render footer in the main content area
    render_footer()

def load_css():
    """Load custom CSS styles in modular fashion"""
    try:
        css_dir = os.path.join(os.path.dirname(__file__), "static", "css")
        css_files = [
            "variables.css",
            "base.css", 
            "components.css",
            "buttons.css",
            "layout.css",
            "responsive.css"
        ]
        
        combined_css = ""
        
        for css_file in css_files:
            css_path = os.path.join(css_dir, css_file)
            if os.path.exists(css_path):
                with open(css_path, 'r', encoding='utf-8') as f:
                    combined_css += f"/* {css_file} */\n"
                    combined_css += f.read()
                    combined_css += "\n\n"
            else:
                st.warning(f"CSS file not found: {css_file}")
        
        if combined_css:
            st.markdown(f"<style>{combined_css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not load CSS: {str(e)}")

def get_base64_of_bin_file(bin_file):
    """Get base64 encoded binary file content"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        # Logo and branding
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "static", "images", "logo_excel_comparison.png")
        if os.path.exists(logo_path):
            img_base64 = get_base64_of_bin_file(logo_path)
            st.markdown(
                f"""
                <div class="logo-container">
                    <img src="data:image/png;base64,{img_base64}" class="logo" alt="ECT Technis" size="small">
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # Use the image from the attachment as fallback
            st.image("https://raw.githubusercontent.com/alexandre-caby/rle-logo/main/excel_comparison_icon.png", 
                    width=150)

        st.markdown('<hr style="margin-top: 0; margin-bottom: 20px; border-color: rgba(255,255,255,0.2);">', unsafe_allow_html=True)

        # Navigation buttons - Translated to French
        pages = {
            "home": "🏠 Accueil",
            "upload": "📤 Télécharger des fichiers", 
            "comparison": "🔍 Comparer des fichiers", 
            "reports": "📊 Rapports",
            "help": "❓ Aide",
            "legal": "📄 Mentions légales"
        }
        
        # Current page indicator
        current_page = st.session_state.current_page
        
        # Create navigation buttons with improved styling
        for page_id, page_name in pages.items():
            # Style active button differently
            if current_page == page_id:
                st.markdown(
                    f"""
                    <div class="nav-button nav-button-active">
                        {page_name}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                button_id = f"nav_{page_id}"
                if st.button(page_name, key=button_id, use_container_width=True):
                    st.session_state.current_page = page_id
                    st.rerun()

def render_footer():
    """Render footer in the main content area"""
    # Create footer with clickable legal link
    footer_cols = st.columns([4, 1, 4])
    
    with footer_cols[1]:
        st.markdown(
            """
            <div class="footer">
                <p style="margin-bottom: 5px;">Version 1.0</p>
                <p style="margin-bottom: 5px;">© 2025 ECT Technis</p>
            </div>
            """,
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    run_app()