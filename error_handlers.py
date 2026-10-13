import streamlit as st
from database_utils import ValidationError, DatabaseError
from ui_components import render_error_message

def handle_database_operation(operation_func, error_msg="Database operation failed", return_default=None):
    """Standard database error handler"""
    try:
        return operation_func()
    except ValidationError as e:
        render_error_message(str(e))
        return return_default
    except DatabaseError as e:
        render_error_message(error_msg)
        return return_default
    except Exception as e:
        render_error_message("An unexpected error occurred. Please try again.")
        return return_default

def handle_file_operation(operation_func, error_msg="File operation failed", return_default=None):
    """Standard file operation error handler"""
    try:
        return operation_func()
    except (IOError, OSError) as e:
       
        render_error_message(error_msg)
        return return_default
    except Exception as e:
        
        render_error_message("File operation failed. Please try again.")
        return return_default

def handle_network_operation(operation_func, error_msg="Network operation failed", return_default=None):
    """Standard network operation error handler"""
    try:
        return operation_func()
    except (ConnectionError, TimeoutError) as e:
        render_error_message("Network error. Please check your connection and try again.")
        return return_default
    except Exception as e:
        render_error_message(error_msg)
        return return_default

def safe_execute(operation_func, error_context="Operation", show_error=True, return_default=None):
    """Generic safe execution wrapper"""
    try:
        return operation_func()
    except Exception as e:
        if show_error:
            render_error_message(f"{error_context} failed. Please try again.")
        return return_default

def log_and_display_error(error, context="", user_message=None):
    """Log error and optionally display to user"""
    if user_message:
        render_error_message(user_message)

class ErrorContext:
    """Context manager for error handling"""
    def __init__(self, context_name, user_message=None, return_default=None):
        self.context_name = context_name
        self.user_message = user_message
        self.return_default = return_default
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.user_message:
                render_error_message(self.user_message)
            return True  
        return False