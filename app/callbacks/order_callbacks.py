# # File: app/callbacks/order_callbacks.py

# from dash import Input, Output, State, callback_context, html, ALL  # Add ALL import
# import dash_bootstrap_components as dbc
# import json
# import time
# from datetime import datetime
# from app.utils.api_utils import place_order, update_order_status

# def register_callbacks(app, socketio):
#     """
#     Register callbacks for order management
    
#     Args:
#         app: Dash application instance
#         socketio: SocketIO instance for real-time communication
#     """
#     @app.callback(
#         Output("cart-alert", "children"),
#         [Input("cart-store", "data")],
#         [State("cart-store", "data")]
#     )
#     def update_cart_alert(data, current_cart):
#         """Show alert when cart is updated"""
#         if not data or not current_cart:
#             return html.Div()
        
#         # Check if items were added to cart
#         if len(current_cart) > 0:
#             # Calculate total items and price
#             total_items = sum(item.get("quantity", 1) for item in current_cart)
#             total_price = sum(item.get("price", 0) * item.get("quantity", 1) for item in current_cart)
            
#             alert = dbc.Alert(
#                 [
#                     html.I(className="fas fa-shopping-cart me-2"),
#                     f"Cart updated: {total_items} items (${total_price:.2f}) ",
#                     dbc.Button("View Cart", color="light", size="sm", href="/orders", className="ms-2")
#                 ],
#                 color="success",
#                 dismissable=True,
#                 is_open=True,
#                 duration=4000,
#                 className="position-fixed bottom-0 end-0 m-3",
#                 style={"zIndex": 1050, "minWidth": "300px"}
#             )
            
#             return alert
        
#         return html.Div()
    
#     @app.callback(
#         Output("orders-table-container", "children"),
#         [
#             Input("orders-update-interval", "n_intervals"),
#             Input("order-status-store", "data"),
#             Input("order-filter", "value")
#         ]
#     )
#     def update_orders_table(n_intervals, status_update, filter_value):
#         """Update the orders table with latest orders"""
#         # In a real app, this would fetch from a database
#         # For demo, using static data with simulated updates
        
#         # Create sample orders with timestamps
#         current_time = datetime.now()
        
#         orders = [
#             {
#                 "id": "ORD-1234567",
#                 "customer": "John Doe",
#                 "items": ["Cappuccino", "Croissant"],
#                 "total": 8.50,
#                 "status": "Completed",
#                 "time": (current_time.replace(hour=current_time.hour-1)).strftime("%H:%M"),
#                 "location": "Table 3"
#             },
#             {
#                 "id": "ORD-1234568",
#                 "customer": "Jane Smith",
#                 "items": ["Latte", "Blueberry Muffin", "Orange Juice"],
#                 "total": 12.75,
#                 "status": "In Progress",
#                 "time": (current_time.replace(minute=current_time.minute-15)).strftime("%H:%M"),
#                 "location": "Table 7"
#             },
#             {
#                 "id": "ORD-1234569",
#                 "customer": "Bob Johnson",
#                 "items": ["Espresso"],
#                 "total": 3.25,
#                 "status": "Ready",
#                 "time": (current_time.replace(minute=current_time.minute-5)).strftime("%H:%M"),
#                 "location": "Counter"
#             },
#             {
#                 "id": "ORD-1234570",
#                 "customer": "Alice Brown",
#                 "items": ["Mocha", "Chocolate Cake"],
#                 "total": 10.00,
#                 "status": "In Progress",
#                 "time": current_time.strftime("%H:%M"),
#                 "location": "Delivery"
#             }
#         ]
        
#         # Apply filter if specified
#         if filter_value and filter_value != "All":
#             orders = [order for order in orders if order["status"] == filter_value]
        
#         # If we have status updates, apply them
#         if status_update:
#             for order in orders:
#                 if order["id"] == status_update["id"]:
#                     order["status"] = status_update["status"]
        
#         # Create table rows
#         rows = []
#         for order in orders:
#             # Create status badge with appropriate color
#             status_color_map = {
#                 "New": "secondary",
#                 "In Progress": "primary",
#                 "Ready": "info",
#                 "Completed": "success",
#                 "Cancelled": "danger"
#             }
            
