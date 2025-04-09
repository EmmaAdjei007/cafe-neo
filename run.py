# File: run.py

"""
Main entry point for the Neo Cafe application
This script starts both the Dash app and Chainlit chatbot
"""
import subprocess
import threading
import time
import os
import signal
import sys

# Set different ports for Dash and Chainlit
DASH_PORT = 8050
CHAINLIT_PORT = 8000

# Set environment variables for communication
os.environ['CHAINLIT_URL'] = f'http://localhost:{CHAINLIT_PORT}'
os.environ['DASHBOARD_URL'] = f'http://localhost:{DASH_PORT}'

def run_dash():
    """Run the Dash application"""
    print(f"Starting Dash application on port {DASH_PORT}...")
    dash_process = subprocess.Popen(["python", "app.py"])
    return dash_process

def run_chainlit():
    """Run the Chainlit application"""
    print(f"Starting Chainlit application on port {CHAINLIT_PORT}...")
    os.chdir("chainlit_app")
    chainlit_process = subprocess.Popen(["chainlit", "run", "app.py", "--port", str(CHAINLIT_PORT)])
    os.chdir("..")
    return chainlit_process

def main():
    """Main function to run both applications"""
    # Start the Chainlit app
    chainlit_process = run_chainlit()
    
    # Wait for Chainlit to initialize
    print("Waiting for Chainlit to initialize...")
    time.sleep(5)
    
    # Start the Dash app
    dash_process = run_dash()
    
    # Setup signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down applications...")
        chainlit_process.terminate()
        dash_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Wait for processes to complete (they won't unless terminated)
    print("\nBoth applications are running!")
    print(f"Visit http://localhost:{DASH_PORT} for the Dash app")
    print(f"Visit http://localhost:{CHAINLIT_PORT} for the Chainlit app directly")
    print("\nPress Ctrl+C to stop both applications")
    
    try:
        while True:
            # Check if processes are still running
            if dash_process.poll() is not None:
                print("Dash application has stopped. Restarting...")
                dash_process = run_dash()
            
            if chainlit_process.poll() is not None:
                print("Chainlit application has stopped. Restarting...")
                chainlit_process = run_chainlit()
            
            time.sleep(5)
    except KeyboardInterrupt:
        # Handle Ctrl+C
        print("\nShutting down applications...")
        chainlit_process.terminate()
        dash_process.terminate()

if __name__ == "__main__":
    main()