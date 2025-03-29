# File: app/layouts/profile.py

import dash_bootstrap_components as dbc
from dash import html, dcc
from app.components.forms import profile_form
from app.components.modals import password_change_modal
from app.components.tables import create_order_history_table

def layout():
    """
    Create the user profile page layout
    
    Returns:
        html.Div: The profile page content
    """
    # Create header
    header = html.Div([
        html.H1("My Profile", className="page-header"),
        html.P("Manage your account and view order history", className="lead")
    ])
    
    # Create tabs for different profile sections
    tabs = dbc.Tabs(
        [
            dbc.Tab(label="Account Information", tab_id="account-info"),
            dbc.Tab(label="Order History", tab_id="profile-orders"),
            dbc.Tab(label="Payment Methods", tab_id="payment-methods"),
            dbc.Tab(label="Preferences", tab_id="preferences")
        ],
        id="profile-tabs",
        active_tab="account-info",
        className="mb-4"
    )
    
    # Account Info Tab Content
    account_info_tab = html.Div([
        dbc.Row([
            # Profile information (left column)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Profile Information"),
                    dbc.CardBody([
                        # Profile content will be filled by callback
                        html.Div(id="profile-content")
                    ])
                ])
            ], md=8),
            
            # Account actions (right column)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Account Actions"),
                    dbc.CardBody([
                        dbc.Button(
                            "Change Password",
                            id="change-password-btn",
                            color="primary",
                            className="w-100 mb-2"
                        ),
                        dbc.Button(
                            "Update Email Preferences",
                            id="email-prefs-btn",
                            color="secondary",
                            className="w-100 mb-2"
                        ),
                        dbc.Button(
                            "Manage Payment Methods",
                            id="manage-payment-btn",
                            color="secondary",
                            className="w-100 mb-4"
                        ),
                        dbc.Button(
                            "Delete Account",
                            id="delete-account-btn",
                            color="danger",
                            className="w-100"
                        )
                    ])
                ]),
                dbc.Card([
                    dbc.CardHeader("Loyalty Status"),
                    dbc.CardBody([
                        html.Div([
                            html.H4("Gold Member", className="text-center mb-3"),
                            dbc.Progress(value=75, color="warning", className="mb-3"),
                            html.P("You have 75 points towards your next reward", className="text-center"),
                            dbc.Button(
                                "View Rewards",
                                id="view-rewards-btn",
                                color="link",
                                className="w-100"
                            )
                        ])
                    ])
                ], className="mt-3")
            ], md=4)
        ])
    ], id="account-info-content", style={"display": "block"})
    
    # Order History Tab Content
    order_history_tab = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Your Order History", className="d-inline"),
                        dbc.Button(
                            html.I(className="fas fa-sync-alt"),
                            id="refresh-profile-orders-btn",
                            color="link",
                            size="sm",
                            className="float-end"
                        )
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Filter by Status:"),
                                dbc.Select(
                                    id="profile-order-filter",
                                    options=[
                                        {"label": "All", "value": "All"},
                                        {"label": "Completed", "value": "Completed"},
                                        {"label": "In Progress", "value": "In Progress"},
                                        {"label": "Cancelled", "value": "Cancelled"}
                                    ],
                                    value="All",
                                    className="mb-3"
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label("Date Range:"),
                                dcc.DatePickerRange(
                                    id="profile-order-date-range",
                                    className="mb-3"
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label("Search:"),
                                dbc.Input(
                                    id="profile-order-search",
                                    placeholder="Search orders...",
                                    type="text",
                                    className="mb-3"
                                )
                            ], md=4)
                        ], className="mb-3"),
                        html.Div(id="profile-order-history-container")
                    ])
                ])
            ])
        ])
    ], id="profile-orders-content", style={"display": "none"})
    
    # Payment Methods Tab Content
    payment_methods_tab = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Saved Payment Methods", className="d-inline"),
                        dbc.Button(
                            "Add New Card",
                            id="add-payment-btn",
                            color="primary",
                            size="sm",
                            className="float-end"
                        )
                    ]),
                    dbc.CardBody([
                        # Payment methods will be filled by callback
                        html.Div(id="payment-methods-container")
                    ])
                ])
            ])
        ])
    ], id="payment-methods-content", style={"display": "none"})
    
    # Preferences Tab Content
    preferences_tab = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Communication Preferences"),
                    dbc.CardBody([
                        dbc.Form([
                            dbc.Label("Email Notifications:"),
                            dbc.Checklist(
                                options=[
                                    {"label": "Order confirmations", "value": "order_confirm"},
                                    {"label": "Order status updates", "value": "order_status"},
                                    {"label": "Special promotions", "value": "promotions"},
                                    {"label": "Newsletter", "value": "newsletter"}
                                ],
                                value=["order_confirm", "order_status"],
                                id="email-preferences",
                                inline=False,
                                className="mb-3"
                            ),
                            dbc.Label("SMS Notifications:"),
                            dbc.Checklist(
                                options=[
                                    {"label": "Order ready notifications", "value": "order_ready"},
                                    {"label": "Delivery updates", "value": "delivery"}
                                ],
                                value=["order_ready"],
                                id="sms-preferences",
                                inline=False,
                                className="mb-3"
                            ),
                            dbc.Label("App Notifications:"),
                            dbc.Checklist(
                                options=[
                                    {"label": "Order status", "value": "app_order_status"},
                                    {"label": "Special offers", "value": "app_offers"},
                                    {"label": "New menu items", "value": "app_menu"}
                                ],
                                value=["app_order_status", "app_offers"],
                                id="app-preferences",
                                inline=False,
                                className="mb-3"
                            ),
                            dbc.Button(
                                "Save Preferences",
                                id="save-preferences-btn",
                                color="primary"
                            )
                        ])
                    ])
                ])
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Display Preferences"),
                    dbc.CardBody([
                        dbc.Form([
                            dbc.Label("Theme:"),
                            dbc.RadioItems(
                                options=[
                                    {"label": "Light Theme", "value": "light"},
                                    {"label": "Dark Theme", "value": "dark"},
                                    {"label": "System Default", "value": "system"}
                                ],
                                value="light",
                                id="theme-preference",
                                inline=False,
                                className="mb-3"
                            ),
                            dbc.Label("Date Format:"),
                            dbc.Select(
                                id="date-format-preference",
                                options=[
                                    {"label": "MM/DD/YYYY", "value": "mm/dd/yyyy"},
                                    {"label": "DD/MM/YYYY", "value": "dd/mm/yyyy"},
                                    {"label": "YYYY-MM-DD", "value": "yyyy-mm-dd"}
                                ],
                                value="mm/dd/yyyy",
                                className="mb-3"
                            ),
                            dbc.Label("Default Ordering Location:"),
                            dbc.Select(
                                id="location-preference",
                                options=[
                                    {"label": "Dine In", "value": "dine_in"},
                                    {"label": "Takeout", "value": "takeout"},
                                    {"label": "Delivery", "value": "delivery"}
                                ],
                                value="dine_in",
                                className="mb-3"
                            ),
                            dbc.Button(
                                "Save Preferences",
                                id="save-display-prefs-btn",
                                color="primary"
                            )
                        ])
                    ])
                ]),
                dbc.Card([
                    dbc.CardHeader("Favorites"),
                    dbc.CardBody([
                        dbc.Label("Quick Order Favorites:"),
                        html.Div(id="favorites-container", className="mb-3"),
                        dbc.Button(
                            "Manage Favorites",
                            id="manage-favorites-btn",
                            color="secondary"
                        )
                    ])
                ], className="mt-3")
            ], md=6)
        ])
    ], id="preferences-content", style={"display": "none"})
    
    # Combine all elements
    layout = html.Div([
        header,
        tabs,
        account_info_tab,
        order_history_tab,
        payment_methods_tab,
        preferences_tab,
        
        # Add modals
        password_change_modal(),
        
        # Add alert container for messages
        html.Div(id="profile-alert-container", className="mt-3"),
        
        # Hidden stores for user data
        dcc.Store(id="profile-data-store", storage_type="session"),
        
        # Hidden div for callback triggers
        html.Div(id="profile-action-trigger", style={"display": "none"})
    ])
    
    return layout

def create_profile_content(user_data):
    """
    Create profile content based on user data
    
    Args:
        user_data (dict): User profile data
        
    Returns:
        html.Div: Profile content
    """
    # Default display if no user data
    if not user_data:
        return html.Div([
            dbc.Alert("Unable to load user profile", color="danger")
        ])
    
    # Create profile content
    profile_content = html.Div([
        profile_form(user_data),
        html.Div(id="profile-update-alert")
    ])
    
    return profile_content