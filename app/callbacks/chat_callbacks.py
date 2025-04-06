# # File: app/callbacks/chat_callbacks.py (Enhanced for floating chat)
# import dash
# from dash import Input, Output, State, callback_context, html, dcc, ALL
# import dash_bootstrap_components as dbc
# import json
# import urllib.parse
# from flask import session
# import os
# import requests
# from app.utils.api_utils import send_message_to_chainlit, get_chainlit_session

# # Base URLs for APIs
# CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8001')

# def register_callbacks(app, socketio):
#     """
#     Register callbacks for the chat interface
    
#     Args:
#         app: Dash application instance
#         socketio: SocketIO instance for real-time communication
#     """
#     # Floating chat panel toggle callbacks
#     @app.callback(
#         [
#             Output('floating-chat-panel', 'style'),
#             Output('floating-chat-panel', 'className'),
#             Output('chat-faq-section', 'style')
#         ],
#         [
#             Input('floating-chat-button', 'n_clicks'),
#             Input('close-chat-button', 'n_clicks'),
#             Input('minimize-chat-button', 'n_clicks')
#         ],
#         [
#             State('floating-chat-panel', 'style'),
#             State('floating-chat-panel', 'className'),
#             State('chat-faq-section', 'style')
#         ]
#     )
#     def toggle_chat_panel(open_clicks, close_clicks, minimize_clicks, 
#                          current_style, current_class, faq_style):
#         """Toggle the floating chat panel visibility and state"""
#         ctx = callback_context
        
#         if not ctx.triggered:
#             return current_style or {"display": "none"}, current_class, faq_style or {"display": "none"}
        
#         button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
#         # Default styles for different states
#         visible_style = {"display": "flex"}  # Full panel
#         hidden_style = {"display": "none"}   # Hidden panel
        
#         # Current display state
#         current_display = current_style.get("display", "none") if current_style else "none"
        
#         # Check if panel is minimized or expanded
#         is_minimized = "minimized" in current_class if current_class else False
#         is_expanded = "expanded" in current_class if current_class else False
        
#         base_class = "floating-chat-panel"
#         minimized_class = f"{base_class} minimized"
#         expanded_class = f"{base_class} expanded"
        
#         # FAQ section visibility
#         show_faq = {"display": "block"}
#         hide_faq = {"display": "none"}
        
#         if button_id == "floating-chat-button":
#             # If panel is hidden, show it
#             if current_display == "none":
#                 return visible_style, base_class, hide_faq
#             # If panel is visible but minimized, maximize it
#             elif is_minimized:
#                 return visible_style, base_class, hide_faq
#             # If panel is expanded, collapse it to normal
#             elif is_expanded:
#                 return visible_style, base_class, hide_faq
#             # If panel is normal, just hide it
#             else:
#                 return hidden_style, base_class, hide_faq
                
#         elif button_id == "close-chat-button":
#             # Always hide the panel
#             return hidden_style, base_class, hide_faq
            
#         elif button_id == "minimize-chat-button":
#             # Toggle between states: normal → minimized → expanded → normal
#             if is_minimized:
#                 # Minimized → Expanded
#                 return visible_style, expanded_class, show_faq
#             elif is_expanded:
#                 # Expanded → Normal
#                 return visible_style, base_class, hide_faq
#             else:
#                 # Normal → Minimized
#                 return visible_style, minimized_class, hide_faq
                
#         # Default: no change
#         return current_style or hidden_style, current_class or base_class, faq_style or hide_faq
    
#     # Set Chainlit iframe source when panel becomes visible
#     @app.callback(
#         Output('floating-chainlit-frame', 'src'),
#         [
#             Input('floating-chat-panel', 'style'),
#             Input('url', 'pathname')
#         ],
#         [State('user-store', 'data')]
#     )
#     def update_floating_chat_frame(panel_style, pathname, user_data):
#         """Update the Chainlit iframe source with correct parameters"""
#         # Only update if panel is being shown
#         if not panel_style or panel_style.get("display") == "none":
#             return dash.no_update
            
#         # Base Chainlit URL
#         chainlit_url = CHAINLIT_URL
        
#         # Default to empty query
#         query_params = {}
        
