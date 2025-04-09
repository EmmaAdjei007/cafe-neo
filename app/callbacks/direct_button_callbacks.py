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
        
        # Send message via bridge
        try:
            # Use MessageBridge if available
            result = MessageBridge.send_message(message, session_id)
            print(f"Message sent via bridge: {message}")
        except Exception as e:
            print(f"Error sending message via bridge: {e}")
            result = {"status": "error", "error": str(e)}
            
            # Fallback to socket.io directly
            try:
                # Emit directly to socket.io
                socketio.emit('chat_message_from_dashboard', {
                    'message': message,
                    'session_id': session_id
                })
                print(f"Message sent via socket.io: {message}")
                result = {"status": "success", "method": "socket.io"}
            except Exception as socket_err:
                print(f"Error sending via socket.io: {socket_err}")
        
        # Emit socket event to trigger panel opening if needed
        if is_panel_hidden:
            # Tell the client to open the chat panel
            socketio.emit('open_chat_panel', {'message_sent': message})
            print(f"Emitted open_chat_panel event")
        
        # Also emit a chat message event for redundancy
        socketio.emit('chat_message_from_dashboard', {
            'message': message,
            'session_id': session_id
        })
        
        # Return status (hidden element)
        return json.dumps({
            'button': triggered_id,
            'message': message,
            'status': result.get('status', 'unknown'),
            'timestamp': time.time()
        })
    
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
        socketio.emit('toggle_voice_mode', {
            'enabled': True  # Toggle to enabled state
        })
        
        return "Voice toggled"