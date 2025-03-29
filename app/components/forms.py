# File: app/components/forms.py

import dash_bootstrap_components as dbc
from dash import html, dcc

def login_form():
    """
    Create a login form
    
    Returns:
        dbc.Form: Login form component
    """
    form = dbc.Form([
        dbc.Row([
            dbc.Col([
                dbc.Label("Username", html_for="login-username"),
                dbc.Input(
                    type="text",
                    id="login-username",
                    placeholder="Enter username",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Password", html_for="login-password"),
                dbc.Input(
                    type="password",
                    id="login-password",
                    placeholder="Enter password",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Checkbox(
                    id="login-remember",
                    label="Remember me",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Login",
                    id="login-button",
                    color="primary",
                    className="w-100"
                )
            ])
        ]),
        html.Div(id="login-alert")
    ])
    
    return form

def signup_form():
    """
    Create a signup form
    
    Returns:
        dbc.Form: Signup form component
    """
    form = dbc.Form([
        dbc.Row([
            dbc.Col([
                dbc.Label("Username", html_for="signup-username"),
                dbc.Input(
                    type="text",
                    id="signup-username",
                    placeholder="Enter username",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Email", html_for="signup-email"),
                dbc.Input(
                    type="email",
                    id="signup-email",
                    placeholder="Enter email",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Password", html_for="signup-password"),
                dbc.Input(
                    type="password",
                    id="signup-password",
                    placeholder="Enter password",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Confirm Password", html_for="signup-confirm-password"),
                dbc.Input(
                    type="password",
                    id="signup-confirm-password",
                    placeholder="Confirm password",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Sign Up",
                    id="signup-button",
                    color="primary",
                    className="w-100"
                )
            ])
        ]),
        html.Div(id="signup-alert")
    ])
    
    return form

def order_form():
    """
    Create an order form
    
    Returns:
        dbc.Form: Order form component
    """
    form = dbc.Form([
        dbc.Row([
            dbc.Col([
                dbc.Label("Delivery Location", html_for="order-location"),
                dbc.Select(
                    id="order-location",
                    options=[
                        {"label": "Table 1", "value": "Table 1"},
                        {"label": "Table 2", "value": "Table 2"},
                        {"label": "Table 3", "value": "Table 3"},
                        {"label": "Table 4", "value": "Table 4"},
                        {"label": "Table 5", "value": "Table 5"},
                        {"label": "Counter", "value": "Counter"},
                        {"label": "Outdoor Patio", "value": "Outdoor Patio"},
                        {"label": "Delivery", "value": "Delivery"}
                    ],
                    value="Table 1",
                    className="mb-3"
                )
            ], md=6),
            dbc.Col([
                dbc.Label("Payment Method", html_for="order-payment"),
                dbc.Select(
                    id="order-payment",
                    options=[
                        {"label": "Credit Card", "value": "Credit Card"},
                        {"label": "Cash", "value": "Cash"},
                        {"label": "Mobile Payment", "value": "Mobile Payment"}
                    ],
                    value="Credit Card",
                    className="mb-3"
                )
            ], md=6)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Special Instructions", html_for="order-instructions"),
                dbc.Textarea(
                    id="order-instructions",
                    placeholder="Enter any special instructions for your order",
                    className="mb-3",
                    style={"height": "100px"}
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Place Order",
                    id="submit-order-button",
                    color="primary",
                    className="me-2"
                ),
                dbc.Button(
                    "Clear",
                    id="clear-order-button",
                    color="secondary"
                )
            ])
        ]),
        html.Div(id="order-alert")
    ])
    
    return form

def contact_form():
    """
    Create a contact form
    
    Returns:
        dbc.Form: Contact form component
    """
    form = dbc.Form([
        dbc.Row([
            dbc.Col([
                dbc.Label("Name", html_for="contact-name"),
                dbc.Input(
                    type="text",
                    id="contact-name",
                    placeholder="Enter your name",
                    className="mb-3"
                )
            ], md=6),
            dbc.Col([
                dbc.Label("Email", html_for="contact-email"),
                dbc.Input(
                    type="email",
                    id="contact-email",
                    placeholder="Enter your email",
                    className="mb-3"
                )
            ], md=6)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Subject", html_for="contact-subject"),
                dbc.Input(
                    type="text",
                    id="contact-subject",
                    placeholder="Enter subject",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Message", html_for="contact-message"),
                dbc.Textarea(
                    id="contact-message",
                    placeholder="Enter your message",
                    className="mb-3",
                    style={"height": "150px"}
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Send Message",
                    id="contact-send-button",
                    color="primary"
                )
            ])
        ]),
        html.Div(id="contact-alert")
    ])
    
    return form

def profile_form(user_data=None):
    """
    Create a profile edit form
    
    Args:
        user_data (dict, optional): User data to pre-fill the form
        
    Returns:
        dbc.Form: Profile form component
    """
    # Default values
    default_values = {
        "username": "",
        "email": "",
        "first_name": "",
        "last_name": "",
        "phone": ""
    }
    
    # Update with provided user data if available
    if user_data:
        default_values.update({k: v for k, v in user_data.items() if k in default_values})
    
    form = dbc.Form([
        dbc.Row([
            dbc.Col([
                dbc.Label("Username", html_for="profile-username"),
                dbc.Input(
                    type="text",
                    id="profile-username",
                    value=default_values["username"],
                    disabled=True,  # Username cannot be changed
                    className="mb-3"
                )
            ], md=6),
            dbc.Col([
                dbc.Label("Email", html_for="profile-email"),
                dbc.Input(
                    type="email",
                    id="profile-email",
                    value=default_values["email"],
                    className="mb-3"
                )
            ], md=6)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("First Name", html_for="profile-first-name"),
                dbc.Input(
                    type="text",
                    id="profile-first-name",
                    value=default_values["first_name"],
                    className="mb-3"
                )
            ], md=6),
            dbc.Col([
                dbc.Label("Last Name", html_for="profile-last-name"),
                dbc.Input(
                    type="text",
                    id="profile-last-name",
                    value=default_values["last_name"],
                    className="mb-3"
                )
            ], md=6)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Phone", html_for="profile-phone"),
                dbc.Input(
                    type="tel",
                    id="profile-phone",
                    value=default_values["phone"],
                    className="mb-3"
                )
            ], md=6)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Update Profile",
                    id="profile-update-button",
                    color="primary",
                    className="me-2"
                ),
                dbc.Button(
                    "Change Password",
                    id="profile-password-button",
                    color="secondary"
                )
            ])
        ]),
        html.Div(id="profile-alert")
    ])
    
    return form

