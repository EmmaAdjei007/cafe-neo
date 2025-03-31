# File: app/layouts/menu.py

import dash_bootstrap_components as dbc
from dash import html, dcc

def layout():
    """
    Create the menu layout
    
    Returns:
        html.Div: The menu content
    """
    # Header section
    header = html.Div([
        html.H1("Menu", className="page-header"),
        html.P("Explore our delicious coffee, pastries, and more", className="lead")
    ])
    
    # Category filter tabs
    category_tabs = dbc.Tabs(
        [
            dbc.Tab(label="All Items", tab_id="all"),
            dbc.Tab(label="Coffee", tab_id="coffee"),
            dbc.Tab(label="Tea", tab_id="tea"),
            dbc.Tab(label="Pastries", tab_id="pastries"),
            dbc.Tab(label="Breakfast", tab_id="breakfast"),
            dbc.Tab(label="Lunch", tab_id="lunch")
        ],
        id="category-tabs",
        active_tab="all",
        className="mb-4"
    )
    
    # Search and filter row
    search_filter_row = dbc.Row([
        dbc.Col([
            dbc.Input(
                id="menu-search",
                type="text",
                placeholder="Search menu items...",
                className="mb-3"
            )
        ], md=6),
        dbc.Col([
            dbc.Select(
                id="menu-sort",
                options=[
                    {"label": "Name (A-Z)", "value": "name_asc"},
                    {"label": "Name (Z-A)", "value": "name_desc"},
                    {"label": "Price (Low to High)", "value": "price_asc"},
                    {"label": "Price (High to Low)", "value": "price_desc"},
                    {"label": "Popularity", "value": "popularity"}
                ],
                value="name_asc",
                className="mb-3"
            )
        ], md=3),
        dbc.Col([
            dbc.Checklist(
                options=[
                    {"label": "Vegetarian", "value": "vegetarian"},
                    {"label": "Vegan", "value": "vegan"},
                    {"label": "Gluten-Free", "value": "gluten_free"}
                ],
                value=[],
                id="menu-dietary",
                inline=True,
                className="mb-3"
            )
        ], md=3)
    ])
    
    # Menu items container
    menu_items_container = html.Div(
        id="menu-items-container",
        className="mb-4"
    )
    
    # Modal content area (doesn't include the quantity input)
    modal_body = html.Div(id="item-details-modal-body")
    
    # Quantity input (always in the layout but can be hidden)
    # Using div instead of FormGroup (which is deprecated)
    quantity_input = html.Div([
        dbc.Label("Quantity:", html_for="item-quantity"),
        dbc.Input(
            id="item-quantity",
            type="number",
            min=1,
            max=10,
            value=1
        )
    ], id="quantity-container", style={"marginTop": "20px"})
    
    # Combine all elements
    layout = html.Div([
        header,
        category_tabs,
        search_filter_row,
        menu_items_container,
        
        # Item details modal
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Item Details"), close_button=True),
                dbc.ModalBody([modal_body, quantity_input]),
                dbc.ModalFooter([
                    dbc.Button("Add to Order", id="modal-add-to-cart", color="primary", className="me-2"),
                    dbc.Button("Close", id="close-item-modal", className="ms-auto", n_clicks=0)
                ]),
            ],
            id="item-details-modal",
            size="lg",
            is_open=False,
        ),
        
        # Hidden stores for menu data and selected item
        dcc.Store(id="menu-data-store", storage_type="memory"),
        dcc.Store(id="selected-item-store", storage_type="memory")
    ])
    
    return layout