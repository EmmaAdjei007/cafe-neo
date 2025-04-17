# File: app/callbacks/auth_callbacks.py
import dash
from dash import Input, Output, State, callback_context, html
import dash_bootstrap_components as dbc
import json
from app.utils.auth_utils import validate_login, register_user, get_user_profile, hash_password

def register_callbacks(app):
    """
    Register callbacks for authentication
    
    Args:
        app: Dash application instance
    """

    @app.callback(
Output("user-store", "data", allow_duplicate=True),
[Input("socket-order-update", "children")],
[State("user-store", "data")],
prevent_initial_call=True
)
    def update_user_active_order(socket_update, current_user):
        """Update user's active order when a new order is received"""
        if not socket_update or not current_user:
            return dash.no_update
        
        try:
            # Parse the order data
            order_data = json.loads(socket_update)
            
            # Verify this is a valid order
            if not isinstance(order_data, dict) or 'id' not in order_data:
                return dash.no_update
            
            # Check if this order belongs to the current user
            # Enhanced: Check both user_id and username fields
            user_identifier = order_data.get('user_id') or order_data.get('username')
            current_username = current_user.get('username')
            
            # Process orders that either:
            # 1. Match the current user
            # 2. Have no user specified (guest orders)
            # 3. Have a user_id of 'guest' (also guest orders)
            if user_identifier and user_identifier != "guest" and user_identifier != current_username:
                print(f"Order {order_data['id']} belongs to {user_identifier}, not current user {current_username}")
                return dash.no_update
            
            # Update the user's active order
            updated_user = dict(current_user)
            updated_user['active_order'] = order_data
            
            print(f"Updated user's active order to {order_data['id']}")
            return updated_user
        
        except Exception as e:
            print(f"Error updating user's active order: {e}")
            return dash.no_update

    @app.callback(
        [
            Output("login-alert", "children"),
            Output("user-store", "data"),
            Output("url", "pathname", allow_duplicate=True)
        ],
        [Input("login-button", "n_clicks")],
        [
            State("login-username", "value"),
            State("login-password", "value"),
            State("user-store", "data")
        ],
        prevent_initial_call=True
    )
    def login_user(n_clicks, username, password, current_user):
        """Handle user login attempt"""
        # If button wasn't clicked, return no changes
        if not n_clicks:
            return None, current_user, dash.no_update
        
        # Validate the login
        if not username or not password:
            alert = dbc.Alert("Please enter both username and password", color="danger")
            return alert, current_user, dash.no_update
        
        # Check credentials
        user_data = validate_login(username, password)
        
        if user_data:
            # Login successful
            return None, user_data, "/dashboard"
        else:
            # Login failed
            alert = dbc.Alert("Invalid username or password", color="danger")
            return alert, current_user, dash.no_update
    
    @app.callback(
        [
            Output("signup-alert", "children"),
            Output("signup-success-modal", "is_open")
        ],
        [Input("signup-button", "n_clicks")],
        [
            State("signup-username", "value"),
            State("signup-email", "value"),
            State("signup-password", "value"),
            State("signup-confirm-password", "value")
        ],
        prevent_initial_call=True
    )
    def signup_user(n_clicks, username, email, password, confirm_password):
        """Handle user signup attempt"""
        # If button wasn't clicked, return no changes
        if not n_clicks:
            return None, False
        
        # Validate inputs
        if not username or not email or not password or not confirm_password:
            alert = dbc.Alert("Please fill in all fields", color="danger")
            return alert, False
        
        if password != confirm_password:
            alert = dbc.Alert("Passwords do not match", color="danger")
            return alert, False
        
        # Attempt registration
        success, message = register_user(username, email, password)
        
        if success:
            # Registration successful
            return None, True
        else:
            # Registration failed
            alert = dbc.Alert(message, color="danger")
            return alert, False
    
    @app.callback(
        Output("logout-alert", "children"),
        [Input("logout-link", "n_clicks")],
        [State("user-store", "data")]
    )
    def logout_user(n_clicks, current_user):
        """Handle user logout"""
        # Clear the user store
        if n_clicks:
            # In a real application, would also destroy server-side session
            # For now, clearing user store happens in another callback
            return dbc.Alert("You have been logged out successfully", color="success")
        
        return None
    
    @app.callback(
        Output("user-store", "clear_data"),
        [Input("logout-link", "n_clicks")]
    )
    def clear_user_data(n_clicks):
        """Clear user data from store on logout"""
        if n_clicks:
            return True
        return False
    
    @app.callback(
        Output("profile-content", "children"),
        [Input("url", "pathname")],
        [State("user-store", "data")]
    )
    def load_profile(pathname, user_data):
        """Load user profile data"""
        if pathname == "/profile" and user_data:
            # Get full profile data
            profile = get_user_profile(user_data.get("username"))
            
            if profile:
                # Create profile content
                from app.layouts.profile import create_profile_content
                return create_profile_content(profile)
            else:
                # Profile not found
                return html.Div([
                    dbc.Alert("Profile not found", color="danger"),
                    dbc.Button("Return to Dashboard", href="/dashboard", color="primary")
                ])
        
        # Not on profile page or not logged in
        return None
    
    @app.callback(
        Output("auth-check", "children"),
        [Input("url", "pathname")],
        [State("user-store", "data")]
    )
    def check_auth_status(pathname, user_data):
        """Check if user is authenticated for protected routes"""
        
        # Define protected routes that require authentication
        protected_routes = [
            "/profile",
            "/orders",
            "/delivery"
        ]
        
        # Define admin-only routes
        admin_routes = [
            "/admin"
        ]
        
        # Check if current path requires authentication
        requires_auth = pathname in protected_routes
        requires_admin = pathname in admin_routes
        
        # Check if user is authenticated
        is_authenticated = user_data is not None and "username" in user_data
        
        # Check if user is admin
        is_admin = is_authenticated and user_data.get("role") == "admin"
        
        # Handle auth requirements
        if requires_auth and not is_authenticated:
            # User trying to access protected route while not logged in
            # Open login modal via a callback
            return "require-login"
        
        elif requires_admin and not is_admin:
            # User trying to access admin route without admin privileges
            return "access-denied"
        
        else:
            # User has appropriate access
            return "authenticated" if is_authenticated else "unauthenticated"
        
    @app.callback(
        [
            Output("auth-buttons", "style"),
            Output("account-dropdown", "style")
        ],
        [Input("user-store", "data")]
    )
    def toggle_auth_ui(user_data):
        """Toggle auth UI elements based on login state"""
        
        # Check if user is logged in
        is_authenticated = user_data is not None and "username" in user_data
        
        if is_authenticated:
            # Show account dropdown, hide auth buttons
            return {"display": "none"}, {"display": "block"}
        else:
            # Show auth buttons, hide account dropdown
            return {"display": "flex"}, {"display": "none"}
    
    # Navbar button callbacks
    @app.callback(
        Output("login-modal", "is_open", allow_duplicate=True),
        [Input("navbar-login-btn", "n_clicks")],
        [State("login-modal", "is_open")],
        prevent_initial_call=True
    )
    def open_login_from_navbar(login_btn_clicks, is_open):
        """Open login modal from navbar button"""
        if login_btn_clicks:
            return True
        return is_open
    
    @app.callback(
        Output("signup-modal", "is_open", allow_duplicate=True),
        [Input("navbar-signup-btn", "n_clicks")],
        [State("signup-modal", "is_open")],
        prevent_initial_call=True
    )
    def open_signup_from_navbar(signup_btn_clicks, is_open):
        """Open signup modal from navbar button"""
        if signup_btn_clicks:
            return True
        return is_open
    
    # Close button callbacks
    @app.callback(
        Output("login-modal", "is_open", allow_duplicate=True),
        [Input("close-login-modal", "n_clicks")],
        [State("login-modal", "is_open")],
        prevent_initial_call=True
    )
    def close_login_modal(close_clicks, is_open):
        """Close login modal when close button is clicked"""
        if close_clicks:
            return False
        return is_open
    
    @app.callback(
        Output("signup-modal", "is_open", allow_duplicate=True),
        [Input("close-signup-modal", "n_clicks")],
        [State("signup-modal", "is_open")],
        prevent_initial_call=True
    )
    def close_signup_modal(close_clicks, is_open):
        """Close signup modal when close button is clicked"""
        if close_clicks:
            return False
        return is_open
    
    # Cross-modal navigation - these only work if signup-link and login-link exist in your modals
    @app.callback(
        [Output("login-modal", "is_open", allow_duplicate=True),
         Output("signup-modal", "is_open", allow_duplicate=True)],
        [Input("signup-link", "n_clicks")],
        [State("login-modal", "is_open"),
         State("signup-modal", "is_open")],
        prevent_initial_call=True
    )
    def switch_to_signup(signup_link_clicks, login_is_open, signup_is_open):
        """Switch from login to signup"""
        if signup_link_clicks:
            return False, True
        return login_is_open, signup_is_open
    
    @app.callback(
        [Output("login-modal", "is_open", allow_duplicate=True),
         Output("signup-modal", "is_open", allow_duplicate=True)],
        [Input("login-link", "n_clicks")],
        [State("login-modal", "is_open"),
         State("signup-modal", "is_open")],
        prevent_initial_call=True
    )
    def switch_to_login(login_link_clicks, login_is_open, signup_is_open):
        """Switch from signup to login"""
        if login_link_clicks:
            return True, False
        return login_is_open, signup_is_open
    
    # Close modal after login/signup actions
    @app.callback(
        Output("login-modal", "is_open", allow_duplicate=True),
        [Input("login-button", "n_clicks")],
        prevent_initial_call=True
    )
    def close_after_login(n_clicks):
        """Close login modal after login attempt"""
        if n_clicks:
            return False
        return dash.no_update
    
    @app.callback(
        Output("signup-modal", "is_open", allow_duplicate=True),
        [Input("signup-button", "n_clicks")],
        prevent_initial_call=True
    )
    def close_after_signup(n_clicks):
        """Close signup modal after signup attempt"""
        if n_clicks:
            return False
        return dash.no_update