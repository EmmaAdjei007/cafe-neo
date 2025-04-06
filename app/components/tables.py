# File: app/components/tables.py

import dash_bootstrap_components as dbc
from dash import html

def create_orders_table(orders=None):
    """
    Create an orders table
    
    Args:
        orders (list, optional): List of order data
        
    Returns:
        dbc.Table: The table component
    """
    # Define table headers
    headers = ["Time", "Order ID", "Customer", "Items", "Total", "Location", "Status", "Actions"]
    
    # Create table header
    header = html.Thead(html.Tr([html.Th(h) for h in headers]))
    
    # Create table body
    if not orders:
        body = html.Tbody(html.Tr(html.Td("No orders found", colSpan=len(headers), className="text-center")))
    else:
        rows = []
        for order in orders:
            # Create status badge with appropriate color
            status_color_map = {
                "New": "secondary",
                "In Progress": "primary",
                "Ready": "info",
                "Completed": "success",
                "Delivered": "success",
                "Cancelled": "danger"
            }
            
            status_badge = dbc.Badge(
                order.get("status", "Unknown"),
                color=status_color_map.get(order.get("status", ""), "secondary"),
                className="p-2"
            )
            
            # Create action buttons
            action_buttons = html.Div([
                dbc.Button(
                    html.I(className="fas fa-eye"),
                    id={"type": "view-order-btn", "index": order.get("id", "")},
                    color="primary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    html.I(className="fas fa-edit"),
                    id={"type": "edit-order-btn", "index": order.get("id", "")},
                    color="secondary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    html.I(className="fas fa-robot"),
                    id={"type": "deliver-order-btn", "index": order.get("id", "")},
                    color="success",
                    size="sm",
                    disabled=order.get("status", "") != "Ready"
                )
            ], className="d-flex")
            
            # Create the table row
            row = html.Tr([
                html.Td(order.get("time", "")),
                html.Td(order.get("id", "")),
                html.Td(order.get("customer", "")),
                html.Td(", ".join(order.get("items", []))),
                html.Td(f"${order.get('total', 0):.2f}"),
                html.Td(order.get("location", "")),
                html.Td(status_badge),
                html.Td(action_buttons)
            ])
            
            rows.append(row)
        
        body = html.Tbody(rows)
    
    # Create the table
    table = dbc.Table(
        [header, body],
        className="order-table",
        bordered=True,
        hover=True,
        responsive=True,
        striped=True
    )
    
    return table

def create_menu_items_table(items=None):
    """
    Create a menu items table for admin
    
    Args:
        items (list, optional): List of menu item data
        
    Returns:
        dbc.Table: The table component
    """
    # Define table headers
    headers = ["ID", "Name", "Category", "Price", "Popular", "Availability", "Actions"]
    
    # Create table header
    header = html.Thead(html.Tr([html.Th(h) for h in headers]))
    
    # Create table body
    if not items:
        body = html.Tbody(html.Tr(html.Td("No menu items found", colSpan=len(headers), className="text-center")))
    else:
        rows = []
        for item in items:
            # Create popular badge
            popular_badge = dbc.Badge(
                "Popular",
                color="primary",
                className="p-2"
            ) if item.get("popular", False) else ""
            
            # Create availability badge
            available = item.get("available", True)
            availability_badge = dbc.Badge(
                "Available",
                color="success",
                className="p-2"
            ) if available else dbc.Badge(
                "Unavailable",
                color="danger",
                className="p-2"
            )
            
            # Create action buttons
            action_buttons = html.Div([
                dbc.Button(
                    html.I(className="fas fa-edit"),
                    id={"type": "edit-item-btn", "index": item.get("id", "")},
                    color="primary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    html.I(className="fas fa-trash-alt"),
                    id={"type": "delete-item-btn", "index": item.get("id", "")},
                    color="danger",
                    size="sm"
                )
            ], className="d-flex")
            
            # Create the table row
            row = html.Tr([
                html.Td(item.get("id", "")),
                html.Td(item.get("name", "")),
                html.Td(item.get("category", "")),
                html.Td(f"${item.get('price', 0):.2f}"),
                html.Td(popular_badge),
                html.Td(availability_badge),
                html.Td(action_buttons)
            ])
            
            rows.append(row)
        
        body = html.Tbody(rows)
    
    # Create the table
    table = dbc.Table(
        [header, body],
        className="menu-table",
        bordered=True,
        hover=True,
        responsive=True,
        striped=True
    )
    
    return table

