# File: app/components/modals.py

import dash_bootstrap_components as dbc
from dash import html, dcc
from app.components.forms import password_change_form, announcement_form, profile_form

def order_details_modal(order_id="", show_close_btn=True):
    """
    Create an order details modal
    
    Args:
        order_id (str): Order ID to display in the title
        show_close_btn (bool): Whether to show the close button
        
    Returns:
        dbc.Modal: The modal component
    """
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(f"Order Details {order_id}"), close_button=show_close_btn),
            dbc.ModalBody(id="order-details-modal-body"),
            dbc.ModalFooter([
                dbc.Button(
                    "Update Status",
                    id="update-order-status-btn",
                    color="primary",
                    className="me-2"
                ),
                dbc.Button(
                    "Close",
                    id="close-order-details-modal",
                    className="ms-auto"
                )
            ]),
        ],
        id="order-details-modal",
        size="lg",
        is_open=False,
    )
    
    return modal


def confirm_order_modal():
    """
    Create a confirm order modal
    
    Returns:
        dbc.Modal: The modal component
    """
    import dash_bootstrap_components as dbc
    from dash import html
    
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Confirm Your Order"), close_button=True),
            dbc.ModalBody([
                html.P("Please review your order before confirming:"),
                html.Div(id="confirm-order-details"),
                html.Hr(),
                html.P(id="confirm-order-total", className="fw-bold"),
                dbc.Label("Special Instructions:"),
                dbc.Textarea(
                    id="confirm-order-instructions",
                    placeholder="Any special instructions for your order?",
                    className="mb-3",
                    style={"height": "100px"}
                )
            ]),
            dbc.ModalFooter([
                dbc.Button(
                    "Edit Order",
                    id="edit-order-btn",
                    color="secondary",
                    className="me-2"
                ),
                dbc.Button(
                    "Confirm Order",
                    id="confirm-final-order-btn",
                    color="primary"
                ),
            ]),
        ],
        id="confirm-order-modal",
        size="lg",
        is_open=False,
    )
    
    return modal

def password_change_modal():
    """
    Create a password change modal
    
    Returns:
        dbc.Modal: The modal component
    """
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Change Password"), close_button=True),
            dbc.ModalBody(password_change_form()),
            dbc.ModalFooter(
                dbc.Button(
                    "Close",
                    id="close-password-modal",
                    className="ms-auto"
                ),
            ),
        ],
        id="password-change-modal",
        is_open=False,
    )
    
    return modal

def announcement_modal():
    """
    Create an announcement creation modal
    
    Returns:
        dbc.Modal: The modal component
    """
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("New Announcement"), close_button=True),
            dbc.ModalBody(announcement_form()),
            dbc.ModalFooter([
                dbc.Button(
                    "Cancel",
                    id="cancel-announcement-btn",
                    color="secondary",
                    className="me-2"
                ),
                dbc.Button(
                    "Post Announcement",
                    id="submit-announcement-btn",
                    color="primary"
                ),
            ]),
        ],
        id="add-announcement-modal",
        is_open=False,
    )
    
    return modal

def item_details_modal():
    """
    Create a menu item details modal
    
    Returns:
        dbc.Modal: The modal component
    """
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Item Details"), close_button=True),
            dbc.ModalBody(id="item-details-modal-body"),
            dbc.ModalFooter([
                dbc.Button(
                    "Add to Order",
                    id="modal-add-to-cart",
                    color="primary",
                    className="me-2"
                ),
                dbc.Button(
                    "Close",
                    id="close-item-modal",
                    color="secondary"
                ),
            ]),
        ],
        id="item-details-modal",
        size="lg",
        is_open=False,
    )
    
    return modal

def login_modal():
    """
    Create a login modal
    
    Returns:
        dbc.Modal: The modal component
    """
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Login"), close_button=True),
            dbc.ModalBody([
                # Username field - removed FormGroup wrapper
                dbc.Label("Username", html_for="login-username"),
                dbc.Input(
                    type="text",
                    id="login-username",
                    placeholder="Enter username",
                    className="mb-3"
                ),
                
                # Password field - removed FormGroup wrapper
                dbc.Label("Password", html_for="login-password"),
                dbc.Input(
                    type="password",
                    id="login-password",
                    placeholder="Enter password",
                    className="mb-3"
                ),
                
                # Remember me checkbox
                dbc.Checkbox(
                    id="login-remember",
                    label="Remember me",
                    className="mb-3"
                ),
                
                # Login button
                dbc.Button(
                    "Login",
                    id="login-button",
                    color="primary",
                    className="w-100 mb-3"
                ),
                
                # Alert area for messages
                html.Div(id="login-alert"),
                
                # Link to signup
                html.Div([
                    html.Span("Don't have an account? "),
                    html.A("Sign Up", id="signup-link", href="#", className="link-primary")
                ], className="text-center mt-3")
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-login-modal", className="ms-auto")
            ),
        ],
        id="login-modal",
        is_open=False,
    )
    
    return modal

