import streamlit as st
from ui_components import render_profile_avatar
from database_utils import get_user_chat_sessions
from navigation_utils import handle_chat_session_switch
from session_manager import handle_user_logout, get_current_chat_session
from constants import MAX_CHAT_SESSIONS_DISPLAY

def render_user_profile_section(user, avatar_size=130):
    """Render user profile section in sidebar"""
    if not user or len(user) < 3:
        return
        
    user_id, firstname, lastname, email = user[:4]
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        render_profile_avatar(user, size=avatar_size)

    st.markdown(
        f'<p style="color: white; font-weight: 700; font-size: 25px; margin: 10px 0 6px 0; text-align: center;">{firstname} {lastname}</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<p style="color: rgba(255,255,255,0.85); font-size: 23px; margin: 0 0 15px 0; text-align: center;">{email}</p>',
        unsafe_allow_html=True
    )

def render_sidebar_title():
    """Render main sidebar title"""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 15px;">
        <p style="color:white; font-weight: 800; margin: 0; font-size: 36px;">⚖️ LegalBot</p>
    </div>
    """, unsafe_allow_html=True)

def render_navigation_buttons(page_type, user_id):
    """Render appropriate navigation buttons based on page type"""
    from navigation_utils import create_and_switch_to_new_chat
    
    if page_type == "dashboard":
        if st.button("👤 View Profile", key="nav_profile", help="View your profile", use_container_width=True):
            st.session_state.page = "view_profile"
            st.rerun()
            
        if st.button("➕ New Chat", key="nav_new_chat_dashboard", help="Start a new legal consultation", use_container_width=True):
            create_and_switch_to_new_chat(user_id)
            
        if st.button("🚪 Logout", key="logout_btn_dashboard", help="Sign out", use_container_width=True):
            handle_user_logout()
    
    elif page_type == "chat":
        if st.button("🏠 Dashboard", key="nav_dashboard", help="Go to dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
            
        if st.button("➕ New Chat", key="nav_new_chat", help="Start a new legal consultation", use_container_width=True):
            create_and_switch_to_new_chat(user_id)
    
    else:  
        if st.button("🏠 Dashboard", key="nav_dashboard", help="Go to dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
            
        if st.button("➕ New Chat", key="nav_new_chat_other", help="Start a new legal consultation", use_container_width=True):
            create_and_switch_to_new_chat(user_id)
            
        if st.button("🚪 Logout", key="logout_btn_other", help="Sign out", use_container_width=True):
            handle_user_logout()

def render_chat_history_section(user_id):
    """Render chat history section for chat page"""
    st.markdown('<hr style="margin: 10px 0; border: 0.5px solid rgba(255,255,255,0.2);">', unsafe_allow_html=True)
    st.markdown('<h4 style="color: white; font-size: 16px; margin: 8px 0;">📜 Recent Chats</h4>', unsafe_allow_html=True)
    
    try:
        recent_sessions = get_user_chat_sessions(user_id, limit=MAX_CHAT_SESSIONS_DISPLAY)
        
        if recent_sessions:
            current_session = get_current_chat_session()
            
            for session in recent_sessions:
                is_current = (session['session_id'] == current_session)
                
                if is_current:
                    st.markdown(f"""
                    <div style="
                        background: rgba(103, 126, 234, 0.3);
                        border: 1px solid rgba(103, 126, 234, 0.6);
                        border-radius: 8px;
                        padding: 8px;
                        margin: 4px 0;
                        color: white;
                        font-size: 12px;
                        font-weight: 600;
                    ">
                        🟢 {session['name'][:25]}{'...' if len(session['name']) > 25 else ''}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    display_name = session['name'][:25] + ('...' if len(session['name']) > 25 else '')
                    if st.button(
                        f"💬 {display_name}", 
                        key=f"chat_{session['session_id']}", 
                        help=f"Open chat: {session['name']}",
                        use_container_width=True
                    ):
                        handle_chat_session_switch(session['session_id'], user_id)
        else:
            st.markdown("""
            <div style="
                text-align: center; 
                color: rgba(255,255,255,0.6); 
                padding: 10px;
                font-size: 12px;
                font-style: italic;
            ">
                No chats yet
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error("Error loading chat history")

def render_legal_disclaimers():
    """Render legal disclaimers for chat page"""
    st.markdown('<hr style="margin: 10px 0; border: 0.5px solid rgba(255,255,255,0.2);">', unsafe_allow_html=True)
    st.markdown('<h4 style="color: white; font-size: 16px; margin: 8px 0;">⚖️ Legal Notice</h4>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="
        background: rgba(220, 38, 38, 0.1);
        border: 1px solid rgba(220, 38, 38, 0.3);
        border-radius: 8px;
        padding: 10px;
        margin: 8px 0;
        color: rgba(255, 255, 255, 0.9);
        font-size: 11px;
        line-height: 1.3;
    ">
        <div style="font-weight: 600; margin-bottom: 4px; color: #fecaca;">⚠️ Important</div>
        <div>📚 Research only - not legal advice</div>
        <div>👨‍⚖️ Consult qualified lawyer</div>
        <div>⚖️ Seek professional help for serious matters</div>
    </div>
    """, unsafe_allow_html=True)

def render_welcome_message_for_guests():
    """Render welcome message for non-logged in users"""
    st.markdown("""
    <div style="text-align: center; color: white; padding: 20px 15px;">
        <h3 style="color: white; font-size: 30px; font-weight: bold; margin-bottom: 10px;">Welcome!</h3>
        <p style="color: white; font-size: 20px; line-height: 1.4;">Please log in to access your legal assistant.</p>
    </div>
    """, unsafe_allow_html=True)

def render_logout_button_with_divider():
    """Render logout button with visual separator"""
    st.markdown('<hr style="margin: 10px 0; border: 0.5px solid rgba(255,255,255,0.2);">', unsafe_allow_html=True)
    if st.button("🚪 Logout", key="logout_btn_chat", help="Sign out", use_container_width=True):
        handle_user_logout()

def render_interactive_sidebar(user, current_page="dashboard"):
    """Main function to render interactive sidebar based on current page"""
    with st.sidebar:
        render_sidebar_title()
        
        if user:
            user_id = user[0]
            
            if current_page == "dashboard":
                render_user_profile_section(user)
                render_navigation_buttons("dashboard", user_id)
                
            elif current_page == "chat":
                render_navigation_buttons("chat", user_id)
                render_chat_history_section(user_id)
                render_legal_disclaimers()
                render_logout_button_with_divider()
                
            else:
                render_user_profile_section(user)
                render_navigation_buttons("other", user_id)
        else:
            render_welcome_message_for_guests()