#             status_badge = dbc.Badge(
#                 order["status"],
#                 color=status_color_map.get(order["status"], "secondary"),
#                 className="p-2"
#             )
            
#             # Create action buttons
#             action_buttons = html.Div([
#                 dbc.Button(
#                     html.I(className="fas fa-eye"),
#                     id={"type": "view-order-btn", "index": order["id"]},
#                     color="primary",
#                     size="sm",
#                     className="me-1"
#                 ),
#                 dbc.Button(
#                     html.I(className="fas fa-edit"),
#                     id={"type": "edit-order-btn", "index": order["id"]},
#                     color="secondary",
#                     size="sm",
#                     className="me-1"
#                 ),
#                 dbc.Button(
#                     html.I(className="fas fa-robot"),
#                     id={"type": "deliver-order-btn", "index": order["id"]},
#                     color="success",
#                     size="sm",
#                     disabled=order["status"] != "Ready"
#                 )
#             ], className="d-flex")
            
#             # Create the table row
#             row = html.Tr([
#                 html.Td(order["time"]),
#                 html.Td(order["id"]),
#                 html.Td(order["customer"]),
#                 html.Td(", ".join(order["items"])),
#                 html.Td(f"${order['total']:.2f}"),
#                 html.Td(order["location"]),
#                 html.Td(status_badge),
#                 html.Td(action_buttons)
#             ])
            
#             rows.append(row)
        
#         # Create the table
#         if rows:
#             table = dbc.Table(
#                 [
#                     html.Thead(
#                         html.Tr([
#                             html.Th("Time"),
#                             html.Th("Order ID"),
#                             html.Th("Customer"),
#                             html.Th("Items"),
#                             html.Th("Total"),
#                             html.Th("Location"),
#                             html.Th("Status"),
#                             html.Th("Actions")
#                         ])
#                     ),
#                     html.Tbody(rows)
#                 ],
#                 className="order-table",
#                 bordered=True,
#                 hover=True,
#                 responsive=True,
#                 striped=True
#             )
            
#             return table
#         else:
#             return html.Div(
#                 dbc.Alert("No orders found matching the current filter.", color="info"),
#                 className="text-center p-4"
#             )
    
#     @app.callback(
#         Output("order-status-store", "data"),
#         [
#             Input({"type": "status-change-btn", "index": ALL}, "n_clicks"),  # Changed "all" to ALL
#             Input("socket-order-update", "children")  # Hidden div updated by SocketIO
#         ],
#         [
#             State({"type": "status-change-btn", "index": ALL}, "id"),  # Changed "all" to ALL
#             State("order-status-store", "data")
#         ],
#         prevent_initial_call=True  # Added to prevent initial callback
#     )
#     def update_order_status_callback(n_clicks_list, socket_update, btn_ids, current_status):
#         """Update order status when a status change button is clicked"""
#         ctx = callback_context
        
#         # If triggered by socket update
#         if ctx.triggered and "socket-order-update" in ctx.triggered[0]["prop_id"]:
#             try:
#                 # Parse the data from socket update
#                 if socket_update:
#                     update_data = json.loads(socket_update)
#                     return update_data
#             except:
#                 pass
        
#         # If no button was clicked or no button IDs
#         if not ctx.triggered or not btn_ids or "n_clicks" not in ctx.triggered[0]["prop_id"]:
#             return current_status
        
#         # Find which button was clicked
#         button_idx = ctx.triggered[0]["prop_id"].split(".")[0]
        
#         # Convert string representation to dictionary
#         button_idx = json.loads(button_idx)
        
#         # Get the parts of the button ID
#         order_id, new_status = button_idx["index"].split("-")
        
#         # Update the status via API (in production)
#         # update_order_status(order_id, new_status)
        
#         # For demo, just return the new status
#         return {"id": order_id, "status": new_status}
    
#     # SocketIO event handler for order updates
#     @socketio.on('new_order')
#     def handle_new_order(data):
#         """Handle new order events from Chainlit"""
#         # Broadcast the new order to all connected clients
#         socketio.emit('order_update', data)
        
#         # In a real app, this would save to a database
#         print(f"New order received: {data['id']}")
        
#         # Acknowledge receipt
#         return {"status": "success", "message": "Order received"}
    