#         # Add floating flag to indicate this is the floating context
#         query_params['floating'] = 'true'
        
#         # Check if we're on a specific page and add appropriate parameters
#         if pathname == '/menu':
#             query_params['tab'] = 'menu'
#         elif pathname == '/orders':
#             query_params['tab'] = 'order'
#         elif pathname == '/delivery':
#             query_params['tab'] = 'status'
#         elif pathname == '/dashboard':
#             query_params['tab'] = 'dashboard'
#         elif pathname == '/profile':
#             query_params['tab'] = 'profile'
#         else:
#             query_params['tab'] = 'home'
        
#         # Add user info if available
#         if user_data and 'username' in user_data:
#             query_params['user'] = user_data['username']
            
#             # If user has active order, add order ID
#             if 'active_order' in user_data and user_data['active_order']:
#                 query_params['order_id'] = user_data['active_order']['id']
        
#         # Add session ID if available
#         if 'session_id' in session:
#             query_params['session_id'] = session['session_id']
#         else:
#             # Create a new session ID
#             session_id = get_chainlit_session()
#             session['session_id'] = session_id
#             query_params['session_id'] = session_id
        
#         # Build query string
#         query_string = urllib.parse.urlencode(query_params)
        
#         # Build full URL
#         if query_string:
#             return f"{chainlit_url}?{query_string}"
#         else:
#             return chainlit_url
    
#     @app.callback(
#         Output('chat-action-trigger', 'children'),
#         [
#             Input('quick-order-btn', 'n_clicks'),
#             Input('quick-track-btn', 'n_clicks'),
#             Input('quick-popular-btn', 'n_clicks'),
#             Input('quick-hours-btn', 'n_clicks'),
#             Input('faq-menu-btn', 'n_clicks'),
#             Input('faq-hours-btn', 'n_clicks'),
#             Input('faq-robot-btn', 'n_clicks'),
#             Input('faq-popular-btn', 'n_clicks'),
#             Input('menu-faq-btn', 'n_clicks'),
#             Input('hours-faq-btn', 'n_clicks'),
#             Input('robot-faq-btn', 'n_clicks'),
#             Input('popular-faq-btn', 'n_clicks'),
#             Input('voice-toggle-btn', 'n_clicks')
#         ],
#         [State('chat-state-store', 'data')]
#     )
#     def handle_quick_actions(order_clicks, track_clicks, popular_clicks, hours_clicks, 
#                              faq_menu_clicks, faq_hours_clicks, faq_robot_clicks, faq_popular_clicks,
#                              menu_faq_clicks, hours_faq_clicks, robot_faq_clicks, popular_faq_clicks,
#                              voice_clicks, chat_state):
#         """Handle quick action button clicks to send commands to Chainlit"""
#         ctx = callback_context
        
#         if not ctx.triggered:
#             return None
        
#         # Get the ID of the button that was clicked
#         button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
#         # Map buttons to messages for the chatbot
#         message_map = {
#             'quick-order-btn': 'I\'d like to place an order',
#             'quick-track-btn': 'Track my order',
#             'quick-popular-btn': 'What are your popular items?',
#             'quick-hours-btn': 'What are your operating hours?',
#             'faq-menu-btn': 'Show me the menu',
#             'faq-hours-btn': 'When are you open?',
#             'faq-robot-btn': 'How does robot delivery work?',
#             'faq-popular-btn': "What\'s your most popular coffee?",
#             'menu-faq-btn': 'Show me the menu',
#             'hours-faq-btn': 'When are you open?',
#             'robot-faq-btn': 'How does robot delivery work?',
#             'popular-faq-btn': "What\'s your most popular coffee?",
#             'voice-toggle-btn': 'Toggle voice mode'
#         }
        
#         if button_id in message_map:
#             # Get the message for this button
#             message = message_map[button_id]
            
#             # Get or create session ID
#             session_id = session.get('session_id')
#             if not session_id:
#                 session_id = get_chainlit_session()
#                 session['session_id'] = session_id
            
#             # Send message to Chainlit via SocketIO
#             socketio.emit('send_chat_message', {
#                 'message': message,
#                 'session_id': session_id
#             })
            
