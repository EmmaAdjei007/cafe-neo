# File: app/layouts/auth.py

import dash_bootstrap_components as dbc
from dash import html, dcc
from app.components.forms import login_form, signup_form
from app.components.modals import signup_success_modal

def login_layout():
    """
    Create the login page layout
    
    Returns:
        html.Div: The login page content
    """
    # Create header
    header = html.Div([
        html.H1("Login", className="page-header text-center"),
        html.P("Welcome back to Neo Cafe! Please login to continue.", className="lead text-center mb-5")
    ])
    
    # Create login section
    login_section = dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    login_form(),
                    html.Hr(className="my-4"),
                    html.Div([
                        html.Span("Don't have an account? "),
                        dbc.Button("Sign Up", id="login-to-signup", color="link", className="p-0")
                    ], className="text-center"),
                    html.Div([
                        html.Span("Forgot your password? "),
                        dbc.Button("Reset Password", id="forgot-password", color="link", className="p-0")
                    ], className="text-center mt-2"),
                ])
            ]),
            md=6,
            className="mx-auto"
        )
    ])
    
    # Create login callout
    callout = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Demo Accounts", className="card-title"),
                    html.P("You can use the following demo accounts to try the application:"),
                    
                    dbc.Table([
                        html.Thead(html.Tr([
                            html.Th("Username"),
                            html.Th("Password"),
                            html.Th("Role")
                        ])),
                        html.Tbody([
                            html.Tr([
                                html.Td("admin"),
                                html.Td("password"),
                                html.Td("Administrator")
                            ]),
                            html.Tr([
                                html.Td("staff"),
                                html.Td("password"),
                                html.Td("Staff Member")
                            ]),
                            html.Tr([
                                html.Td("customer"),
                                html.Td("password"),
                                html.Td("Customer")
                            ])
                        ])
                    ], bordered=True, size="sm")
                ])
            ], className="mt-4 bg-light")
        ], md=6, className="mx-auto")
    ])
    
    # Combine all elements
    layout = html.Div([
        header,
        login_section,
        callout,
        
        # Add alert container for messages
        html.Div(id="login-message-container", className="mt-3"),
        
        # Add hidden div for callback triggers
        html.Div(id="login-trigger", style={"display": "none"})
    ])
    
    return layout

def signup_layout():
    """
    Create the signup page layout
    
    Returns:
        html.Div: The signup page content
    """
    # Create header
    header = html.Div([
        html.H1("Sign Up", className="page-header text-center"),
        html.P("Create a Neo Cafe account to place orders and earn rewards.", className="lead text-center mb-5")
    ])
    
    # Create signup section
    signup_section = dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    signup_form(),
                    html.Hr(className="my-4"),
                    html.Div([
                        html.Span("Already have an account? "),
                        dbc.Button("Log In", id="signup-to-login", color="link", className="p-0")
                    ], className="text-center")
                ])
            ]),
            md=6,
            className="mx-auto"
        )
    ])
    
    # Create benefits section
    benefits = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Benefits of Joining", className="card-title"),
                    html.Ul([
                        html.Li("Quick and easy online ordering"),
                        html.Li("Earn rewards with every purchase"),
                        html.Li("Get exclusive access to special promotions"),
                        html.Li("Save your favorite orders for quick reordering"),
                        html.Li("Track your order and delivery status in real-time")
                    ])
                ])
            ], className="mt-4")
        ], md=6, className="mx-auto")
    ])
    
    # Combine all elements
    layout = html.Div([
        header,
        signup_section,
        benefits,
        
        # Add success modal
        signup_success_modal(),
        
        # Add alert container for messages
        html.Div(id="signup-message-container", className="mt-3"),
        
        # Add hidden div for callback triggers
        html.Div(id="signup-trigger", style={"display": "none"})
    ])
    
    return layout

def reset_password_layout():
    """
    Create the password reset page layout
    
    Returns:
        html.Div: The password reset page content
    """
    # Create header
    header = html.Div([
        html.H1("Reset Password", className="page-header text-center"),
        html.P("Enter your email address to receive a password reset link.", className="lead text-center mb-5")
    ])
    
    # Create reset form
    reset_form = dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    dbc.Form([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Email", html_for="reset-email"),
                                dbc.Input(
                                    type="email",
                                    id="reset-email",
                                    placeholder="Enter your email address",
                                    className="mb-3"
                                )
                            ])
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "Send Reset Link",
                                    id="send-reset-button",
                                    color="primary",
                                    className="w-100"
                                )
                            ])
                        ]),
                        html.Div(id="reset-alert")
                    ]),
                    html.Hr(className="my-4"),
                    html.Div([
                        html.Span("Remember your password? "),
                        dbc.Button("Log In", id="reset-to-login", color="link", className="p-0")
                    ], className="text-center")
                ])
            ]),
            md=6,
            className="mx-auto"
        )
    ])
    
    # Combine all elements
    layout = html.Div([
        header,
        reset_form,
        
        # Add alert container for messages
        html.Div(id="reset-message-container", className="mt-3"),
        
        # Add hidden div for callback triggers
        html.Div(id="reset-trigger", style={"display": "none"})
    ])
    
    return layout

def logout_layout():
    """
    Create the logout page layout
    
    Returns:
        html.Div: The logout page content
    """
    # Create logout confirmation
    logout_content = dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H3("You have been logged out", className="text-center"),
                    html.P("Thank you for visiting Neo Cafe.", className="text-center mb-4"),
                    html.Div([
                        dbc.Button("Log In Again", href="/login", color="primary", className="me-2"),
                        dbc.Button("Home", href="/", color="secondary")
                    ], className="text-center")
                ])
            ]),
            md=6,
            className="mx-auto"
        )
    ])
    
    # Combine all elements
    layout = html.Div([
        html.Div(style={"height": "100px"}),  # Spacer
        logout_content,
        
        # Alert for logout message
        html.Div(id="logout-alert", className="mt-3 d-flex justify-content-center")
    ])
    
    return layout