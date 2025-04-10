# app/callbacks/direct_button_callbacks.py - FIXED VERSION

import dash
from dash import Input, Output, State, callback_context, html, dcc, no_update, ALL
import dash_bootstrap_components as dbc
import json
import time
import uuid

def register_callbacks(app, socketio):
    """
    Register direct button callbacks for quick actions
    
    Args:
        app: Dash application instance
        socketio: SocketIO instance for real-time communication
    """
    # Map buttons to messages
    button_message_map = {
        'quick-order-btn': 'I\'d like to place an order',
        'quick-track-btn': 'Track my order',
        'quick-popular-btn': 'What are your popular items?',
        'quick-hours-btn': 'What are your operating hours?',
        'faq-menu-btn': 'Show me the menu',
        'faq-hours-btn': 'When are you open?',
        'faq-robot-btn': 'How does robot delivery work?',
        'faq-popular-btn': "What\'s your most popular coffee?",
        'menu-faq-btn': 'Show me the menu',
        'hours-faq-btn': 'When are you open?',
        'robot-faq-btn': 'How does robot delivery work?',
        'popular-faq-btn': "What\'s your most popular coffee?"
    }
    
    # Create a list of all button IDs
    button_ids = list(button_message_map.keys())
    
    # Create a single callback that handles all buttons
    @app.callback(
        Output('direct-message-status', 'children'),
        [Input(btn_id, 'n_clicks') for btn_id in button_ids],
        [State('floating-chat-panel', 'style')],
        prevent_initial_call=True
    )
    def handle_all_buttons(*args):
        """Handle all button clicks in a single callback"""
        # Get context to determine which button was clicked
        ctx = callback_context
        if not ctx.triggered:
            return no_update
            
        # Get the ID of the button that was clicked
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Get the panel style (last argument)
        panel_style = args[-1]
        
        # If the triggered ID is not in our map, return no update
        if triggered_id not in button_message_map:
            return no_update
            
        # Get the message for this button
        message = button_message_map[triggered_id]
        
        # Check if chat panel is currently hidden
        is_panel_hidden = not panel_style or panel_style.get('display') == 'none'
        
        # Create a session ID
        session_id = str(uuid.uuid4())
        
        # Use socketio for reliable communication (no API call)
        try:
            # First make sure panel is open
            if is_panel_hidden:
                socketio.emit('open_chat_panel', {'message_sent': message})
            
            # Send the message via socketio directly
            socketio.emit('chat_message_from_dashboard', {
                'message': message,
                'session_id': session_id
            })
            
            print(f"Message sent via socket.io: {message}")
            
            # Also add client-side handling for redundancy
            add_client_js(app, message)
            
            return message
        except Exception as e:
            print(f"Error sending message via socket.io: {e}")
            
            # Try client-side method as backup
            add_client_js(app, message)
            
            return f"Error sending message: {str(e)}"
    
    # Special case for voice toggle button
    @app.callback(
        Output('voice-status', 'children'),
        [Input('voice-toggle-btn', 'n_clicks')],
        prevent_initial_call=True
    )
    def toggle_voice(n_clicks):
        """Handle voice toggle button"""
        if not n_clicks:
            return no_update
        
        # Emit socket event for voice toggle
        try:
            socketio.emit('toggle_voice_mode', {
                'enabled': True  # Toggle to enabled state
            })
            return "Voice toggled"
        except Exception as e:
            print(f"Error toggling voice: {e}")
            return "Voice toggle failed"

def add_client_js(app, message):
    """Add client-side callback for redundant message delivery"""
    js_code = f'''
    (function() {{
        console.log("Client-side message handler activated");
        
        // Function to try all message sending methods
        function trySendingMessage() {{
            const message = "{message}";
            let sent = false;
            
            // Make sure chat panel is visible
            if (document.getElementById('floating-chat-panel')) {{
                document.getElementById('floating-chat-panel').style.display = 'flex';
                document.getElementById('floating-chat-panel').className = 'floating-chat-panel';
            }}
            
            // Method 1: Using sendDirectMessageToChainlit if available
            if (window.sendDirectMessageToChainlit) {{
                try {{
                    window.sendDirectMessageToChainlit(message);
                    console.log("Sent via sendDirectMessageToChainlit");
                    sent = true;
                }} catch(e) {{
                    console.error("Error with sendDirectMessageToChainlit:", e);
                }}
            }}
            
            // Method 2: Using chatClient if available
            if (!sent && window.chatClient && window.chatClient.sendMessage) {{
                try {{
                    window.chatClient.sendMessage(message);
                    console.log("Sent via chatClient");
                    sent = true;
                }} catch(e) {{
                    console.error("Error with chatClient:", e);
                }}
            }}
            
            // Method 3: Direct postMessage to iframe
            if (!sent) {{
                try {{
                    const iframe = document.getElementById('floating-chainlit-frame');
                    if (iframe && iframe.contentWindow) {{
                        iframe.contentWindow.postMessage({{
                            type: 'userMessage',
                            message: message
                        }}, '*');
                        console.log("Sent via postMessage");
                        sent = true;
                    }}
                }} catch(e) {{
                    console.error("Error with postMessage:", e);
                }}
            }}
            
            return sent;
        }}
        
        // Try sending the message after a delay to ensure panel is visible
        setTimeout(trySendingMessage, 500);
    }})();
    '''
    
    # Create a temporary clientside callback
    app.clientside_callback(
        js_code,
        Output('direct-message-status', 'className', allow_duplicate=True),
        Input('direct-message-status', 'children'),
        prevent_initial_call=True
    )