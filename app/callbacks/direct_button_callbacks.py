# app/callbacks/direct_button_callbacks.py - FIXED VERSION

import dash
from dash import Input, Output, State, callback_context, html, dcc, no_update, ALL
import dash_bootstrap_components as dbc
from app.utils.message_bridge import MessageBridge
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
        
        # Create a JavaScript code to trigger the client-side message sending
        js_code = f'''
        if (document.getElementById('floating-chat-panel')) {{
            // Make sure the panel is visible
            document.getElementById('floating-chat-panel').style.display = 'flex';
            document.getElementById('floating-chat-panel').className = 'floating-chat-panel';
            
            // Wait a short while for the panel to be visible
            setTimeout(function() {{
                const message = "{message}";
                
                // Try using our direct message sender if available
                if (window.sendDirectMessageToChainlit) {{
                    console.log("Sending via sendDirectMessageToChainlit:", message);
                    window.sendDirectMessageToChainlit(message);
                }}
                
                // Also try using chatClient as a backup
                if (window.chatClient && window.chatClient.sendMessage) {{
                    console.log("Sending via chatClient:", message);
                    window.chatClient.sendMessage(message);
                }}
                
                // Also try direct postMessage to the iframe as a last resort
                try {{
                    const iframe = document.getElementById('floating-chainlit-frame');
                    if (iframe && iframe.contentWindow) {{
                        console.log("Sending via direct postMessage:", message);
                        iframe.contentWindow.postMessage({{
                            type: 'userMessage',
                            message: message
                        }}, '*');
                    }}
                }} catch(e) {{
                    console.error("Error sending via postMessage:", e);
                }}
            }}, 500);
        }}
        '''
        
        # Execute the JavaScript
        app.clientside_callback(
            js_code,
            Output('direct-message-status', 'className', allow_duplicate=True),
            Input('direct-message-status', 'children'),
            prevent_initial_call=True
        )
        
        # Attempt all methods to send the message
        methods_attempted = []
        
        # Method 1: Try via Socket.IO
        try:
            socketio.emit('chat_message_from_dashboard', {
                'message': message,
                'session_id': session_id
            })
            print(f"Message sent via socket.io: {message}")
            methods_attempted.append("socket.io")
        except Exception as e:
            print(f"Error sending via socket.io: {e}")
        
        # Method 2: Try via MessageBridge (file-based approach)
        try:
            result = MessageBridge.send_message(message, session_id)
            if result.get('status') == 'success':
                print(f"Message sent via bridge: {message}")
                methods_attempted.append("message_bridge")
        except Exception as e:
            print(f"Error sending via bridge: {e}")
        
        # Method 3: If panel is hidden, emit event to open it
        if is_panel_hidden:
            try:
                socketio.emit('open_chat_panel', {
                    'message_sent': message
                })
                methods_attempted.append("open_panel")
            except Exception as e:
                print(f"Error opening chat panel: {e}")
        
        # Return status as a string message
        return message
    
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