def create_users_table(users=None):
    """
    Create a users table for admin
    
    Args:
        users (list, optional): List of user data
        
    Returns:
        dbc.Table: The table component
    """
    # Define table headers
    headers = ["ID", "Username", "Email", "Role", "Last Login", "Actions"]
    
    # Create table header
    header = html.Thead(html.Tr([html.Th(h) for h in headers]))
    
    # Create table body
    if not users:
        body = html.Tbody(html.Tr(html.Td("No users found", colSpan=len(headers), className="text-center")))
    else:
        rows = []
        for user in users:
            # Create role badge
            role = user.get("role", "customer")
            role_colors = {
                "admin": "danger",
                "staff": "warning",
                "customer": "info"
            }
            role_badge = dbc.Badge(
                role.capitalize(),
                color=role_colors.get(role, "secondary"),
                className="p-2"
            )
            
            # Create action buttons
            action_buttons = html.Div([
                dbc.Button(
                    html.I(className="fas fa-edit"),
                    id={"type": "edit-user-btn", "index": user.get("id", "")},
                    color="primary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    html.I(className="fas fa-key"),
                    id={"type": "reset-password-btn", "index": user.get("id", "")},
                    color="warning",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    html.I(className="fas fa-trash-alt"),
                    id={"type": "delete-user-btn", "index": user.get("id", "")},
                    color="danger",
                    size="sm"
                )
            ], className="d-flex")
            
            # Create the table row
            row = html.Tr([
                html.Td(user.get("id", "")),
                html.Td(user.get("username", "")),
                html.Td(user.get("email", "")),
                html.Td(role_badge),
                html.Td(user.get("last_login", "")),
                html.Td(action_buttons)
            ])
            
            rows.append(row)
        
        body = html.Tbody(rows)
    
    # Create the table
    table = dbc.Table(
        [header, body],
        className="users-table",
        bordered=True,
        hover=True,
        responsive=True,
        striped=True
    )
    
    return table

def create_inventory_table(items=None):
    """
    Create an inventory table
    
    Args:
        items (list, optional): List of inventory item data
        
    Returns:
        dbc.Table: The table component
    """
    # Define table headers
    headers = ["ID", "Item", "Category", "Current Stock", "Min Stock", "Status", "Actions"]
    
    # Create table header
    header = html.Thead(html.Tr([html.Th(h) for h in headers]))
    
    # Create table body
    if not items:
        body = html.Tbody(html.Tr(html.Td("No inventory items found", colSpan=len(headers), className="text-center")))
    else:
        rows = []
        for item in items:
            # Get stock values
            current_stock = item.get("current_stock", 0)
            min_stock = item.get("min_stock", 1)
            
            # Create status badge
            if current_stock <= 0:
                status_badge = dbc.Badge("Out of Stock", color="danger", className="p-2")
            elif current_stock < min_stock:
                status_badge = dbc.Badge("Low Stock", color="warning", className="p-2")
            else:
                status_badge = dbc.Badge("In Stock", color="success", className="p-2")
            
            # Create action buttons
            action_buttons = html.Div([
                dbc.Button(
                    html.I(className="fas fa-edit"),
                    id={"type": "edit-inventory-btn", "index": item.get("id", "")},
                    color="primary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    "Restock",
                    id={"type": "restock-btn", "index": item.get("id", "")},
                    color="success",
                    size="sm"
                )
            ], className="d-flex")
            
            # Create the table row
            row = html.Tr([
                html.Td(item.get("id", "")),
                html.Td(item.get("name", "")),
                html.Td(item.get("category", "")),
                html.Td(current_stock),
                html.Td(min_stock),
                html.Td(status_badge),
                html.Td(action_buttons)
            ])
            
            rows.append(row)
        
        body = html.Tbody(rows)
    
    # Create the table
    table = dbc.Table(
        [header, body],
        className="inventory-table",
        bordered=True,
        hover=True,
        responsive=True,
        striped=True
    )
    
    return table

