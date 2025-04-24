# File: app/components/delivery_widgets.py

import dash_bootstrap_components as dbc
from dash import html, dcc

def robot_delivery_status_widget(order_id=None):
    """
    Create a robot delivery status widget component
    
    Args:
        order_id (str, optional): Order ID to track
        
    Returns:
        dbc.Card: The status widget component
    """
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-robot me-2"),
                "Robot Delivery Status"
            ], className="d-inline"),
            dbc.Button(
                html.I(className="fas fa-sync-alt"),
                id="refresh-robot-status-btn",
                color="link",
                size="sm",
                className="float-end"
            )
        ]),
        dbc.CardBody([
            # Order ID selector or display
            dbc.Row([
                dbc.Col([
                    dbc.Label("Order ID:"),
                    dbc.InputGroup([
                        dbc.Input(
                            id="robot-tracking-order-id",
                            value=order_id or "",
                            placeholder="Enter order ID to track"
                        ),
                        dbc.Button(
                            "Track",
                            id="track-robot-order-btn",
                            color="primary"
                        )
                    ], className="mb-3")
                ], md=12)
            ]),
            
            # Status indicators
            html.Div([
                # Progress steps
                dbc.Row([
                    dbc.Col([
                        dbc.Progress([
                            dbc.Progress(value=100, color="success", bar=True, label="Preparing", style={"width": "25%"}),
                            dbc.Progress(
                                id="robot-dispatch-progress",
                                value=0, 
                                color="info", 
                                bar=True, 
                                label="Dispatched", 
                                style={"width": "25%"}
                            ),
                            dbc.Progress(
                                id="robot-transit-progress",
                                value=0, 
                                color="info", 
                                bar=True, 
                                label="In Transit", 
                                style={"width": "25%"}
                            ),
                            dbc.Progress(
                                id="robot-delivery-progress",
                                value=0, 
                                color="info", 
                                bar=True, 
                                label="Delivered", 
                                style={"width": "25%"}
                            )
                        ], style={"height": "30px"}),
                    ], md=12, className="mb-3")
                ]),
                
                # Current status
                dbc.Row([
                    dbc.Col([
                        html.H5("Current Status:"),
                        html.Div(id="robot-current-status", children=[
                            dbc.Badge("Preparing Order", color="primary", className="p-2 fs-6")
                        ])
                    ], md=6),
                    dbc.Col([
                        html.H5("Estimated Arrival:"),
                        html.Div(id="robot-eta", children=[
                            html.Span("Calculating...", className="fs-5")
                        ])
                    ], md=6)
                ], className="mb-3"),
                
                # Robot details
                dbc.Row([
                    dbc.Col([
                        html.H5("Robot Details:"),
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Strong("Robot ID: "),
                                html.Span(id="robot-id", children="--")
                            ]),
                            dbc.ListGroupItem([
                                html.Strong("Battery: "),
                                html.Span(id="robot-battery", children="--")
                            ]),
                            dbc.ListGroupItem([
                                html.Strong("Speed: "),
                                html.Span(id="robot-speed", children="--")
                            ])
                        ], flush=True, className="mb-3")
                    ], md=12)
                ]),
                
                # Action buttons
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "View on Map",
                            id="view-robot-map-btn",
                            color="primary",
                            className="me-2",
                            href="/delivery"
                        ),
                        dbc.Button(
                            "Send Message to Robot",
                            id="message-robot-btn",
                            color="secondary"
                        )
                    ], className="d-flex")
                ])
            ], id="robot-status-container")
        ])
    ])

def robot_control_widget():
    """
    Create a robot control widget for staff dashboard
    
    Returns:
        dbc.Card: The control widget component
    """
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-robot me-2"),
                "Robot Fleet Control"
            ], className="d-inline"),
            dbc.Badge("Staff Only", color="warning", className="ms-2")
        ]),
        dbc.CardBody([
            # Robot status overview
            dbc.Row([
                dbc.Col([
                    html.H6("Available Robots:"),
                    html.Div(id="available-robots-count", children=[
                        dbc.Badge("3", color="success", className="p-2 fs-5")
                    ])
                ], md=4),
                dbc.Col([
                    html.H6("Active Deliveries:"),
                    html.Div(id="active-robots-count", children=[
                        dbc.Badge("2", color="primary", className="p-2 fs-5")
                    ])
                ], md=4),
                dbc.Col([
                    html.H6("Fleet Status:"),
                    html.Div(id="fleet-status", children=[
                        dbc.Badge("Operational", color="success", className="p-2 fs-5")
                    ])
                ], md=4)
            ], className="mb-3"),
            
            # Robot selector
            dbc.Row([
                dbc.Col([
                    dbc.Label("Select Robot:"),
                    dbc.Select(
                        id="robot-selector",
                        options=[
                            {"label": "All Robots", "value": "all"},
                            {"label": "Robot-001", "value": "robot-001"},
                            {"label": "Robot-002", "value": "robot-002"},
                            {"label": "Robot-003", "value": "robot-003"},
                            {"label": "Robot-004", "value": "robot-004"},
                            {"label": "Robot-005", "value": "robot-005"}
                        ],
                        value="all",
                        className="mb-3"
                    )
                ], md=12)
            ]),
            
            # Control buttons
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Dispatch Robot",
                        id="dispatch-robot-btn",
                        color="primary",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Recall Robot",
                        id="recall-robot-btn",
                        color="warning",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Emergency Stop",
                        id="emergency-stop-btn",
                        color="danger"
                    )
                ], className="d-flex mb-3")
            ]),
            
            # Interface control
            dbc.Row([
                dbc.Col([
                    dbc.Label("Network Interface:"),
                    dbc.Input(
                        id="robot-interface-input",
                        placeholder="Network interface (e.g., en7)",
                        value="en7",
                        className="mb-2"
                    ),
                    dbc.FormText("Specify the network interface used for robot communication"),
                    dbc.Button(
                        "Test Connection",
                        id="test-robot-connection-btn",
                        color="secondary",
                        size="sm",
                        className="mt-2"
                    )
                ], md=12)
            ])
        ])
    ])