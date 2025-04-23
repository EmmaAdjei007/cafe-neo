# File: app.py (Updated to remove eventlet patching)

import sys
import os

# Get Chainlit URL from environment variables or use default
CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8000')

from dash import Dash, dcc, html, Input, Output, State, callback_context
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
from app.layouts import register_order_update_callback
from app.config import config
from server import configure_server


import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log')
    ]
)

# Create logger
logger = logging.getLogger('neo_cafe')
logger.setLevel(logging.DEBUG)

# Add this after imports in both app.py and chainlit_app/app.py

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
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',  
    '/assets/css/styles.css',
    '/assets/css/floating_chat.css'  # Add floating chat CSS
]

external_scripts = [
    '/assets/js/chat_client.js',  # Add chat client JS
    'assets/js/direct_message_handler.js',  # Add direct message handler JS
    '/assets/js/chat_messenger.js',  # Add chat messenger JS
    '/assets/js/auth_bridge.js',  # Add auth bridge JS
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


# Add this JavaScript to the index_string for chat persistence
chat_persistence_js = '''
<script>
    // Chat state persistence
    window.addEventListener('DOMContentLoaded', function() {
        console.log("Setting up chat persistence");
        
        // Store chat state when navigating
        window.addEventListener('beforeunload', function(event) {
            // Only store if not actually leaving the site
            if (event.currentTarget.location.hostname === window.location.hostname) {
                const chatPanel = document.getElementById('floating-chat-panel');
                if (chatPanel) {
                    const isVisible = chatPanel.style.display !== 'none';
                    const isMinimized = chatPanel.className.includes('minimized');
                    const isExpanded = chatPanel.className.includes('expanded');
                    
                    localStorage.setItem('chat_visible', isVisible);
                    localStorage.setItem('chat_minimized', isMinimized);
                    localStorage.setItem('chat_expanded', isExpanded);
                    console.log(`Stored chat state: visible=${isVisible}, minimized=${isMinimized}, expanded=${isExpanded}`);
                }
            }
        });
        
        // Restore chat state after navigation (with a slight delay)
        setTimeout(function() {
            try {
                const chatVisible = localStorage.getItem('chat_visible') === 'true';
                const chatMinimized = localStorage.getItem('chat_minimized') === 'true';
                const chatExpanded = localStorage.getItem('chat_expanded') === 'true';
                
                console.log(`Restoring chat state: visible=${chatVisible}, minimized=${chatMinimized}, expanded=${chatExpanded}`);
                
                const chatPanel = document.getElementById('floating-chat-panel');
                const chatButton = document.getElementById('floating-chat-button');
                
                if (chatPanel && chatVisible) {
                    chatPanel.style.display = 'flex';
                    
                    // Apply correct class
                    if (chatMinimized) {
                        chatPanel.className = 'floating-chat-panel minimized';
                    } else if (chatExpanded) {
                        chatPanel.className = 'floating-chat-panel expanded';
                        // Also show FAQ section if expanded
                        const faqSection = document.getElementById('chat-faq-section');
                        if (faqSection) faqSection.style.display = 'block';
                    } else {
                        chatPanel.className = 'floating-chat-panel';
                    }
                }
            } catch (e) {
                console.error("Error restoring chat state:", e);
            }
        }, 500);
    });
</script>
'''

# Update the app.index_string to include the persistence JS
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
        ''' + chat_persistence_js + '''
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
register_order_update_callback(app)
register_all_callbacks(app, socketio)


# This is now handled by run_with_eventlet.py
if __name__ == '__main__':
    import sys
    try:
        port = int(os.environ.get('PORT', 8050))
        debug = os.environ.get('DEBUG', 'True').lower() == 'true'
        
        logger.info(f"Starting Neo Cafe Dashboard on port {port} (debug={debug})")
        logger.info("Visit http://localhost:8050 in your browser")
        logger.info("For better Socket.IO performance, run using 'python run_with_eventlet.py' instead")
        
        # Fallback to using the Dash run method when run directly
        app.run(debug=debug, port=port)
    except Exception as e:
        print(f"ERROR: Failed to start the application: {e}")
        import traceback
        traceback.print_exc(file=sys.stdout)   