def create_order_items_table(items=None):
    """
    Create a table of items within an order
    
    Args:
        items (list, optional): List of order items
        
    Returns:
        dbc.Table: The table component
    """
    import dash_bootstrap_components as dbc
    from dash import html
    
    # Define table headers
    headers = ["Item", "Price", "Quantity", "Subtotal", "Actions"]
    
    # Create table header
    header = html.Thead(html.Tr([html.Th(h) for h in headers]))
    
    # Create table body
    if not items:
        body = html.Tbody(html.Tr(html.Td("No items in order", colSpan=len(headers), className="text-center")))
    else:
        rows = []
        for i, item in enumerate(items):
            # Get item values with defaults
            name = item.get("name", "")
            price = item.get("price", 0)
            quantity = item.get("quantity", 1)
            item_id = item.get("id", i)  # Use index as fallback ID
            
            # Calculate subtotal
            subtotal = price * quantity
            
            # Create action buttons
            action_buttons = html.Div([
                dbc.Button(
                    html.I(className="fas fa-minus"),
                    id={"type": "decrease-item-btn", "index": item_id},
                    color="secondary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    html.I(className="fas fa-plus"),
                    id={"type": "increase-item-btn", "index": item_id},
                    color="secondary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    html.I(className="fas fa-trash"),
                    id={"type": "remove-item-btn", "index": item_id},
                    color="danger",
                    size="sm"
                )
            ], className="d-flex justify-content-center")
            
            # Create the table row
            row = html.Tr([
                html.Td(name),
                html.Td(f"${price:.2f}"),
                html.Td(quantity),
                html.Td(f"${subtotal:.2f}"),
                html.Td(action_buttons)
            ])
            
            rows.append(row)
        
        body = html.Tbody(rows)
    
    # Create the table
    table = dbc.Table(
        [header, body],
        className="order-items-table",
        bordered=True,
        hover=True,
        responsive=True,
        striped=True
    )
    
    return table

def create_order_history_table(orders=None):
    """
    Create an order history table for customer profile
    
    Args:
        orders (list, optional): List of order data
        
    Returns:
        dbc.Table: The table component
    """
    # Define table headers
    headers = ["Date", "Order ID", "Items", "Total", "Status", "Actions"]
    
    # Create table header
    header = html.Thead(html.Tr([html.Th(h) for h in headers]))
    
    # Create table body
    if not orders:
        body = html.Tbody(html.Tr(html.Td("No order history found", colSpan=len(headers), className="text-center")))
    else:
        rows = []
        for order in orders:
            # Create status badge with appropriate color
            status_color_map = {
                "New": "secondary",
                "In Progress": "primary",
                "Ready": "info",
                "Completed": "success",
                "Delivered": "success",
                "Cancelled": "danger"
            }
            
            status_badge = dbc.Badge(
                order.get("status", "Unknown"),
                color=status_color_map.get(order.get("status", ""), "secondary"),
                className="p-2"
            )
            
            # Create action buttons
            action_buttons = html.Div([
                dbc.Button(
                    html.I(className="fas fa-eye"),
                    id={"type": "view-history-btn", "index": order.get("id", "")},
                    color="primary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    "Reorder",
                    id={"type": "reorder-btn", "index": order.get("id", "")},
                    color="success",
                    size="sm"
                )
            ], className="d-flex")
            
            # Create the table row
            row = html.Tr([
                html.Td(order.get("date", "")),
                html.Td(order.get("id", "")),
                html.Td(", ".join(order.get("items", []))),
                html.Td(f"${order.get('total', 0):.2f}"),
                html.Td(status_badge),
                html.Td(action_buttons)
            ])
            
            rows.append(row)
        
        body = html.Tbody(rows)
    
    # Create the table
    table = dbc.Table(
        [header, body],
        className="order-history-table",
        bordered=True,
        hover=True,
        responsive=True,
        striped=True
    )
    
    return table

