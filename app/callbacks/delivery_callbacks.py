# File: app/callbacks/delivery_callbacks.py

from dash import Input, Output, State, html, callback_context, ALL  # Add ALL import
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime

def register_callbacks(app, socketio):
    """
    Register callbacks for delivery tracking
    
    Args:
        app: Dash application instance
        socketio: SocketIO instance for real-time communication
    """
    @app.callback(
        Output("robot-location-map", "figure"),
        [Input("status-update-interval", "n_intervals")],
        [State("delivery-update-store", "data")]
    )
    def update_robot_map(n_intervals, delivery_data):
        """Update the robot location map"""
        # Create base map
        fig = go.Figure(go.Scattermapbox())
        
        # Set map center and zoom
        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(
                center=dict(lat=37.7749, lon=-122.4194),  # Default to San Francisco
                zoom=15
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=500
        )
        
        # If we have delivery data, plot the robot and route
        if delivery_data:
            # Try to parse the delivery data
            try:
                delivery = json.loads(delivery_data)
                
                # Get robot location
                robot_location = delivery.get("robot_location", {})
                
                # Get route coordinates
                route = delivery.get("route", [])
                
                # Add robot marker
                if robot_location and "lat" in robot_location and "lng" in robot_location:
                    fig.add_trace(go.Scattermapbox(
                        lat=[robot_location["lat"]],
                        lon=[robot_location["lng"]],
                        mode="markers",
                        marker=dict(size=15, color="red"),
                        name="Robot"
                    ))
                    
                    # Center map on robot
                    fig.update_layout(
                        mapbox=dict(
                            center=dict(lat=robot_location["lat"], lon=robot_location["lng"]),
                            zoom=15
                        )
                    )
                
                # Add route line
                if route and len(route) > 1:
                    lats = [point["lat"] for point in route]
                    lons = [point["lng"] for point in route]
                    
                    fig.add_trace(go.Scattermapbox(
                        lat=lats,
                        lon=lons,
                        mode="lines",
                        line=dict(width=4, color="blue"),
                        name="Route"
                    ))
                
                # Add destination marker
                if route and len(route) > 0:
                    destination = route[-1]
                    fig.add_trace(go.Scattermapbox(
                        lat=[destination["lat"]],
                        lon=[destination["lng"]],
                        mode="markers",
                        marker=dict(size=12, color="green"),
                        name="Destination"
                    ))
                
                # Add origin marker (store)
                if route and len(route) > 0:
                    origin = route[0]
                    fig.add_trace(go.Scattermapbox(
                        lat=[origin["lat"]],
                        lon=[origin["lng"]],
                        mode="markers",
                        marker=dict(size=12, color="blue"),
                        name="Store"
                    ))
            except Exception as e:
                print(f"Error updating robot map: {e}")
        
        return fig
    
    @app.callback(
        Output("robot-status-indicators", "children"),
        [Input("status-update-interval", "n_intervals")]
    )
    def update_robot_status_indicators(n_intervals):
        """Update the robot status indicators"""
        # In a real app, this would fetch from the robot API
        # For demo purposes, simulating data
        
        # Generate random battery level that trends downward
        battery_level = max(0, 100 - (n_intervals % 20) * 5)
        
        # Cycle through statuses
        statuses = ["Idle", "Delivering", "Returning", "Charging"]
        status = statuses[n_intervals % len(statuses)]
        
        # Generate random connection quality (0-100)
        connection_quality = max(0, min(100, 80 + np.random.randint(-20, 20)))
        
        # Calculate appropriate colors
        battery_color = "success" if battery_level > 50 else "warning" if battery_level > 20 else "danger"
        connection_color = "success" if connection_quality > 70 else "warning" if connection_quality > 40 else "danger"
        
        # Create the indicators
        indicators = [
            dbc.Row([
                dbc.Col([
                    html.H5("Robot Status"),
                    dbc.Badge(status, color="primary", className="py-2 px-3 fs-6 d-block")
                ], md=4),
                dbc.Col([
                    html.H5("Battery Level"),
                    dbc.Progress(value=battery_level, color=battery_color, className="mb-2"),
                    html.Span(f"{battery_level}%")
                ], md=4),
                dbc.Col([
                    html.H5("Connection Quality"),
                    dbc.Progress(value=connection_quality, color=connection_color, className="mb-2"),
                    html.Span(f"{connection_quality}%")
                ], md=4),
            ], className="mb-4")
        ]
        
        return indicators
    
    @app.callback(
        Output("active-deliveries-list", "children"),
        [Input("status-update-interval", "n_intervals")]
    )
    def update_active_deliveries(n_intervals):
        """Update the list of active deliveries"""
        # In a real app, this would fetch from a database
        # For demo purposes, creating static data with simulated updates
        
        # Create sample deliveries
        current_time = datetime.now()
        
        deliveries = [
            {
                "id": "ORD-1234570",
                "customer": "Alice Brown",
                "items": ["Mocha", "Chocolate Cake"],
                "status": "In Transit",
                "progress": min(100, (n_intervals % 20) * 5),
                "eta": "5 minutes",
                "robot_id": "R-101"
            },
            {
                "id": "ORD-1234571",
                "customer": "Michael Wilson",
                "items": ["Americano", "Blueberry Scone"],
                "status": "Preparing",
                "progress": min(100, (n_intervals % 10) * 10),
                "eta": "12 minutes",
                "robot_id": "R-102"
            }
        ]
        
        # Create list items
        items = []
        for delivery in deliveries:
            # Create progress color based on status
            progress_color = "info"
            if delivery["status"] == "In Transit":
                progress_color = "primary"
            elif delivery["status"] == "Delivered":
                progress_color = "success"
            elif delivery["status"] == "Cancelled":
                progress_color = "danger"
            
            # Create list item
            item = dbc.ListGroupItem([
                dbc.Row([
                    dbc.Col([
                        html.H5(f"Order {delivery['id']}"),
                        html.P(f"Customer: {delivery['customer']}"),
                        html.P(f"Items: {', '.join(delivery['items'])}")
                    ], md=6),
                    dbc.Col([
                        html.H5(delivery["status"]),
                        dbc.Progress(value=delivery["progress"], color=progress_color, className="mb-2"),
                        html.P([
                            html.Strong("ETA: "),
                            html.Span(delivery["eta"])
                        ]),
                        html.P([
                            html.Strong("Robot: "),
                            html.Span(delivery["robot_id"])
                        ])
                    ], md=4),
                    dbc.Col([
                        dbc.Button(
                            "Track",
                            id={"type": "track-delivery-btn", "index": delivery["id"]},
                            color="primary",
                            className="mb-2 w-100"
                        ),
                        dbc.Button(
                            "Details",
                            id={"type": "delivery-details-btn", "index": delivery["id"]},
                            color="secondary",
                            className="w-100"
                        )
                    ], md=2)
                ])
            ])
            
            items.append(item)
        
        # Return the list group
        if items:
            return dbc.ListGroup(items)
        else:
            return dbc.Alert("No active deliveries.", color="info")
    
    # SocketIO event handler for robot location updates
    @socketio.on('robot_location_update')
    def handle_robot_update(data):
        """Handle robot location update events"""
        # Broadcast the robot update to all connected clients
        socketio.emit('robot_update', data)
        
        # In a real app, this would update a database
        print(f"Robot update received for order {data.get('order_id')}")
        
        # Acknowledge receipt
        return {"status": "success", "message": "Update received"}