#     @app.callback(
#         [
#             Output("cart-items-container", "children"),
#             Output("empty-cart-alert", "is_open"),
#             Output("cart-subtotal", "children"),
#             Output("cart-tax", "children"),
#             Output("cart-total", "children"),
#             Output("checkout-btn", "disabled")
#         ],
#         [Input("cart-store", "data")]
#     )
#     def update_cart_display(cart_data):
#         """Update the cart display with items from cart-store"""
        
#         # Default values when cart is empty
#         if not cart_data or len(cart_data) == 0:
#             return (
#                 None,
#                 True,  # Show empty cart alert
#                 "$0.00",
#                 "$0.00",
#                 "$0.00",
#                 True  # Disable checkout button
#             )
        
#         # Create table of items
#         from app.components.tables import create_order_items_table
#         items_table = create_order_items_table(cart_data)
        
#         # Calculate totals
#         subtotal = sum(item.get("price", 0) * item.get("quantity", 1) for item in cart_data)
#         tax = subtotal * 0.08  # Assuming 8% tax
#         total = subtotal + tax
        
#         # Format currency values
#         subtotal_formatted = f"${subtotal:.2f}"
#         tax_formatted = f"${tax:.2f}"
#         total_formatted = f"${total:.2f}"
        
#         return (
#             items_table,
#             False,  # Hide empty cart alert
#             subtotal_formatted,
#             tax_formatted,
#             total_formatted,
#             False  # Enable checkout button
#         )

# =====================================================

# File: app/callbacks/order_callbacks.py

