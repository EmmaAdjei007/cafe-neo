# File: app/layouts/dashboard.py

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from app.components.cards import summary_card, order_card
from app.components.charts import create_sales_chart, create_orders_chart

def layout():
    """
    Create the dashboard layout
    
    Returns:
        html.Div: The dashboard content
    """
    # Create dashboard elements
    header = html.Div([
        html.H1("Dashboard", className="page-header"),
        html.P("Overview of Neo Cafe metrics and operations", className="lead")
    ])
    
    # Summary cards row
    summary_row = dbc.Row([
        dbc.Col(summary_card(
            title="Today's Sales", 
            value="$1,250", 
            subtitle="↑ 15% from yesterday",
            icon="fas fa-dollar-sign",
            color="success"
        ), md=3),
        dbc.Col(summary_card(
            title="Orders", 
            value="42", 
            subtitle="↑ 8% from yesterday",
            icon="fas fa-shopping-cart",
            color="info"
        ), md=3),
        dbc.Col(summary_card(
            title="Active Deliveries", 
            value="7", 
            subtitle="2 robots active",
            icon="fas fa-robot",
            color="warning"
        ), md=3),
        dbc.Col(summary_card(
            title="Inventory Status", 
            value="92%", 
            subtitle="3 items low stock",
            icon="fas fa-box",
            color="danger"
        ), md=3),
    ], className="mb-4")
    
    # Charts row
    charts_row = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Sales Overview"),
                dbc.CardBody([
                    dcc.Graph(
                        id='sales-chart',
                        figure=create_sales_chart(),
                        config={'displayModeBar': False}
                    )
                ])
            ])
        ], md=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Order Distribution"),
                dbc.CardBody([
                    dcc.Graph(
                        id='orders-chart',
                        figure=create_orders_chart(),
                        config={'displayModeBar': False}
                    )
                ])
            ])
        ], md=4),
    ], className="mb-4")
    
    # Recent orders and announcements
    bottom_row = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("Recent Orders", className="d-inline"),
                    dbc.Button("View All", color="link", href="/orders", size="sm", className="float-end")
                ]),
                dbc.CardBody([
                    html.Div(id='recent-orders-container', children=[
                        order_card("ORD-12345", "Table 3", "2 items", "In Progress", "5 mins ago"),
                        order_card("ORD-12344", "Table 7", "4 items", "Ready", "12 mins ago"),
                        order_card("ORD-12343", "Delivery", "1 item", "Delivered", "25 mins ago"),
                    ])
                ])
            ])
        ], md=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("Announcements & Events", className="d-inline"),
                    dbc.Button("Add New", color="link", id="add-announcement-btn", size="sm", className="float-end")
                ]),
                dbc.CardBody([
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            html.H5("New Summer Menu Launch", className="mb-1"),
                            html.P("Starting next Monday, we'll be introducing our new summer drinks.", className="mb-1"),
                            html.Small("Posted 2 hours ago", className="text-muted")
                        ]),
                        dbc.ListGroupItem([
                            html.H5("Staff Meeting", className="mb-1"),
                            html.P("Reminder: Staff meeting today at 3 PM in the back office.", className="mb-1"),
                            html.Small("Posted yesterday", className="text-muted")
                        ]),
                    ], flush=True)
                ])
            ])
        ], md=6),
    ])
    
    # Combine all elements
    layout = html.Div([
        header,
        summary_row,
        charts_row,
        bottom_row
    ])
    
    return layout