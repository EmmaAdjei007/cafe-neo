# File: app.py (Updated to remove eventlet patching)

import sys
import os
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app components
from app.layouts import create_main_layout
from app.callbacks import register_all_callbacks
from app.config import config
from server import configure_server

# Get Chainlit URL from environment variables or use default
CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8001')

# Initialize Flask and SocketIO with proper config
server = Flask(__name__, 
               static_folder='assets',
               static_url_path='/assets')
server.secret_key = os.environ.get('FLASK_SECRET_KEY', config['flask_secret_key'])

# Configure SocketIO with explicit CORS settings - don't specify async_mode here
socketio = SocketIO(
    server,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Initialize Dash with a coffee-themed bootstrap and additional CSS/JS
external_stylesheets = [
    dbc.themes.BOOTSTRAP, 
    '/assets/css/styles.css',
    '/assets/css/floating_chat.css'  # Add floating chat CSS
]

external_scripts = [
    '/assets/js/chat_client.js'  # Add chat client JS
]

app = Dash(__name__, 
           server=server, 
           external_stylesheets=external_stylesheets,
           external_scripts=external_scripts,
           suppress_callback_exceptions=True,
           meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
           assets_folder='assets')

app.title = "Neo Cafe - Give me coffee or give me death"

# Log initialization
logger.info("Initializing Neo Cafe Dashboard")
logger.info(f"Chainlit URL: {CHAINLIT_URL}")

# Custom index string to inject environment variables for JavaScript
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.4.1/socket.io.min.js"></script>
        <script>
            // Inject environment variables for JavaScript
            window.CHAINLIT_URL = "''' + CHAINLIT_URL + '''";
            window.DEBUG_MODE = true;
            console.log("Neo Cafe Dashboard Initializing...");
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

# Configure custom server routes
configure_server(server, socketio)

# Set the main layout
app.layout = create_main_layout()

# Register all callbacks
register_all_callbacks(app, socketio)

# This is now handled by run_with_eventlet.py
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting Neo Cafe Dashboard on port {port} (debug={debug})")
    logger.info("Visit http://localhost:8050 in your browser")
    logger.info("For better Socket.IO performance, run using 'python run_with_eventlet.py' instead")
    
    # Fallback to using the Dash run method when run directly
    app.run(debug=debug, port=port)