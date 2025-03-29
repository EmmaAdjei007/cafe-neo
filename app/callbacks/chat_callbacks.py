# File: app/callbacks/chat_callbacks.py (Updated)
import dash
from dash import Input, Output, State, callback_context, html, dcc
import dash_bootstrap_components as dbc
import json
import urllib.parse
from flask import session
import os
import requests
from app.utils.api_utils import send_message_to_chainlit, get_chainlit_session

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

# File: app/layouts/chat.py (Updated)

import dash_bootstrap_components as dbc
from dash import html, dcc

def layout():
    """
    Create the chat layout with integrated Chainlit
    
    Returns:
        html.Div: The chat interface content
    """
    header = html.Div([
        html.H1("Neo Cafe Assistant", className="page-header"),
        html.P("Ask questions, place orders, or get help from our virtual barista", className="lead")
    ])
    
    # Chat interface with Chainlit integration
    chat_interface = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("BaristaBot", className="d-inline"),
                    dbc.Badge("Online", color="success", className="ms-2")
                ]),
                dbc.CardBody([
                    # Chainlit integration via iframe
                    html.Iframe(
                        id="chainlit-frame",
                        src="/chainlit",  # This will be handled by a Flask route
                        style={
                            "width": "100%",
                            "height": "600px",
                            "border": "none",
                            "borderRadius": "0.25rem"
                        }
                    )
                ]),
                dbc.CardFooter([
                    dbc.Button(
                        html.I(className="fas fa-microphone"),
                        id="voice-toggle-btn",
                        color="primary",
                        className="me-2",
                        n_clicks=0,
                        tooltip="Toggle voice mode"
                    ),
                    dbc.Button(
                        "Order Status",
                        id="order-status-btn",
                        color="info",
                        className="me-2",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "View Menu",
                        id="view-menu-btn",
                        color="secondary",
                        className="me-2",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "Help",
                        id="chat-help-btn",
                        color="link",
                        className="me-2",
                        n_clicks=0
                    )
                ])
            ])
        ], md=8),
        dbc.Col([
            # Sidebar with quick actions and information
            dbc.Card([
                dbc.CardHeader("Quick Actions"),
                dbc.CardBody([
                    dbc.Button(
                        "Place Order",
                        id="quick-order-btn",
                        color="primary",
                        className="mb-2 w-100",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "Track Delivery",
                        id="quick-track-btn",
                        color="info",
                        className="mb-2 w-100",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "Popular Items",
                        id="quick-popular-btn",
                        color="secondary",
                        className="mb-2 w-100",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "Operating Hours",
                        id="quick-hours-btn",
                        color="secondary",
                        className="mb-4 w-100",
                        n_clicks=0
                    ),
                ]),
            ], className="mb-3"),
            
            # Current order status card (if any)
            dbc.Card([
                dbc.CardHeader([
                    html.H5("Your Current Order", className="d-inline"),
                    dbc.Button(
                        html.I(className="fas fa-sync-alt"),
                        id="refresh-order-btn",
                        color="link",
                        size="sm",
                        className="float-end",
                        n_clicks=0
                    )
                ]),
                dbc.CardBody(id="current-order-status", children=[
                    html.P("No active order.", className="text-muted")
                ])
            ])
        ], md=4)
    ])
    
    # Common queries and help section
    help_section = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Common Questions"),
                dbc.CardBody([
                    dbc.ListGroup([
                        dbc.ListGroupItem(
                            "What's on the menu?", 
                            action=True, 
                            id="faq-menu-btn",
                            className="d-flex justify-content-between align-items-center"
                        ),
                        dbc.ListGroupItem(
                            "What are your operating hours?", 
                            action=True, 
                            id="faq-hours-btn",
                            className="d-flex justify-content-between align-items-center"
                        ),
                        dbc.ListGroupItem(
                            "How does robot delivery work?", 
                            action=True, 
                            id="faq-robot-btn",
                            className="d-flex justify-content-between align-items-center"
                        ),
                        dbc.ListGroupItem(
                            "What's your most popular coffee?", 
                            action=True, 
                            id="faq-popular-btn",
                            className="d-flex justify-content-between align-items-center"
                        ),
                    ], flush=True)
                ])
            ])
        ], md=12)
    ], className="mt-4")
    
    # Combine all elements
    layout = html.Div([
        header,
        chat_interface,
        help_section,
        
        # Hidden store for chat state
        dcc.Store(id='chat-state-store', storage_type='session'),
        
        # Hidden div for chat callback triggers
        html.Div(id='chat-action-trigger', style={'display': 'none'}),
        
        # Hidden div for listening to messages from Chainlit
        html.Div(id='chat-message-listener', style={'display': 'none'})
    ])
    
    return layout



# Add this to templates/chainlit_embed.html or create this file

"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neo Cafe - Chat</title>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
        }
        
        #chatframe {
            width: 100%;
            height: 100%;
            border: none;
        }
    </style>
</head>
<body>
    <iframe id="chatframe" src="{{ chainlit_url }}" allowfullscreen></iframe>
    
    <script>
        // Handle postMessage communication from the Chainlit iframe
        window.addEventListener('message', function(event) {
            // Verify the origin of the message
            if (event.origin !== new URL("{{ chainlit_url }}").origin) {
                return;
            }
            
            // Handle different message types
            if (event.data.type === 'orderPlaced') {
                // Notify the parent window about an order being placed
                window.parent.postMessage({
                    type: 'orderPlaced',
                    order: event.data.order
                }, '*');
            } else if (event.data.type === 'navigation') {
                // Forward navigation requests to the parent window
                window.parent.postMessage({
                    type: 'navigation',
                    destination: event.data.destination
                }, '*');
            } else if (event.data.type === 'chatMessage') {
                // Forward chat messages to the parent window
                window.parent.postMessage({
                    type: 'chatMessage',
                    message: event.data.message
                }, '*');
            }
        });
        
        // Forward messages from the parent to the Chainlit iframe
        window.addEventListener('message', function(event) {
            // Only process messages from the parent
            if (event.source === window.parent) {
                const chatframe = document.getElementById('chatframe');
                chatframe.contentWindow.postMessage(event.data, "{{ chainlit_url }}");
            }
        });
    </script>
</body>
</html>
"""

# Add this to app/layouts/__init__.py (Update main layout with client-side callback)

# Add this import at the top
from dash import html, dcc, clientside_callback, ClientsideFunction

# Then add this after creating the layout
# Register client-side callback for message passing
clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='updateChatListener'
    ),
    Output('chat-message-listener', 'children', allow_duplicate=True),
    Input('chat-message-listener', 'id'),
    prevent_initial_call='initial_duplicate'
)


