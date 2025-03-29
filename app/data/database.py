"""
Database utilities for Neo Cafe
"""
import os
import json
import time
from datetime import datetime
from pathlib import Path

# Define data directory path
DATA_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "seed_data"

def load_json_data(filename):
    """
    Load data from a JSON file
    
    Args:
        filename (str): Name of the JSON file (without path)
        
    Returns:
        list/dict: The loaded data
    """
    file_path = DATA_DIR / filename
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filename} not found in {DATA_DIR}")
        return []
    except json.JSONDecodeError:
        print(f"Error: {filename} is not valid JSON")
        return []

def save_json_data(data, filename):
    """
    Save data to a JSON file
    
    Args:
        data (list/dict): Data to save
        filename (str): Name of the JSON file (without path)
        
    Returns:
        bool: Success status
    """
    file_path = DATA_DIR / filename
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write data to file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False

# User data operations
def get_users():
    """
    Get all users
    
    Returns:
        list: List of user data
    """
    return load_json_data("users.json")

def get_user_by_username(username):
    """
    Get user by username
    
    Args:
        username (str): Username to look for
        
    Returns:
        dict/None: User data or None if not found
    """
    users = get_users()
    user = next((u for u in users if u["username"] == username), None)
    return user

def create_user(user_data):
    """
    Create a new user
    
    Args:
        user_data (dict): User data
        
    Returns:
        bool: Success status
    """
    users = get_users()
    
    # Check if username already exists
    if any(u["username"] == user_data["username"] for u in users):
        return False
    
    # Generate ID if not provided
    if "id" not in user_data:
        user_data["id"] = str(int(time.time()))
    
    # Add created_at timestamp
    user_data["created_at"] = datetime.now().isoformat()
    
    # Add to users list
    users.append(user_data)
    
    # Save updated users list
    return save_json_data(users, "users.json")

def update_user(username, updated_data):
    """
    Update user data
    
    Args:
        username (str): Username of user to update
        updated_data (dict): Updated user data
        
    Returns:
        bool: Success status
    """
    users = get_users()
    
    # Find user by username
    for i, user in enumerate(users):
        if user["username"] == username:
            # Update user data, preserving id and username
            user_id = user["id"]
            user_username = user["username"]
            users[i] = {**user, **updated_data}
            users[i]["id"] = user_id  # Ensure ID doesn't change
            users[i]["username"] = user_username  # Ensure username doesn't change
            users[i]["updated_at"] = datetime.now().isoformat()
            
            # Save updated users list
            return save_json_data(users, "users.json")
    
    # User not found
    return False

# Menu data operations
def get_menu_items():
    """
    Get all menu items
    
    Returns:
        list: List of menu items
    """
    return load_json_data("menu.json")

def get_menu_item_by_id(item_id):
    """
    Get menu item by ID
    
    Args:
        item_id (int/str): Item ID to look for
        
    Returns:
        dict/None: Item data or None if not found
    """
    items = get_menu_items()
    
    # Convert item_id to correct type
    try:
        if isinstance(item_id, str) and item_id.isdigit():
            item_id = int(item_id)
    except:
        pass
    
    # Find item by ID
    item = next((i for i in items if i["id"] == item_id), None)
    return item

def create_menu_item(item_data):
    """
    Create a new menu item
    
    Args:
        item_data (dict): Item data
        
    Returns:
        bool: Success status
    """
    items = get_menu_items()
    
    # Generate ID if not provided
    if "id" not in item_data:
        # Find highest existing ID and increment
        max_id = max([i["id"] for i in items], default=0)
        item_data["id"] = max_id + 1
    
    # Add to items list
    items.append(item_data)
    
    # Save updated items list
    return save_json_data(items, "menu.json")

def update_menu_item(item_id, updated_data):
    """
    Update menu item
    
    Args:
        item_id (int/str): ID of item to update
        updated_data (dict): Updated item data
        
    Returns:
        bool: Success status
    """
    items = get_menu_items()
    
    # Convert item_id to correct type
    try:
        if isinstance(item_id, str) and item_id.isdigit():
            item_id = int(item_id)
    except:
        pass
    
    # Find item by ID
    for i, item in enumerate(items):
        if item["id"] == item_id:
            # Update item data, preserving ID
            item_id_value = item["id"]
            items[i] = {**item, **updated_data}
            items[i]["id"] = item_id_value  # Ensure ID doesn't change
            
            # Save updated items list
            return save_json_data(items, "menu.json")
    
    # Item not found
    return False

# Order data operations
def get_orders():
    """
    Get all orders
    
    Returns:
        list: List of orders
    """
    return load_json_data("orders.json")

def get_order_by_id(order_id):
    """
    Get order by ID
    
    Args:
        order_id (str): Order ID to look for
        
    Returns:
        dict/None: Order data or None if not found
    """
    orders = get_orders()
    order = next((o for o in orders if o["id"] == order_id), None)
    return order

def create_order(order_data):
    """
    Create a new order
    
    Args:
        order_data (dict): Order data
        
    Returns:
        dict/None: Created order data or None if failed
    """
    orders = get_orders()
    
    # Generate ID if not provided
    if "id" not in order_data:
        timestamp = int(time.time())
        order_data["id"] = f"ORD-{timestamp}"
    
    # Add created_at timestamp
    order_data["created_at"] = datetime.now().isoformat()
    
    # Set default status if not provided
    if "status" not in order_data:
        order_data["status"] = "New"
    
    # Add to orders list
    orders.append(order_data)
    
    # Save updated orders list
    if save_json_data(orders, "orders.json"):
        return order_data
    
    return None

def update_order(order_id, updated_data):
    """
    Update order data
    
    Args:
        order_id (str): ID of order to update
        updated_data (dict): Updated order data
        
    Returns:
        dict/None: Updated order data or None if failed
    """
    orders = get_orders()
    
    # Find order by ID
    for i, order in enumerate(orders):
        if order["id"] == order_id:
            # Update order data, preserving ID
            order_id_value = order["id"]
            orders[i] = {**order, **updated_data}
            orders[i]["id"] = order_id_value  # Ensure ID doesn't change
            orders[i]["updated_at"] = datetime.now().isoformat()
            
            # Save updated orders list
            if save_json_data(orders, "orders.json"):
                return orders[i]
    
    # Order not found
    return None

def get_orders_by_username(username):
    """
    Get orders for a specific user
    
    Args:
        username (str): Username to filter by
        
    Returns:
        list: List of matching orders
    """
    orders = get_orders()
    
    # Filter orders by username
    user_orders = [o for o in orders if o.get("username") == username]
    
    # Sort by date descending (newest first)
    user_orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
    
    return user_orders