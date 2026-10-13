
# UI Constants
AVATAR_SIZES = {
    "small": 80,
    "medium": 130, 
    "large": 150
}

# File handling
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = ["image/png", "image/jpg", "image/jpeg"]
MAX_IMAGE_DIMENSIONS = (800, 800)

# Database Constants  
DB_TIMEOUT = 30.0
PASSWORD_MIN_LENGTH = 6
MAX_NAME_LENGTH = 50
MAX_EMAIL_LENGTH = 254
MAX_CHAT_NAME_LENGTH = 100

# Chat Constants
MAX_CHAT_SESSIONS_DISPLAY = 6
MAX_CHAT_HISTORY_DISPLAY = 8
CHAT_MESSAGE_MAX_LENGTH = 10000

# Session Constants
SESSION_TIMEOUT_MINUTES = 30
MAX_RETRY_ATTEMPTS = 3

# RAG Constants
RAG_MAX_DOCS = 5
RAG_TEMPERATURE = 0.1
RAG_MAX_TOKENS = 2000
RAG_TIMEOUT_SECONDS = 30

# UI Text Constants
APP_TITLE = "Legal Assistant"
APP_ICON = "⚖️"
DEFAULT_WELCOME_MESSAGE = "Welcome to your Legal Assistant!"

# Error Messages
ERROR_MESSAGES = {
    "database_error": "Database error occurred. Please try again.",
    "validation_error": "Please check your input and try again.",
    "authentication_failed": "Invalid credentials",
    "session_expired": "Your session has expired. Please log in again.",
    "file_too_large": f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)",
    "invalid_file_type": f"Invalid file type. Only {', '.join(ALLOWED_IMAGE_TYPES)} allowed",
    "chat_creation_failed": "Failed to create new chat session",
    "rag_initialization_failed": "RAG system initialization failed",
    "network_error": "Network error. Please check your connection.",
    "generic_error": "An unexpected error occurred. Please try again."
}

# Success Messages
SUCCESS_MESSAGES = {
    "account_created": "Account created successfully! Please log in.",
    "profile_updated": "Profile updated successfully!",
    "password_changed": "Password changed successfully!",
    "logout_success": "Logged out successfully",
    "chat_created": "New chat session created"
}

# Page Names
PAGES = {
    "login": "login",
    "register": "register", 
    "dashboard": "dashboard",
    "chat": "chat",
    "view_profile": "view_profile"  # New key
}
# Protected pages that require authentication
PROTECTED_PAGES = [PAGES["dashboard"], PAGES["chat"], PAGES["view_profile"]]

# Default chat welcome suggestions
CHAT_SUGGESTIONS = [
    "What is Section 302 IPC?",
    "Explain bail procedure", 
    "Difference between FIR and complaint",
    "Article 21 of Constitution",
    "How to file a PIL?"
]



# Environment variables (with defaults)
ENV_DEFAULTS = {
    "PINECONE_INDEX_NAME": "chatbot",
    "OPENAI_MODEL": "gpt-3.5-turbo",
    "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
}