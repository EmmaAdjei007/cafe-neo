# File: app/layouts/navbar.py

import dash_bootstrap_components as dbc
from dash import html

def create_navbar():
    """
    Create the navigation bar for the app
    
    Returns:
        dbc.Navbar: The navbar component
    """
    navbar = dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo/brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src="/assets/images/logo.png", height="40px"), width="auto"),
                            dbc.Col(dbc.NavbarBrand("Neo Cafe", className="ms-2 brand-text")),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="/",
                    style={"textDecoration": "none"},
                ),
                # Toggle button for mobile view
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                # Navigation links that will collapse on mobile
                dbc.Collapse(
                    dbc.Nav(
                        [
                            dbc.NavItem(dbc.NavLink("Dashboard", href="/dashboard", id="dashboard-link")),
                            dbc.NavItem(dbc.NavLink("Menu", href="/menu", id="menu-link")),
                            dbc.NavItem(dbc.NavLink("Orders", href="/orders", id="orders-link")),
                            dbc.NavItem(dbc.NavLink("Delivery", href="/delivery", id="delivery-link")),
                            # Chat link removed, as it's now floating
                            
                            # Auth buttons - show conditionally based on login state
                            html.Div([
                                dbc.Button(
                                    "Login", 
                                    id="navbar-login-btn", 
                                    color="light", 
                                    className="me-2"
                                ),
                                dbc.Button(
                                    "Sign Up", 
                                    id="navbar-signup-btn", 
                                    color="success"
                                )
                            ], id="auth-buttons", className="ms-auto d-flex"),
                            
                            # User dropdown - show when logged in
                            dbc.DropdownMenu(
                                [
                                    dbc.DropdownMenuItem("Profile", href="/profile", id="profile-link"),
                                    dbc.DropdownMenuItem("Settings", href="/settings", id="settings-link"),
                                    dbc.DropdownMenuItem(divider=True),
                                    dbc.DropdownMenuItem("Logout", href="/logout", id="logout-link"),
                                ],
                                nav=True,
                                label="Account",
                                id="account-dropdown",
                                align_end=True,
                                style={"display": "none"}  # Hide by default
                            ),
                        ],
                        className="ms-auto",
                        navbar=True,
                    ),
                    id="navbar-collapse",
                    navbar=True,
                ),
            ],
            fluid=True,
        ),
        color="primary",
        dark=True,
        sticky="top",
        className="mb-4",
    )
    
    return navbar