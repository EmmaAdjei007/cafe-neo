# Updated app/layouts/__init__.py

from dash import Input, Output, html, dcc, clientside_callback, ClientsideFunction
from app.layouts.navbar import create_navbar
from app.layouts.footer import create_footer
from app.components.modals import login_modal, signup_modal, signup_success_modal
from app.components.floating_chat import create_floating_chat

def create_main_layout():
    """
    Create the main layout structure for the app
    
    Returns:
        html.Div: The main layout container
    """
    # Define the necessary stores for state management
    stores = [
        dcc.Store(id='user-store', storage_type='session'),
        dcc.Store(id='cart-store', storage_type='session', data=[]),
        dcc.Store(id='active-tab-store', storage_type='session'),
        dcc.Store(id='delivery-update-store', storage_type='memory'),
        dcc.Store(id='auth-store', storage_type='session'),
        dcc.Store(id='chat-state-store', storage_type='session'),  # Add chat state
    ]

    # Define an interval for periodic updates
    intervals = [
        dcc.Interval(
            id='status-update-interval',
            interval=5000,  # 5 seconds
            n_intervals=0
        ),
        dcc.Interval(
            id='orders-update-interval',
            interval=10000,  # 10 seconds
            n_intervals=0
        ),
        # Add client interval for checking navigation messages
        dcc.Interval(
            id='client-interval',
            interval=1000,  # 1 second
            n_intervals=0
        )
    ]

    # Create the floating chat component
    floating_chat = create_floating_chat()

    # Create the main layout with routing
    layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='navbar-container', children=create_navbar()),
        html.Div(id='page-content', className='container py-4'),
        html.Div(id='tab-content'),
        html.Div(id='footer-container', children=create_footer()),
        html.Div(id='alert-container'),
        html.Div(id='cart-alert'),
        
        # Add floating chat component
        floating_chat,
        
        # Add auth modals
        login_modal(),
        signup_modal(),
        signup_success_modal(),
        
        # Add the hidden auth-check div
        html.Div(id="auth-check", style={"display": "none"}),
        
        # Add hidden divs for chat communication
        html.Div(id='chat-message-listener', style={'display': 'none'}),
        html.Div(id='chat-action-trigger', style={'display': 'none'}),
        html.Div(id='socket-chat-update', style={'display': 'none'}),
        
        # Add navigation trigger div for handling navigation requests from chat
        html.Div(id='navigation-trigger', style={'display': 'none'}),
        
        # Add hidden divs for direct message support
        html.Div(id='voice-status', style={'display': 'none'}),
        
        # Add hidden div for order updates
        html.Div(id="socket-order-update", style={"display": "none"}),
        
        # Add stores and intervals
        *stores,
        *intervals
    ])
    
    return layout

def register_order_update_callback(app):
    """
    Register the clientside callback for order updates
    This function should be called after the app is created
    
    Args:
        app: The Dash app instance
    """
    app.clientside_callback(
        """
        function(n) {
            if (!window._orderUpdateListenerInitialized) {
                window._orderUpdateListenerInitialized = true;
                
                // Listen for order updates from socket.io
                if (window.socket) {
                    window.socket.on('order_update', function(data) {
                        console.log('Order update received:', data);
                        window._lastOrderUpdate = JSON.stringify(data);
                        
                        // Trigger callback by returning data
                        if (window._dashCallbacks) {
                            window._dashCallbacks.forEach(callback => callback());
                        }
                    });
                } else {
                    // Wait for socket to be available
                    window._socketInitInterval = setInterval(function() {
                        if (window.socket) {
                            window.socket.on('order_update', function(data) {
                                console.log('Order update received:', data);
                                window._lastOrderUpdate = JSON.stringify(data);
                                
                                // Trigger callback by returning data
                                if (window._dashCallbacks) {
                                    window._dashCallbacks.forEach(callback => callback());
                                }
                            });
                            clearInterval(window._socketInitInterval);
                        }
                    }, 1000);
                }
            }
            
            return window._lastOrderUpdate || null;
        }
        """,
        Output("socket-order-update", "children"),
        [Input("client-interval", "n_intervals")]
    )