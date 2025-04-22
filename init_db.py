# File: init_db.py

"""
Initialize the shared database for Neo Cafe
"""
import sqlite3
import os
import sys

# Set up database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neo_cafe.db')

def init_shared_db():
    """
    Initialize the shared database with all required tables
    """
    print(f"Initializing shared database at: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create conversation tables
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (session_id TEXT PRIMARY KEY,
                  user_id TEXT,
                  created_at TIMESTAMP,
                  last_active TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT,
                  content TEXT,
                  is_user BOOLEAN,
                  timestamp TIMESTAMP)''')
    
    # Create order tables
    c.execute('''CREATE TABLE IF NOT EXISTS order_history
                 (order_id TEXT PRIMARY KEY,
                  user_id TEXT,
                  items TEXT,
                  status TEXT,
                  created_at TIMESTAMP)''')
    
    # Create user session table
    c.execute('''CREATE TABLE IF NOT EXISTS user_sessions
                 (user_id TEXT PRIMARY KEY,
                  username TEXT,
                  email TEXT,
                  first_name TEXT,
                  last_name TEXT,
                  token TEXT,
                  context TEXT,
                  last_active TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_shared_db()