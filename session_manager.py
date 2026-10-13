import streamlit as st
from database_utils import ensure_chat_session_exists
SESSION_KEYS = {
    "user": "user",
    "page": "page", 
    "current_chat_session": "current_chat_session",  
    "messages": "messages",
    "chat_loaded_for": "chat_loaded_for",
    "show_chat_history": "show_chat_history"
}

def clear_chat_session_data():
    """Clear chat-related session state data"""
    chat_keys = [SESSION_KEYS["messages"], SESSION_KEYS["chat_loaded_for"]]
    for key in chat_keys:
        if key in st.session_state:
            del st.session_state[key]

def clear_all_session_data():
    """Clear all session data except user"""
    keys_to_clear = [
        SESSION_KEYS["current_chat_session"], 
        SESSION_KEYS["messages"], 
        SESSION_KEYS["chat_loaded_for"],
        SESSION_KEYS["show_chat_history"]
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def handle_user_logout():
    """Centralized logout functionality"""
    try:
        if (st.session_state.get(SESSION_KEYS["current_chat_session"]) and 
            st.session_state.get(SESSION_KEYS["user"]) and
            st.session_state.get(SESSION_KEYS["messages"])):
            
            user_id = st.session_state[SESSION_KEYS["user"]][0]
            session_id = st.session_state[SESSION_KEYS["current_chat_session"]]
            ensure_chat_session_exists(session_id, user_id)
        

        st.session_state[SESSION_KEYS["user"]] = None
        st.session_state[SESSION_KEYS["page"]] = "login"
        clear_all_session_data()
        
        st.rerun()
        
    except Exception as e:
        st.session_state[SESSION_KEYS["user"]] = None
        st.session_state[SESSION_KEYS["page"]] = "login"
        st.rerun()

def initialize_session_state():
    """Initialize session state with default values"""
    defaults = {
        SESSION_KEYS["page"]: "login",
        SESSION_KEYS["user"]: None,
        SESSION_KEYS["current_chat_session"]: None,
        SESSION_KEYS["show_chat_history"]: False
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def validate_user_session():
    """Validate user session and redirect if necessary"""
    protected_pages = ["dashboard", "chat", "view_profile"]
    current_page = st.session_state.get(SESSION_KEYS["page"], "login")
    current_user = st.session_state.get(SESSION_KEYS["user"])
    
    if current_page in protected_pages and not current_user:
        st.session_state[SESSION_KEYS["page"]] = "login"
        st.rerun()
        return False
    
    return True

def get_current_user():
    """Get current user from session state"""
    return st.session_state.get(SESSION_KEYS["user"])

def set_current_page(page_name):
    """Set current page in session state"""
    st.session_state[SESSION_KEYS["page"]] = page_name

def get_current_page():
    """Get current page from session state"""
    return st.session_state.get(SESSION_KEYS["page"], "login")

def set_current_chat_session(session_id):
    """Set current chat session"""
    st.session_state[SESSION_KEYS["current_chat_session"]] = session_id

def get_current_chat_session():
    """Get current chat session"""
    return st.session_state.get(SESSION_KEYS["current_chat_session"])

def ensure_user_authenticated(redirect_page="login"):
    """Ensure user is authenticated, redirect if not"""
    if not get_current_user():
        set_current_page(redirect_page)
        st.rerun()
        return False
    return True