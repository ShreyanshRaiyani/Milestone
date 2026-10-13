import time
import streamlit as st
from datetime import datetime
from database_utils import (
    get_user_by_email, update_user_profile, update_user_password, 
    create_new_chat_session, update_chat_session_activity, 
    ensure_chat_session_exists, verify_password,
    ValidationError, DatabaseError
)
from sidebar_component import render_interactive_sidebar
from ui_components import (
    render_feature_card, render_chat_welcome, render_profile_avatar,
    render_error_message, render_success_message, safe_image_processing
)
from rag_utils import load_rag_chain, get_session_history, create_conversational_chain
from session_manager import (
    ensure_user_authenticated, get_current_user, clear_chat_session_data,
    set_current_chat_session, get_current_chat_session
)
from constants import PAGES


def dashboard_page():
    """Enhanced dashboard page with improved layout and error handling."""
    if not ensure_user_authenticated():
        return

    user = get_current_user()
    user_id, firstname, lastname, email, *_ = user
    render_interactive_sidebar(user, "dashboard")
    
    st.markdown(f'<h1 class="app-header animate-fade-in">Welcome back, {firstname}!</h1>', unsafe_allow_html=True)
    st.markdown('<div class="animate-slide-up">', unsafe_allow_html=True)
    
    st.markdown("### Powerful Legal AI Features")
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        render_feature_card(
            "Legal Research",
            "Get instant access to Indian Penal Code, case laws, and statutory interpretations with AI-powered search capabilities.",
            "⚖️",
            "#667eea",
            "#764ba2"
        )
        
        render_feature_card(
            "Case Analysis", 
            "Analyze legal precedents and get detailed explanations of court decisions and their real-world implications.",
            "📚",
            "#f093fb",
            "#f5576c"
        )

    with col2:
        render_feature_card(
            "Document Search",
            "Search through extensive legal documents and find relevant sections quickly using advanced RAG technology.",
            "🔍", 
            "#4facfe",
            "#00f2fe"
        )
        
        render_feature_card(
            "Interactive Q&A",
            "Ask complex legal questions and get comprehensive answers with context from authoritative sources.",
            "💬",
            "#43e97b", 
            "#38f9d7"
        )

