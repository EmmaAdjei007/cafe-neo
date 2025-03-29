# File: app/layouts/landing.py

import dash_bootstrap_components as dbc
from dash import html, dcc
from app.config import config

def layout():
    """
    Create the landing page layout
    
    Returns:
        html.Div: The landing page content
    """
    colors = config['theme_colors']
    hero_style = {
        'background': f'linear-gradient(rgba(44, 27, 15, 0.7), rgba(111, 78, 55, 0.7)), url("/assets/images/hero-bg.jpg")',
        'background-size': 'cover',
        'background-position': 'center',
        'color': 'white',
        'text-align': 'center',
        'padding': '120px 0 80px',
        'margin-top': '-54px',  # To offset the fixed navbar
    }

    hero = html.Div(
    dbc.Container(
        dbc.Row(
            [
                # Content Column
                dbc.Col(
                    [
                        html.H1("Welcome to Neo Cafe", className="display-4 fw-bold mb-2"),  # Reduced mb-3 to mb-2
                        html.P(
                            "Experience the perfect blend of technology and artisanal coffee.",
                            className="lead fs-5 mb-3"  # Reduced mb-4 to mb-3
                        ),
                        html.Div(
                            [
                                dbc.Button(
                                    "Order Now", 
                                    color="light", 
                                    size="md", 
                                    href="/menu", 
                                    className="px-3 py-2",
                                    style={"width": "fit-content"}
                                ),
                                dbc.Button(
                                    "View Dashboard", 
                                    color="primary", 
                                    outline=True, 
                                    size="md", 
                                    href="/dashboard", 
                                    className="px-3 py-2",
                                    style={
                                        "background": "transparent", 
                                        "color": "white", 
                                        "border-color": "white",
                                        "width": "fit-content"
                                    }
                                ),
                            ],
                            className="d-flex gap-2"  # Reduced gap from 3 to 2
                        )
                    ],
                    className="text-start d-flex flex-column justify-content-center",
                    md=6
                ),

                # Image Column
                dbc.Col(
                    html.Div(
                        html.Img(
                            src="/assets/images/hero-coffee.jpg",
                            className="img-fluid",
                            alt="Neo Cafe Coffee",
                            style={
                                "max-width": "250px",  # Reduced from 300px
                                "border-radius": "30%",
                                "height": "auto",
                                "object-fit": "cover",
                                "aspect-ratio": "1/1"
                            }
                        ),
                        className="ratio ratio-1x1",
                        style={"max-width": "250px"}  # Constrain container size
                    ),
                    className="d-flex align-items-center justify-content-center",
                    md=6
                )
            ],
            className="align-items-center g-2"  # Reduced gap from 3 to 2
        ),
        className="py-2"  # Reduced vertical padding from py-3 to py-2
    ),
    style=hero_style,
    className="mb-2"  # Reduced bottom margin from mb-3 to mb-2
)

    # Features section
    features = html.Div(
    dbc.Container(
        [
            html.H2("Why Choose Neo Cafe?", className="text-center mb-5 section-title"),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div(html.I(className="fas fa-robot fa-3x mb-4", style={"color": colors["primary"]})),
                                html.H4("Robot Delivery", className="card-title"),
                                html.P(
                                    "Our robot delivery service brings coffee right to your table or doorstep.",
                                    className="card-text"
                                )
                            ],
                            body=True,
                            className="text-center py-4 h-100"
                        ),
                        md=4,
                        className="mb-4"
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div(html.I(className="fas fa-coffee fa-3x mb-4", style={"color": colors["primary"]})),
                                html.H4("Premium Coffee", className="card-title"),
                                html.P(
                                    "We source and roast the finest beans for a perfect cup every time.",
                                    className="card-text"
                                )
                            ],
                            body=True,
                            className="text-center py-4 h-100"
                        ),
                        md=4,
                        className="mb-4"
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                html.Div(html.I(className="fas fa-comment-dots fa-3x mb-4", style={"color": colors["primary"]})),
                                html.H4("AI Assistant", className="card-title"),
                                html.P(
                                    "Our AI assistant helps you place orders and answers all your questions.",
                                    className="card-text"
                                )
                            ],
                            body=True,
                            className="text-center py-4 h-100"
                        ),
                        md=4,
                        className="mb-4"
                    ),
                ]
            )
        ]
    ),
    className="py-5 bg-light"
)


    # Special offers section
    special = html.Div(
        dbc.Container(
            [
                html.H2("Today's Special", className="text-center mb-5 section-title"),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Img(src="/assets/images/special-offer.jpg", className="img-fluid rounded"),
                            md=6,
                            className="mb-4 mb-md-0"
                        ),
                        dbc.Col(
                            [
                                html.H3(config['special_offer'], className="mb-4"),
                                html.P(
                                    "Start your day with our signature espresso and pair it with a freshly baked pastry at a special price.",
                                    className="mb-4"
                                ),
                                html.P(
                                    "This offer is valid for today only. Don't miss out on this delightful combination!",
                                    className="mb-4"
                                ),
                                dbc.Button(
                                    "Claim Offer", 
                                    color="primary", 
                                    size="lg", 
                                    className="mt-2"
                                ),
                            ],
                            md=6,
                            className="d-flex flex-column justify-content-center"
                        ),
                    ],
                )
            ]
        ),
        className="py-5"
    )

    menu_preview = html.Div(
        dbc.Container(
            [
                html.H2("Most Popular", className="text-center mb-5 section-title"),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(src="/assets/images/menu-items/cappuccino.jpg", top=True),
                                    dbc.CardBody(
                                        [
                                            html.H4("Cappuccino", className="card-title"),
                                            html.H6("$4.50", className="card-subtitle mb-2 text-muted"),
                                            html.P(
                                                "A perfect balance of espresso, steamed milk, and foam.",
                                                className="card-text"
                                            ),
                                            dbc.Button("Order Now", color="primary", className="mt-2")
                                        ]
                                    )
                                ],
                                className="menu-card h-100"
                            ),
                            md=4,
                            className="mb-4"
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(src="/assets/images/menu-items/latte.jpg", top=True),
                                    dbc.CardBody(
                                        [
                                            html.H4("Latte", className="card-title"),
                                            html.H6("$4.75", className="card-subtitle mb-2 text-muted"),
                                            html.P(
                                                "Espresso with steamed milk and a small layer of foam.",
                                                className="card-text"
                                            ),
                                            dbc.Button("Order Now", color="primary", className="mt-2")
                                        ]
                                    )
                                ],
                                className="menu-card h-100"
                            ),
                            md=4,
                            className="mb-4"
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(src="/assets/images/menu-items/mocha.jpg", top=True),
                                    dbc.CardBody(
                                        [
                                            html.H4("Mocha", className="card-title"),
                                            html.H6("$5.25", className="card-subtitle mb-2 text-muted"),
                                            html.P(
                                                "Espresso with chocolate and steamed milk for a sweet treat.",
                                                className="card-text"
                                            ),
                                            dbc.Button("Order Now", color="primary", className="mt-2")
                                        ]
                                    )
                                ],
                                className="menu-card h-100"
                            ),
                            md=4,
                            className="mb-4"
                        ),
                    ],
                ),
                html.Div(
                    dbc.Button(
                        "View Full Menu", 
                        href="/menu", 
                        color="secondary", 
                        className="mx-auto d-block mt-4 px-4"
                    ),
                    className="text-center"
                )
            ]
        ),
        className="py-5 bg-light"
    )

    # Testimonials section
    testimonials = html.Div(
        dbc.Container(
            [
                html.H2("What Our Customers Say", className="text-center mb-5 section-title"),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    html.Div(
                                        html.Img(
                                            src="/assets/images/lynn.jpg", 
                                            className="rounded-circle",
                                            width="80px",
                                            height="80px",
                                            style={"object-fit": "cover"}
                                        ),
                                        className="text-center mb-3"
                                    ),
                                    html.Div(
                                        html.I(className="fas fa-quote-left fa-2x", style={"color": colors['accent'], "opacity": "0.2"}),
                                        className="mb-3"
                                    ),
                                    html.P(
                                        "The AI assistant recommended a coffee I'd never tried before. Now it's my favorite! Neo Cafe knows exactly what I need.",
                                        className="card-text mb-4"
                                    ),
                                    html.H5("Lynn Ahabwe", className="card-title mb-1"),
                                    html.P("Regular Customer", className="card-subtitle text-muted"),
                                ],
                                body=True,
                                className="text-center h-100 py-4"
                            ),
                            md=4,
                            className="mb-4"
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    html.Div(
                                        html.Img(
                                            src="/assets/images/emmanuel.jpg", 
                                            className="rounded-circle",
                                            width="80px",
                                            height="80px",
                                            style={"object-fit": "cover"}
                                        ),
                                        className="text-center mb-3"
                                    ),
                                    html.Div(
                                        html.I(className="fas fa-quote-left fa-2x", style={"color": colors['accent'], "opacity": "0.2"}),
                                        className="mb-3"
                                    ),
                                    html.P(
                                        "Fast delivery and always accurate orders. The coffee arrives hot and fresh every single time. Neo Cafe has changed my mornings.",
                                        className="card-text mb-4"
                                    ),
                                    html.H5("Emmanuel Adjei", className="card-title mb-1"),
                                    html.P("Coffee Enthusiast", className="card-subtitle text-muted"),
                                ],
                                body=True,
                                className="text-center h-100 py-4"
                            ),
                            md=4,
                            className="mb-4"
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    html.Div(
                                        html.Img(
                                            src="/assets/images/romerik.jpg", 
                                            className="rounded-circle",
                                            width="80px",
                                            height="80px",
                                            style={"object-fit": "cover"}
                                        ),
                                        className="text-center mb-3"
                                    ),
                                    html.Div(
                                        html.I(className="fas fa-quote-left fa-2x", style={"color": colors['accent'], "opacity": "0.2"}),
                                        className="mb-3"
                                    ),
                                    html.P(
                                        "The quality of the coffee at Neo Cafe is unmatched. From bean to cup, you can taste the attention to detail in every sip.",
                                        className="card-text mb-4"
                                    ),
                                    html.H5("Romerik Lokossou", className="card-title mb-1"),
                                    html.P("Barista Apprentice", className="card-subtitle text-muted"),
                                ],
                                body=True,
                                className="text-center h-100 py-4"
                            ),
                            md=4,
                            className="mb-4"
                        ),
                    ],
                )
            ]
        ),
        className="py-5"
    )
    
    # CTA section
    cta = html.Div(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H2("Ready to experience Neo Cafe?", className="text-center text-light mb-4"),
                    html.P(
                        "Start your order now or chat with our AI assistant.",
                        className="text-center text-white mb-5 lead"
                    ),
                    html.Div([
                        dbc.Button("Order Now", color="light", size="lg", href="/menu", className="me-2"),
                        dbc.Button("Chat with BaristaBot", color="light", outline=True, size="lg", href="/chat")
                    ], className="text-center")
                ], md=8, className="mx-auto")
            ], className="py-5")
        ]),
        style={
            "background": f"linear-gradient(to right, {colors['primary']}, {colors['secondary']})",
        },
        className="py-5"
    )
    
    # Combine all sections
    layout = html.Div([
        hero,
        features,
        special,
        menu_preview,
        testimonials,
        cta
    ])
    
    return layout
