import os
import sqlite3
import hashlib
import secrets
import uuid
from typing import Optional, List, Dict
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "chat1.db"

# Custom exceptions
class DatabaseError(Exception):
    """Custom database exception"""
    pass

class ValidationError(Exception):
    """Custom validation exception"""
    pass

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise DatabaseError(f"Database operation failed: {str(e)}")
    finally:
        if conn:
            conn.close()

def init_db():
    """Initialize SQLite db for users and chat sessions with proper schema versioning."""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            c.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            c.execute("SELECT MAX(version) FROM schema_version")
            current_version = c.fetchone()[0] or 0
            
            if current_version < 1:
                c.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        firstname TEXT NOT NULL,
                        lastname TEXT,
                        email TEXT UNIQUE NOT NULL,
                        password_hash BLOB NOT NULL,
                        salt BLOB NOT NULL,
                        photo BLOB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                c.execute("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
                
                c.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
                c.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)")
                c.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_message ON chat_sessions(last_message_at)")
                c.execute("INSERT INTO schema_version (version) VALUES (1)")
            
            conn.commit()
            
    except Exception as e:
        raise DatabaseError(f"Database initialization failed: {str(e)}")

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) and len(email) <= 254

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if len(password) > 128:
        return False, "Password too long"
    return True, "Password is valid"

def validate_name(name: str) -> bool:
    """Validate name input"""
    return bool(name and name.strip() and len(name.strip()) <= 50)

def get_user_by_email(email: str):
    """Get user by email address with validation."""
    if not validate_email(email):
        raise ValidationError("Invalid email format")
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, firstname, lastname, email, password_hash, salt, photo 
                FROM users WHERE email = ?
            """, (email.lower(),))
            return c.fetchone()
    except DatabaseError:
        raise
    except Exception as e:
        return None

def get_user_by_name(name: str):
    """Try to find a user by first+last or by first only or last only (case-insensitive)."""
    if not name or not name.strip():
        return None
    
    name = name.strip()
    if len(name) > 100:  
        return None
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            parts = name.split()
            if len(parts) >= 2:
                first = parts[0]
                last = " ".join(parts[1:])
                c.execute("""
                    SELECT id, firstname, lastname, email, password_hash, salt, photo 
                    FROM users 
                    WHERE LOWER(firstname) = ? AND LOWER(lastname) = ?
                """, (first.lower(), last.lower()))
                row = c.fetchone()
                if row:
                    return row
            c.execute("""
                SELECT id, firstname, lastname, email, password_hash, salt, photo 
                FROM users 
                WHERE LOWER(firstname) = ? OR LOWER(lastname) = ?
                LIMIT 1
            """, (name.lower(), name.lower()))
            return c.fetchone()
            
    except DatabaseError:
        raise
    except Exception as e:
        return None

def _hash_password(password: str, salt: bytes) -> bytes:
    """Derive a password hash using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)

def verify_password(stored_hash: bytes, salt: bytes, provided_password: str) -> bool:
    """Verify a password against stored hash and salt."""
    if not all([stored_hash, salt, provided_password]):
        return False
    
    try:
        return secrets.compare_digest(stored_hash, _hash_password(provided_password, salt))
    except Exception as e:
        return False

