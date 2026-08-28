import hashlib
import os
from database.db_manager import create_user, get_user_by_email

def hash_password(password: str) -> str:
    """Generates a secure PBKDF2 hash of the password with a unique salt."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt, 
        100000  # Number of iterations
    )
    return f"{salt.hex()}:{pwd_hash.hex()}"

def verify_password(stored_password_hash: str, provided_password: str) -> bool:
    """Verifies a password against its stored PBKDF2 hash and salt."""
    try:
        salt_hex, hash_hex = stored_password_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            provided_password.encode('utf-8'), 
            salt, 
            100000
        )
        return pwd_hash.hex() == hash_hex
    except Exception:
        return False

def register_user(name: str, email: str, password: str) -> int:
    """
    Registers a new user in the database.
    Returns the user's ID or raises ValueError if validation fails or email exists.
    """
    name = name.strip()
    email = email.lower().strip()
    password = password.strip()
    
    if not name:
        raise ValueError("Name cannot be empty.")
    if not email or "@" not in email:
        raise ValueError("Invalid email address.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
        
    password_hash = hash_password(password)
    return create_user(name, email, password_hash)

def authenticate_user(email: str, password: str) -> dict:
    """
    Authenticates a user using email and password.
    Returns the user record (dict) on success, or None on failure.
    """
    email = email.lower().strip()
    user = get_user_by_email(email)
    if not user:
        return None
        
    if verify_password(user["password_hash"], password):
        # Remove hash from dictionary before passing it to session states
        user_dict = dict(user)
        user_dict.pop("password_hash", None)
        return user_dict
        
    return None