#             # Also send via API as backup
#             try:
#                 send_message_to_chainlit(message, session_id)
#             except Exception as e:
#                 print(f"Error sending message to Chainlit API: {e}")
            
#             # Return the message as confirmation
#             return message
        
#         return None
    
#     @app.callback(
#         Output('current-order-status', 'children'),
#         [
#             Input('refresh-order-btn', 'n_clicks'),
#             Input('status-update-interval', 'n_intervals')
#         ],
#         [State('user-store', 'data')]
#     )
#     def update_order_status(n_clicks, n_intervals, user_data):
#         """Update the current order status display"""
#         # Default content for no active orders
#         no_order_content = html.P("No active order.", className="text-muted")
        
#         # Check if user is logged in and has active order
#         if not user_data or 'active_order' not in user_data:
#             return no_order_content
        
#         active_order = user_data.get('active_order')
        
#         if not active_order:
#             return no_order_content
        
#         # Create order status content
#         order_content = [
#             html.H6(f"Order #{active_order['id']}", className="card-subtitle mb-2"),
#             html.P([
#                 html.Strong("Status: "),
#                 html.Span(active_order['status'], className=f"text-{get_status_color(active_order['status'])}")
#             ]),
#             html.P([
#                 html.Strong("Items: "),
#                 html.Span(f"{len(active_order['items'])} items")
#             ]),
#             html.P([
#                 html.Strong("Total: "),
#                 html.Span(f"${active_order['total']:.2f}")
#             ]),
#             html.P([
#                 html.Strong("Delivery: "),
#                 html.Span(active_order['delivery_location'])
#             ]),
#             dbc.Button(
#                 "View Details",
#                 id="view-order-details-btn",
#                 color="primary",
#                 size="sm",
#                 className="mt-2"
#             )
#         ]
        
#         return order_content
    
#     # Listen for navigation messages from Chainlit
#     @app.callback(
#         Output('url', 'pathname', allow_duplicate=True),
#         [Input('chat-message-listener', 'children')],
#         prevent_initial_call=True
#     )
#     def handle_chat_navigation(message_data):
#         """Handle navigation messages from Chainlit"""
#         if not message_data:
#             return dash.no_update
        
#         try:
#             # Parse the message data
#             data = json.loads(message_data)
            
#             # Check if it's a navigation message
#             if data.get('type') == 'navigation':
#                 destination = data.get('destination')
                
#                 # Map destination to URL
#                 url_map = {
#                     'menu': '/menu',
#                     'orders': '/orders',
#                     'order': '/orders',
#                     'delivery': '/delivery',
#                     'profile': '/profile',
#                     'dashboard': '/dashboard',
#                     'home': '/'
#                 }
                
#                 # Navigate to the appropriate URL
#                 if destination in url_map:
#                     return url_map[destination]
            
#             # Not a navigation message
#             return dash.no_update
            
#         except Exception as e:
#             print(f"Error handling chat navigation: {e}")
#             return dash.no_update

#     # Handle messages from Chainlit via socket.io
#     @socketio.on('chainlit_message')
#     def handle_chainlit_message(data):
#         """
#         Handle messages from Chainlit
        
#         Args:
#             data (dict): Message data from Chainlit
#         """
#         message_type = data.get('type')
        
#         if message_type == 'order_update':
#             # Order update from Chainlit
#             order_data = data.get('order')
            
#             if order_data:
#                 # Broadcast to all clients
#                 socketio.emit('order_update', order_data)
                
#                 # Update hidden div for triggering callbacks
#                 socketio.emit('update_chat_message_listener', json.dumps(data))
                
#                 # In a real app, would also update database
#                 print(f"Order update from Chainlit: {order_data['id']}")
        
#         elif message_type == 'navigation':
#             # Navigation request from Chainlit
#             destination = data.get('destination')
            
#             # Broadcast to all clients
#             socketio.emit('update_chat_message_listener', json.dumps(data))
            
#             print(f"Navigation request from Chainlit: {destination}")
        
#         elif message_type == 'voice_update':
#             # Voice mode toggled in Chainlit
#             voice_enabled = data.get('enabled', False)
            
