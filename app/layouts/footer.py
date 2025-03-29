# File: app/layouts/footer.py

import dash_bootstrap_components as dbc
from dash import html

def create_footer():
    """
    Create the footer component for the app
    
    Returns:
        html.Footer: The footer component
    """
    footer = html.Footer(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                           html.Div(
                                    [
                                        html.Img(src="/assets/images/logo.png", height="40px", className="mb-3"),
                                    ],
                                    className="pe-lg-5"
                                ),             
                    html.H5("Neo Cafe", className="text-light"),
                    html.P("Give me coffee or give me death", className="text-light opacity-75"),
                    html.P("© 2025 Neo Cafe. All rights reserved.", className="text-light opacity-75")
                ], md=4),
                dbc.Col([
                    html.H5("Contact", className="text-light"),
                    html.P([
                        html.I(className="fas fa-map-marker-alt me-2"),
                        "123 Coffee Street, Downtown"
                    ], className="text-light opacity-75"),
                    html.P([
                        html.I(className="fas fa-phone me-2"),
                        "(555) 123-4567"
                    ], className="text-light opacity-75"),
                    html.P([
                        html.I(className="fas fa-envelope me-2"),
                        "info@neocafe.com"
                    ], className="text-light opacity-75")
                ], md=4),
                dbc.Col([
                    html.H5("Hours", className="text-light"),
                    html.P("Monday - Friday: 7am - 8pm", className="text-light opacity-75"),
                    html.P("Saturday - Sunday: 8am - 6pm", className="text-light opacity-75"),
                    html.Div([
                        dbc.Button(
                            html.I(className="fab fa-facebook"),
                            color="link",
                            className="text-light me-2",
                            size="sm"
                        ),
                        dbc.Button(
                            html.I(className="fab fa-twitter"),
                            color="link",
                            className="text-light me-2",
                            size="sm"
                        ),
                        dbc.Button(
                            html.I(className="fab fa-instagram"),
                            color="link",
                            className="text-light me-2",
                            size="sm"
                        )
                    ])
                ], md=4)
            ], className="py-4")
        ]),
        className="bg-dark mt-5"
    )
    
    return footer