# File: app/utils/auth_utils.py

"""
Authentication utilities for Neo Cafe
"""
import hashlib
import hmac
import os
import secrets
import string
import time
from datetime import datetime, timedelta
import re
from app.data.database import get_user_by_username, create_user, update_user, get_users

# Password hashing
def hash_password(password):
    """
    Hash a password using PBKDF2
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: Password hash
    """
    if not password:
        return None
    
    # Create salt
    salt = secrets.token_hex(8)
    
    # Set iterations
    iterations = 150000
    
    # Hash password
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    )
    
    # Format the hash
    hash_str = f"pbkdf2:sha256:{iterations}${salt}${dk.hex()}"
    
    return hash_str

def verify_password(stored_hash, provided_password):
    """
    Verify a password against a stored hash
    
    Args:
        stored_hash (str): Stored password hash
        provided_password (str): Password to verify
        
    Returns:
        bool: True if password matches, False otherwise
    """
    if not stored_hash or not provided_password:
        return False
    
    try:
        # Parse the stored hash
        algorithm, hash_name, iterations, salt, hash_value = re.match(
            r'(\w+):(\w+):(\d+)\$(.+)\$(.+)',
            stored_hash
        ).groups()
        
        # Convert iterations to int
        iterations = int(iterations)
        
        # Compute hash of provided password
        dk = hashlib.pbkdf2_hmac(
            hash_name,
            provided_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        
        # Compare hashes using constant-time comparison
        return hmac.compare_digest(dk.hex(), hash_value)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

# Token generation
def generate_token(username, expiry_hours=24):
    """
    Generate authentication token
    
    Args:
        username (str): Username
        expiry_hours (int): Token expiry in hours
        
    Returns:
        dict: Token data
    """
    # Create random token
    token = secrets.token_urlsafe(32)
    
    # Set expiry
    expiry = datetime.now() + timedelta(hours=expiry_hours)
    
    # Create token data
    token_data = {
        "token": token,
        "username": username,
        "expiry": expiry.isoformat()
    }
    
    return token_data

def validate_token(token_data):
    """
    Validate authentication token
    
    Args:
        token_data (dict): Token data
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    if not token_data or "expiry" not in token_data:
        return False
    
    try:
        # Parse expiry
        expiry = datetime.fromisoformat(token_data["expiry"])
        
        # Check if token has expired
        if expiry < datetime.now():
            return False
        
        # Token is valid
        return True
    except Exception as e:
        print(f"Error validating token: {e}")
        return False

# User authentication
def validate_login(username, password):
    """
    Validate user login
    
    Args:
        username (str): Username
        password (str): Password
        
    Returns:
        dict/None: User data if login successful, None otherwise
    """
    # Get user by username
    user = get_user_by_username(username)
    
    # Check if user exists
    if not user:
        return None
    
    # Verify password
    if verify_password(user.get("password_hash"), password):
        # Update last login time
        user["last_login"] = datetime.now().isoformat()
        update_user(username, {"last_login": user["last_login"]})
        
        # Return user data (excluding password hash)
        return {k: v for k, v in user.items() if k != "password_hash"}
    
    # Password incorrect
    return None

def register_user(username, email, password):
    """
    Register a new user
    
    Args:
        username (str): Username
        email (str): Email address
        password (str): Password
        
    Returns:
        tuple: (success, message)
    """
    # Validate username
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    # Check if username already exists
    if get_user_by_username(username):
        return False, "Username already exists"
    
    # Validate email
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email address"
    
    # Validate password
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    # Create user
    user_data = {
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "role": "customer",  # Default role
        "created_at": datetime.now().isoformat()
    }
    
    # Save user
    if create_user(user_data):
        return True, "User registered successfully"
    else:
        return False, "Error creating user"

def get_user_profile(username):
    """
    Get user profile data
    
    Args:
        username (str): Username
        
    Returns:
        dict/None: User profile data or None if not found
    """
    # Get user by username
    user = get_user_by_username(username)
    
    # Check if user exists
    if not user:
        return None
    
    # Return user profile data (excluding password hash)
    return {k: v for k, v in user.items() if k != "password_hash"}

def change_password(username, current_password, new_password):
    """
    Change user password
    
    Args:
        username (str): Username
        current_password (str): Current password
        new_password (str): New password
        
    Returns:
        tuple: (success, message)
    """
    # Get user by username
    user = get_user_by_username(username)
    
    # Check if user exists
    if not user:
        return False, "User not found"
    
    # Verify current password
    if not verify_password(user.get("password_hash"), current_password):
        return False, "Current password is incorrect"
    
    # Validate new password
    if not new_password or len(new_password) < 8:
        return False, "New password must be at least 8 characters"
    
    # Update password
    updated_data = {
        "password_hash": hash_password(new_password),
        "updated_at": datetime.now().isoformat()
    }
    
    if update_user(username, updated_data):
        return True, "Password changed successfully"
    else:
        return False, "Error changing password"

def is_admin(username):
    """
    Check if user is an admin
    
    Args:
        username (str): Username
        
    Returns:
        bool: True if user is admin, False otherwise
    """
    user = get_user_by_username(username)
    return user is not None and user.get("role") == "admin"

def is_staff(username):
    """
    Check if user is staff
    
    Args:
        username (str): Username
        
    Returns:
        bool: True if user is staff, False otherwise
    """
    user = get_user_by_username(username)
    return user is not None and user.get("role") in ["admin", "staff"]