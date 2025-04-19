#!/usr/bin/env python3
# Debug helper script (debug_neocafe.py)
# Run this script to check for common integration issues

import os
import sys
import json
import sqlite3
import requests
import logging
import traceback
import importlib.util
import base64
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_results.log')
    ]
)

logger = logging.getLogger('debug_neocafe')

# Constants
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:8050')
CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8000')
DB_PATH = os.environ.get('DB_PATH', 'neo_cafe.db')

def banner(text):
    """Print a banner with the given text."""
    width = 80
    print("\n" + "=" * width)
    print(f"{text.center(width)}")
    print("=" * width + "\n")

def check_imports():
    """Check for required imports."""
    banner("CHECKING IMPORTS")
    
    required_packages = [
        "dash", "dash_bootstrap_components", "flask", "flask_socketio", 
        "plotly", "pandas", "numpy", "requests", "dotenv", "chainlit", 
        "langchain", "openai", "tiktoken"
    ]
    
    for package in required_packages:
        try:
            spec = importlib.util.find_spec(package)
            if spec is not None:
                print(f"✅ {package} is installed")
            else:
                print(f"❌ {package} is NOT installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")

def check_files():
    """Check if key files exist."""
    banner("CHECKING FILES")
    
    key_files = [
        "app.py",
        "server.py",
        "app/callbacks/chat_callbacks.py",
        "app/callbacks/order_callbacks.py",
        "app/callbacks/auth_callbacks.py",
        "app/layouts/__init__.py",
        "chainlit_app/app.py",
        "chainlit_app/states.py"
    ]
    
    for file_path in key_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} MISSING")

def check_database():
    """Check database configuration."""
    banner("CHECKING DATABASE")
    
    # Check if database file exists
    if os.path.exists(DB_PATH):
        print(f"✅ Database file exists: {DB_PATH}")
        
        # Check table structure
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Get all tables
            c.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = c.fetchall()
            
            if tables:
                print("✅ Database contains tables:")
                for table in tables:
                    print(f"  - {table[0]}")
                    
                    # Get table schema
                    c.execute(f"PRAGMA table_info({table[0]})")
                    columns = c.fetchall()
                    print(f"    Columns: {', '.join(col[1] for col in columns)}")
                    
                    # Get row count
                    c.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = c.fetchone()[0]
                    print(f"    Rows: {count}")
            else:
                print("❌ Database exists but contains no tables")
                
            conn.close()
            
        except Exception as e:
            print(f"❌ Error accessing database: {e}")
    else:
        print(f"❌ Database file does not exist: {DB_PATH}")

def check_environment():
    """Check environment variables."""
    banner("CHECKING ENVIRONMENT")
    
    required_vars = [
        "FLASK_SECRET_KEY",
        "OPENAI_API_KEY",
        "DASHBOARD_URL",
        "CHAINLIT_URL"
    ]
    
    for var in required_vars:
        value = os.environ.get(var, "NOT SET")
        
        if value != "NOT SET":
            # Mask API keys
            if "API_KEY" in var:
                masked_value = value[:4] + "..." + value[-4:]
                print(f"✅ {var} is set: {masked_value}")
            else:
                print(f"✅ {var} is set: {value}")
        else:
            print(f"❌ {var} is NOT set")

def test_auth_flow():
    """Test the authentication flow between Dash and Chainlit."""
    banner("TESTING AUTH FLOW")
    
    # Create a test user
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "id": "1234",
        "role": "customer"
    }
    
    print("1. Creating auth token...")
    
    # Create a token in the same way as the app
    try:
        auth_token = base64.b64encode(json.dumps(test_user).encode()).decode()
        print(f"✅ Created auth token: {auth_token[:10]}...")
        
        # Simulate token verification in Chainlit
        print("\n2. Testing token verification...")
        
        try:
            # Import the token verification function
            sys.path.append('.')
            from chainlit_app.app import verify_auth_token
            user_id, is_authenticated, user_data = verify_auth_token(auth_token)
            
            if is_authenticated and user_id == test_user["username"]:
                print(f"✅ Token verification successful: user_id={user_id}, authenticated={is_authenticated}")
                print(f"✅ User data: {user_data}")
            else:
                print(f"❌ Token verification failed: user_id={user_id}, authenticated={is_authenticated}")
                print(f"❌ User data: {user_data}")
        except Exception as e:
            print(f"❌ Error importing/calling verify_auth_token: {e}")
            print(traceback.format_exc())
        
    except Exception as e:
        print(f"❌ Error creating auth token: {e}")

