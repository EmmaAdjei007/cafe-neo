# File: app/layouts/orders.py

import dash_bootstrap_components as dbc
from dash import html, dcc
from app.components.forms import order_form
from app.components.modals import order_details_modal, confirm_order_modal, order_status_modal
from app.components.tables import create_order_items_table



def layout():
    """
    Create the orders page layout
    
    Returns:
        html.Div: The orders page content
    """
    # Create header
    header = html.Div([
        html.H1("Orders", className="page-header"),
        html.P("Manage your orders and checkout", className="lead")
    ])
    
    # Create tabs for different order views
    tabs = dbc.Tabs(
        [
            dbc.Tab(label="Current Order", tab_id="current-order"),
            dbc.Tab(label="Order History", tab_id="order-history"),
            dbc.Tab(label="All Orders", tab_id="all-orders", id="admin-orders-tab")
        ],
        id="orders-tabs",
        active_tab="current-order",
        className="mb-4"
    )
    
    # Current Order Tab Content
    current_order_tab = html.Div([
        dbc.Row([
            # Cart items (left column)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Your Cart", className="d-inline"),
                        html.Span(id="cart-items-count", className="ms-2")
                    ]),
                    dbc.CardBody([
                        html.Div(id="cart-items-container", className="mb-3"),
                        dbc.Alert(
                            "Your cart is empty. Add items from the menu.",
                            color="info",
                            id="empty-cart-alert",
                            is_open=True
                        ),
                        html.Hr(),
                        html.Div([
                            html.H5("Subtotal:", className="d-inline me-2"),
                            html.Span(id="cart-subtotal")
                        ], className="d-flex justify-content-between"),
                        html.Div([
                            html.H5("Tax:", className="d-inline me-2"),
                            html.Span(id="cart-tax")
                        ], className="d-flex justify-content-between"),
                        html.Div([
                            html.H5("Total:", className="d-inline me-2 fw-bold"),
                            html.Span(id="cart-total", className="fw-bold")
                        ], className="d-flex justify-content-between"),
                        html.Div([
                            dbc.Button(
                                "Continue Shopping",
                                href="/menu",
                                color="secondary",
                                className="me-2"
                            ),
                            dbc.Button(
                                "Clear Cart",
                                id="clear-cart-btn",
                                color="danger",
                                className="me-2"
                            ),
                            dbc.Button(
                                "Checkout",
                                id="checkout-btn",
                                color="primary",
                                disabled=True
                            )
                        ], className="mt-3 d-flex justify-content-end")
                    ])
                ])
            ], md=7),
            
            # Order form (right column)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Order Details"),
                    dbc.CardBody([
                        order_form()
                    ])
                ])
            ], md=5)
        ]),
        
        # Order Status Section (visible after order is placed)
        dbc.Row([
            dbc.Col([
                html.Div(id="order-status-container", className="mt-4")
            ])
        ])
    ], id="current-order-content", style={"display": "block"})
    
    # Order History Tab Content
    order_history_tab = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Your Order History", className="d-inline"),
                        dbc.Button(
                            html.I(className="fas fa-sync-alt"),
                            id="refresh-history-btn",
                            color="link",
                            size="sm",
                            className="float-end"
                        )
                    ]),
                    dbc.CardBody([
                        html.Div(id="order-history-container")
                    ])
                ])
            ])
        ])
    ], id="order-history-content", style={"display": "none"})
    
    # All Orders Tab Content (Admin)
    all_orders_tab = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("All Orders", className="d-inline"),
                        dbc.Button(
                            html.I(className="fas fa-sync-alt"),
                            id="refresh-all-orders-btn",
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
                                    id="order-filter",
                                    options=[
                                        {"label": "All", "value": "All"},
                                        {"label": "New", "value": "New"},
                                        {"label": "In Progress", "value": "In Progress"},
                                        {"label": "Ready", "value": "Ready"},
                                        {"label": "Completed", "value": "Completed"},
                                        {"label": "Cancelled", "value": "Cancelled"}
                                    ],
                                    value="All",
                                    className="mb-3"
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label("Search Orders:"),
                                dbc.Input(
                                    id="order-search",
                                    placeholder="Order ID or customer name...",
                                    type="text",
                                    className="mb-3"
                                )
                            ], md=4),
                            dbc.Col([
                                dbc.Label("Date Range:"),
                                dcc.DatePickerRange(
                                    id="order-date-range",
                                    className="mb-3"
                                )
                            ], md=4)
                        ], className="mb-3"),
                        html.Div(id="orders-table-container")
                    ])
                ])
            ])
        ])
    ], id="all-orders-content", style={"display": "none"})
    
    # Combine all elements
    layout = html.Div([
        header,
        tabs,
        current_order_tab,
        order_history_tab,
        all_orders_tab,
        
        # Add modals
        order_details_modal(),
        confirm_order_modal(),
        order_status_modal(),
        
        # Hidden stores
        dcc.Store(id="order-data-store", storage_type="session"),
        dcc.Store(id="order-status-store", storage_type="memory"),
        
        # Hidden div for callback triggers
        html.Div(id="order-action-trigger", style={"display": "none"}),
        
        # Hidden div for Socket.IO updates
        html.Div(id="socket-order-update", style={"display": "none"})
    ])
    
    return layout