from dash import Input, Output, State, callback_context, html, ALL, no_update
import dash_bootstrap_components as dbc
import json
import time
from datetime import datetime
from app.utils.api_utils import place_order, update_order_status
from app.components.tables import create_order_items_table

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
    
    # 1. Clear Cart button callback
    @app.callback(
        Output("cart-store", "data", allow_duplicate=True),
        [Input("clear-cart-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def clear_cart(n_clicks):
        """Clear the cart when the Clear Cart button is clicked"""
        if n_clicks:
            return []  # Return empty list to clear cart
        return no_update
    
    # 2. Checkout button callback
    @app.callback(
        Output("confirm-order-modal", "is_open"),
        [Input("checkout-btn", "n_clicks")],
        [State("cart-store", "data"), State("confirm-order-modal", "is_open")],
        prevent_initial_call=True
    )
    def handle_checkout(n_clicks, cart_items, is_modal_open):
        """Open the confirm order modal when the Checkout button is clicked"""
        if n_clicks and cart_items:
            return True
        return is_modal_open
    
    # 3. Fill confirm order modal with cart details
    @app.callback(
        [Output("confirm-order-details", "children"),
         Output("confirm-order-total", "children")],
        [Input("confirm-order-modal", "is_open")],
        [State("cart-store", "data")],
        prevent_initial_call=True
    )
    def fill_confirm_order_modal(is_open, cart_items):
        """Fill the confirm order modal with cart details"""
        if not is_open or not cart_items:
            return no_update, no_update
        
        # Create list of items
        items_list = []
        for item in cart_items:
            items_list.append(html.P([
                html.Strong(f"{item.get('quantity', 1)}x {item.get('name', 'Unknown')}: "),
                f"${item.get('price', 0) * item.get('quantity', 1):.2f}"
            ]))
        
        # Calculate total
        total = sum(item.get("price", 0) * item.get("quantity", 1) for item in cart_items)
        tax = total * 0.08  # Assuming 8% tax
        final_total = total + tax
        
        # Format total message
        total_message = f"Total (inc. tax): ${final_total:.2f}"
        
        return items_list, total_message
    
    # 4. Place Order button in form callback
    @app.callback(
        [Output("order-alert", "children"),
         Output("cart-store", "data", allow_duplicate=True)],
        [Input("submit-order-button", "n_clicks")],
        [State("order-location", "value"),
         State("order-payment", "value"),
         State("order-instructions", "value"),
         State("cart-store", "data"),
         State("user-store", "data")],
        prevent_initial_call=True
    )
    def place_order_callback(n_clicks, location, payment_method, instructions, cart_items, user_data):
        """Place an order when the Place Order button is clicked"""
        if not n_clicks or not cart_items:
            return no_update, no_update
        
        # Create order data
        order_id = f"ORD-{int(time.time())}"
        total = sum(item.get("price", 0) * item.get("quantity", 1) for item in cart_items)
        
        order_data = {
            "id": order_id,
            "items": cart_items,
            "total": total,
            "special_instructions": instructions,
            "delivery_location": location,
            "payment_method": payment_method,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "New"
        }
        
        if user_data and "username" in user_data:
            order_data["username"] = user_data["username"]
        
        try:
            # In a real app, this would call the place_order function
            # For demo, we'll simulate success
            
            # Emit socket event for order update
            socketio.emit('new_order', order_data)
            
            # Create success alert
            alert = dbc.Alert(
                f"Order placed successfully! Order ID: {order_id}",
                color="success",
                dismissable=True
            )
            
            # Return success alert and empty cart
            return alert, []
            
        except Exception as e:
            # Create error alert
            alert = dbc.Alert(
                f"Error placing order: {str(e)}",
                color="danger",
                dismissable=True
            )
            
            # Return error alert and keep cart
            return alert, cart_items
    
    # 5. Handle final confirm order from modal
    @app.callback(
        [Output("confirm-order-modal", "is_open", allow_duplicate=True),
         Output("order-status-container", "children"),
         Output("cart-store", "data", allow_duplicate=True)],
        [Input("confirm-final-order-btn", "n_clicks")],
        [State("cart-store", "data"),
         State("confirm-order-instructions", "value"),
         State("user-store", "data")],
        prevent_initial_call=True
    )
    def confirm_final_order(n_clicks, cart_items, instructions, user_data):
        """Process the final order confirmation"""
        if not n_clicks or not cart_items:
            return no_update, no_update, no_update
        
        # Create order data (similar to place_order_callback)
        order_id = f"ORD-{int(time.time())}"
        total = sum(item.get("price", 0) * item.get("quantity", 1) for item in cart_items)
        
        order_data = {
            "id": order_id,
            "items": cart_items,
            "total": total,
            "special_instructions": instructions,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "New"
        }
        
        # Create order status display
        order_status = html.Div([
            dbc.Card([
                dbc.CardHeader("Order Confirmed!"),
                dbc.CardBody([
                    html.H5(f"Order #{order_id}", className="card-title"),
                    html.P([
                        html.Strong("Status: "),
                        html.Span("New", className="text-secondary")
                    ]),
                    html.P([
                        html.Strong("Items: "),
                        html.Span(f"{len(cart_items)} items")
                    ]),
                    html.P([
                        html.Strong("Total: "),
                        html.Span(f"${total:.2f}")
                    ]),
                    dbc.Button(
                        "Track Order",
                        color="primary",
                        className="mt-2"
                    )
                ])
            ])
        ])
        
        # Emit socket event for new order
        socketio.emit('new_order', order_data)
        
        # Close modal, show order status, and clear cart
        return False, order_status, []
    
    # 6. Clear button in order form callback
    @app.callback(
        Output("order-instructions", "value"),
        [Input("clear-order-button", "n_clicks")],
        prevent_initial_call=True
    )
    def clear_order_form(n_clicks):
        """Clear the order form when the Clear button is clicked"""
        if n_clicks:
            return ""  # Clear special instructions
        return no_update
    
    # 7. Order tabs callback
    @app.callback(
        [Output("current-order-content", "style"),
         Output("order-history-content", "style"),
         Output("all-orders-content", "style")],
        [Input("orders-tabs", "active_tab")]
    )
    def switch_order_tabs(active_tab):
        """Switch between order tabs"""
        # Default styles (all hidden)
        styles = [
            {"display": "none"},  # current-order
            {"display": "none"},  # order-history
            {"display": "none"}   # all-orders
        ]
        
        # Show active tab
        if active_tab == "current-order":
            styles[0] = {"display": "block"}
        elif active_tab == "order-history":
            styles[1] = {"display": "block"}
        elif active_tab == "all-orders":
            styles[2] = {"display": "block"}
        
        return styles
    
    # 8. Update cart items display
    @app.callback(
        Output("cart-items-container", "children"),
        [Input("cart-store", "data")]
    )
    def update_cart_items_display(cart_items):
        """Update the cart items display"""
        if not cart_items or len(cart_items) == 0:
            return dbc.Alert(
                "Your cart is empty. Add items from the menu.",
                color="info",
                id="empty-cart-alert",
                is_open=True
            )
        
        # Display cart items using the table component
        return create_order_items_table(cart_items)
    
    # 9. Update cart totals
    @app.callback(
        [Output("cart-subtotal", "children"),
         Output("cart-tax", "children"),
         Output("cart-total", "children"),
         Output("checkout-btn", "disabled")],
        [Input("cart-store", "data")]
    )
    def update_cart_totals(cart_items):
        """Update cart totals and checkout button state"""
        if not cart_items or len(cart_items) == 0:
            return "$0.00", "$0.00", "$0.00", True
        
        # Calculate totals
        subtotal = sum(item.get("price", 0) * item.get("quantity", 1) for item in cart_items)
        tax = subtotal * 0.08  # Assuming 8% tax
        total = subtotal + tax
        
        # Format as currency
        subtotal_str = f"${subtotal:.2f}"
        tax_str = f"${tax:.2f}"
        total_str = f"${total:.2f}"
        
        # Enable checkout button if cart has items
        checkout_disabled = len(cart_items) == 0
        
        return subtotal_str, tax_str, total_str, checkout_disabled
    
    # 10. Order history callback
    @app.callback(
        Output("order-history-container", "children"),
        [Input("refresh-history-btn", "n_clicks"),
         Input("orders-update-interval", "n_intervals")]
    )
    def update_order_history(n_clicks, n_intervals):
        """Update the order history display"""
        # This would normally fetch from a database
        # Using sample data for demo purposes
        
        # Create sample order history
        order_history = [
            {
                "id": "ORD-1234567",
                "date": "2025-03-31",
                "items": ["Cappuccino", "Croissant"],
                "total": 8.50,
                "status": "Completed"
            },
            {
                "id": "ORD-1234568",
                "date": "2025-03-30",
                "items": ["Latte", "Blueberry Muffin", "Orange Juice"],
                "total": 12.75,
                "status": "Completed"
            },
            {
                "id": "ORD-1234569",
                "date": "2025-03-28",
                "items": ["Espresso"],
                "total": 3.25,
                "status": "Completed"
            }
        ]
        
        # Create the table
        if order_history:
            # Create table rows
            rows = []
            for order in order_history:
                # Create status badge
                status_badge = dbc.Badge(
                    order["status"],
                    color="success" if order["status"] == "Completed" else "secondary",
                    className="p-2"
                )
                
                # Create action buttons
                action_buttons = html.Div([
                    dbc.Button(
                        html.I(className="fas fa-eye"),
                        id={"type": "view-history-btn", "index": order["id"]},
                        color="primary",
                        size="sm",
                        className="me-1"
                    ),
                    dbc.Button(
                        "Reorder",
                        id={"type": "reorder-btn", "index": order["id"]},
                        color="success",
                        size="sm"
                    )
                ], className="d-flex")
                
                # Create row
                row = html.Tr([
                    html.Td(order["date"]),
                    html.Td(order["id"]),
                    html.Td(", ".join(order["items"])),
                    html.Td(f"${order['total']:.2f}"),
                    html.Td(status_badge),
                    html.Td(action_buttons)
                ])
                
                rows.append(row)
            
            # Create table
            table = dbc.Table(
                [
                    html.Thead(
                        html.Tr([
                            html.Th("Date"),
                            html.Th("Order ID"),
                            html.Th("Items"),
                            html.Th("Total"),
                            html.Th("Status"),
                            html.Th("Actions")
                        ])
                    ),
                    html.Tbody(rows)
                ],
                bordered=True,
                hover=True,
                responsive=True,
                striped=True
            )
            
            return table
        else:
            return dbc.Alert("No order history found.", color="info")
    
    # Keep existing callbacks for orders table and order status
    # Update this in app/callbacks/order_callbacks.py

    @app.callback(
        Output("orders-table-container", "children"),
        [
            Input("orders-update-interval", "n_intervals"),
            Input("order-status-store", "data"),
            Input("order-filter", "value"),
            Input("socket-order-update", "children")  # Added input for Socket.IO updates
        ],
        [State("user-store", "data")]  # Added user data to get current user
    )
    def update_orders_table(n_intervals, status_update, filter_value, socket_update, user_data):
        """Update the orders table with latest orders"""
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        
        # Get orders from the database instead of using static data
        try:
            from app.data.database import get_orders, get_orders_by_username
            
            # If user is logged in, show their orders
            if user_data and 'username' in user_data:
                orders = get_orders_by_username(user_data['username'])
                print(f"Loaded {len(orders)} orders for user {user_data['username']}")
            else:
                # For admin or demo, show all orders
                orders = get_orders()
                print(f"Loaded {len(orders)} orders (all users)")
        except Exception as e:
            print(f"Error loading orders from database: {e}")
            # Fallback to static demo data if database query fails
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
                # Other demo orders...
            ]
        
        # Check if we have an order update from socket
        if trigger_id == "socket-order-update" and socket_update:
            try:
                new_order = json.loads(socket_update)
                
                # Check if this order is already in our list
                existing_idx = next((i for i, order in enumerate(orders) if order['id'] == new_order['id']), None)
                
                if existing_idx is not None:
                    # Update existing order
                    orders[existing_idx].update(new_order)
                    print(f"Updated order {new_order['id']} in table")
                else:
                    # Add new order to the beginning of the list
                    # Format the items - convert from objects to strings if needed
                    if 'items' in new_order and isinstance(new_order['items'], list):
                        # Extract item names from different formats
                        formatted_items = []
                        for item in new_order['items']:
                            if isinstance(item, dict):
                                # Different item formats
                                if 'name' in item:
                                    formatted_items.append(item['name'])
                                elif 'item_id' in item:
                                    # Try to get name from menu items
                                    try:
                                        from app.data.database import get_menu_item_by_id
                                        menu_item = get_menu_item_by_id(item['item_id'])
                                        if menu_item:
                                            formatted_items.append(menu_item['name'])
                                        else:
                                            formatted_items.append(f"Item #{item['item_id']}")
                                    except:
                                        formatted_items.append(f"Item #{item['item_id']}")
                            elif isinstance(item, str):
                                formatted_items.append(item)
                        
                        new_order['items'] = formatted_items
                    
                    # Set customer name if available
                    if 'customer' not in new_order and user_data and 'username' in user_data:
                        new_order['customer'] = user_data['username']
                    elif 'customer' not in new_order:
                        new_order['customer'] = "Guest"
                    
                    # Set time if not available
                    if 'time' not in new_order:
                        new_order['time'] = datetime.now().strftime("%H:%M")
                    
                    # Add to orders list
                    orders.insert(0, new_order)
                    print(f"Added new order {new_order['id']} to table")
            except Exception as e:
                print(f"Error processing socket order update: {e}")
        
        # Apply status updates from order status store
        if status_update:
            for order in orders:
                if order["id"] == status_update["id"]:
                    order["status"] = status_update["status"]
                    print(f"Updated status of order {order['id']} to {status_update['status']}")
        
        # Apply filter if specified
        if filter_value and filter_value != "All":
            orders = [order for order in orders if order.get("status") == filter_value]
        
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
                order.get("status", "New"),
                color=status_color_map.get(order.get("status", "New"), "secondary"),
                className="p-2"
            )
            
            # Format items for display
            if isinstance(order.get("items"), list):
                if all(isinstance(item, str) for item in order["items"]):
                    items_display = ", ".join(order["items"])
                else:
                    # Handle complex item structures
                    items_display = ", ".join([
                        item["name"] if isinstance(item, dict) and "name" in item 
                        else f"Item #{item['item_id']}" if isinstance(item, dict) and "item_id" in item
                        else str(item)
                        for item in order["items"]
                    ])
            else:
                items_display = "No items"
            
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
                    disabled=order.get("status") != "Ready"
                )
            ], className="d-flex")
            
            # Create the table row
            row = html.Tr([
                html.Td(order.get("time", "")),
                html.Td(order["id"]),
                html.Td(order.get("customer", "Guest")),
                html.Td(items_display),
                html.Td(f"${order.get('total', 0):.2f}"),
                html.Td(order.get("location", order.get("delivery_location", "Unknown"))),
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
            Input({"type": "status-change-btn", "index": ALL}, "n_clicks"),
            Input("socket-order-update", "children")  # Hidden div updated by SocketIO
        ],
        [
            State({"type": "status-change-btn", "index": ALL}, "id"),
            State("order-status-store", "data")
        ],
        prevent_initial_call=True
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