def create_user(firstname: str, lastname: str, email: str, password: str, photo_bytes: Optional[bytes] = None) -> int:
    """Create a new user and return the user ID with validation."""
    if not validate_name(firstname):
        raise ValidationError("Invalid first name")
    if lastname and not validate_name(lastname):
        raise ValidationError("Invalid last name")
    if not validate_email(email):
        raise ValidationError("Invalid email format")
    
    is_valid_pwd, pwd_msg = validate_password(password)
    if not is_valid_pwd:
        raise ValidationError(pwd_msg)

    firstname = firstname.strip()
    lastname = lastname.strip() if lastname else ""
    email = email.strip().lower()

    if photo_bytes and len(photo_bytes) > 5 * 1024 * 1024:  # 5MB limit
        raise ValidationError("Profile photo too large (max 5MB)")
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE email = ?", (email,))
            if c.fetchone():
                raise ValidationError("Email already exists")

            salt = secrets.token_bytes(32)
            password_hash = _hash_password(password, salt)
            
            c.execute("""
                INSERT INTO users (firstname, lastname, email, password_hash, salt, photo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (firstname, lastname, email, password_hash, salt, photo_bytes))
            
            user_id = c.lastrowid
            conn.commit()
            return user_id
            
    except ValidationError:
        raise
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise ValidationError("Email already exists")
        raise DatabaseError(f"Database constraint violation: {str(e)}")
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(f"User creation failed: {str(e)}")

def update_user_profile(user_id: int, firstname: str, lastname: str, email: str, photo_bytes: Optional[bytes]):
    """Update user profile information with validation."""
    # Validation
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValidationError("Invalid user ID")
    if not validate_name(firstname):
        raise ValidationError("Invalid first name")
    if lastname and not validate_name(lastname):
        raise ValidationError("Invalid last name")
    if not validate_email(email):
        raise ValidationError("Invalid email format")
 
    firstname = firstname.strip()
    lastname = lastname.strip() if lastname else ""
    email = email.strip().lower()
    
    if photo_bytes and len(photo_bytes) > 5 * 1024 * 1024:  
        raise ValidationError("Profile photo too large (max 5MB)")
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not c.fetchone():
                raise ValidationError("User not found")
            
            c.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
            if c.fetchone():
                raise ValidationError("Email already exists")
            
            if photo_bytes is not None:
                c.execute("""
                    UPDATE users 
                    SET firstname=?, lastname=?, email=?, photo=?, last_active=CURRENT_TIMESTAMP 
                    WHERE id=?
                """, (firstname, lastname, email, photo_bytes, user_id))
            else:
                c.execute("""
                    UPDATE users 
                    SET firstname=?, lastname=?, email=?, last_active=CURRENT_TIMESTAMP 
                    WHERE id=?
                """, (firstname, lastname, email, user_id))
            
            conn.commit()
            
    except ValidationError:
        raise
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise ValidationError("Email already exists")
        raise DatabaseError(f"Database constraint violation: {str(e)}")
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(f"Profile update failed: {str(e)}")

def update_user_password(user_id: int, new_password: str):
    """Update user password with new hash and salt."""
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValidationError("Invalid user ID")
    
    is_valid, msg = validate_password(new_password)
    if not is_valid:
        raise ValidationError(msg)
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not c.fetchone():
                raise ValidationError("User not found")
            
            salt = secrets.token_bytes(32)
            password_hash = _hash_password(new_password, salt)
            
            c.execute("""
                UPDATE users 
                SET password_hash=?, salt=?, last_active=CURRENT_TIMESTAMP 
                WHERE id=?
            """, (password_hash, salt, user_id))
            
            conn.commit()
            
    except ValidationError:
        raise
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(f"Password update failed: {str(e)}")

def get_user_chat_sessions(user_id: int, limit: int = 8) -> List[Dict]:
    """Get chat sessions for a user with validation."""
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValidationError("Invalid user ID")
    if not isinstance(limit, int) or limit <= 0 or limit > 50:
        limit = 8  
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT session_id, name, created_at, last_message_at 
                FROM chat_sessions 
                WHERE user_id = ? 
                ORDER BY last_message_at DESC, created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            sessions = []
            for row in c.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'name': row[1],
                    'created_at': row[2],
                    'last_message_at': row[3]
                })
            
            return sessions
            
    except DatabaseError:
        raise
    except Exception as e:
        return []

def create_new_chat_session(user_id: int, max_retries: int = 3) -> Optional[str]:
    """Create a new chat session for the user with retry logic."""
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValidationError("Invalid user ID")
    
    for attempt in range(max_retries):
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                
                c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if not c.fetchone():
                    raise ValidationError("User not found")
                
                session_id = str(uuid.uuid4())
                
                c.execute("SELECT session_id FROM chat_sessions WHERE session_id = ?", (session_id,))
                if c.fetchone():
                    continue  
                
                chat_name = f"Legal Chat - {datetime.now().strftime('%b %d, %Y %I:%M %p')}"
                
                c.execute("""
                    INSERT INTO chat_sessions (session_id, user_id, name)
                    VALUES (?, ?, ?)
                """, (session_id, user_id, chat_name))
                
                conn.commit()
                return session_id
                
        except ValidationError:
            raise
        except DatabaseError as e:
            if attempt == max_retries - 1:
                raise
            continue
        except Exception as e:
            if attempt == max_retries - 1:
                return None
            continue
    
    return None

def ensure_chat_session_exists(session_id: str, user_id: int) -> bool:
    """Ensure a chat session exists in the database, create if it doesn't."""
    if not session_id or not isinstance(user_id, int) or user_id <= 0:
        return False
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Check if session exists
            c.execute("""
                SELECT session_id FROM chat_sessions 
                WHERE session_id = ? AND user_id = ?
            """, (session_id, user_id))
            
            if c.fetchone():
                return True
            
            # Session doesn't exist, create it
            chat_name = f"Legal Chat - {datetime.now().strftime('%b %d, %Y %I:%M %p')}"
            c.execute("""
                INSERT INTO chat_sessions (session_id, user_id, name)
                VALUES (?, ?, ?)
            """, (session_id, user_id, chat_name))
            
            conn.commit()
            return True
            
    except DatabaseError:
        raise
    except Exception as e:
        return False

def update_chat_session_activity(session_id: str):
    """Update the last message time for a chat session."""
    if not session_id:
        return False
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE chat_sessions 
                SET last_message_at = CURRENT_TIMESTAMP 
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            return c.rowcount > 0
            
    except DatabaseError:
        raise
    except Exception as e:
        return False

def delete_chat_session(session_id: str, user_id: int) -> bool:
    """Delete a chat session (with user verification for security)."""
    if not session_id or not isinstance(user_id, int) or user_id <= 0:
        return False
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Verify and delete in one operation
            c.execute("""
                DELETE FROM chat_sessions 
                WHERE session_id = ? AND user_id = ?
            """, (session_id, user_id))
            
            deleted = c.rowcount > 0
            conn.commit()
            
            return deleted
            
    except DatabaseError:
        raise
    except Exception as e:
        return False

def rename_chat_session(session_id: str, user_id: int, new_name: str) -> bool:
    """Rename a chat session (with user verification for security)."""
    if not session_id or not isinstance(user_id, int) or user_id <= 0:
        return False
    if not new_name or len(new_name.strip()) > 100:
        return False
    
    new_name = new_name.strip()
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE chat_sessions 
                SET name = ? 
                WHERE session_id = ? AND user_id = ?
            """, (new_name, session_id, user_id))
            
            updated = c.rowcount > 0
            conn.commit()
            
            return updated
            
    except DatabaseError:
        raise
    except Exception as e:
        return False

def get_chat_session_by_id(session_id: str, user_id: int) -> Optional[Dict]:
    """Get a specific chat session by ID (with user verification)."""
    if not session_id or not isinstance(user_id, int) or user_id <= 0:
        return None
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT session_id, name, created_at, last_message_at 
                FROM chat_sessions 
                WHERE session_id = ? AND user_id = ?
            """, (session_id, user_id))
            
            row = c.fetchone()
            if row:
                return {
                    'session_id': row[0],
                    'name': row[1],
                    'created_at': row[2],
                    'last_message_at': row[3]
                }
            return None
            
    except DatabaseError:
        raise
    except Exception as e:
        return None

def delete_user_account(user_id: int) -> bool:
    """Delete user account and all associated data"""
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValidationError("Invalid user ID")
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not c.fetchone():
                raise ValidationError("User not found")
            
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            deleted = c.rowcount > 0
            conn.commit()
            
            return deleted
            
    except ValidationError:
        raise
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError(f"Account deletion failed: {str(e)}")