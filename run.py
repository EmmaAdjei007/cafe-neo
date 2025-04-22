# File: run.py

"""
Main entry point for the Neo Cafe application using eventlet
This script starts both the Dash app and Chainlit chatbot with proper monkey patching
"""

# Apply eventlet monkey patch FIRST - before ANY other imports
import eventlet
eventlet.monkey_patch()

import subprocess
import threading
import time
import os
import signal
import sys
from eventlet.green import subprocess as green_subprocess

# Set different ports for Dash and Chainlit
DASH_PORT = 8050
CHAINLIT_PORT = 8000

# Set environment variables for communication
os.environ['CHAINLIT_URL'] = f'http://localhost:{CHAINLIT_PORT}'
os.environ['DASHBOARD_URL'] = f'http://localhost:{DASH_PORT}'
os.environ['DB_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'neo_cafe.db')
os.environ['EVENTLET_MONKEY_PATCH'] = 'True'

def init_database():
    """Initialize the shared database using eventlet green threads"""
    print("Initializing shared database...")
    try:
        # Run the init_db script with green subprocess
        process = green_subprocess.Popen(
            [sys.executable, "init_db.py"],
            stdout=green_subprocess.PIPE,
            stderr=green_subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            print("Database initialization complete")
        else:
            print(f"Database initialization failed: {stderr.decode()}")
    except Exception as e:
        print(f"Error initializing database: {e}")

def run_dash():
    """Run the Dash application using eventlet-compatible process"""
    print(f"Starting Dash application on port {DASH_PORT}...")
    return green_subprocess.Popen(
        [sys.executable, "app.py"],
        env=os.environ.copy()
    )

def run_chainlit():
    """Run the Chainlit application using eventlet-compatible process"""
    print(f"Starting Chainlit application on port {CHAINLIT_PORT}...")
    env = os.environ.copy()
    env['CHAINLIT_PORT'] = str(CHAINLIT_PORT)
    
    return green_subprocess.Popen(
        ["chainlit", "run", "app.py", "--port", str(CHAINLIT_PORT)],
        env=env,
        cwd="chainlit_app"
    )

def signal_handler(sig, frame):
    """Handle signals with eventlet-compatible shutdown"""
    print("\nShutting down applications...")
    try:
        if 'chainlit_process' in globals():
            chainlit_process.terminate()
        if 'dash_process' in globals():
            dash_process.terminate()
    except Exception as e:
        print(f"Error during shutdown: {e}")
    finally:
        sys.exit(0)

def main():
    """Main function to run both applications with eventlet"""
    # Initialize the database first
    init_database()
    
    # Start the applications
    global chainlit_process, dash_process
    chainlit_process = run_chainlit()
    dash_process = run_dash()
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\nBoth applications are running!")
    print(f"Visit http://localhost:{DASH_PORT} for the Dash app")
    print(f"Visit http://localhost:{CHAINLIT_PORT} for the Chainlit app directly")
    print("\nPress Ctrl+C to stop both applications")
    
    try:
        while True:
            # Use eventlet-friendly sleep
            eventlet.sleep(5)
            
            # Check process status
            if dash_process.poll() is not None:
                print("Dash application has stopped. Restarting...")
                dash_process = run_dash()
            
            if chainlit_process.poll() is not None:
                print("Chainlit application has stopped. Restarting...")
                chainlit_process = run_chainlit()
                
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()