def test_order_flow():
    """Test the order flow between Chainlit and Dash."""
    banner("TESTING ORDER FLOW")
    
    # Create a test order
    test_order = {
        "id": "ORD-TEST12345",
        "user_id": "testuser",
        "username": "testuser",
        "items": [
            {"item_id": 1, "quantity": 1, "special_instructions": ""},
            {"item_id": 2, "quantity": 2, "special_instructions": ""}
        ],
        "delivery_location": "Table 3",
        "total": 11.95,
        "timestamp": "2025-04-18T12:00:00",
        "status": "New"
    }
    
    print("1. Testing order file creation...")
    
    # Test file saving
    try:
        os.makedirs('order_data', exist_ok=True)
        with open(f"order_data/order_{test_order['id']}.json", 'w') as f:
            json.dump(test_order, f)
        
        print(f"✅ Saved order to file: order_{test_order['id']}.json")
        
        # Check if file was created
        if os.path.exists(f"order_data/order_{test_order['id']}.json"):
            print("✅ Order file exists")
            
            # Read file back
            with open(f"order_data/order_{test_order['id']}.json", 'r') as f:
                loaded_order = json.load(f)
            
            if loaded_order["id"] == test_order["id"]:
                print("✅ Order data loaded correctly")
            else:
                print("❌ Order data does not match")
        else:
            print("❌ Order file was not created")
        
    except Exception as e:
        print(f"❌ Error creating order file: {e}")
    
    # Test database saving
    print("\n2. Testing order database insertion...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_history';")
        if c.fetchone():
            # Insert test order
            c.execute('''INSERT OR REPLACE INTO order_history 
                         (order_id, user_id, items, status, created_at)
                         VALUES (?, ?, ?, ?, ?)''',
                     (test_order["id"], 
                      test_order["user_id"], 
                      json.dumps(test_order["items"]), 
                      test_order["status"], 
                      test_order["timestamp"]))
            conn.commit()
            print("✅ Order inserted into database")
            
            # Verify insertion
            c.execute('SELECT * FROM order_history WHERE order_id = ?', (test_order["id"],))
            result = c.fetchone()
            
            if result:
                print("✅ Order found in database")
            else:
                print("❌ Order not found in database after insertion")
        else:
            print("❌ order_history table does not exist")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error with database operations: {e}")
        print(traceback.format_exc())

def test_menu_data():
    """Test menu data loading."""
    banner("TESTING MENU DATA")
    
    menu_paths = [
        "app/data/seed_data/menu.json",
        "data/menu.json",
        "chainlit_app/data/menu.json"
    ]
    
    found = False
    
    for path in menu_paths:
        if os.path.exists(path):
            print(f"✅ Menu file found: {path}")
            found = True
            
            # Try to load the file
            try:
                with open(path, 'r') as f:
                    menu_data = json.load(f)
                
                print(f"✅ Menu file loaded successfully with {len(menu_data)} items")
                
                # Check a few menu items
                if len(menu_data) > 0:
                    print("\nSample menu items:")
                    for i, item in enumerate(menu_data[:3]):
                        print(f"  - {item.get('name', 'Unknown')}: ${item.get('price', 0)}")
            except Exception as e:
                print(f"❌ Error loading menu file: {e}")
        else:
            print(f"❌ Menu file not found: {path}")
    
    if not found:
        print("❌ No menu files found in any of the expected locations")

def print_summary():
    """Print a summary of the debug results."""
    banner("DEBUG SUMMARY")
    
    print("Debug checks complete. Please check the logs above for any issues.")
    print("\nCommon issues and fixes:")
    print("1. Missing imports - Install with pip: pip install -r requirements.txt")
    print("2. Missing files - Ensure all code is in the correct location")
    print("3. Database issues - Make sure the database path is correct")
    print("4. Authentication flow - Check the token encoding/decoding")
    print("5. Order flow - Check file permissions and database access")
    
    print("\nIf problems persist, check the following:")
    print("- Restart both the Dash app and Chainlit")
    print("- Clear browser cache and cookies")
    print("- Check browser console for JavaScript errors")
    print("- Verify network connections in browser DevTools")

if __name__ == "__main__":
    banner("NEO CAFE DEBUG UTILITY")
    print("This script checks for common integration issues between Dash and Chainlit\n")
    
    check_imports()
    check_files()
    check_environment()
    check_database()
    test_auth_flow()
    test_menu_data()
    test_order_flow()
    print_summary()