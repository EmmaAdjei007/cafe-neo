# # File: app/layouts/__init__.py
from dash import html, dcc, Input, Output
from app.layouts.navbar import create_navbar
from app.layouts.footer import create_footer
from app.components.modals import login_modal, signup_modal , signup_success_modal # Import the modals
from dash import html, dcc, clientside_callback, ClientsideFunction


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
        dcc.Store(id='auth-store', storage_type='session')  # Add auth store
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
        )
    ]

    # Create the main layout with routing
    layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='navbar-container', children=create_navbar()),
        html.Div(id='page-content', className='container py-4'),
        html.Div(id='tab-content'),
        html.Div(id='footer-container', children=create_footer()),
        html.Div(id='alert-container'),
        html.Div(id='cart-alert'),
        
        # Add auth modals
        login_modal(),
        signup_modal(),
        signup_success_modal(),
        
        # Add the hidden auth-check div
        html.Div(id="auth-check", style={"display": "none"}),
        
        # Add stores and intervals
        *stores,
        *intervals
    ])
    
    return layout

# Register client-side callback for message passing
clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='updateChatListener'
    ),
    Output('chat-message-listener', 'children'),
    Input('chat-message-listener', 'id')
)