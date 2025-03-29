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

def run_dash():
    """Run the Dash application"""
    print("Starting Dash application...")
    dash_process = subprocess.Popen(["python", "app.py"])
    return dash_process

def run_chainlit():
    """Run the Chainlit application"""
    print("Starting Chainlit application...")
    os.chdir("chainlit_app")
    chainlit_process = subprocess.Popen(["chainlit", "run", "app.py", "--port", "8001"])
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
    print("Visit http://localhost:8050 for the Dash app")
    print("Visit http://localhost:8001 for the Chainlit app directly")
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