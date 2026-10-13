
import time
import sqlite3
import streamlit as st
from database_utils import get_user_by_email, get_user_by_name, verify_password, create_user
from sidebar_component import render_interactive_sidebar
from ui_components import safe_image_processing, render_error_message, render_success_message
from session_manager import set_current_page
from constants import PAGES, PASSWORD_MIN_LENGTH, SUCCESS_MESSAGES, ERROR_MESSAGES

def register_page():
    """User registration page with improved validation and error handling."""
    render_interactive_sidebar(None)
    
    st.markdown('<h1 class="app-header">Create Your Account</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        with st.form("register_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                firstname = st.text_input("First Name *", placeholder="Enter your first name")
                email = st.text_input("Email *", placeholder="your.email@example.com")
            with c2:
                lastname = st.text_input("Last Name", placeholder="Enter your last name")
                password = st.text_input("Password *", type="password", placeholder="Create a password")
            
            confirm = st.text_input("Confirm Password *", type="password", placeholder="Repeat your password")
            photo_file = st.file_uploader("Profile Photo (Optional)", type=["png", "jpg", "jpeg"])
            
            submitted = st.form_submit_button("Create Account", use_container_width=True)

        if submitted:
            if not firstname or not email or not password:
                render_error_message("Please fill in all required fields")
                return
                
            if password != confirm:
                render_error_message("Passwords do not match")
                return
                
            if len(password) < PASSWORD_MIN_LENGTH:
                render_error_message(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
                return
                
            photo_bytes = None
            if photo_file:
                try:
                    photo_bytes = safe_image_processing(photo_file)
                except Exception as e:
                    render_error_message(f"Error processing image: {str(e)}")
                    return
            try:
                with st.spinner("Creating your account..."):
                    user_id = create_user(
                        firstname.strip(), 
                        lastname.strip(), 
                        email.strip().lower(), 
                        password, 
                        photo_bytes
                    )
                    
                render_success_message(SUCCESS_MESSAGES["account_created"])
                time.sleep(1)
                set_current_page(PAGES["login"])
                st.rerun()
                
            except sqlite3.IntegrityError:
                render_error_message("An account with this email already exists")
            except Exception as e:
                render_error_message(ERROR_MESSAGES["generic_error"])
    
    st.markdown("---")
    if st.button("Already have an account? Login", use_container_width=True):
        set_current_page(PAGES["login"])
        st.rerun()

def login_page():
    """User login page with improved validation and session handling."""
    render_interactive_sidebar(None)

    st.markdown('<h1 class="app-header">Welcome!</h1>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            '<h2 style="color: white; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">🔒 Login</h2>',
            unsafe_allow_html=True
        )

        with st.form("login_form"):
            identifier = st.text_input("Email or Name", placeholder="Enter your email or name")
            password = st.text_input("Password", type="password", placeholder="Enter your password")

            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if not identifier or not password:
                render_error_message("Please fill in all fields")
            else:
                try:
                    with st.spinner("Signing you in..."):
                        user_row = None
                        if "@" in identifier:
                            user_row = get_user_by_email(identifier.strip().lower())
                        else:
                            user_row = get_user_by_name(identifier.strip())

                        if not user_row:
                            render_error_message("No user found with that email/name")
                        else:
                            user_id, firstname, lastname, email, password_hash, salt, photo = user_row

                            if verify_password(password_hash, salt, password):
                                render_success_message(f"Welcome, {firstname}!")

                                st.session_state.user = user_row
                                set_current_page(PAGES["dashboard"])
                                time.sleep(1)
                                st.rerun()
                            else:
                                render_error_message(ERROR_MESSAGES["authentication_failed"])

                except Exception:
                    render_error_message(ERROR_MESSAGES["generic_error"])

        if st.button("Create New Account", use_container_width=True):
            set_current_page(PAGES["register"])
            st.rerun()
def logout_user():
    """Centralized logout function with proper cleanup"""
    try:
        from session_manager import handle_user_logout
        handle_user_logout()
    except Exception as e:
        # Fallback logout
        st.session_state.user = None
        set_current_page(PAGES["login"])
        st.rerun()