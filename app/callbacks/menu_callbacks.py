# File: app/callbacks/menu_callbacks.py

from dash import Input, Output, State, callback_context, html, dcc
import dash_bootstrap_components as dbc
import json
import pandas as pd
import math

def register_callbacks(app):
    """
    Register callbacks for menu management
    
    Args:
        app: Dash application instance
    """
    @app.callback(
        Output("menu-data-store", "data"),
        [Input("menu-data-store", "id")]
    )
    def load_menu_data(id):
        """Load menu data into store"""
        # In a real app, this would load from a database
        # For demo purposes, using static data
        
        menu_items = [
            {
                "id": 1,
                "name": "Espresso",
                "description": "Rich and complex, our signature espresso blend has notes of cocoa and caramel.",
                "price": 2.95,
                "category": "coffee",
                "image": "/assets/images/menu-items/espresso.jpg",
                "popular": True,
                "vegetarian": True,
                "vegan": True,
                "gluten_free": True
            },
            {
                "id": 2,
                "name": "Cappuccino",
                "description": "Espresso with steamed milk and a deep layer of foam.",
                "price": 4.25,
                "category": "coffee",
                "image": "/assets/images/menu-items/cappuccino.jpg",
                "popular": True,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": True
            },
            {
                "id": 3,
                "name": "Latte",
                "description": "Smooth espresso with steamed milk and a light layer of foam.",
                "price": 4.50,
                "category": "coffee",
                "image": "/assets/images/menu-items/latte.jpg",
                "popular": True,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": True
            },
            {
                "id": 4,
                "name": "Mocha",
                "description": "Espresso with steamed milk, chocolate syrup, and whipped cream.",
                "price": 4.95,
                "category": "coffee",
                "image": "/assets/images/menu-items/mocha.jpg",
                "popular": False,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": True
            },
            {
                "id": 5,
                "name": "Green Tea",
                "description": "Premium Japanese green tea with a delicate, earthy flavor.",
                "price": 3.50,
                "category": "tea",
                "image": "/assets/images/menu-items/green-tea.jpg",
                "popular": False,
                "vegetarian": True,
                "vegan": True,
                "gluten_free": True
            },
            {
                "id": 6,
                "name": "Chai Latte",
                "description": "Black tea infused with spices and steamed milk.",
                "price": 4.50,
                "category": "tea",
                "image": "/assets/images/menu-items/chai-latte.jpg",
                "popular": True,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": True
            },
            {
                "id": 7,
                "name": "Croissant",
                "description": "Buttery, flaky pastry made with pure butter.",
                "price": 3.25,
                "category": "pastries",
                "image": "/assets/images/menu-items/croissant.jpg",
                "popular": True,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": False
            },
            {
                "id": 8,
                "name": "Blueberry Muffin",
                "description": "Moist muffin packed with fresh blueberries.",
                "price": 3.50,
                "category": "pastries",
                "image": "/assets/images/menu-items/blueberry-muffin.jpg",
                "popular": False,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": False
            },
            {
                "id": 9,
                "name": "Avocado Toast",
                "description": "Whole grain toast with smashed avocado, salt, pepper, and red pepper flakes.",
                "price": 7.95,
                "category": "breakfast",
                "image": "/assets/images/menu-items/avocado-toast.jpg",
                "popular": True,
                "vegetarian": True,
                "vegan": True,
                "gluten_free": False
            },
            {
                "id": 10,
                "name": "Breakfast Sandwich",
                "description": "Egg, cheddar, and bacon on a toasted English muffin.",
                "price": 6.95,
                "category": "breakfast",
                "image": "/assets/images/menu-items/breakfast-sandwich.jpg",
                "popular": True,
                "vegetarian": True,
                "vegan": False,
                "gluten_free": False
            },
            {
                "id": 11,
                "name": "Chicken Panini",
                "description": "Grilled chicken with pesto, mozzarella, and roasted red peppers.",
                "price": 9.95,
                "category": "lunch",
                "image": "/assets/images/menu-items/chicken-panini.jpg",
                "popular": False,
                "vegetarian": False,
                "vegan": False,
                "gluten_free": False
            },
            {
                "id": 12,
                "name": "Vegetable Wrap",
                "description": "Seasonal vegetables with hummus in a whole wheat wrap.",
                "price": 8.95,
                "category": "lunch",
                "image": "/assets/images/menu-items/vegetable-wrap.jpg",
                "popular": False,
                "vegetarian": True,
                "vegan": True,
                "gluten_free": False
            }
        ]
        
        return menu_items
    
    @app.callback(
        Output("menu-items-container", "children"),
        [
            Input("menu-data-store", "data"),
            Input("category-tabs", "active_tab"),
            Input("menu-search", "value"),
            Input("menu-sort", "value"),
            Input("menu-dietary", "value")
        ]
    )
    def update_menu_items(menu_data, active_tab, search_term, sort_value, dietary_filters):
        """Update the menu items based on filters and search"""
        from app.components.cards import menu_item_card
        
        if not menu_data:
            return html.Div("No menu items found.")
        
        # Filter by category
        if active_tab and active_tab != "all":
            filtered_items = [item for item in menu_data if item.get("category") == active_tab]
        else:
            filtered_items = menu_data
        
        # Filter by search term
        if search_term:
            search_term = search_term.lower()
            filtered_items = [
                item for item in filtered_items 
                if search_term in item["name"].lower() or search_term in item["description"].lower()
            ]
        
        # Filter by dietary restrictions
        if dietary_filters:
            for filter_value in dietary_filters:
                filtered_items = [item for item in filtered_items if item.get(filter_value, False)]
        
        # Sort items
        if sort_value:
            if sort_value == "name_asc":
                filtered_items = sorted(filtered_items, key=lambda x: x["name"])
            elif sort_value == "name_desc":
                filtered_items = sorted(filtered_items, key=lambda x: x["name"], reverse=True)
            elif sort_value == "price_asc":
                filtered_items = sorted(filtered_items, key=lambda x: x["price"])
            elif sort_value == "price_desc":
                filtered_items = sorted(filtered_items, key=lambda x: x["price"], reverse=True)
            elif sort_value == "popularity":
                filtered_items = sorted(filtered_items, key=lambda x: (0 if x.get("popular", False) else 1, x["name"]))
        
        # Create item cards
        if filtered_items:
            # Create rows of cards, 3 items per row
            rows = []
            for i in range(0, len(filtered_items), 3):
                # Get items for this row
                row_items = filtered_items[i:i+3]
                
                # Create columns for items
                cols = []
                for item in row_items:
                    cols.append(dbc.Col(menu_item_card(item), md=4, className="mb-4"))
                
                # Add empty columns if row is not full
                while len(cols) < 3:
                    cols.append(dbc.Col(md=4))
                
                # Create row
                rows.append(dbc.Row(cols))
            
            return html.Div(rows)
        else:
            return dbc.Alert("No items match your filters. Try adjusting your search or filters.", color="info")
    
    @app.callback(
        [
            Output("item-details-modal", "is_open"),
            Output("item-details-modal-body", "children"),
            Output("selected-item-store", "data")
        ],
        [
            Input({"type": "item-details-btn", "index": "all"}, "n_clicks"),
            Input("close-item-modal", "n_clicks")
        ],
        [
            State({"type": "item-details-btn", "index": "all"}, "id"),
            State("menu-data-store", "data"),
            State("item-details-modal", "is_open")
        ]
    )
    def toggle_item_modal(n_clicks_list, close_clicks, btn_ids, menu_data, is_open):
        """Toggle the item details modal and show selected item details"""
        ctx = callback_context
        
        # Default return if no button clicked
        if not ctx.triggered or not btn_ids:
            return False, None, None
        
        # Check if close button was clicked
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "close-item-modal":
            return False, None, None
        
        # Find which item button was clicked
        for i, n_clicks in enumerate(n_clicks_list):
            if n_clicks and btn_ids[i]["type"] == "item-details-btn":
                item_id = btn_ids[i]["index"]
                
                # Find the item in menu data
                item = next((item for item in menu_data if item["id"] == item_id), None)
                
                if item:
                    # Create modal content
                    modal_content = [
                        dbc.Row([
                            dbc.Col([
                                html.Img(
                                    src=item.get("image", "/assets/images/menu-items/default.jpg"),
                                    className="img-fluid rounded",
                                    style={"width": "100%"}
                                )
                            ], md=6),
                            dbc.Col([
                                html.H3(item["name"], className="mb-3"),
                                html.P(item["description"], className="mb-3"),
                                html.H5(f"Price: ${item['price']:.2f}", className="mb-3"),
                                html.Div([
                                    dbc.Badge("Vegetarian", color="success", className="me-2") if item.get("vegetarian") else None,
                                    dbc.Badge("Vegan", color="success", className="me-2") if item.get("vegan") else None,
                                    dbc.Badge("Gluten-Free", color="warning", className="me-2") if item.get("gluten_free") else None,
                                    dbc.Badge("Popular", color="primary", className="me-2") if item.get("popular") else None
                                ], className="mb-4"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("Quantity"),
                                    dbc.Input(
                                        id="item-quantity",
                                        type="number",
                                        min=1,
                                        max=10,
                                        value=1
                                    ),
                                    dbc.Button(
                                        "Add to Order",
                                        id="modal-add-to-cart",
                                        color="primary"
                                    )
                                ])
                            ], md=6)
                        ])
                    ]
                    
                    return True, modal_content, item
        
        # If no matching button found
        return is_open, None, None
    
    @app.callback(
        Output("cart-store", "data"),
        [
            Input({"type": "add-to-cart-btn", "index": "all"}, "n_clicks"),
            Input("modal-add-to-cart", "n_clicks")
        ],
        [
            State({"type": "add-to-cart-btn", "index": "all"}, "id"),
            State("menu-data-store", "data"),
            State("selected-item-store", "data"),
            State("item-quantity", "value"),
            State("cart-store", "data")
        ]
    )
    def add_to_cart(n_clicks_list, modal_clicks, btn_ids, menu_data, selected_item, quantity, current_cart):
        """Add items to the cart"""
        ctx = callback_context
        
        # Default return if no button clicked
        if not ctx.triggered:
            return current_cart or []
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Initialize cart if empty
        if not current_cart:
            current_cart = []
        
        # Check if modal add button was clicked
        if button_id == "modal-add-to-cart" and modal_clicks and selected_item:
            # Add the selected item to cart with specified quantity
            item_to_add = selected_item.copy()
            item_to_add["quantity"] = quantity or 1
            
            # Check if item already in cart
            existing_item = next((item for item in current_cart if item["id"] == item_to_add["id"]), None)
            
            if existing_item:
                # Update quantity
                existing_item["quantity"] += item_to_add["quantity"]
            else:
                # Add new item
                current_cart.append(item_to_add)
            
            return current_cart
        
        # Check if regular add button was clicked
        if n_clicks_list and btn_ids:
            for i, n_clicks in enumerate(n_clicks_list):
                if n_clicks and btn_ids[i]["type"] == "add-to-cart-btn":
                    item_id = btn_ids[i]["index"]
                    
                    # Find the item in menu data
                    item = next((item for item in menu_data if item["id"] == item_id), None)
                    
                    if item:
                        # Add the item to cart with quantity 1
                        item_to_add = item.copy()
                        item_to_add["quantity"] = 1
                        
                        # Check if item already in cart
                        existing_item = next((item for item in current_cart if item["id"] == item_to_add["id"]), None)
                        
                        if existing_item:
                            # Update quantity
                            existing_item["quantity"] += 1
                        else:
                            # Add new item
                            current_cart.append(item_to_add)
                        
                        return current_cart
        
        # If no matching button found
        return current_cart