def view_profile_page():
    """Profile editing page with tabbed interface and improved error handling."""
    if not ensure_user_authenticated():
        return

    user = get_current_user()
    user_id, firstname, lastname, email, *_ = user

    render_interactive_sidebar(user, "view_profile")
    
    st.markdown('<h1 class="app-header animate-fade-in">View Your Profile</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Current Profile", "Update Info", "Change Password"])
    
    with tab1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Current Profile")
            
            col_img, col_info = st.columns([1, 2])
            with col_img:
                render_profile_avatar(user, size=150)
            
            with col_info:
                st.markdown(f"""
                <div style="
                    background: rgba(255, 255, 255, 0.08);
                    padding: 25px;
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    backdrop-filter: blur(10px);
                    margin-top: 10px;
                ">
                    <p style="color: white; margin: 15px 0; font-size: 20px; text-shadow: 1px 1px 3px rgba(0,0,0,0.8);">
                        <strong style="color: #fbbf24;">Name:</strong> {firstname} {lastname}
                    </p>
                    <p style="color: white; margin: 15px 0; font-size: 20px; text-shadow: 1px 1px 3px rgba(0,0,0,0.8);">
                        <strong style="color: #fbbf24;">Email:</strong> {email}
                    </p>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        col1, col2, col3 = st.columns([0.5, 3, 0.5])
        with col2:
            with st.form("edit_form"):
                st.markdown("### Update Information")
                
                c1, c2 = st.columns(2)
                with c1:
                    new_first = st.text_input("First Name", value=firstname, placeholder="Enter first name")
                    new_email = st.text_input("Email", value=email, placeholder="Enter email address")
                with c2:
                    new_last = st.text_input("Last Name", value=lastname, placeholder="Enter last name")
                    photo_file = st.file_uploader(
                        "Update Profile Photo", 
                        type=["png", "jpg", "jpeg"],
                        help="Upload a new profile photo (max 5MB)"
                    )
                submitted = st.form_submit_button("Save Changes", use_container_width=True)
            
            if submitted:
                try:
                    if not new_first.strip():
                        render_error_message("First name is required")
                        st.stop()
                    
                    if not new_email.strip():
                        render_error_message("Email is required")
                        st.stop()
                    photo_bytes = None
                    if photo_file:
                        photo_bytes = safe_image_processing(photo_file)
                    
                    with st.spinner("Updating your profile..."):
                        update_user_profile(
                            user_id, 
                            new_first.strip(), 
                            new_last.strip(), 
                            new_email.strip().lower(), 
                            photo_bytes
                        )
                    
                    render_success_message("Profile updated successfully!")                    
                    st.session_state.user = get_user_by_email(new_email.strip().lower())
                    time.sleep(1)
                    st.session_state.page = PAGES["dashboard"]
                    st.rerun()
                    
                except ValidationError as e:
                    render_error_message(str(e))
                except DatabaseError as e:
                    render_error_message("Database error occurred. Please try again.")
                  
                except Exception as e:
                    render_error_message("An unexpected error occurred. Please try again.")
                  
    with tab3:
        col1, col2, col3 = st.columns([0.5, 3, 0.5])
        with col2:
            st.markdown("### Change Password")
            
            with st.form("password_form"):
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    current_password = st.text_input("Current Password", type="password", placeholder="Enter your current password")
                    new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
                with col_p2:
                    st.write("")  
                    confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
                
                password_submitted = st.form_submit_button("Change Password", use_container_width=True)
            
            if password_submitted:
                try:
                    if not all([current_password, new_password, confirm_password]):
                        render_error_message("All password fields are required")
                        st.stop()
                    if new_password != confirm_password:
                        render_error_message("New passwords do not match")
                        st.stop()
                    
                    if len(new_password) < 6:
                        render_error_message("New password must be at least 6 characters long")
                        st.stop()
                    
                    user_row = get_user_by_email(email)
                    if not user_row:
                        render_error_message("User verification failed")
                        st.stop()
                    
                    stored_hash = user_row[4]  # password_hash
                    salt = user_row[5]  # salt
                    
                    if not verify_password(stored_hash, salt, current_password):
                        render_error_message("Current password is incorrect")
                        st.stop()
                    
                    with st.spinner("Changing password..."):
                        update_user_password(user_id, new_password)
                    
                    render_success_message("Password changed successfully!")
                    time.sleep(1)
                    st.rerun()
                    
                except ValidationError as e:
                    render_error_message(str(e))
                except DatabaseError as e:
                    render_error_message("Database error occurred. Please try again.")
                    
                except Exception as e:
                    render_error_message("An unexpected error occurred. Please try again.")
                    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button("Back to Dashboard", use_container_width=True):
                st.session_state.page = PAGES["dashboard"]
                st.rerun()
        
        with btn_col2:
            if st.button("🗑️ Delete Account", key="delete_btn", use_container_width=True, type="secondary"):
                st.session_state.show_delete_confirm = True
                st.rerun()
    
    if st.session_state.get('show_delete_confirm', False):
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.warning("⚠️ This will permanently delete your account and all chat history!")
            
            confirm_email = st.text_input("Type your email to confirm:", placeholder=email, key="confirm_email")
            
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_delete_confirm = False
                    st.rerun()
            
            with confirm_col2:
                if confirm_email == email:
                    if st.button("🗑️ CONFIRM DELETE", key="confirm_delete_btn", use_container_width=True, type="primary"):
                        try:
                            from database_utils import delete_user_account
                            delete_user_account(user_id)
                            st.success("Account deleted")
                            st.session_state.user = None
                            st.session_state.page = "login"
                            st.session_state.show_delete_confirm = False
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.button("🗑️ CONFIRM DELETE", disabled=True, use_container_width=True, help="Enter your email to enable")
def initialize_chat_session(user_id: int):
    """Initialize or retrieve current chat session"""
    current_session = get_current_chat_session()
    
    if not current_session:
        try:
            new_session_id = create_new_chat_session(user_id)
            if not new_session_id:
                return None
            set_current_chat_session(new_session_id)
            clear_chat_session_data()
            return new_session_id
        except Exception as e:
            return None
    
    try:
        ensure_chat_session_exists(current_session, user_id)
        return current_session
    except Exception as e:
        return None
def render_chat_controls(session_id: str, user_id: int):
    """Render chat control buttons and session info"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col3:
        if st.button("🗑️ Clear Chat", help="Start a new conversation"):
            try:
                new_session_id = create_new_chat_session(user_id)
                if new_session_id:
                    clear_chat_session_data()
                    set_current_chat_session(new_session_id)
                    st.rerun()
                else:
                    render_error_message("Failed to create new chat session")
            except Exception as e:
                render_error_message("Error creating new chat session")

def handle_chat_input(prompt: str, session_id: str, user_id: int, conversational_rag_chain):
    """Handle chat input and generate response"""
    try:
        ensure_chat_session_exists(session_id, user_id)
        update_chat_session_activity(session_id)
        with st.chat_message("user"):
            st.markdown(prompt)
        config = {"configurable": {"session_id": session_id}}
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            full_response = ""
            with st.spinner("🤔 Thinking..."):
                try:
                    for chunk in conversational_rag_chain.stream({"input": prompt}, config=config):
                        if "answer" in chunk:
                            full_response += chunk["answer"]
                            message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)
                    
                    message_placeholder.markdown(full_response, unsafe_allow_html=True)
                    
                except Exception as e:
                    render_error_message("Error generating response. Please try again.")
                    return False
            
        return True
    except Exception as e:
        render_error_message("Error processing your message. Please try again.")
        return False

def chat_page():
    """Legal assistant chat page with proper session management and error handling."""
    if not ensure_user_authenticated():
        return

    user = get_current_user()
    user_id, firstname, lastname, email, *_ = user
    render_interactive_sidebar(user, "chat")
    
    st.markdown('<h1 class="app-header animate-fade-in">Legal Assistant Chat</h1>', unsafe_allow_html=True)
    
    session_id = initialize_chat_session(user_id)
    if not session_id:
        render_error_message("Failed to initialize chat session. Please try again.")
        if st.button("Return to Dashboard"):
            st.session_state.page = PAGES["dashboard"]
            st.rerun()
        return
    render_chat_controls(session_id, user_id)
    try:
        rag_chain = load_rag_chain()
        conversational_rag_chain = create_conversational_chain(rag_chain)
    except Exception as e:
        render_error_message("RAG system initialization failed. Please contact support.")
        return
    try:
        history = get_session_history(session_id)
        if ("chat_loaded_for" not in st.session_state or 
            st.session_state.chat_loaded_for != session_id):
            st.session_state.chat_loaded_for = session_id
            st.session_state.messages = history.messages
        chat_container = st.container()
        with chat_container:
            if not st.session_state.messages:
                render_chat_welcome()
            else:
                for message in st.session_state.messages:
                    role = "user" if message.type == "human" else "assistant"
                    with st.chat_message(role):
                        if role == "assistant":
                            st.markdown(message.content, unsafe_allow_html=True)
                        else:
                            st.markdown(message.content)

    except Exception as e:
        render_error_message("Error loading chat history")
    st.markdown("---")
    prompt = st.chat_input(
        "Ask your legal question here... (e.g., 'What is Section 302 IPC?', 'Explain bail procedure')",
        key=f"main_chat_input_{session_id[:8]}"
    )
    if 'chat_input' in st.session_state:
        prompt = st.session_state['chat_input']
        del st.session_state['chat_input']
    if prompt:
        success = handle_chat_input(prompt, session_id, user_id, conversational_rag_chain)
        if success:
            try:
                history = get_session_history(session_id)
                st.session_state.messages = history.messages
                st.rerun()
            except Exception as e:
                render_error_message("Error reloading chat history")