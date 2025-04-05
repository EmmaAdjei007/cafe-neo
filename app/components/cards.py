# File: app/components/cards.py

import dash_bootstrap_components as dbc
from dash import html

def summary_card(title, value, subtitle=None, icon=None, color="primary"):
    """
    Create a summary card component
    
    Args:
        title (str): Card title
        value (str): Main value to display
        subtitle (str, optional): Subtitle text
        icon (str, optional): Font Awesome icon class
        color (str, optional): Card color theme
        
    Returns:
        dbc.Card: The summary card component
    """
    # Create icon if specified
    icon_element = html.Div(html.I(className=icon), className=f"icon text-{color}") if icon else None
    
    # Create subtitle if specified
    subtitle_element = html.Div(subtitle, className="subtitle") if subtitle else None
    
    # Create the card content
    card_content = [
        icon_element,
        html.Div(value, className=f"value text-{color}"),
        html.Div(title, className="title"),
        subtitle_element
    ]
    
    # Remove None elements
    card_content = [element for element in card_content if element is not None]
    
    # Create the card
    card = dbc.Card(
        dbc.CardBody(card_content),
        className=f"summary-card border-{color}"
    )
    
    return card

def order_card(order_id, location, items, status, time):
    """
    Create an order card component
    
    Args:
        order_id (str): Order ID
        location (str): Delivery location
        items (str): Item summary
        status (str): Order status
        time (str): Time information
        
    Returns:
        dbc.Card: The order card component
    """
    # Map status to appropriate color
    status_colors = {
        "New": "secondary",
        "In Progress": "primary",
        "Ready": "info",
        "Delivered": "success",
        "Completed": "success",
        "Cancelled": "danger"
    }
    
    color = status_colors.get(status, "secondary")
    
    # Create the card
    card = dbc.Card(
        [
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H5(order_id, className="card-title"),
                        html.P(f"Location: {location}", className="card-text mb-0"),
                        html.P(f"Items: {items}", className="card-text mb-0 text-muted"),
                        html.Small(f"Time: {time}", className="text-muted")
                    ], width=8),
                    dbc.Col([
                        dbc.Badge(status, color=color, className="p-2"),
                        dbc.Button(
                            "Details",
                            id={"type": "order-details-btn", "index": order_id},
                            color="link",
                            size="sm",
                            className="mt-2"
                        )
                    ], width=4, className="text-end")
                ])
            ])
        ],
        className="mb-3"
    )
    
    return card

def menu_item_card(item):
    """
    Create a menu item card component with improved sizing to match reference image.
    
    Args:
        item (dict): Menu item data
        
    Returns:
        dbc.Card: The menu item card component
    """
    # Create badge elements for dietary info
    badges = []
    if item.get("vegetarian"):
        badges.append(dbc.Badge("Vegetarian", color="success", className="me-1"))
    if item.get("vegan"):
        badges.append(dbc.Badge("Vegan", color="success", className="me-1"))
    if item.get("gluten_free"):
        badges.append(dbc.Badge("Gluten-Free", color="warning", className="me-1"))

    # Create the card
    card = dbc.Card(
        [
            # Image at the top with fixed height
            dbc.CardImg(src=item.get("image", "/assets/images/menu-items/default.jpg"), top=True, className="menu-item-img"),
            
            # Card body
            dbc.CardBody([
                html.H5(item["name"], className="card-title text-center fw-bold"),
                html.P(f"${item['price']:.2f}", className="card-price text-center fw-bold"),
                html.P(item["description"], className="card-text text-center text-muted"),
                
                # Badge section
                html.Div(badges, className="text-center mb-3"),
                
                # Buttons aligned centrally
                html.Div([
                    dbc.Button(
                        "Add to Order",
                        id={"type": "add-to-cart-btn", "index": item["id"]},
                        color="primary",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Details",
                        id={"type": "item-details-btn", "index": item["id"]},
                        color="secondary",
                        outline=True
                    )
                ], className="d-flex justify-content-center"),
            ])
        ],
        className="menu-card shadow-sm rounded"
    )

    return card

