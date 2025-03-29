# File: app/layouts/delivery.py

import dash_bootstrap_components as dbc
from dash import html, dcc

def layout():
    """
    Create the delivery tracking layout
    
    Returns:
        html.Div: The delivery tracking content
    """
    # Header section
    header = html.Div([
        html.H1("Delivery Tracking", className="page-header"),
        html.P("Track and manage robot deliveries", className="lead")
    ])
    
    # Robot status overview
    status_row = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Robot Status Overview"),
                dbc.CardBody([
                    html.Div(id="robot-status-indicators")
                ])
            ])
        ])
    ], className="mb-4")
    
    # Map and deliveries section
    map_deliveries_row = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Live Tracking Map"),
                dbc.CardBody([
                    dcc.Graph(
                        id="robot-location-map",
                        config={'displayModeBar': False}
                    )
                ])
            ])
        ], md=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("Active Deliveries", className="d-inline"),
                    dbc.Button(
                        html.I(className="fas fa-sync-alt"),
                        id="refresh-deliveries-btn",
                        color="link",
                        size="sm",
                        className="float-end"
                    )
                ]),
                dbc.CardBody([
                    html.Div(id="active-deliveries-list")
                ])
            ])
        ], md=4)
    ], className="mb-4")
    
    # Delivery control section
    control_row = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Delivery Controls"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Dispatch Robot",
                                id="dispatch-robot-btn",
                                color="primary",
                                className="w-100 mb-2"
                            ),
                            dbc.Button(
                                "Recall Robot",
                                id="recall-robot-btn",
                                color="warning",
                                className="w-100 mb-2"
                            ),
                            dbc.Button(
                                "Emergency Stop",
                                id="emergency-stop-btn",
                                color="danger",
                                className="w-100 mb-4"
                            )
                        ], md=6),
                        dbc.Col([
                            html.H6("Delivery Queue", className="mb-3"),
                            dbc.ListGroup([
                                dbc.ListGroupItem(
                                    "Order ORD-1234570 waiting...",
                                    className="d-flex justify-content-between align-items-center"
                                ),
                                dbc.ListGroupItem(
                                    "Order ORD-1234571 waiting...",
                                    className="d-flex justify-content-between align-items-center"
                                )
                            ], flush=True)
                        ], md=6)
                    ])
                ])
            ])
        ])
    ])
    
    # Combine all elements
    layout = html.Div([
        header,
        status_row,
        map_deliveries_row,
        control_row,
        
        # Hidden stores for delivery data
        dcc.Store(id="delivery-data-store", storage_type="memory"),
        dcc.Store(id="delivery-update-store", storage_type="memory")
    ])
    
    return layout