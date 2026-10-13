
import os
import streamlit as st
import base64
import warnings
from database_utils import init_db, DatabaseError
from ui_components import load_css, render_error_message
from session_manager import initialize_session_state, validate_user_session, handle_user_logout, get_current_page
from navigation_utils import navigate_to_page
from constants import APP_TITLE, APP_ICON
from auth_pages import login_page, register_page
from app_pages import dashboard_page, view_profile_page, chat_page

warnings.filterwarnings("ignore")

def safe_init_db():
    """Safely initialize database with error handling"""
    try:
        init_db()
        return True
    except DatabaseError as e:
        st.error("Database initialization failed. Please contact support.")
        return False
    except Exception as e:
        st.error("Critical system error. Please contact support.")
        return False

def set_background_image(image_path):
    """Set background image for the app with fallback."""
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            
            st.markdown(f"""
            <style>
            .stApp {{
                background-image: url(data:image/png;base64,{encoded_string});
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """, unsafe_allow_html=True)
        else:
            load_gradient_background()
            
    except Exception as e:
        load_gradient_background()

def load_gradient_background():
    """Load gradient background as fallback"""
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    </style>
    """, unsafe_allow_html=True)

def route_to_page():
    """Route to appropriate page with error handling"""
    try:
        current_page = get_current_page()
        
        page_routes = {
            "login": login_page,
            "register": register_page,
            "dashboard": dashboard_page,
            "view_profile": view_profile_page,  
            "chat": chat_page
        }
        
        if current_page in page_routes:
            page_routes[current_page]()
        else:
            navigate_to_page("login")
            
    except Exception as e:
        render_error_message("Navigation error occurred. Please try again.")
        navigate_to_page("login")

def configure_page():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title=f"{APP_ICON} {APP_TITLE}", 
        page_icon=APP_ICON, 
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': f"{APP_TITLE} - AI-powered legal research tool"
        }
    )

def main():
    """Main application function with comprehensive error handling."""
    try:
        configure_page()
        
        if not safe_init_db():
            st.stop()
        load_css()
        set_background_image('bg1.png')
        
        initialize_session_state()
        
        if not validate_user_session():
            return
        
        route_to_page()
        
    except Exception as e:
        st.error("A critical error occurred. Please refresh the page and try again.")
        st.stop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        st.error("Application interrupted by user")
    except Exception as e:
        st.error("Failed to start application. Please check logs and try again.")