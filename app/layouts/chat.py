# File: app/layouts/chat.py

import dash_bootstrap_components as dbc
from dash import html, dcc

def layout():
    """
    Create the chat layout with integrated Chainlit
    
    Returns:
        html.Div: The chat interface content
    """
    header = html.Div([
        html.H1("Neo Cafe Assistant", className="page-header"),
        html.P("Ask questions, place orders, or get help from our virtual barista", className="lead")
    ])
    
    # Chat interface with Chainlit integration
    chat_interface = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("BaristaBot", className="d-inline"),
                    dbc.Badge("Online", color="success", className="ms-2")
                ]),
                dbc.CardBody([
                    # Chainlit integration via iframe
                    html.Iframe(
                        id="chainlit-frame",
                        src="/chainlit",  # This will be handled by a Flask route
                        style={
                            "width": "100%",
                            "height": "600px",
                            "border": "none",
                            "borderRadius": "0.25rem"
                        }
                    )
                ]),
                dbc.CardFooter([
                    dbc.Button(
                        html.I(className="fas fa-microphone"),
                        id="voice-toggle-btn",
                        color="primary",
                        className="me-2",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "Order Status",
                        id="order-status-btn",
                        color="info",
                        className="me-2",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "View Menu",
                        id="view-menu-btn",
                        color="secondary",
                        className="me-2",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "Help",
                        id="chat-help-btn",
                        color="link",
                        className="me-2",
                        n_clicks=0
                    )
                ])
            ])
        ], md=8),
        dbc.Col([
            # Sidebar with quick actions and information
            dbc.Card([
                dbc.CardHeader("Quick Actions"),
                dbc.CardBody([
                    dbc.Button(
                        "Place Order",
                        id="quick-order-btn",
                        color="primary",
                        className="mb-2 w-100",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "Track Delivery",
                        id="quick-track-btn",
                        color="info",
                        className="mb-2 w-100",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "Popular Items",
                        id="quick-popular-btn",
                        color="secondary",
                        className="mb-2 w-100",
                        n_clicks=0
                    ),
                    dbc.Button(
                        "Operating Hours",
                        id="quick-hours-btn",
                        color="secondary",
                        className="mb-4 w-100",
                        n_clicks=0
                    ),
                ]),
            ], className="mb-3"),
            
            # Current order status card (if any)
            dbc.Card([
                dbc.CardHeader([
                    html.H5("Your Current Order", className="d-inline"),
                    dbc.Button(
                        html.I(className="fas fa-sync-alt"),
                        id="refresh-order-btn",
                        color="link",
                        size="sm",
                        className="float-end",
                        n_clicks=0
                    )
                ]),
                dbc.CardBody(id="current-order-status", children=[
                    html.P("No active order.", className="text-muted")
                ])
            ])
        ], md=4)
    ])
    
    # Common queries and help section
    help_section = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Common Questions"),
                dbc.CardBody([
                    dbc.ListGroup([
                        dbc.ListGroupItem(
                            "What's on the menu?", 
                            action=True, 
                            id="faq-menu-btn",
                            className="d-flex justify-content-between align-items-center"
                        ),
                        dbc.ListGroupItem(
                            "What are your operating hours?", 
                            action=True, 
                            id="faq-hours-btn",
                            className="d-flex justify-content-between align-items-center"
                        ),
                        dbc.ListGroupItem(
                            "How does robot delivery work?", 
                            action=True, 
                            id="faq-robot-btn",
                            className="d-flex justify-content-between align-items-center"
                        ),
                        dbc.ListGroupItem(
                            "What's your most popular coffee?", 
                            action=True, 
                            id="faq-popular-btn",
                            className="d-flex justify-content-between align-items-center"
                        ),
                    ], flush=True)
                ])
            ])
        ], md=12)
    ], className="mt-4")
    
    # Combine all elements
    layout = html.Div([
        header,
        chat_interface,
        help_section,
        
        # Hidden store for chat state
        dcc.Store(id='chat-state-store', storage_type='session'),
        
        # Hidden div for chat callback triggers
        html.Div(id='chat-action-trigger', style={'display': 'none'})
    ])
    
    return layout