def create_announcements_table(announcements=None):
    """
    Create an announcements table for admin
    
    Args:
        announcements (list, optional): List of announcement data
        
    Returns:
        dbc.Table: The table component
    """
    # Define table headers
    headers = ["Date", "Title", "Posted By", "Visibility", "Duration", "Actions"]
    
    # Create table header
    header = html.Thead(html.Tr([html.Th(h) for h in headers]))
    
    # Create table body
    if not announcements:
        body = html.Tbody(html.Tr(html.Td("No announcements found", colSpan=len(headers), className="text-center")))
    else:
        rows = []
        for announcement in announcements:
            # Create visibility badge
            visibility = announcement.get("visibility", "all")
            visibility_badge = dbc.Badge(
                "All Users" if visibility == "all" else "Staff Only",
                color="info" if visibility == "all" else "warning",
                className="p-2"
            )
            
            # Create action buttons
            action_buttons = html.Div([
                dbc.Button(
                    html.I(className="fas fa-edit"),
                    id={"type": "edit-announcement-btn", "index": announcement.get("id", "")},
                    color="primary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    html.I(className="fas fa-trash-alt"),
                    id={"type": "delete-announcement-btn", "index": announcement.get("id", "")},
                    color="danger",
                    size="sm"
                )
            ], className="d-flex")
            
            # Create the table row
            row = html.Tr([
                html.Td(announcement.get("date", "")),
                html.Td(announcement.get("title", "")),
                html.Td(announcement.get("posted_by", "")),
                html.Td(visibility_badge),
                html.Td(announcement.get("duration", "Permanent")),
                html.Td(action_buttons)
            ])
            
            rows.append(row)
        
        body = html.Tbody(rows)
    
    # Create the table
    table = dbc.Table(
        [header, body],
        className="announcements-table",
        bordered=True,
        hover=True,
        responsive=True,
        striped=True
    )
    
    return table

def create_robot_delivery_table(deliveries=None):
    """
    Create a robot delivery table
    
    Args:
        deliveries (list, optional): List of delivery data
        
    Returns:
        dbc.Table: The table component
    """
    # Define table headers
    headers = ["Time", "Order ID", "Customer", "Destination", "Robot ID", "Status", "Actions"]
    
    # Create table header
    header = html.Thead(html.Tr([html.Th(h) for h in headers]))
    
    # Create table body
    if not deliveries:
        body = html.Tbody(html.Tr(html.Td("No active deliveries", colSpan=len(headers), className="text-center")))
    else:
        rows = []
        for delivery in deliveries:
            # Create status badge with appropriate color
            status = delivery.get("status", "unknown")
            status_color_map = {
                "preparing": "secondary",
                "in transit": "primary",
                "delivered": "success",
                "returning": "info",
                "delayed": "warning",
                "failed": "danger"
            }
            
            status_badge = dbc.Badge(
                status.capitalize(),
                color=status_color_map.get(status, "secondary"),
                className="p-2"
            )
            
            # Create action buttons
            action_buttons = html.Div([
                dbc.Button(
                    "Track",
                    id={"type": "track-delivery-btn", "index": delivery.get("order_id", "")},
                    color="primary",
                    size="sm",
                    className="me-1"
                ),
                dbc.Button(
                    "Control",
                    id={"type": "control-robot-btn", "index": delivery.get("robot_id", "")},
                    color="secondary",
                    size="sm"
                )
            ], className="d-flex")
            
            # Create the table row
            row = html.Tr([
                html.Td(delivery.get("time", "")),
                html.Td(delivery.get("order_id", "")),
                html.Td(delivery.get("customer", "")),
                html.Td(delivery.get("destination", "")),
                html.Td(delivery.get("robot_id", "")),
                html.Td(status_badge),
                html.Td(action_buttons)
            ])
            
            rows.append(row)
        
        body = html.Tbody(rows)
    
    # Create the table
    table = dbc.Table(
        [header, body],
        className="robot-delivery-table",
        bordered=True,
        hover=True,
        responsive=True,
        striped=True
    )
    
    return table