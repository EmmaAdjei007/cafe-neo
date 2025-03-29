# File: app/config.py

"""
Configuration settings for Neo Cafe
"""
import os
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Application settings
config = {
    # Flask settings
    "flask_secret_key": os.environ.get('FLASK_SECRET_KEY', uuid.uuid4().hex),
    "debug": os.environ.get('DEBUG', 'True').lower() == 'true',
    "port": int(os.environ.get('PORT', 8050)),

    # Default special offer
    'special_offer': 'Buy one coffee, get a pastry at half price',
    
    # API URLs
    "chainlit_url": os.environ.get('CHAINLIT_URL', 'http://localhost:8001'),
    "robot_simulator_url": os.environ.get('ROBOT_SIMULATOR_URL', 'http://localhost:8051'),
    
    # Database settings
    "data_dir": os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'),
    
    # Authentication settings
    "session_timeout": 24 * 60 * 60,  # 24 hours in seconds
    "remember_me_timeout": 30 * 24 * 60 * 60,  # 30 days in seconds
    "password_reset_timeout": 24 * 60 * 60,  # 24 hours in seconds
    
    # Application appearance
    "app_title": "Neo Cafe - Give me coffee or give me death",
    "theme_colors": {
        "primary": "#6F4E37",  # Medium brown
        "secondary": "#A67B5B",  # Light brown
        "accent": "C8B6A6", # Cream
        "info": "#4682B4",  # Steel blue
        "success": "#7F9172",  # Sage green
        "warning": "#F0E68C",  # Khaki
        "danger": "#992800",  # Brick red
        "light": "#F3ECE7",  # Light Cream
        "dark": "#2C1B0F"  # Dark coffee
    },
    
    # Menu settings
    "default_menu_sort": "name_asc",
    "menu_categories": [
        "coffee",
        "tea",
        "pastries",
        "breakfast",
        "lunch"
    ],
    
    # Order settings
    "default_delivery_location": "Table 1",
    "payment_methods": [
        "Credit Card",
        "Cash",
        "Mobile Payment"
    ],
    "order_statuses": [
        "New",
        "In Progress",
        "Ready",
        "Delivered",
        "Completed",
        "Cancelled"
    ],
    
    # Robot settings
    "robot_statuses": [
        "idle",
        "busy",
        "returning",
        "charging",
        "maintenance",
        "emergency_stop"
    ],
    "delivery_statuses": [
        "preparing",
        "in transit",
        "delivered",
        "returning",
        "delayed",
        "failed"
    ],
    
    # Integration settings
    "enable_socket_io": True,
    "enable_voice_recognition": True,
    "enable_robot_simulation": True,
    
    # Feature flags
    "features": {
        "online_ordering": True,
        "robot_delivery": True,
        "voice_assistant": True,
        "subscription_service": False,
        "loyalty_program": True,
        "inventory_management": True,
        "staff_scheduling": True
    }
}

# Environment-specific settings
if os.environ.get('ENVIRONMENT') == 'production':
    # Production settings
    config.update({
        "debug": False,
        "enable_socket_io": True,
        "session_timeout": 2 * 60 * 60,  # 2 hours in seconds
    })
elif os.environ.get('ENVIRONMENT') == 'testing':
    # Testing settings
    config.update({
        "debug": True,
        "session_timeout": 24 * 60 * 60,  # 24 hours in seconds
        "data_dir": os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'test')
    })

# Function to get config value
def get_config(key, default=None):
    """
    Get a configuration value
    
    Args:
        key (str): Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    return config.get(key, default)