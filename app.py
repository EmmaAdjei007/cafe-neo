# File: app.py (Main Application Entry Point)

import sys
import os
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app components
from app.layouts import create_main_layout
from app.callbacks import register_all_callbacks
from app.config import config

# Get Chainlit URL from environment variables or use default
CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8001')

# Initialize Flask and SocketIO
server = Flask(__name__, 
               static_folder='assets',
               static_url_path='/assets')
server.secret_key = os.environ.get('FLASK_SECRET_KEY', config['flask_secret_key'])
socketio = SocketIO(server, cors_allowed_origins="*")

# Initialize Dash with a coffee-themed bootstrap
app = Dash(__name__, 
           server=server, 
           external_stylesheets=[dbc.themes.BOOTSTRAP, '/assets/styles.css'],
           suppress_callback_exceptions=True,
           meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
           assets_folder='assets')

app.title = "Neo Cafe - Give me coffee or give me death"

# Custom index string to inject environment variables for JavaScript
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script>
            // Inject environment variables for JavaScript
            window.CHAINLIT_URL = "''' + CHAINLIT_URL + '''";
        </script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Set the main layout
app.layout = create_main_layout()

# Register all callbacks
register_all_callbacks(app, socketio)

# Run the server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"Starting Neo Cafe Dashboard on port {port} (debug={debug})")
    print("Visit http://localhost:8050 in your browser")
    
    # Use Dash's run method first
    try:
        app.run(debug=debug, port=port)
    except Exception as e:
        print(f"Error running with app.run_server: {e}")
        print("Falling back to socketio.run...")
        socketio.run(server, debug=debug, port=port, allow_unsafe_werkzeug=True)