def signup_modal():
    """
    Create a signup modal
    
    Returns:
        dbc.Modal: The modal component
    """
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Sign Up"), close_button=True),
            dbc.ModalBody([
                # Username field - removed FormGroup wrapper
                dbc.Label("Username", html_for="signup-username"),
                dbc.Input(
                    type="text",
                    id="signup-username",
                    placeholder="Choose a username",
                    className="mb-3"
                ),
                
                # Email field - removed FormGroup wrapper
                dbc.Label("Email", html_for="signup-email"),
                dbc.Input(
                    type="email",
                    id="signup-email",
                    placeholder="Enter your email",
                    className="mb-3"
                ),
                
                # Password field - removed FormGroup wrapper
                dbc.Label("Password", html_for="signup-password"),
                dbc.Input(
                    type="password",
                    id="signup-password",
                    placeholder="Choose a password",
                    className="mb-3"
                ),
                
                # Confirm password field - removed FormGroup wrapper
                dbc.Label("Confirm Password", html_for="signup-confirm-password"),
                dbc.Input(
                    type="password",
                    id="signup-confirm-password",
                    placeholder="Confirm your password",
                    className="mb-3"
                ),
                
                # Signup button
                dbc.Button(
                    "Sign Up",
                    id="signup-button",
                    color="primary",
                    className="w-100 mb-3"
                ),
                
                # Alert area for messages
                html.Div(id="signup-alert"),
                
                # Link to login
                html.Div([
                    html.Span("Already have an account? "),
                    html.A("Log In", id="login-link", href="#", className="link-primary")
                ], className="text-center mt-3")
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-signup-modal", className="ms-auto")
            ),
        ],
        id="signup-modal",
        is_open=False,
    )
    
    return modal

def signup_success_modal():
    """
    Create a signup success modal
    
    Returns:
        dbc.Modal: The modal component
    """
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Registration Successful"), close_button=True),
            dbc.ModalBody([
                html.P("Your account has been created successfully!"),
                html.P("You can now log in with your credentials.")
            ]),
            dbc.ModalFooter(
                dbc.Button(
                    "Log In",
                    id="success-login-btn",
                    color="primary"
                ),
            ),
        ],
        id="signup-success-modal",
        is_open=False,
    )
    
    return modal

def order_status_modal():
    """
    Create an order status update modal
    
    Returns:
        dbc.Modal: The modal component
    """
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Update Order Status"), close_button=True),
            dbc.ModalBody([
                html.P("Change the status of this order:"),
                dbc.Select(
                    id="order-status-select",
                    options=[
                        {"label": "New", "value": "New"},
                        {"label": "In Progress", "value": "In Progress"},
                        {"label": "Ready", "value": "Ready"},
                        {"label": "Delivered", "value": "Delivered"},
                        {"label": "Completed", "value": "Completed"},
                        {"label": "Cancelled", "value": "Cancelled"}
                    ],
                    value="In Progress",
                    className="mb-3"
                ),
                # Removed FormGroup wrapper
                dbc.Label("Status Notes (optional):"),
                dbc.Textarea(
                    id="status-notes",
                    placeholder="Add notes about this status change",
                    className="mb-3",
                    style={"height": "100px"}
                )
            ]),
            dbc.ModalFooter([
                dbc.Button(
                    "Cancel",
                    id="cancel-status-change",
                    color="secondary",
                    className="me-2"
                ),
                dbc.Button(
                    "Update Status",
                    id="confirm-status-change",
                    color="primary"
                ),
            ]),
        ],
        id="order-status-modal",
        is_open=False,
    )
    
    return modal

def robot_control_modal():
    """
    Create a robot control modal
    
    Returns:
        dbc.Modal: The modal component
    """
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Robot Control Panel"), close_button=True),
            dbc.ModalBody([
                html.Div(id="robot-status-display", className="mb-3"),
                html.Div([
                    dbc.Button(
                        "Dispatch Robot",
                        id="modal-dispatch-btn",
                        color="primary",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Recall Robot",
                        id="modal-recall-btn",
                        color="warning",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Emergency Stop",
                        id="modal-emergency-btn",
                        color="danger"
                    )
                ], className="mb-3"),
                html.Hr(),
                dbc.Label("Destination Override:"),
                dbc.Input(
                    id="destination-override",
                    placeholder="Enter coordinates or address",
                    className="mb-3"
                ),
                dbc.Button(
                    "Set Destination",
                    id="set-destination-btn",
                    color="secondary",
                    className="mb-3"
                )
            ]),
            dbc.ModalFooter(
                dbc.Button(
                    "Close",
                    id="close-robot-modal",
                    color="secondary"
                ),
            ),
        ],
        id="robot-control-modal",
        size="lg",
        is_open=False,
    )
    
    return modal