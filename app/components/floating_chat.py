# File: app/components/floating_chat.py

import dash_bootstrap_components as dbc
from dash import html, dcc

def create_floating_chat():
    """
    Create a floating chat button and panel component with enhanced functionality
    
    Returns:
        html.Div: The floating chat component
    """
    # Floating chat button (fixed position at bottom right)
    chat_button = html.Div(
        html.Button(
            [
                html.I(className="fas fa-comments me-2"),
                html.Span("Chat with BaristaBot", className="chat-button-text")
            ],
            id="floating-chat-button",
            className="floating-chat-button d-flex align-items-center"
        ),
        className="floating-chat-button-container"
    )
    # Chat panel (initially hidden) - Using the original chat layout
    chat_panel = html.Div(
        [
            # Chat header with title and close button
            html.Div(
                [
                    html.Div(
                        [
                            html.Img(src="/assets/images/logo.png", height="30px", className="me-2"),
                            html.H5("BaristaBot", className="m-0")
                        ],
                        className="d-flex align-items-center"
                    ),
            html.Div(
                [
                    html.Button(
                        [
                            # Use both Font Awesome and HTML entity for minus
                            html.I(className="fas fa-minus me-1"),
                            html.Span("−", className="btn-symbol")  # Unicode minus symbol
                        ],
                        id="minimize-chat-button",
                        className="chat-control-button me-2",
                        title="Minimize Chat"
                    ),
                    html.Button(
                        [
                            # Use both Font Awesome and HTML entity for X
                            html.I(className="fas fa-times me-1"),
                            html.Span("×", className="btn-symbol")  # Unicode multiplication X
                        ],
                        id="close-chat-button",
                        className="chat-control-button",
                        title="Close Chat"
                    )
                ],
                className="d-flex"
            )
                ],
                className="chat-panel-header d-flex justify-content-between align-items-center"
            ),
            
            # Main chat content - Using the original chat.py layout
            html.Div(
                [
                    # Left column: Chainlit iframe
                    html.Div(
                        html.Iframe(
                            id="floating-chainlit-frame",
                            src="",  # Will be set by callback
                            style={
                                "width": "100%",
                                "height": "100%",
                                "border": "none",
                                "borderRadius": "0"
                            }
                        ),
                        className="chat-panel-body-left"
                    ),
                    
                    # Right column: Quick actions and order status
                    html.Div(
                        [
                            # Quick actions card
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
                                ])
                            ], className="mb-3"),
                            
                            # Current order status card
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
                        ],
                        className="chat-panel-body-right"
                    )
                ],
                className="chat-panel-body d-flex"
            ),
            
            # Footer with quick access buttons
            html.Div(
                [
                    dbc.Button(
                        html.I(className="fas fa-microphone me-2"),
                        id="voice-toggle-btn",
                        color="link",
                        className="me-2 p-0",
                        size="sm"
                    ),
                    html.Div([
                        dbc.Button(
                            "Menu",
                            id="faq-menu-btn",
                            color="link",
                            className="me-2 p-0",
                            size="sm"
                        ),
                        dbc.Button(
                            "Hours",
                            id="faq-hours-btn",
                            color="link",
                            className="me-2 p-0",
                            size="sm"
                        ),
                        dbc.Button(
                            "Robot",
                            id="faq-robot-btn",
                            color="link",
                            className="me-2 p-0",
                            size="sm"
                        ),
                        dbc.Button(
                            "Popular",
                            id="faq-popular-btn",
                            color="link",
                            className="p-0",
                            size="sm"
                        )
                    ])
                ],
                className="chat-panel-footer d-flex justify-content-between align-items-center px-3 py-2"
            )
        ],
        id="floating-chat-panel",
        className="floating-chat-panel",
        style={"display": "none"}  # Initially hidden
    )
    
    # Common questions element (from original chat layout)
    # This is hidden by default and only shown in expanded mode
    faq_section = html.Div(
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Common Questions"),
                    dbc.CardBody([
                        dbc.ListGroup([
                            dbc.ListGroupItem(
                                "What's on the menu?", 
                                action=True, 
                                id="menu-faq-btn",
                                className="d-flex justify-content-between align-items-center"
                            ),
                            dbc.ListGroupItem(
                                "What are your operating hours?", 
                                action=True, 
                                id="hours-faq-btn",
                                className="d-flex justify-content-between align-items-center"
                            ),
                            dbc.ListGroupItem(
                                "How does robot delivery work?", 
                                action=True, 
                                id="robot-faq-btn",
                                className="d-flex justify-content-between align-items-center"
                            ),
                            dbc.ListGroupItem(
                                "What's your most popular coffee?", 
                                action=True, 
                                id="popular-faq-btn",
                                className="d-flex justify-content-between align-items-center"
                            ),
                        ], flush=True)
                    ])
                ])
            ], md=12)
        ]),
        id="chat-faq-section",
        style={"display": "none"}  # Initially hidden, shown in expanded mode
    )
    
     # Hidden div for Socket.IO communication
    hidden_elements = html.Div([
        # This is used to receive updates from Socket.IO
        html.Div(id="floating-chat-socket-update", 
                 **{"data-open-chat": False},  # For opening the chat panel
                 style={"display": "none"}),
        
        # Status elements for debugging
        html.Div(id="chat-connection-status", style={"display": "none"}),
        html.Div(id="direct-message-status", style={"display": "none"})
    ], style={"display": "none"})
    
    # Combine button, panel, hidden faq section, and hidden elements
    floating_chat = html.Div(
        [chat_button, chat_panel, faq_section, hidden_elements],
        id="floating-chat-container"
    )
    
    return floating_chat