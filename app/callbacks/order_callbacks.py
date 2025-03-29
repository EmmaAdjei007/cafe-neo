# File: app/callbacks/order_callbacks.py

from dash import Input, Output, State, callback_context, html
import dash_bootstrap_components as dbc
import json
import time
from datetime import datetime
from app.utils.api_utils import place_order, update_order_status

def register_callbacks(app, socketio):
    """
    Register callbacks for order management
    
    Args:
        app: Dash application instance
        socketio: SocketIO instance for real-time communication
    """
    @app.callback(
        Output("cart-alert", "children"),
        [Input("cart-store", "data")],
        [State("cart-store", "data")]
    )
    def update_cart_alert(data, current_cart):
        """Show alert when cart is updated"""
        if not data or not current_cart:
            return html.Div()
        
        # Check if items were added to cart
        if len(current_cart) > 0:
            # Calculate total items and price
            total_items = sum(item.get("quantity", 1) for item in current_cart)
            total_price = sum(item.get("price", 0) * item.get("quantity", 1) for item in current_cart)
            
            alert = dbc.Alert(
                [
                    html.I(className="fas fa-shopping-cart me-2"),
                    f"Cart updated: {total_items} items (${total_price:.2f}) ",
                    dbc.Button("View Cart", color="light", size="sm", href="/orders", className="ms-2")
                ],
                color="success",
                dismissable=True,
                is_open=True,
                duration=4000,
                className="position-fixed bottom-0 end-0 m-3",
                style={"zIndex": 1050, "minWidth": "300px"}
            )
            
            return alert
        
        return html.Div()
    
    @app.callback(
        Output("orders-table-container", "children"),
        [
            Input("orders-update-interval", "n_intervals"),
            Input("order-status-store", "data"),
            Input("order-filter", "value")
        ]
    )
    def update_orders_table(n_intervals, status_update, filter_value):
        """Update the orders table with latest orders"""
        # In a real app, this would fetch from a database
        # For demo, using static data with simulated updates
        
        # Create sample orders with timestamps
        current_time = datetime.now()
        
        orders = [
            {
                "id": "ORD-1234567",
                "customer": "John Doe",
                "items": ["Cappuccino", "Croissant"],
                "total": 8.50,
                "status": "Completed",
                "time": (current_time.replace(hour=current_time.hour-1)).strftime("%H:%M"),
                "location": "Table 3"
            },
            {
                "id": "ORD-1234568",
                "customer": "Jane Smith",
                "items": ["Latte", "Blueberry Muffin", "Orange Juice"],
                "total": 12.75,
                "status": "In Progress",
                "time": (current_time.replace(minute=current_time.minute-15)).strftime("%H:%M"),
                "location": "Table 7"
            },
            {
                "id": "ORD-1234569",
                "customer": "Bob Johnson",
                "items": ["Espresso"],
                "total": 3.25,
                "status": "Ready",
                "time": (current_time.replace(minute=current_time.minute-5)).strftime("%H:%M"),
                "location": "Counter"
            },
            {
                "id": "ORD-1234570",
                "customer": "Alice Brown",
                "items": ["Mocha", "Chocolate Cake"],
                "total": 10.00,
                "status": "In Progress",
                "time": current_time.strftime("%H:%M"),
                "location": "Delivery"
            }
        ]
        
        # Apply filter if specified
        if filter_value and filter_value != "All":
            orders = [order for order in orders if order["status"] == filter_value]
        
        # If we have status updates, apply them
        if status_update:
            for order in orders:
                if order["id"] == status_update["id"]:
                    order["status"] = status_update["status"]
        
        # Create table rows
        rows = []
        for order in orders:
            # Create status badge with appropriate color
            status_color_map = {
                "New": "secondary",
                "In Progress": "primary",
                "Ready": "info",
                "Completed": "success",
                "Cancelled": "danger"
            }
            
            status_badge = dbc.Badge(
                order["status"],
                color=status_color_map.get(order["status"], "secondary"),
                className="p-2"
            )
            
            # Create action buttons
            action_buttons = html.Div([
                dbc.Button(
                    html.I(className="fas fa-eye"),
                    id={"type": "view-order-btn", "index": order["id"]},
                    color="primary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    html.I(className="fas fa-edit"),
                    id={"type": "edit-order-btn", "index": order["id"]},
                    color="secondary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    html.I(className="fas fa-robot"),
                    id={"type": "deliver-order-btn", "index": order["id"]},
                    color="success",
                    size="sm",
                    disabled=order["status"] != "Ready"
                )
            ], className="d-flex")
            
            # Create the table row
            row = html.Tr([
                html.Td(order["time"]),
                html.Td(order["id"]),
                html.Td(order["customer"]),
                html.Td(", ".join(order["items"])),
                html.Td(f"${order['total']:.2f}"),
                html.Td(order["location"]),
                html.Td(status_badge),
                html.Td(action_buttons)
            ])
            
            rows.append(row)
        
        # Create the table
        if rows:
            table = dbc.Table(
                [
                    html.Thead(
                        html.Tr([
                            html.Th("Time"),
                            html.Th("Order ID"),
                            html.Th("Customer"),
                            html.Th("Items"),
                            html.Th("Total"),
                            html.Th("Location"),
                            html.Th("Status"),
                            html.Th("Actions")
                        ])
                    ),
                    html.Tbody(rows)
                ],
                className="order-table",
                bordered=True,
                hover=True,
                responsive=True,
                striped=True
            )
            
            return table
        else:
            return html.Div(
                dbc.Alert("No orders found matching the current filter.", color="info"),
                className="text-center p-4"
            )
    
    @app.callback(
        Output("order-status-store", "data"),
        [
            Input({"type": "status-change-btn", "index": "all"}, "n_clicks"),
            Input("socket-order-update", "children")  # Hidden div updated by SocketIO
        ],
        [
            State({"type": "status-change-btn", "index": "all"}, "id"),
            State("order-status-store", "data")
        ]
    )
    def update_order_status_callback(n_clicks_list, socket_update, btn_ids, current_status):
        """Update order status when a status change button is clicked"""
        ctx = callback_context
        
        # If triggered by socket update
        if ctx.triggered and "socket-order-update" in ctx.triggered[0]["prop_id"]:
            try:
                # Parse the data from socket update
                if socket_update:
                    update_data = json.loads(socket_update)
                    return update_data
            except:
                pass
        
        # If no button was clicked or no button IDs
        if not ctx.triggered or not btn_ids or "n_clicks" not in ctx.triggered[0]["prop_id"]:
            return current_status
        
        # Find which button was clicked
        button_idx = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Convert string representation to dictionary
        button_idx = json.loads(button_idx)
        
        # Get the parts of the button ID
        order_id, new_status = button_idx["index"].split("-")
        
        # Update the status via API (in production)
        # update_order_status(order_id, new_status)
        
        # For demo, just return the new status
        return {"id": order_id, "status": new_status}
    
    # SocketIO event handler for order updates
    @socketio.on('new_order')
    def handle_new_order(data):
        """Handle new order events from Chainlit"""
        # Broadcast the new order to all connected clients
        socketio.emit('order_update', data)
        
        # In a real app, this would save to a database
        print(f"New order received: {data['id']}")
        
        # Acknowledge receipt
        return {"status": "success", "message": "Order received"}