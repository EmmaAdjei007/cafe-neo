# File: app/callbacks/chat_callbacks.py (SocketIO Update)
import dash
from dash import Input, Output, State, callback_context, html, dcc, ALL
import dash_bootstrap_components as dbc
import json
import urllib.parse
from flask import session
import logging
import os
import sys
import requests
import time
from datetime import datetime
from app.utils.api_utils import get_chainlit_session

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

# Base URLs for APIs
CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8001')

def register_callbacks(app, socketio):
    """
    Register callbacks for the chat interface
    
    Args:
        app: Dash application instance
        socketio: SocketIO instance for real-time communication
    """
    @app.callback(
    Output('chat-message-listener', 'children', allow_duplicate=True),
    [Input('socket-chat-update', 'children')],
    prevent_initial_call=True
)
    def update_chat_listener_from_socket(socket_data):
        """Update the chat message listener when socket data is received"""
        if socket_data:
            # Just pass through the socket data
            return socket_data
        return dash.no_update

    # Updated callback function for toggle_chat_panel in app/callbacks/chat_callbacks.py

    @app.callback(
        [
            Output('floating-chat-panel', 'style'),
            Output('floating-chat-panel', 'className'),
            Output('chat-faq-section', 'style')
        ],
        [
            Input('floating-chat-button', 'n_clicks'),
            Input('close-chat-button', 'n_clicks'),
            Input('minimize-chat-button', 'n_clicks'),
            Input('expand-chat-button', 'n_clicks'),  # Added input for expand button
            Input('floating-chat-socket-update', 'data-open-chat')
        ],
        [
            State('floating-chat-panel', 'style'),
            State('floating-chat-panel', 'className'),
            State('chat-faq-section', 'style')
        ]
    )
    def toggle_chat_panel(open_clicks, close_clicks, minimize_clicks, expand_clicks, open_chat_data,
                        current_style, current_class, faq_style):
        """Toggle the floating chat panel visibility and state"""
        ctx = callback_context
        
        if not ctx.triggered:
            return current_style or {"display": "none"}, current_class, faq_style or {"display": "none"}
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Default styles for different states
        visible_style = {"display": "flex"}  # Full panel
        hidden_style = {"display": "none"}   # Hidden panel
        
        # Current display state
        current_display = current_style.get("display", "none") if current_style else "none"
        
        # Check if panel is minimized or expanded
        is_minimized = "minimized" in current_class if current_class else False
        is_expanded = "expanded" in current_class if current_class else False
        
        base_class = "floating-chat-panel"
        minimized_class = f"{base_class} minimized"
        expanded_class = f"{base_class} expanded"
        
        # FAQ section visibility
        show_faq = {"display": "block"}
        hide_faq = {"display": "none"}
        
        # Socket.IO triggered open
        if button_id == 'floating-chat-socket-update' and open_chat_data:
            # Socket.IO is requesting to open the chat
            return visible_style, base_class, hide_faq
        
        # Handle buttons for different states
        if button_id == "floating-chat-button":
            # If panel is hidden, show it
            if current_display == "none":
                return visible_style, base_class, hide_faq
            # Otherwise toggle to hide it (better UX)
            else:
                return hidden_style, base_class, hide_faq
                
        elif button_id == "close-chat-button":
            # Always hide the panel completely
            return hidden_style, base_class, hide_faq
            
        elif button_id == "minimize-chat-button":
            # If already minimized, restore to normal
            if is_minimized:
                return visible_style, base_class, hide_faq
            # Otherwise minimize it
            else:
                return visible_style, minimized_class, hide_faq
                
        elif button_id == "expand-chat-button":
            # If already expanded, restore to normal
            if is_expanded:
                return visible_style, base_class, hide_faq
            # Otherwise expand it
            else:
                return visible_style, expanded_class, show_faq
                
        # Default: no change
        return current_style or hidden_style, current_class or base_class, faq_style or hide_faq
    
    # Set Chainlit iframe source when panel becomes visible
    # Fix for authentication passing in app/callbacks/chat_callbacks.py
        # Find this function and replace it with the below:
    @app.callback(
        Output('floating-chainlit-frame', 'src'),
        [
            Input('floating-chat-panel', 'style'),
            Input('url', 'pathname')
        ],
        [State('user-store', 'data'), 
        State('floating-chainlit-frame', 'src')]  # Added src state to preserve URL during navigation
    )
    def update_floating_chat_frame(panel_style, pathname, user_data, current_src):
        """Update the Chainlit iframe source with correct parameters"""
        ctx = callback_context
        trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        
        # Only update if panel is being shown for the first time or we've changed pages
        # If it's just a page change and the panel isn't visible, don't update
        if not panel_style or panel_style.get("display") == "none":
            if trigger == 'url':
                return dash.no_update  # Don't update on page change if panel is hidden
            
        # If we already have a URL and this is a page navigation, keep most parameters
        if current_src and trigger == 'url':
            # Parse the current URL to keep the session ID and authentication
            parts = urllib.parse.urlparse(current_src)
            query_params = dict(urllib.parse.parse_qsl(parts.query))
            
            # We only update the tab parameter based on the new pathname
            if pathname == '/menu':
                query_params['tab'] = 'menu'
            elif pathname == '/orders':
                query_params['tab'] = 'order'
            elif pathname == '/delivery':
                query_params['tab'] = 'status'
            elif pathname == '/dashboard':
                query_params['tab'] = 'dashboard'
            elif pathname == '/profile':
                query_params['tab'] = 'profile'
            else:
                query_params['tab'] = 'home'
                
            # Rebuild the URL with the updated tab
            url = f"{CHAINLIT_URL}?{urllib.parse.urlencode(query_params)}"
            return url
        
        # For new iframe creation (first open or complete refresh)
        query_params = {}
        
        # Add floating flag
        query_params['floating'] = 'true'
        
        # Set tab based on current page
        if pathname == '/menu':
            query_params['tab'] = 'menu'
        elif pathname == '/orders':
            query_params['tab'] = 'order'
        elif pathname == '/delivery':
            query_params['tab'] = 'status'
        elif pathname == '/dashboard':
            query_params['tab'] = 'dashboard'
        elif pathname == '/profile':
            query_params['tab'] = 'profile'
        else:
            query_params['tab'] = 'home'
        
        # Enhanced user info
        if user_data and 'username' in user_data:
            query_params['user'] = user_data['username']
            
            # Create a more robust authentication token with user details
            auth_data = {
                "username": user_data['username'],
                "id": user_data.get('id', ''),
                "role": user_data.get('role', 'customer'),
                "email": user_data.get('email', '')
            }
            
            # JSON encode and base64 the token for security
            import base64
            auth_token = base64.b64encode(json.dumps(auth_data).encode()).decode()
            query_params['token'] = auth_token
            
            # If user has active order, add order ID
            if 'active_order' in user_data and user_data['active_order']:
                if isinstance(user_data['active_order'], dict) and 'id' in user_data['active_order']:
                    query_params['order_id'] = user_data['active_order']['id']
        
        # Add session ID if available
        if 'session_id' in session:
            query_params['session_id'] = session['session_id']
        else:
            # Create a new session ID
            session_id = get_chainlit_session()
            session['session_id'] = session_id
            query_params['session_id'] = session_id
        
        # Add timestamp to prevent caching
        query_params['t'] = str(int(time.time()))
        
        # Build query string
        query_string = urllib.parse.urlencode(query_params)
        
        # Build full URL
        if query_string:
            return f"{CHAINLIT_URL}?{query_string}"
        else:
            return CHAINLIT_URL
    
    @app.callback(
        Output('chat-action-trigger', 'children'),
        [
            Input('quick-order-btn', 'n_clicks'),
            Input('quick-track-btn', 'n_clicks'),
            Input('quick-popular-btn', 'n_clicks'),
            Input('quick-hours-btn', 'n_clicks'),
            Input('faq-menu-btn', 'n_clicks'),
            Input('faq-hours-btn', 'n_clicks'),
            Input('faq-robot-btn', 'n_clicks'),
            Input('faq-popular-btn', 'n_clicks'),
            Input('menu-faq-btn', 'n_clicks'),
            Input('hours-faq-btn', 'n_clicks'),
            Input('robot-faq-btn', 'n_clicks'),
            Input('popular-faq-btn', 'n_clicks'),
            Input('voice-toggle-btn', 'n_clicks')
        ],
        [State('chat-state-store', 'data')]
    )
    def handle_quick_actions(order_clicks, track_clicks, popular_clicks, hours_clicks, 
                             faq_menu_clicks, faq_hours_clicks, faq_robot_clicks, faq_popular_clicks,
                             menu_faq_clicks, hours_faq_clicks, robot_faq_clicks, popular_faq_clicks,
                             voice_clicks, chat_state):
        """Handle quick action button clicks to send commands to Chainlit"""
        ctx = callback_context
        
        if not ctx.triggered:
            return None
        
        # Get the ID of the button that was clicked
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Map buttons to messages for the chatbot
        message_map = {
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
            'popular-faq-btn': "What\'s your most popular coffee?",
            'voice-toggle-btn': 'Toggle voice mode'
        }
        
        if button_id in message_map:
            # Get the message for this button
            message = message_map[button_id]
            
            # Create JavaScript to execute in the client
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
                Output('chat-action-trigger', 'className', allow_duplicate=True),
                Input('chat-action-trigger', 'children'),
                prevent_initial_call=True
            )
            
            # Get or create session ID
            session_id = session.get('session_id')
            if not session_id:
                session_id = get_chainlit_session()
                session['session_id'] = session_id
            
            # Send message to Chainlit via SocketIO (server-side)
            try:
                socketio.emit('send_chat_message', {
                    'message': message,
                    'session_id': session_id
                })
                print(f"Message sent to Chainlit via SocketIO: {message}")
            except Exception as e:
                print(f"Error sending message to Chainlit via SocketIO: {e}")
            
            # Return the message as confirmation
            return message
        
        return None
    
    # Add this improved callback to app/callbacks/chat_callbacks.py

    @app.callback(
    Output('current-order-status', 'children'),
    [
        Input('refresh-order-btn', 'n_clicks'),
        Input('status-update-interval', 'n_intervals'),
        Input('socket-order-update', 'children')  # Added input to listen for order updates from Socket.IO
    ],
    [State('user-store', 'data')]
)
    def update_order_status(n_clicks, n_intervals, socket_update, user_data):
        """Update the current order status display"""
        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        
        # Default content for no active orders
        no_order_content = html.P("No active order.", className="text-muted")
        
        # Get active order from different sources depending on what triggered the callback
        active_order = None
        
        # If triggered by socket update, try to parse the order data
        if triggered_id == 'socket-order-update' and socket_update:
            try:
                # Parse the socket data
                order_data = json.loads(socket_update)
                
                # Check if it's a valid order update
                if isinstance(order_data, dict) and 'id' in order_data:
                    active_order = order_data
                    
                    # If user is logged in, update their active order in user_store
                    if user_data:
                        # This would need to be handled by a separate callback that updates user-store
                        print(f"Socket update received for order: {order_data['id']}")
            except Exception as e:
                print(f"Error parsing order socket data: {e}")
        
        # If no active order from socket, check user data
        if not active_order and user_data and 'active_order' in user_data:
            active_order = user_data.get('active_order')
        
        # If still no active order, check the most recent order in the database
        if not active_order:
            try:
                # This would be a function to get the most recent order from your data storage
                # For demo purposes, we're just returning None
                from app.data.database import get_orders
                orders = get_orders()
                if orders:
                    # Get the most recent order (assuming they're ordered by date)
                    active_order = orders[0]
            except Exception as e:
                print(f"Error getting recent orders: {e}")
        
        # If after all attempts, we still don't have an order, return the default content
        if not active_order:
            return no_order_content
        
        # Now we know active_order exists, let's create the order status content
        # Create order status content
        order_content = [
            html.H6(f"Order #{active_order['id']}", className="card-subtitle mb-2"),
            html.P([
                html.Strong("Status: "),
                html.Span(active_order.get('status', 'New'), className=f"text-{get_status_color(active_order.get('status', 'New'))}")
            ]),
            
            # Show items if available
            html.P([
                html.Strong("Items: "),
                html.Span(
                    f"{len(active_order.get('items', []))} items" if 'items' in active_order else "Items not available"
                )
            ]),
            
            # Show total if available
            html.P([
                html.Strong("Total: "),
                html.Span(f"${active_order.get('total', 0):.2f}")
            ]),
            
            # Show delivery location if available
            html.P([
                html.Strong("Delivery: "),
                html.Span(active_order.get('delivery_location', 'Not specified'))
            ]),
            
            # Button to view details
            dbc.Button(
                "View Details",
                id="view-order-details-btn",
                color="primary",
                size="sm",
                className="mt-2"
            )
        ]
        
        return order_content
        
    # Listen for navigation messages from Chainlit
    @app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        [Input('chat-message-listener', 'children')],
        prevent_initial_call=True
    )
    def handle_chat_navigation(message_data):
        """Handle navigation messages from Chainlit"""
        if not message_data:
            return dash.no_update
        
        try:
            # Parse the message data
            data = json.loads(message_data)
            
            # Check if it's a navigation message
            if data.get('type') == 'navigation':
                destination = data.get('destination')
                
                # Map destination to URL
                url_map = {
                    'menu': '/menu',
                    'orders': '/orders',
                    'order': '/orders',
                    'delivery': '/delivery',
                    'profile': '/profile',
                    'dashboard': '/dashboard',
                    'home': '/'
                }
                
                # Navigate to the appropriate URL
                if destination in url_map:
                    return url_map[destination]
            
            # Not a navigation message
            return dash.no_update
            
        except Exception as e:
            print(f"Error handling chat navigation: {e}")
            return dash.no_update

    # Set up a callback to handle open_floating_chat events
    @app.callback(
        Output('socket-chat-update', 'data-open-chat'),
        [Input('socket-chat-update', 'data')],
        prevent_initial_call=True
    )
    def handle_open_chat_event(data):
        """Handle open chat events from Socket.IO"""
        if data:
            try:
                parsed_data = json.loads(data)
                if parsed_data.get('type') == 'open_chat':
                    return True
            except Exception as e:
                print(f"Error parsing socket data: {e}")
        
        return dash.no_update
    
    

    


# Helper function for order status colors
# Helper function for order status colors
def get_status_color(status):
    """Get appropriate Bootstrap color class for order status"""
    status_lower = status.lower() if status else ""
    if status_lower == 'completed' or status_lower == 'delivered':
        return 'success'
    elif status_lower == 'in progress' or status_lower == 'preparing':
        return 'primary'
    elif status_lower == 'ready':
        return 'info'
    elif status_lower == 'cancelled':
        return 'danger'
    else:
        return 'secondary'