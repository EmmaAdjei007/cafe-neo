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
        # html.Div(id='direct-message-status', style={'display': 'none'}),
        html.Div(id='voice-status', style={'display': 'none'}),
        
        # Add stores and intervals
        *stores,
        *intervals
    ])
    
    return layout