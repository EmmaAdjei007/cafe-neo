# File: app/components/charts.py

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_sales_chart():
    """
    Create a sales overview chart
    
    Returns:
        go.Figure: Plotly figure for the sales chart
    """
    # Generate sample data for the last 7 days
    dates = [(datetime.now() - timedelta(days=i)).strftime("%a %d") for i in range(6, -1, -1)]
    
    # Create sales data with some randomness but trending upward
    coffee_sales = [round(np.random.normal(80, 10) + i * 5) for i in range(7)]
    food_sales = [round(np.random.normal(50, 8) + i * 3) for i in range(7)]
    
    # Create DataFrame
    df = pd.DataFrame({
        "Date": dates,
        "Coffee Sales": coffee_sales,
        "Food Sales": food_sales,
        "Total": [c + f for c, f in zip(coffee_sales, food_sales)]
    })
    
    # Create the figure
    fig = go.Figure()
    
    # Add bar traces
    fig.add_trace(go.Bar(
        x=dates,
        y=df["Coffee Sales"],
        name="Coffee",
        marker_color="#8B5A2B"
    ))
    
    fig.add_trace(go.Bar(
        x=dates,
        y=df["Food Sales"],
        name="Food",
        marker_color="#C4A484"
    ))
    
    # Add line trace for total
    fig.add_trace(go.Scatter(
        x=dates,
        y=df["Total"],
        mode="lines+markers",
        name="Total",
        line=dict(color="#4682B4", width=3),
        marker=dict(size=8)
    ))
    
    # Update layout
    fig.update_layout(
        barmode="stack",
        xaxis_title="",
        yaxis_title="Sales ($)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=20, t=60, b=40),
        hovermode="x unified"
    )
    
    return fig

def create_orders_chart():
    """
    Create an order distribution pie chart
    
    Returns:
        go.Figure: Plotly figure for the orders chart
    """
    # Create sample data
    categories = ["Dine In", "Takeaway", "Delivery", "Mobile Order"]
    values = [42, 28, 15, 15]
    colors = ["#8B5A2B", "#C4A484", "#4682B4", "#7F9172"]
    
    # Create the figure
    fig = go.Figure(data=[go.Pie(
        labels=categories,
        values=values,
        hole=.4,
        marker_colors=colors
    )])
    
    # Update layout
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=30, b=20),
        annotations=[dict(text="100<br>Orders", x=0.5, y=0.5, font_size=14, showarrow=False)]
    )
    
    return fig

def create_robot_location_map(robot_location=None, destination=None, route=None):
    """
    Create a map for robot location tracking
    
    Args:
        robot_location (dict, optional): Robot location coordinates
        destination (dict, optional): Destination coordinates
        route (list, optional): List of route coordinates
        
    Returns:
        go.Figure: Plotly figure for the map
    """
    # Create base map
    fig = go.Figure(go.Scattermapbox())
    
    # Default to San Francisco if no robot location provided
    center_lat = robot_location["lat"] if robot_location else 37.7749
    center_lon = robot_location["lng"] if robot_location else -122.4194
    
    # Set map center and zoom
    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            center=dict(lat=center_lat, lon=center_lon),
            zoom=15
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=400
    )
    
    # Add robot marker if provided
    if robot_location:
        fig.add_trace(go.Scattermapbox(
            lat=[robot_location["lat"]],
            lon=[robot_location["lng"]],
            mode="markers",
            marker=dict(size=15, color="red"),
            name="Robot"
        ))
    
    # Add destination marker if provided
    if destination:
        fig.add_trace(go.Scattermapbox(
            lat=[destination["lat"]],
            lon=[destination["lng"]],
            mode="markers",
            marker=dict(size=12, color="green"),
            name="Destination"
        ))
    
    # Add route line if provided
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
    
    return fig