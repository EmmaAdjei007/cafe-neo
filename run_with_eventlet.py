# File: run_with_eventlet.py

"""
Runner script that ensures eventlet monkey patching happens before importing any other modules.
This resolves the issue with monkey patching that occurs when doing it later in the app initialization.
"""

# Apply eventlet monkey patch FIRST - before ANY other imports
import eventlet
eventlet.monkey_patch()

# Now import the rest of the modules
import os
import sys
import importlib.util

def run_app():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Import app.py as a module without executing it
    spec = importlib.util.spec_from_file_location("main_app", os.path.join(current_dir, "app.py"))
    main_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_app)
    
    # Now we have access to server and socketio from the app.py module
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"Starting Neo Cafe Dashboard on port {port} (debug={debug})")
    print("Visit http://localhost:8050 in your browser")
    
    # Use socketio.run with the Flask server
    main_app.socketio.run(main_app.server, debug=debug, port=port, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_app()