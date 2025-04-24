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
    [Input("status-update-interval", "n_intervals"),
     Input("socket-order-update", "children")],  # Added to update when new orders come in
    [State("delivery-update-store", "data"),
     State("user-store", "data")]  # Added user_store to check active orders
)
    def update_robot_map(n_intervals, socket_update, delivery_data, user_data):
        """Update the robot location map with enhanced robot delivery integration"""
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
        
        # Try to get delivery data from multiple sources
        active_delivery = None
        
        # First check if we got a socket update with delivery info
        if socket_update:
            try:
                update_data = json.loads(socket_update)
                if isinstance(update_data, dict) and update_data.get("robot_delivery"):
                    active_delivery = update_data
                    print(f"Got delivery data from socket update: {update_data.get('id')}")
            except Exception as e:
                print(f"Error parsing socket update for delivery: {e}")
        
        # If no active delivery from socket update, check the delivery store
        if not active_delivery and delivery_data:
            try:
                active_delivery = json.loads(delivery_data) if isinstance(delivery_data, str) else delivery_data
                print(f"Using delivery data from store: {active_delivery.get('order_id')}")
            except Exception as e:
                print(f"Error parsing delivery store data: {e}")
        
        # If still no active delivery, check if user has an active order with delivery
        if not active_delivery and user_data and "active_order" in user_data:
            active_order = user_data["active_order"]
            if isinstance(active_order, dict) and active_order.get("delivery_type", "").lower() == "delivery":
                active_delivery = active_order
                print(f"Using active order as delivery: {active_order.get('id')}")
        
        # If we have delivery data, plot the robot and route
        if active_delivery:
            try:
                # Try to get real-time robot location from API
                from app.utils.robot_api_utils import get_robot_delivery_status
                
                order_id = active_delivery.get("id") or active_delivery.get("order_id")
                if order_id:
                    status_result = get_robot_delivery_status(order_id=order_id)
                    
                    if status_result.get("status") == "success" and status_result.get("data"):
                        robot_data = status_result["data"]
                        
                        # Get robot location
                        if "location" in robot_data:
                            robot_location = robot_data["location"]
                            
                            # Add robot marker
                            fig.add_trace(go.Scattermapbox(
                                lat=[robot_location.get("lat", 37.7749)],
                                lon=[robot_location.get("lng", -122.4194)],
                                mode="markers",
                                marker=dict(size=15, color="red"),
                                name="Robot"
                            ))
                            
                            # Center map on robot
                            fig.update_layout(
                                mapbox=dict(
                                    center=dict(
                                        lat=robot_location.get("lat", 37.7749), 
                                        lon=robot_location.get("lng", -122.4194)
                                    ),
                                    zoom=15
                                )
                            )
                        
                        # Get route coordinates
                        if "route" in robot_data and len(robot_data["route"]) > 1:
                            route = robot_data["route"]
                            
                            # Add route line
                            lats = [point.get("lat") for point in route if "lat" in point]
                            lons = [point.get("lng") for point in route if "lng" in point]
                            
                            if lats and lons and len(lats) == len(lons):
                                fig.add_trace(go.Scattermapbox(
                                    lat=lats,
                                    lon=lons,
                                    mode="lines",
                                    line=dict(width=4, color="blue"),
                                    name="Route"
                                ))
                            
                            # Add destination marker
                            if len(route) > 0:
                                destination = route[-1]
                                fig.add_trace(go.Scattermapbox(
                                    lat=[destination.get("lat")],
                                    lon=[destination.get("lng")],
                                    mode="markers",
                                    marker=dict(size=12, color="green"),
                                    name="Destination"
                                ))
                            
                            # Add origin marker (store)
                            if len(route) > 0:
                                origin = route[0]
                                fig.add_trace(go.Scattermapbox(
                                    lat=[origin.get("lat")],
                                    lon=[origin.get("lng")],
                                    mode="markers",
                                    marker=dict(size=12, color="blue"),
                                    name="Store"
                                ))
                else:
                    print("No order ID available for robot status lookup")
            except Exception as e:
                print(f"Error getting robot status: {e}")
                import traceback
                traceback.print_exc()
        
        return fig
    
    @app.callback(
    Output("robot-status-indicators", "children"),
    [Input("status-update-interval", "n_intervals"),
     Input("socket-order-update", "children")],  # Added to update when new orders come in
    [State("user-store", "data")]  # Added to check active orders
)
    def update_robot_status_indicators(n_intervals, socket_update, user_data):
        """Update the robot status indicators with real data when available"""
        
        # Try to get active delivery information
        active_delivery = None
        robot_status = "Unknown"
        battery_level = 0
        connection_quality = 0
        eta = "Unknown"
        
        # Check socket update for delivery info
        if socket_update:
            try:
                update_data = json.loads(socket_update)
                if isinstance(update_data, dict) and update_data.get("robot_delivery"):
                    active_delivery = update_data
                    print(f"Got delivery data from socket update: {update_data.get('id')}")
            except Exception as e:
                print(f"Error parsing socket update for delivery status: {e}")
        
        # If no active delivery from socket, check if user has an active order with delivery
        if not active_delivery and user_data and "active_order" in user_data:
            active_order = user_data["active_order"]
            if isinstance(active_order, dict) and active_order.get("delivery_type", "").lower() == "delivery":
                active_delivery = active_order
                print(f"Using active order for delivery status: {active_order.get('id')}")
        
        # If we have delivery data, get real-time status from API
        if active_delivery:
            try:
                from app.utils.robot_api_utils import get_robot_delivery_status
                
                order_id = active_delivery.get("id") or active_delivery.get("order_id")
                if order_id:
                    status_result = get_robot_delivery_status(order_id=order_id)
                    
                    if status_result.get("status") == "success" and status_result.get("data"):
                        robot_data = status_result["data"]
                        
                        # Extract status information
                        robot_status = robot_data.get("delivery_status", "Unknown")
                        battery_level = robot_data.get("battery_level", 80)  # Default to 80% if not provided
                        connection_quality = robot_data.get("connection_quality", 70)  # Default to 70% if not provided
                        eta = robot_data.get("eta", "Unknown")
            except Exception as e:
                print(f"Error getting robot status for indicators: {e}")
        else:
            # If no active delivery, use simulated data or default values
            # For demo purposes, show simulated data
            battery_level = max(0, 100 - (n_intervals % 20) * 5)
            
            # Cycle through statuses
            statuses = ["Idle", "Delivering", "Returning", "Charging"]
            robot_status = statuses[n_intervals % len(statuses)]
            
            # Generate random connection quality (0-100)
            import numpy as np
            connection_quality = max(0, min(100, 80 + np.random.randint(-20, 20)))
            
            # Generate ETA
            minutes = (n_intervals % 15) + 1
            eta = f"{minutes} minute{'s' if minutes != 1 else ''}"
        
        # Calculate appropriate colors
        battery_color = "success" if battery_level > 50 else "warning" if battery_level > 20 else "danger"
        connection_color = "success" if connection_quality > 70 else "warning" if connection_quality > 40 else "danger"
        
        # Create the indicators
        indicators = [
            dbc.Row([
                dbc.Col([
                    html.H5("Robot Status"),
                    dbc.Badge(robot_status, color="primary", className="py-2 px-3 fs-6 d-block")
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
            ], className="mb-4"),
            
            # Add ETA information if available
            dbc.Row([
                dbc.Col([
                    html.H5("Estimated Time of Arrival"),
                    html.Div([
                        html.I(className="fas fa-clock me-2"),
                        html.Span(eta, className="fs-5")
                    ], className="d-flex align-items-center")
                ], md=12)
            ], className="mb-4") if eta and eta != "Unknown" else None
        ]
        
        # Filter out None elements
        indicators = [indicator for indicator in indicators if indicator is not None]
        
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