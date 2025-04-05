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

    fallback_chat = html.Div([
    html.Div([
        html.H4("Chat Service Unavailable", className="text-danger mb-3"),
        html.P("The BaristaBot chat service is currently offline.", className="mb-3"),
        html.P("Please try again later or use the quick actions below:", className="mb-4"),
        
        # Quick action buttons
        html.Div([
            dbc.Button("View Menu", color="primary", href="/menu", className="me-2 mb-2"),
            dbc.Button("Place Order", color="success", href="/orders", className="me-2 mb-2"),
            dbc.Button("Order Status", color="info", href="/orders", className="me-2 mb-2"),
            dbc.Button("Track Delivery", color="warning", href="/delivery", className="me-2 mb-2"),
            dbc.Button("Operating Hours", color="secondary", id="fallback-hours-btn", className="me-2 mb-2", n_clicks=0),
        ], className="mb-4"),
        
        # Hours collapse
        dbc.Collapse([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Neo Cafe Hours", className="card-title"),
                    html.P("Monday - Friday: 7am - 8pm", className="mb-1"),
                    html.P("Saturday - Sunday: 8am - 6pm", className="mb-1"),
                ])
            ])
        ], id="hours-collapse", is_open=False),
        
        # Helper text
        html.Div([
            html.Hr(),
            html.P([
                "If you need immediate assistance, please call us at ",
                html.Strong("(555) 123-4567"),
                " or visit us in person at ",
                html.Strong("123 Coffee Street, Downtown"),
                "."
            ], className="text-muted")
        ], className="mt-3")
    ], className="p-4 border rounded")
], id="simple-fallback-container", style={"display": "none"})
    
    # Chat interface with Chainlit integration
    chat_interface = dbc.Row([
    dbc.Col([
        dbc.Card([
            dbc.CardHeader([
                html.H4("BaristaBot", className="d-inline"),
                dbc.Badge("Online", color="success", className="ms-2"),
                html.Div([
                    dbc.Switch(
                        id="chat-implementation-toggle",
                        label="Use fallback mode",
                        value=False,
                        className="float-end"
                    ),
                ], className="float-end me-2")
            ]),
            dbc.CardBody([
                # Container for the iframe implementation
                html.Div([
                    # Loading spinner that shows while iframe is loading
                    dbc.Spinner(
                        html.Div(id="chainlit-loading-indicator", style={"height": "50px"}),
                        color="primary",
                        type="grow",
                    ),
                    
                    # Iframe with improved error handling
                    html.Iframe(
                        id="chainlit-frame",
                        src="/chainlit",
                        style={
                            "width": "100%",
                            "height": "600px",
                            "border": "none",
                            "borderRadius": "0.25rem"
                        }
                    ),
                    
                    # Hidden div for error messages
                    html.Div(id="chainlit-error", style={"display": "none"}),
                    
                ], id="chainlit-container"),
                
                # Container for the React implementation
                html.Div(id="react-chat-container", style={"display": "none", "height": "600px"}),
                
                # Container for the simple fallback implementation
                fallback_chat,

                # Add connection status check interval
                dcc.Interval(
                    id='chainlit-status-check',
                    interval=5000,  # check every 5 seconds
                    n_intervals=0
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