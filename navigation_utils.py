import streamlit as st
from session_manager import (
    clear_chat_session_data,set_current_page, set_current_chat_session)
from database_utils import create_new_chat_session


def navigate_to_page(page_name, clear_chat=False):
    """Centralized page navigation with optional chat clearing"""
    try:
        if clear_chat:
            clear_chat_session_data()
        
        set_current_page(page_name)
        st.rerun()
        
    except Exception as e:
        set_current_page("login")
        st.rerun()
def create_and_switch_to_new_chat(user_id):
    """Create new chat session and navigate to chat page"""
    try:
        new_session_id = create_new_chat_session(user_id)
        if new_session_id:
            clear_chat_session_data()
            set_current_chat_session(new_session_id)
            navigate_to_page("chat")
            return True
        else:
            st.error("Failed to create new chat session")
            return False
            
    except Exception as e:
        st.error("Error creating new chat session")
        return False
def render_nav_button(text, key, help_text, target_page, clear_chat=False, user_id=None):
    """Render a reusable navigation button"""
    try:
        if st.button(text, key=key, help=help_text, use_container_width=True):
            if target_page == "new_chat" and user_id:
                return create_and_switch_to_new_chat(user_id)
            else:
                navigate_to_page(target_page, clear_chat)
                return True
        return False
    except Exception as e:
        return False

def render_dashboard_nav_buttons(user_id):
    """Render navigation buttons for dashboard"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_nav_button(
        "👤 View Profile", 
        "nav_profile", 
        "View your profile", 
        "view_profile"  # New value
    )
    with col2:
        render_nav_button(
            "➕ New Chat", 
            "nav_new_chat_dashboard", 
            "Start a new legal consultation", 
            "new_chat",
            user_id=user_id
        )
    
    with col3:
        if st.button("🚪 Logout", key="logout_btn_dashboard", help="Sign out of your account", use_container_width=True):
            from session_manager import handle_user_logout
            handle_user_logout()

def render_chat_nav_buttons(user_id):
    """Render navigation buttons for chat page"""
    col1, col2 = st.columns(2)
    with col1:
        render_nav_button(
        "🏠 Dashboard", 
        "nav_dashboard", 
        "Go to dashboard", 
        "dashboard"
    )
    with col2:
        render_nav_button(
            "➕ New Chat", 
            "nav_new_chat_chat", 
            "Start a new legal consultation", 
            "new_chat",
            user_id=user_id
        )
def render_standard_nav_buttons(user_id):
    """Render standard navigation buttons for other pages"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_nav_button(
            "🏠 Dashboard", 
            "nav_dashboard", 
            "Go to dashboard", 
            "dashboard"
        )
    
    with col2:
        render_nav_button(
            "➕ New Chat", 
            "nav_new_chat_other", 
            "Start a new legal consultation", 
            "new_chat",
            user_id=user_id
        )
    
    with col3:
        if st.button("🚪 Logout", key="logout_btn_other", help="Sign out of your account", use_container_width=True):
            from session_manager import handle_user_logout
            handle_user_logout()

def handle_chat_session_switch(session_id, user_id):
    """Handle switching to a different chat session"""
    try:
        current_session = st.session_state.get('current_chat_session')  
        if (current_session and 
            st.session_state.get('messages')):
            from database_utils import ensure_chat_session_exists
            ensure_chat_session_exists(current_session, user_id)

        set_current_chat_session(session_id)
        set_current_page("chat")
        clear_chat_session_data()
        st.rerun()
        
    except Exception as e:
        st.error("Error switching chat sessions")