def password_change_form():
    """
    Create a password change form
    
    Returns:
        dbc.Form: Password change form component
    """
    form = dbc.Form([
        dbc.Row([
            dbc.Col([
                dbc.Label("Current Password", html_for="current-password"),
                dbc.Input(
                    type="password",
                    id="current-password",
                    placeholder="Enter your current password",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("New Password", html_for="new-password"),
                dbc.Input(
                    type="password",
                    id="new-password",
                    placeholder="Enter new password",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Confirm New Password", html_for="confirm-new-password"),
                dbc.Input(
                    type="password",
                    id="confirm-new-password",
                    placeholder="Confirm new password",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Change Password",
                    id="change-password-button",
                    color="primary"
                )
            ])
        ]),
        html.Div(id="password-alert")
    ])
    
    return form

def announcement_form():
    """
    Create an announcement form for staff
    
    Returns:
        dbc.Form: Announcement form component
    """
    form = dbc.Form([
        dbc.Row([
            dbc.Col([
                dbc.Label("Title", html_for="announcement-title"),
                dbc.Input(
                    type="text",
                    id="announcement-title",
                    placeholder="Enter announcement title",
                    className="mb-3"
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label("Content", html_for="announcement-content"),
                dbc.Textarea(
                    id="announcement-content",
                    placeholder="Enter announcement content",
                    className="mb-3",
                    style={"height": "150px"}
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label("Visibility"),
                    dbc.RadioItems(
                        options=[
                            {"label": "All Users", "value": "all"},
                            {"label": "Staff Only", "value": "staff"}
                        ],
                        value="all",
                        id="announcement-visibility",
                        inline=True,
                        className="mb-3"
                    )
                ])
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label("Duration"),
                    dbc.Select(
                        id="announcement-duration",
                        options=[
                            {"label": "1 day", "value": "1"},
                            {"label": "1 week", "value": "7"},
                            {"label": "2 weeks", "value": "14"},
                            {"label": "1 month", "value": "30"},
                            {"label": "Permanent", "value": "0"}
                        ],
                        value="7",
                        className="mb-3"
                    )
                ])
            ])
        ])
    ])
    
    return form