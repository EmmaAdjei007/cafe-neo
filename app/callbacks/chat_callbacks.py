# File: app/callbacks/chat_callbacks.py (Updated)
import dash
from dash import Input, Output, State, callback_context, html, dcc, ALL  # Add ALL import
import dash_bootstrap_components as dbc
import json
import urllib.parse
from flask import session
import os
import requests
from app.utils.api_utils import send_message_to_chainlit, get_chainlit_session

# Base URLs for APIs
CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8000')
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:8050')  # Add this line


def register_callbacks(app, socketio):
    """
    Register callbacks for the chat interface
    
    Args:
        app: Dash application instance
        socketio: SocketIO instance for real-time communication
    """

    @app.callback(
    Output("hours-collapse", "is_open"),
    [Input("fallback-hours-btn", "n_clicks")],
    [State("hours-collapse", "is_open")]
)
    def toggle_hours_collapse(n_clicks, is_open):
        """Toggle the hours collapse section"""
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        [
            Output("chainlit-container", "style"),
            Output("react-chat-container", "style"),
            Output("simple-fallback-container", "style")
        ],
        [Input("chat-implementation-toggle", "value")]
    )
    def toggle_chat_implementation(use_fallback):
        """Toggle between Chainlit iframe and fallback implementations"""
        if use_fallback:
            try:
                # Check if we can create the React implementation
                # Use React implementation
                return {"display": "none"}, {"display": "block", "height": "40px"}, html.Div([
                    html.Script(src="/assets/js/ChatComponent.js"),
                    html.Div(id="chat-component-mount-point")
                ])
            except ImportError:
                # If dash_extensions is not available, use the simple fallback
                return {"display": "none"}, {"display": "none"}, {"display": "block"}
        else:
            # Use Chainlit iframe
            return {"display": "block"}, {"display": "none"}, {"display": "none"}
   
    @app.callback(
    [Output("chainlit-loading-indicator", "children"),
     Output("chainlit-error", "children"),
     Output("chainlit-error", "style")],
    [Input("chainlit-status-check", "n_intervals")]
)
    def check_chainlit_status(n_intervals):
        """Check if Chainlit is accessible"""
        if n_intervals is None or n_intervals == 0:
            # Initial load, show nothing
            return None, None, {"display": "none"}
        
        try:
            # Make a request to our own status endpoint or directly to Chainlit
            try:
                # Try to access our own endpoint first
                response = requests.get(f"/chainlit-status", timeout=2)
            except:
                # If that fails, try to directly access Chainlit
                response = requests.get(f"{CHAINLIT_URL}/health", timeout=2)
            
            if response.status_code == 200:
                # All good, hide everything
                return None, None, {"display": "none"}
            else:
                # Error response from our endpoint
                error_msg = f"Chainlit service is not responding properly. Status: {response.json().get('message', 'Unknown error')}"
                return None, html.Div([
                    html.H5("Connection Issue", className="text-danger"),
                    html.P(error_msg),
                    html.P("Please try refreshing the page or contact support.")
                ]), {"display": "block", "margin": "20px", "padding": "20px", "border": "1px solid #dc3545", "borderRadius": "5px"}
        
        except Exception as e:
            # Request failed
            error_msg = f"Could not connect to Chainlit service: {str(e)}"
            return None, html.Div([
                html.H5("Connection Issue", className="text-danger"),
                html.P(error_msg),
                html.P("Please ensure the Chainlit service is running and try again.")
            ]), {"display": "block", "margin": "20px", "padding": "20px", "border": "1px solid #dc3545", "borderRadius": "5px"}

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
            Input('voice-toggle-btn', 'n_clicks')
        ],
        [State('chat-state-store', 'data')]
    )
    def handle_quick_actions(order_clicks, track_clicks, popular_clicks, hours_clicks, 
                             faq_menu_clicks, faq_hours_clicks, faq_robot_clicks, faq_popular_clicks,
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
            socketio.emit('send_chat_message', {
                'message': message,
                'session_id': session_id
            })
            
            # Also send via API as backup
            try:
                send_message_to_chainlit(message, session_id)
            except Exception as e:
                print(f"Error sending message to Chainlit API: {e}")
            
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
    
    @app.callback(
        Output('chainlit-frame', 'src'),
        [Input('url', 'pathname')],
        [State('user-store', 'data')]
    )
    def update_chat_frame(pathname, user_data):
        """Update the Chainlit iframe source with correct parameters"""
        # Base Chainlit URL
        chainlit_url = CHAINLIT_URL
        
        # Default to empty query
        query_params = {}
        
        # Check if we're on a specific page and add appropriate parameters
        if pathname == '/menu':
            query_params['tab'] = 'menu'
        elif pathname == '/orders':
            query_params['tab'] = 'order'
        elif pathname == '/delivery':
            query_params['tab'] = 'status'
        
        # Add user info if available
        if user_data and 'username' in user_data:
            query_params['user'] = user_data['username']
            
            # If user has active order, add order ID
            if 'active_order' in user_data and user_data['active_order']:
                query_params['order_id'] = user_data['active_order']['id']
        
        # Add session ID if available
        if 'session_id' in session:
            query_params['session_id'] = session['session_id']
        
        # Build query string
        query_string = urllib.parse.urlencode(query_params)
        
        # Build full URL
        if query_string:
            return f"{chainlit_url}?{query_string}"
        else:
            return chainlit_url

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
                    'chat': '/chat'
                }
                
                # Navigate to the appropriate URL
                if destination in url_map:
                    return url_map[destination]
            
            # Not a navigation message
            return dash.no_update
            
        except Exception as e:
            print(f"Error handling chat navigation: {e}")
            return dash.no_update

    # Handle messages from Chainlit via socket.io
    @socketio.on('chainlit_message')
    def handle_chainlit_message(data):
        """
        Handle messages from Chainlit
        
        Args:
            data (dict): Message data from Chainlit
        """
        message_type = data.get('type')
        
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