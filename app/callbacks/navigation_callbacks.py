# File: app/callbacks/navigation_callbacks.py
import dash
from dash import Input, Output, State, callback_context, dcc, html
import dash_bootstrap_components as dbc

def register_callbacks(app):
    """
    Register callbacks for navigation
    
    Args:
        app: Dash application instance
    """
    @app.callback(
        [
            Output('page-content', 'children'),
            Output('tab-content', 'children'),
            Output('active-tab-store', 'data')
        ],
        [Input('url', 'pathname')],
        [State('active-tab-store', 'data')]
    )
    def display_page(pathname, active_tab):
        """Route to the appropriate page based on URL pathname"""
        from app.layouts.landing import layout as landing_layout
        from app.layouts.dashboard import layout as dashboard_layout
        from app.layouts.menu import layout as menu_layout
        from app.layouts.orders import layout as orders_layout
        from app.layouts.delivery import layout as delivery_layout
        from app.layouts.chat import layout as chat_layout
        from app.layouts.auth import login_layout, signup_layout
        from app.layouts.profile import layout as profile_layout
        
        # Set default active tab
        if active_tab is None:
            active_tab = 'dashboard'
        
        # Empty tab content by default
        tab_content = html.Div()
        
        # Check the pathname and return the appropriate layout
        if pathname == '/' or pathname == '/landing':
            return landing_layout(), tab_content, active_tab
        
        elif pathname == '/dashboard':
            return dashboard_layout(), tab_content, 'dashboard'
        
        elif pathname == '/menu':
            return menu_layout(), tab_content, 'menu'
        
        elif pathname == '/orders':
            return orders_layout(), tab_content, 'orders'
        
        elif pathname == '/delivery':
            return delivery_layout(), tab_content, 'delivery'
        
        elif pathname == '/chat':
            return chat_layout(), tab_content, 'chat'
        
        elif pathname == '/login':
            return login_layout(), tab_content, active_tab
        
        elif pathname == '/signup':
            return signup_layout(), tab_content, active_tab
        
        elif pathname == '/profile':
            return profile_layout(), tab_content, active_tab
        
        # If the pathname isn't recognized, return a 404 message
        return html.Div([
            html.H1('404 - Page Not Found', className='text-danger'),
            html.P('The page you requested does not exist.'),
            dbc.Button('Return Home', href='/', color='primary')
        ]), tab_content, active_tab
    
    @app.callback(
        Output('navbar-collapse', 'is_open'),
        [Input('navbar-toggler', 'n_clicks')],
        [State('navbar-collapse', 'is_open')]
    )
    def toggle_navbar_collapse(n_clicks, is_open):
        """Toggle the navbar collapse on mobile view"""
        if n_clicks:
            return not is_open
        return is_open
    
    @app.callback(
        [Output(f"{page}-link", "active") for page in ["dashboard", "menu", "orders", "delivery", "chat"]],
        [Input("url", "pathname")]
    )
    def set_active_link(pathname):
        """Set the active state of navbar links based on current page"""
        # Map paths to their corresponding link IDs
        path_map = {
            "/dashboard": "dashboard",
            "/menu": "menu",
            "/orders": "orders",
            "/delivery": "delivery",
            "/chat": "chat"
        }
        
        # Get the current page from the pathname
        current_page = path_map.get(pathname, None)
        
        # Set active state for each link
        return [page == current_page for page in ["dashboard", "menu", "orders", "delivery", "chat"]]
    
    @app.callback(
    [
        Output("login-modal", "is_open"),
        Output("url", "pathname", allow_duplicate=True)
    ],
    [
        Input("auth-check", "children"),
        Input("navbar-login-btn", "n_clicks"),
        Input("login-link", "n_clicks"),
        Input("close-login-modal", "n_clicks"),
        Input("login-button", "n_clicks")
    ],
    [
        State("login-modal", "is_open"),
        State("url", "pathname")
    ],
    prevent_initial_call=True
)
    def handle_auth_navigation(auth_status, navbar_login_clicks, login_link_clicks, 
                            close_clicks, login_button_clicks, is_modal_open, current_path):
        """
        Combined callback to handle login modal state and URL redirection
        This resolves conflicts with multiple callbacks trying to control the same outputs
        """
        ctx = callback_context
        
        if not ctx.triggered:
            # No triggers yet, return current state
            return is_modal_open, current_path
        
        # Get the ID of the component that triggered the callback
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Handle auth-check triggers
        if trigger_id == "auth-check" and auth_status == "require-login":
            # Open the login modal when auth check requires login
            return True, current_path
        
        # Handle login modal open triggers
        elif trigger_id in ["navbar-login-btn", "login-link"]:
            return True, current_path
        
        # Handle login modal close triggers
        elif trigger_id in ["close-login-modal", "login-button"]:
            # If login was successful, we stay on current page
            # If login was canceled on a protected route, redirect to home
            if trigger_id == "close-login-modal" and any(route in current_path for route in ["/profile", "/orders", "/delivery"]):
                return False, "/"
            else:
                return False, current_path
        
        # Default: no change
        return is_modal_open, current_path
    
    @app.callback(
    Output("login-modal", "is_open", allow_duplicate=True),
    [
        Input("navbar-login-btn", "n_clicks"),
        Input("login-link", "n_clicks"),
        Input("close-login-modal", "n_clicks"),
        Input("login-button", "n_clicks")
    ],
    [State("login-modal", "is_open")],
    prevent_initial_call=True
)
    def toggle_login_modal(login_clicks, login_link_clicks, close_clicks, submit_clicks, is_open):
        """Toggle the login modal"""
        ctx = callback_context
        
        if not ctx.triggered:
            return is_open
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if button_id in ["navbar-login-btn", "login-link"]:
            return True
        elif button_id in ["close-login-modal", "login-button"]:
            return False
        
        return is_open