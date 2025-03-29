# File: app/callbacks/dashboard_callbacks.py

from dash import Input, Output, State, callback_context, html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from app.components.cards import order_card

def register_callbacks(app, socketio):
    """
    Register callbacks for the dashboard
    
    Args:
        app: Dash application instance
        socketio: SocketIO instance for real-time communication
    """
    @app.callback(
        Output("sales-chart", "figure"),
        [Input("status-update-interval", "n_intervals")]
    )
    def update_sales_chart(n_intervals):
        """Update the sales chart with latest data"""
        from app.components.charts import create_sales_chart
        return create_sales_chart()
    
    @app.callback(
        Output("orders-chart", "figure"),
        [Input("status-update-interval", "n_intervals")]
    )
    def update_orders_chart(n_intervals):
        """Update the orders distribution chart with latest data"""
        from app.components.charts import create_orders_chart
        return create_orders_chart()
    
    @app.callback(
        Output("recent-orders-container", "children"),
        [Input("orders-update-interval", "n_intervals")]
    )
    def update_recent_orders(n_intervals):
        """Update the recent orders display with latest orders"""
        # In a real app, this would fetch from a database
        # For demo purposes, using static data with simulated updates
        
        # Create sample orders with timestamps
        current_time = datetime.now()
        
        # Create order cards
        orders = [
            order_card(
                "ORD-12345", 
                "Table 3", 
                "2 items", 
                "In Progress", 
                f"{(current_time - timedelta(minutes=5)).strftime('%H:%M')}"
            ),
            order_card(
                "ORD-12344", 
                "Table 7", 
                "4 items", 
                "Ready", 
                f"{(current_time - timedelta(minutes=12)).strftime('%H:%M')}"
            ),
            order_card(
                "ORD-12343", 
                "Delivery", 
                "1 item", 
                "Delivered", 
                f"{(current_time - timedelta(minutes=25)).strftime('%H:%M')}"
            )
        ]
        
        # Randomly shuffle the order to simulate changes
        if n_intervals and n_intervals % 3 == 0:
            import random
            random.shuffle(orders)
        
        return orders
    
    @app.callback(
        Output("add-announcement-modal", "is_open"),
        [
            Input("add-announcement-btn", "n_clicks"),
            Input("submit-announcement-btn", "n_clicks"),
            Input("cancel-announcement-btn", "n_clicks")
        ],
        [State("add-announcement-modal", "is_open")]
    )
    def toggle_announcement_modal(add_clicks, submit_clicks, cancel_clicks, is_open):
        """Toggle the announcement modal"""
        ctx = callback_context
        
        if not ctx.triggered:
            return is_open
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if button_id == "add-announcement-btn":
            return True
        elif button_id in ["submit-announcement-btn", "cancel-announcement-btn"]:
            return False
        
        return is_open
    
    @app.callback(
        Output("announcements-list", "children"),
        [Input("submit-announcement-btn", "n_clicks")],
        [
            State("announcement-title", "value"),
            State("announcement-content", "value"),
            State("announcements-list", "children")
        ]
    )
    def add_announcement(n_clicks, title, content, current_announcements):
        """Add a new announcement to the list"""
        if not n_clicks or not title or not content:
            return current_announcements
        
        # Create new announcement
        new_announcement = dbc.ListGroupItem([
            html.H5(title, className="mb-1"),
            html.P(content, className="mb-1"),
            html.Small(f"Posted just now", className="text-muted")
        ])
        
        # If no current announcements, create a new list
        if not current_announcements:
            return [new_announcement]
        
        # Otherwise, add to the beginning of the list
        if isinstance(current_announcements, list):
            return [new_announcement] + current_announcements
        else:
            return [new_announcement, current_announcements]
    
    @app.callback(
        Output("inventory-alerts", "children"),
        [Input("status-update-interval", "n_intervals")]
    )
    def update_inventory_alerts(n_intervals):
        """Update inventory alerts"""
        # In a real app, this would fetch from a database
        # For demo, using static data
        
        # Items with low stock
        low_stock_items = [
            {"name": "Espresso Beans", "current": 2, "min": 5},
            {"name": "Almond Milk", "current": 1, "min": 3},
            {"name": "Vanilla Syrup", "current": 1, "min": 2}
        ]
        
        if not low_stock_items:
            return html.P("No inventory alerts at this time.", className="text-muted")
        
        # Create alerts
        alerts = []
        for item in low_stock_items:
            alerts.append(
                dbc.Alert(
                    [
                        html.Strong(f"{item['name']}: "),
                        f"Low stock ({item['current']}/{item['min']})"
                    ],
                    color="warning",
                    className="mb-2"
                )
            )
        
        return alerts
    
    @app.callback(
        Output("staff-schedule", "children"),
        [Input("status-update-interval", "n_intervals")]
    )
    def update_staff_schedule(n_intervals):
        """Update staff schedule display"""
        # In a real app, this would fetch from a database
        # For demo, using static data
        
        # Current staff
        current_time = datetime.now()
        day_of_week = current_time.strftime("%A")
        
        staff_schedule = {
            "Morning Shift": ["Alex", "Jamie", "Taylor"],
            "Afternoon Shift": ["Jordan", "Casey", "Morgan"],
            "Evening Shift": ["Riley", "Avery", "Quinn"]
        }
        
        # Determine current shift
        current_hour = current_time.hour
        if 6 <= current_hour < 12:
            current_shift = "Morning Shift"
        elif 12 <= current_hour < 18:
            current_shift = "Afternoon Shift"
        else:
            current_shift = "Evening Shift"
        
        # Create schedule display
        schedule_items = []
        for shift, staff in staff_schedule.items():
            # Highlight current shift
            is_current = shift == current_shift
            
            schedule_items.append(
                dbc.ListGroupItem(
                    [
                        html.Div(
                            [
                                html.Strong(shift),
                                html.Badge(
                                    "Current", 
                                    color="success", 
                                    className="ms-2"
                                ) if is_current else None
                            ],
                            className="d-flex justify-content-between align-items-center"
                        ),
                        html.P(", ".join(staff), className="mb-0")
                    ],
                    color="light" if not is_current else None
                )
            )
        
        return dbc.ListGroup(schedule_items)
    
    # Register SocketIO handlers specifically for dashboard updates
    @socketio.on('dashboard_update')
    def handle_dashboard_update(data):
        """Handle dashboard update events"""
        # Broadcast the update to all connected clients
        socketio.emit('dashboard_refresh', data)
        
        # If it's a new order, also send order update
        if data.get('type') == 'new_order':
            socketio.emit('order_update', data.get('order', {}))