#             # Broadcast to all clients
#             socketio.emit('voice_update', {'enabled': voice_enabled})
            
#             print(f"Voice mode {'enabled' if voice_enabled else 'disabled'} from Chainlit")
        
#         # Acknowledge receipt
#         return {'status': 'success', 'message': 'Message received'}


# # Helper function for order status colors
# def get_status_color(status):
#     """Get appropriate Bootstrap color class for order status"""
#     status_lower = status.lower()
#     if status_lower == 'completed' or status_lower == 'delivered':
#         return 'success'
#     elif status_lower == 'in progress' or status_lower == 'preparing':
#         return 'primary'
#     elif status_lower == 'ready':
#         return 'info'
#     elif status_lower == 'cancelled':
#         return 'danger'
#     else:
#         return 'secondary'

#==================================================================================


# File: app/callbacks/chat_callbacks.py (SocketIO Update)
import dash
from dash import Input, Output, State, callback_context, html, dcc, ALL
import dash_bootstrap_components as dbc
import json
import urllib.parse
from flask import session
import os
import requests
from app.utils.api_utils import get_chainlit_session

# Base URLs for APIs
CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8001')

def register_callbacks(app, socketio):
    """
    Register callbacks for the chat interface
    
    Args:
        app: Dash application instance
        socketio: SocketIO instance for real-time communication
    """
    # Floating chat panel toggle callbacks
    @app.callback(
        [
            Output('floating-chat-panel', 'style'),
            Output('floating-chat-panel', 'className'),
            Output('chat-faq-section', 'style')
        ],
        [
            Input('floating-chat-button', 'n_clicks'),
            Input('close-chat-button', 'n_clicks'),
            Input('minimize-chat-button', 'n_clicks')
        ],
        [
            State('floating-chat-panel', 'style'),
            State('floating-chat-panel', 'className'),
            State('chat-faq-section', 'style')
        ]
    )
    def toggle_chat_panel(open_clicks, close_clicks, minimize_clicks, 
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
        
        if button_id == "floating-chat-button":
            # If panel is hidden, show it
            if current_display == "none":
                return visible_style, base_class, hide_faq
            # If panel is visible but minimized, maximize it
            elif is_minimized:
                return visible_style, base_class, hide_faq
            # If panel is expanded, collapse it to normal
            elif is_expanded:
                return visible_style, base_class, hide_faq
            # If panel is normal, just hide it
            else:
                return hidden_style, base_class, hide_faq
                
        elif button_id == "close-chat-button":
            # Always hide the panel
            return hidden_style, base_class, hide_faq
            
        elif button_id == "minimize-chat-button":
            # Toggle between states: normal → minimized → expanded → normal
            if is_minimized:
                # Minimized → Expanded
                return visible_style, expanded_class, show_faq
            elif is_expanded:
                # Expanded → Normal
                return visible_style, base_class, hide_faq
            else:
                # Normal → Minimized
                return visible_style, minimized_class, hide_faq
                
        # Default: no change
        return current_style or hidden_style, current_class or base_class, faq_style or hide_faq
    
    # Set Chainlit iframe source when panel becomes visible
    @app.callback(
        Output('floating-chainlit-frame', 'src'),
        [
            Input('floating-chat-panel', 'style'),
            Input('url', 'pathname')
        ],
        [State('user-store', 'data')]
    )
    def update_floating_chat_frame(panel_style, pathname, user_data):
        """Update the Chainlit iframe source with correct parameters"""
        # Only update if panel is being shown
        if not panel_style or panel_style.get("display") == "none":
            return dash.no_update
            
        # Base Chainlit URL
        chainlit_url = CHAINLIT_URL
        
        # Default to empty query
        query_params = {}
        
        # Add floating flag to indicate this is the floating context
        query_params['floating'] = 'true'
        
        # Check if we're on a specific page and add appropriate parameters
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
        
        # Add user info if available
        if user_data and 'username' in user_data:
            query_params['user'] = user_data['username']
            
            # If user has active order, add order ID
            if 'active_order' in user_data and user_data['active_order']:
                query_params['order_id'] = user_data['active_order']['id']
        
        # Add session ID if available
        if 'session_id' in session:
            query_params['session_id'] = session['session_id']
        else:
            # Create a new session ID
            session_id = get_chainlit_session()
            session['session_id'] = session_id
            query_params['session_id'] = session_id
        
        # Build query string
        query_string = urllib.parse.urlencode(query_params)
        
        # Build full URL
        if query_string:
            return f"{chainlit_url}?{query_string}"
        else:
            return chainlit_url
    
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
            
            # Get or create session ID
            session_id = session.get('session_id')
            if not session_id:
                session_id = get_chainlit_session()
                session['session_id'] = session_id
            
            # Send message to Chainlit via SocketIO
            # This is the recommended approach for Chainlit communication
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
    
    @app.callback(
        Output('current-order-status', 'children'),
        [
            Input('refresh-order-btn', 'n_clicks'),
            Input('status-update-interval', 'n_intervals')
        ],
        [State('user-store', 'data')]
    )
    def update_order_status(n_clicks, n_intervals, user_data):
        """Update the current order status display"""
        # Default content for no active orders
        no_order_content = html.P("No active order.", className="text-muted")
        
        # Check if user is logged in and has active order
        if not user_data or 'active_order' not in user_data:
            return no_order_content
        
        active_order = user_data.get('active_order')
        
        if not active_order:
            return no_order_content
        
        # Create order status content
        order_content = [
            html.H6(f"Order #{active_order['id']}", className="card-subtitle mb-2"),
            html.P([
                html.Strong("Status: "),
                html.Span(active_order['status'], className=f"text-{get_status_color(active_order['status'])}")
            ]),
            html.P([
                html.Strong("Items: "),
                html.Span(f"{len(active_order['items'])} items")
            ]),
            html.P([
                html.Strong("Total: "),
                html.Span(f"${active_order['total']:.2f}")
            ]),
            html.P([
                html.Strong("Delivery: "),
                html.Span(active_order['delivery_location'])
            ]),
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

    # Set up Socket.IO event handlers
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print('Client connected to Socket.IO')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print('Client disconnected from Socket.IO')
    
    @socketio.on('send_chat_message')
    def handle_send_chat_message(data):
        """
        Handle message sending from dashboard to Chainlit
        
        Args:
            data (dict): Message data
        """
        message = data.get('message')
        session_id = data.get('session_id')
        
        print(f"Received message to send to Chainlit: {message}")
        
        # Forward the message to all clients (including the Chainlit iframe)
        socketio.emit('chat_message_from_dashboard', {
            'message': message,
            'session_id': session_id
        })
        
        # Acknowledge receipt
        return {'status': 'success', 'message': 'Message received and forwarded'}

    # Handle messages from Chainlit via socket.io
    @socketio.on('chainlit_message')
    def handle_chainlit_message(data):
        """
        Handle messages from Chainlit
        
        Args:
            data (dict): Message data from Chainlit
        """
        message_type = data.get('type')
        
        print(f"Received message from Chainlit: {message_type}")
        
        if message_type == 'order_update':
            # Order update from Chainlit
            order_data = data.get('order')
            
            if order_data:
                # Broadcast to all clients
                socketio.emit('order_update', order_data)
                
                # Update hidden div for triggering callbacks
                socketio.emit('update_chat_message_listener', json.dumps(data))
                
                # In a real app, would also update database
                print(f"Order update from Chainlit: {order_data['id']}")
        
        elif message_type == 'navigation':
            # Navigation request from Chainlit
            destination = data.get('destination')
            
            # Broadcast to all clients
            socketio.emit('update_chat_message_listener', json.dumps(data))
            
            print(f"Navigation request from Chainlit: {destination}")
        
        elif message_type == 'voice_update':
            # Voice mode toggled in Chainlit
            voice_enabled = data.get('enabled', False)
            
            # Broadcast to all clients
            socketio.emit('voice_update', {'enabled': voice_enabled})
            
            print(f"Voice mode {'enabled' if voice_enabled else 'disabled'} from Chainlit")
        
        # Acknowledge receipt
        return {'status': 'success', 'message': 'Message received'}


# Helper function for order status colors
def get_status_color(status):
    """Get appropriate Bootstrap color class for order status"""
    status_lower = status.lower()
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