# chainlit_app/app.py
import os
import sys
import json
import time
import uuid
import sqlite3
import traceback
import urllib.parse
import requests
from typing import Dict, List, Optional
from datetime import datetime

import chainlit as cl
from chainlit.element import Element
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.schema import SystemMessage, HumanMessage, AIMessage

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log')
    ]
)

# Create logger
logger = logging.getLogger('neo_cafe')
logger.setLevel(logging.DEBUG)

# Add this after imports in both app.py and chainlit_app/app.py

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Constants
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:8050')
ROBOT_SIMULATOR_URL = os.environ.get('ROBOT_SIMULATOR_URL', 'http://localhost:8051')
DB_PATH = os.environ.get('DB_PATH', 'neo_cafe.db')
SESSION_TIMEOUT = 1800  # 30 minutes

# Global variables
menu_items = []  # Will be populated in the create_knowledge_base function
processed_message_ids = set()  # Track processed message IDs to avoid duplicates
is_floating_chat = False  # Flag to check if running in floating mode


# ----- Database Setup -----

def init_db():
    """Initialize database for conversation history and orders"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (session_id TEXT PRIMARY KEY,
                  user_id TEXT,
                  created_at TIMESTAMP,
                  last_active TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT,
                  content TEXT,
                  is_user BOOLEAN,
                  timestamp TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS order_history
                 (order_id TEXT PRIMARY KEY,
                  user_id TEXT,
                  items TEXT,
                  status TEXT,
                  created_at TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

# Initialize the database on module load
try:
    init_db()
except Exception as e:
    print(f"Error initializing database: {e}")

# ----- Knowledge Base Setup -----

def load_menu_data():
    """
    Load menu data from menu.json with robust error handling.
    Returns:
        list: Menu items.
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        possible_paths = [
            os.path.join(base_dir, 'app', 'data', 'seed_data', 'menu.json'),
            os.path.join(base_dir, 'data', 'seed_data', 'menu.json'),
            os.path.join(base_dir, 'data', 'menu.json'),
            os.path.join(base_dir, 'app', 'data', 'menu.json')
        ]
        
        for menu_path in possible_paths:
            if os.path.exists(menu_path):
                print(f"Found menu file at: {menu_path}")
                with open(menu_path, 'r') as f:
                    data = json.load(f)
                    validate_menu_data(data)
                    return data
        
        print("Warning: Could not find menu.json, using default menu")
        return default_menu()
    except Exception as e:
        print(f"Error loading menu data: {e}")
        return default_menu()

def validate_menu_data(data: list):
    """Validate menu items have required fields"""
    required = ['id', 'name', 'price', 'category']
    
    for item in data:
        # Check required fields
        if not all(key in item for key in required):
            raise ValueError(f"Missing required field in item: {item}")
            
        # Validate field types
        if not isinstance(item['price'], (int, float)):
            raise ValueError(f"Invalid price format in item: {item['id']}")

def default_menu():
    """Provide a fallback menu if the main one can't be loaded"""
    return [
        {
            "id": 1, 
            "name": "Espresso", 
            "description": "Rich and complex, our signature espresso blend has notes of cocoa and caramel.", 
            "price": 2.95, 
            "category": "coffee", 
            "popular": True,
            "vegetarian": True,
            "vegan": True,
            "gluten_free": True
        },
        {
            "id": 2, 
            "name": "Latte", 
            "description": "Smooth espresso with steamed milk and a light layer of foam.", 
            "price": 4.50, 
            "category": "coffee", 
            "popular": True,
            "vegetarian": True,
            "vegan": False,
            "gluten_free": True
        },
        {
            "id": 3, 
            "name": "Cappuccino", 
            "description": "Espresso with steamed milk and a deep layer of foam.", 
            "price": 4.25, 
            "category": "coffee", 
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
            "popular": True,
            "vegetarian": True,
            "vegan": False,
            "gluten_free": False
        }
    ]

def create_knowledge_base():
    """
    Create vector store knowledge base for menu items and other information.
    Returns:
        FAISS: Vector store.
    """
    menu_data = load_menu_data()
    global menu_items
    menu_items = menu_data
    documents = []
    
    for item in menu_data:
        # Safely access optional fields
        description = item.get('description', 'No description available')
        
        # Build document text
        doc_text = f"Menu Item: {item['name']}\n"
        doc_text += f"Description: {description}\n"
        doc_text += f"Price: ${item['price']:.2f}\n"
        doc_text += f"Category: {item['category']}\n"
        
        # Add dietary info if available
        dietary = []
        if item.get('vegetarian'):
            dietary.append('Vegetarian')
        if item.get('vegan'):
            dietary.append('Vegan')
        if item.get('gluten_free'):
            dietary.append('Gluten-Free')
        doc_text += "Dietary Info: "
        doc_text += ', '.join(dietary) if dietary else 'None specified'
        
        documents.append(doc_text)
    
    # Add operational information
    documents.append("""
    Operating Hours:
    Monday - Friday: 7:00 AM to 8:00 PM
    Saturday - Sunday: 8:00 AM to 6:00 PM

    Location:
    123 Coffee Street, Downtown

    Contact:
    Phone: (555) 123-4567
    Email: info@neocafe.com
    """)
    
    documents.append("""
    How to Order:
    1. Browse the menu and select your items
    2. Add items to your cart
    3. Specify delivery location (table or address)
    4. Add any special instructions
    5. Confirm your order
    6. Track your order status in real-time

    Payment Methods:
    - Credit Card
    - Cash
    - Mobile Payment
    """)
    
    documents.append("""
    Returns Policy:
    If you're not satisfied with your order, please let our staff know within 15 minutes of receiving it.
    We'll be happy to remake your order or provide a refund.
    """)
    
    embeddings = OpenAIEmbeddings()
    try:
        vector_store = FAISS.from_texts(documents, embeddings)
        return vector_store
    except Exception as e:
        print(f"Error creating vector store: {e}")
        # Return a simple retriever that just returns the first few documents
        class SimpleRetriever:
            def similarity_search(self, query, k=5):
                class Document:
                    def __init__(self, content):
                        self.page_content = content
                return [Document(doc) for doc in documents[:k]]
            
            def as_retriever(self, **kwargs):
                return self
        
        return SimpleRetriever()

# ----- Order Management System -----

class OrderManager:
    @staticmethod
    def place_order(order_data):
        """
        Place an order with the Neo Cafe system with improved format handling.
        Args:
            order_data (dict or str): Order information in various formats.
        Returns:
            dict: Order details with ID.
        """
        try:
            # Step 1: Better input handling for various formats
            print(f"Original order data: {order_data}")
            
            if isinstance(order_data, str):
                try:
                    # Try to parse as JSON first
                    order_data = json.loads(order_data)
                    print(f"Parsed order data from JSON: {order_data}")
                except json.JSONDecodeError:
                    # If not valid JSON, try to parse as text
                    try:
                        order_data = parse_order_text(order_data)
                        print(f"Parsed order data from text: {order_data}")
                    except Exception as parse_err:
                        print(f"Error in text parsing: {parse_err}")
                        # Additional fallback - try to extract menu items directly
                        items = []
                        text_lower = order_data.lower()
                        
                        # Check for common menu items
                        for menu_item in menu_items:
                            item_name_lower = menu_item["name"].lower()
                            if item_name_lower in text_lower:
                                # Try to find quantity
                                quantity = 1
                                for i in range(1, 10):  # Look for numbers 1-9
                                    if f"{i} {item_name_lower}" in text_lower or f"{i}{item_name_lower}" in text_lower:
                                        quantity = i
                                        break
                                
                                items.append({
                                    "item_id": menu_item["id"],
                                    "quantity": quantity,
                                    "special_instructions": ""
                                })
                                print(f"Found item in text: {menu_item['name']}, quantity: {quantity}")
                        
                        if items:
                            order_data = {
                                "items": items,
                                "user_id": "guest",
                                "delivery_type": "table"
                            }
                        else:
                            raise ValueError("No menu items found in text and couldn't parse as JSON")
            
            # Step 2: Better validation and standardization
            if not isinstance(order_data, dict):
                raise ValueError(f"Invalid order data type: {type(order_data)}")
                
            # Generate order ID if not present
            if "id" not in order_data:
                order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
                order_data["id"] = order_id
            
            # Handle different item formats
            if "items" not in order_data:
                raise ValueError("Order must contain items")
            
            # Step 3: Convert items to standard format
            items = order_data["items"]
            standardized_items = []
            
            for item in items:
                if isinstance(item, dict):
                    # Handle different formats
                    if "item_id" in item:
                        # Already in correct format
                        standardized_item = item
                    elif "id" in item:
                        # Convert from {id: X} to {item_id: X}
                        standardized_item = {
                            "item_id": item["id"],
                            "quantity": item.get("quantity", 1),
                            "special_instructions": item.get("special_instructions", "")
                        }
                    elif "name" in item:
                        # Convert from {name: X} to {item_id: Y}
                        item_name = item["name"].lower()
                        found = False
                        for menu_item in menu_items:
                            if menu_item["name"].lower() == item_name:
                                found = True
                                standardized_item = {
                                    "item_id": menu_item["id"],
                                    "quantity": item.get("quantity", 1),
                                    "special_instructions": item.get("special_instructions", "")
                                }
                                break
                        if not found:
                            # Use fuzzy matching if exact match not found
                            best_match = None
                            best_score = 0
                            for menu_item in menu_items:
                                menu_name = menu_item["name"].lower()
                                # Simple matching score - can be improved
                                score = 0
                                for word in item_name.split():
                                    if word in menu_name:
                                        score += 1
                                if score > best_score:
                                    best_score = score
                                    best_match = menu_item
                            
                            if best_match and best_score > 0:
                                print(f"Using fuzzy match: '{item_name}' -> '{best_match['name']}'")
                                standardized_item = {
                                    "item_id": best_match["id"],
                                    "quantity": item.get("quantity", 1),
                                    "special_instructions": item.get("special_instructions", "")
                                }
                            else:
                                raise ValueError(f"Item not found on menu: {item_name}")
                    else:
                        raise ValueError(f"Invalid item format: {item}")
                elif isinstance(item, str):
                    # Handle string items like ["espresso", "croissant"]
                    item_name = item.lower()
                    found = False
                    for menu_item in menu_items:
                        if menu_item["name"].lower() == item_name:
                            found = True
                            standardized_item = {
                                "item_id": menu_item["id"],
                                "quantity": 1,
                                "special_instructions": ""
                            }
                            break
                    if not found:
                        # Try fuzzy matching
                        best_match = None
                        best_score = 0
                        for menu_item in menu_items:
                            menu_name = menu_item["name"].lower()
                            # Simple matching score
                            score = 0
                            for word in item_name.split():
                                if word in menu_name:
                                    score += 1
                            if score > best_score:
                                best_score = score
                                best_match = menu_item
                        
                        if best_match and best_score > 0:
                            print(f"Using fuzzy match: '{item_name}' -> '{best_match['name']}'")
                            standardized_item = {
                                "item_id": best_match["id"],
                                "quantity": 1,
                                "special_instructions": ""
                            }
                        else:
                            raise ValueError(f"Item not found on menu: {item}")
                else:
                    raise ValueError(f"Invalid item type: {type(item)}")
                    
                standardized_items.append(standardized_item)
            
            # Replace items with standardized format
            order_data["items"] = standardized_items
            
            print(f"Standardized order: {order_data}")
            
            # Step 4: Validate final order (with more lenient validation)
            valid_items = []
            for item in order_data["items"]:
                if any(menu_item["id"] == item["item_id"] for menu_item in menu_items):
                    valid_items.append(item)
                else:
                    print(f"Warning: Skipping invalid item ID: {item['item_id']}")
            
            if not valid_items:
                raise ValueError("No valid items found in order")
                
            order_data["items"] = valid_items

            # Step 5: Add context data with enhanced user handling
            context = cl.user_session.get("context", {})
            if "user_id" not in order_data:
                user_id = context.get("user_id")
                if user_id and user_id != "guest" and context.get("is_authenticated", False):
                    order_data["user_id"] = user_id
                    order_data["username"] = context.get("username", user_id)
                    print(f"Setting authenticated user_id from context: {user_id}")
                else:
                    order_data["user_id"] = "guest"
                    order_data["username"] = "guest"
                    print("Using guest user ID for unauthenticated order")
            
            # Make sure username field is also set for compatibility with Dash
            if "username" not in order_data and "user_id" in order_data:
                order_data["username"] = order_data["user_id"]
                print(f"Setting username to match user_id: {order_data['username']}")
            
            # Add timestamp
            order_data["timestamp"] = datetime.now().isoformat()
            
            # Add delivery information with better defaults
            if "delivery_location" not in order_data and "delivery_details" in order_data:
                order_data["delivery_location"] = order_data["delivery_details"]
            
            if "delivery_location" not in order_data:
                # Get from context if available
                if "delivery_location" in context:
                    order_data["delivery_location"] = context["delivery_location"]
                else:
                    order_data["delivery_location"] = "Table 1"  # Default
            
            # Step 6: Save to database (original functionality)
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('''INSERT INTO order_history 
                            (order_id, user_id, items, status, created_at)
                            VALUES (?, ?, ?, ?, ?)''',
                          (order_data["id"], 
                           order_data.get("user_id", "guest"), 
                           json.dumps(order_data["items"]), 
                           "received", 
                           datetime.now()))
                conn.commit()
                conn.close()
                print(f"Order saved to database: {order_data['id']}")
            except Exception as db_error:
                print(f"Database error: {db_error}")
            
            # Step 7: Notify dashboard (original functionality)
            success = False
            try:
                # First try Socket.IO if available
                try:
                    import socketio
                    sio = socketio.Client()
                    sio.connect(DASHBOARD_URL)
                    sio.emit('order_update', order_data)
                    sio.disconnect()
                    print("Order sent via Socket.IO")
                    success = True
                except Exception as e:
                    print(f"Error sending order via Socket.IO: {e}")
                
                # Then try REST API
                if not success:
                    try:
                        response = requests.post(
                            f"{DASHBOARD_URL}/api/place-order", 
                            json=order_data, 
                            timeout=5
                        )
                        print(f"Place order API response: {response.status_code}")
                        if response.status_code == 200:
                            success = True
                    except Exception as e:
                        print(f"Error calling place-order API: {e}")
                
                # Finally, use postMessage as last resort
                if not success:
                    try:
                        cl.send_to_parent({
                            "type": "order_update", 
                            "order": order_data
                        })
                        print("Order notification sent to parent via postMessage")
                        success = True
                    except Exception as e:
                        print(f"Error sending order via cl.send_to_parent: {e}")
                
            except Exception as e:
                print(f"Error in dashboard notification: {e}")
            
            # Always save to file as backup
            try:
                os.makedirs('order_data', exist_ok=True)
                with open(f"order_data/order_{order_data['id']}.json", 'w') as f:
                    json.dump(order_data, f)
                print(f"Order saved to file: order_{order_data['id']}.json")
            except Exception as e:
                print(f"Error saving order to file: {e}")
            
            # Store in session context
            context = cl.user_session.get("context", {})
            context["active_order"] = order_data
            context["delivery_location"] = order_data.get("delivery_location", "Table 1") 
            cl.user_session.set("context", context)
            print("Order saved to session context")
            
            return order_data if success else {"error": "Failed to notify dashboard about order", "order_data": order_data}
            
        except Exception as e:
            print(f"Unexpected error placing order: {e}")
            import traceback
            traceback.print_exc()
            raise


    @staticmethod
    def get_order_status(order_id):
        """
        Get status of an existing order.
        Args:
            order_id (str): Order ID to check.
        Returns:
            str: Order status information.
        """
        try:
            # Check for valid order ID format
            if not order_id or not isinstance(order_id, str):
                return "Invalid order ID format"
                
            # Clean up the order_id
            order_id = order_id.strip().upper()
            if not order_id.startswith("ORD-"):
                if order_id.isalnum():
                    order_id = f"ORD-{order_id}"
                    
            # Query database
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('''SELECT status, items, created_at FROM order_history
                         WHERE order_id = ?''', (order_id,))
            result = c.fetchone()
            conn.close()
            
            if not result:
                return f"No record found for order {order_id}"
                
            status, items_json, created_at = result
            items = json.loads(items_json)
            
            # Format a nice response
            response = f"Order {order_id} status: {status.upper()}\n"
            response += f"Placed: {created_at}\n"
            response += "Items:\n"
            
            for item in items:
                item_name = next((menu_item["name"] for menu_item in menu_items 
                                 if menu_item["id"] == item["item_id"]), f"Item #{item['item_id']}")
                response += f"- {item['quantity']}x {item_name}\n"
            
            return response
        except Exception as e:
            print(f"Error getting order status: {e}")
            return f"Error retrieving order status: {str(e)}"

    @staticmethod
    def update_order(order_id, updates):
        """
        Update an existing order.
        Args:
            order_id (str): Order ID to update.
            updates (dict): Update information.
        Returns:
            bool: Success status.
        """
        try:
            if isinstance(updates, str):
                try:
                    updates = json.loads(updates)
                except:
                    return {"error": "Invalid updates format"}
                    
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Verify order exists
            c.execute('SELECT items, status FROM order_history WHERE order_id = ?', 
                      (order_id,))
            result = c.fetchone()
            if not result:
                conn.close()
                return {"error": f"Order {order_id} not found"}
                
            items_json, current_status = result
            items = json.loads(items_json)
            
            # Update status if provided
            new_status = updates.get("status", current_status)
            
            # Update items if provided
            if "items" in updates:
                for update_item in updates["items"]:
                    item_id = update_item.get("item_id")
                    # Find matching item in order
                    for i, item in enumerate(items):
                        if item["item_id"] == item_id:
                            # Update quantity if specified
                            if "quantity" in update_item:
                                if update_item["quantity"] <= 0:
                                    # Remove item
                                    items.pop(i)
                                else:
                                    # Update quantity
                                    items[i]["quantity"] = update_item["quantity"]
                            # Update special instructions if specified
                            if "special_instructions" in update_item:
                                items[i]["special_instructions"] = update_item["special_instructions"]
                            break
                    else:
                        # Item not found, add if quantity > 0
                        if update_item.get("quantity", 0) > 0:
                            items.append(update_item)
            
            # Save updates
            c.execute('''UPDATE order_history 
                         SET items = ?, status = ? 
                         WHERE order_id = ?''',
                      (json.dumps(items), new_status, order_id))
            conn.commit()
            conn.close()
            
            # Notify dashboard
            try:
                cl.send_to_parent({
                    "type": "order_update",
                    "order": {
                        "id": order_id,
                        "status": new_status,
                        "items": items
                    }
                })
            except Exception as e:
                print(f"Error sending update via cl.send_to_parent: {e}")
                
            try:
                response = requests.put(
                    f"{DASHBOARD_URL}/api/orders/{order_id}",
                    json={"status": new_status, "items": items},
                    timeout=5
                )
                print(f"Update order API response: {response.status_code}")
            except Exception as e:
                print(f"Error calling update-order API: {e}")
                
            return {"success": True, "message": f"Order {order_id} updated successfully"}
        except Exception as e:
            print(f"Error updating order: {e}")
            return {"error": str(e)}

# ----- API Integration Tools -----

def navigate_to_page(destination):
    """
    Send navigation request to the Dash app.
    Args:
        destination (str): Navigation destination.
    Returns:
        str: Response message.
    """
    try:
        if not destination:
            return "Please specify a destination page"
            
        valid_destinations = ["menu", "orders", "delivery", "profile", "dashboard", "home"]
        destination = destination.lower().strip()
        
        if destination not in valid_destinations:
            return f"Invalid destination. Valid options are: {', '.join(valid_destinations)}"
            
        print(f"Attempting to navigate to: {destination}")
        
        # Method 1: Send to parent window
        try:
            cl.send_to_parent({
                "type": "navigation",
                "destination": destination
            })
        except Exception as e:
            print(f"Error sending navigation via cl.send_to_parent: {e}")
            
        # Method 2: Call API endpoint
        try:
            response = requests.post(
                f"{DASHBOARD_URL}/api/navigate", 
                json={"destination": destination}, 
                timeout=3
            )
            print(f"Navigation API response: {response.status_code}")
        except Exception as e:
            print(f"Error calling navigation API: {e}")
            
        return f"Navigating to {destination} page..."
    except Exception as e:
        print(f"Navigate error: {e}")
        return f"Failed to navigate: {str(e)}"
    
def list_menu_items(query:str = "") -> str:
    """List all available menu items for debugging."""
    if not menu_items:
        return "No menu items loaded."
    
    result = "Available menu items:\n"
    for item in menu_items:
        result += f"ID: {item['id']} - {item['name']} (${item['price']:.2f})\n"
    return result

def search_menu(query):
    """
    Search menu items based on query with improved matching.
    Args:
        query (str): Search query.
    Returns:
        str: Search results.
    """
    try:
        if not query or not isinstance(query, str):
            return "Please provide a search term"
            
        print(f"Searching menu for: '{query}'")
        print(f"Available menu items: {[item['name'] for item in menu_items]}")
        
        # If menu is empty, return a helpful message
        if not menu_items:
            return "Our menu is currently being updated. Please check back soon."
            
        query_lower = query.lower().strip()
        query_terms = []
        
        # Handle multiple search terms separated by commas
        if ',' in query_lower:
            query_terms = [term.strip() for term in query_lower.split(',')]
        else:
            # Handle space-separated terms, but intelligently
            # For example "gluten free" should be one term, not two
            common_phrases = ["gluten free", "dairy free", "sugar free", 
                             "almond milk", "soy milk", "oat milk",
                             "avocado toast", "ice coffee", "iced coffee"]
            
            # Check if any common phrases are in the query
            remaining_query = query_lower
            for phrase in common_phrases:
                if phrase in remaining_query:
                    query_terms.append(phrase)
                    remaining_query = remaining_query.replace(phrase, "")
            
            # Add remaining individual words
            remaining_terms = [term.strip() for term in remaining_query.split() if term.strip()]
            query_terms.extend(remaining_terms)
        
        print(f"Parsed search terms: {query_terms}")
        
        # Search for matching items
        matching_items = []
        match_reasons = {}  # Store why each item matched
        
        # First pass: Look for exact matches in name, description, category
        for item in menu_items:
            item_name = item["name"].lower()
            item_desc = item.get("description", "").lower()
            item_category = item["category"].lower()
            
            # Check each query term separately
            for term in query_terms:
                if term in item_name:
                    if item not in matching_items:
                        matching_items.append(item)
                        match_reasons[item["id"]] = f"Name contains '{term}'"
                        print(f"Name match: {item['name']} matched '{term}'")
                elif term in item_desc:
                    if item not in matching_items:
                        matching_items.append(item)
                        match_reasons[item["id"]] = f"Description mentions '{term}'"
                        print(f"Description match: {item['name']} matched '{term}'")
                elif term in item_category:
                    if item not in matching_items:
                        matching_items.append(item)
                        match_reasons[item["id"]] = f"Category matches '{term}'"
                        print(f"Category match: {item['name']} matched '{term}'")
                        
        # Second pass: Look for dietary matches
        for term in query_terms:
            if any(word in term for word in ["vegetarian", "vegetable", "veggie"]):
                vegetarian_items = [item for item in menu_items if item.get("vegetarian")]
                for item in vegetarian_items:
                    if item not in matching_items:
                        matching_items.append(item)
                        match_reasons[item["id"]] = "Vegetarian option"
                        print(f"Dietary match: {item['name']} is vegetarian")
                        
            if any(word in term for word in ["vegan", "plant", "dairy-free"]):
                vegan_items = [item for item in menu_items if item.get("vegan")]
                for item in vegan_items:
                    if item not in matching_items:
                        matching_items.append(item)
                        match_reasons[item["id"]] = "Vegan option"
                        print(f"Dietary match: {item['name']} is vegan")
                        
            if any(word in term for word in ["gluten", "gluten-free", "gluten free", "gf"]):
                gf_items = [item for item in menu_items if item.get("gluten_free")]
                for item in gf_items:
                    if item not in matching_items:
                        matching_items.append(item)
                        match_reasons[item["id"]] = "Gluten-free option"
                        print(f"Dietary match: {item['name']} is gluten-free")
                        
            # Check for category matches
            if any(term == cat for cat in ["coffee", "drink", "drinks", "beverage", "beverages"]):
                coffee_items = [item for item in menu_items if item["category"].lower() == "coffee"]
                for item in coffee_items:
                    if item not in matching_items:
                        matching_items.append(item)
                        match_reasons[item["id"]] = "Coffee beverage"
                        
            if any(term == cat for cat in ["food", "eat", "meal", "snack"]):
                food_items = [item for item in menu_items if item["category"].lower() in ["food", "pastries"]]
                for item in food_items:
                    if item not in matching_items:
                        matching_items.append(item)
                        match_reasons[item["id"]] = "Food item"
                        
            if any(term == cat for cat in ["pastry", "pastries", "bakery", "baked"]):
                pastry_items = [item for item in menu_items if item["category"].lower() == "pastries"]
                for item in pastry_items:
                    if item not in matching_items:
                        matching_items.append(item)
                        match_reasons[item["id"]] = "Pastry item"
        
        # Third pass: Look for fuzzy matches if we didn't find anything yet
        if not matching_items:
            print("No exact matches, trying fuzzy matching")
            for item in menu_items:
                item_name = item["name"].lower()
                item_parts = item_name.split()
                
                for term in query_terms:
                    # Check if term is similar to any part of the item name
                    term_parts = term.split()
                    for term_part in term_parts:
                        if len(term_part) <= 3:  # Skip short words like "the", "and"
                            continue
                            
                        for item_part in item_parts:
                            # Simple fuzzy match - if term part is contained in item part
                            if len(term_part) > 3 and term_part in item_part:
                                if item not in matching_items:
                                    matching_items.append(item)
                                    match_reasons[item["id"]] = f"Similar to '{term}'"
                                    print(f"Fuzzy match: {item['name']} similar to '{term}'")
                                    break
        
        # If still no matches but the query contains legitimate words, suggest popular items
        if not matching_items and any(len(term) > 3 for term in query_terms):
            popular_items = [item for item in menu_items if item.get("popular")]
            
            # If we have popular items, suggest them instead
            if popular_items:
                results = "We didn't find an exact match for your search. Here are some of our popular items:\n\n"
                for item in popular_items[:5]:  # Show up to 5 popular items
                    results += f"• **{item['name']}** - ${item['price']:.2f}\n"
                    if "description" in item:
                        results += f"  {item['description']}\n"
                    results += "\n"
                return results
        
        # If STILL no matches or query too vague, show menu categories
        if not matching_items:
            categories = set(item["category"] for item in menu_items)
            results = "I couldn't find specific items matching your query. Here are our menu categories:\n\n"
            for category in categories:
                results += f"• **{category.title()}**\n"
            results += "\nYou can search for items in a specific category or ask to see all items."
            return results
            
        # Format results
        if not matching_items:
            print("No matches found after all attempts.")
            return "No menu items found matching your query."
            
        results = f"Found {len(matching_items)} menu items matching your query:\n\n"
        
        for item in matching_items:
            results += f"• **{item['name']}** (ID: {item['id']}) - ${item['price']:.2f}\n"
            
            # Add match reason if available
            if item["id"] in match_reasons:
                results += f"  *{match_reasons[item['id']]}*\n"
                
            if "description" in item and item["description"]:
                results += f"  {item['description']}\n"
            
            # Add dietary info
            dietary = []
            if item.get("vegetarian"):
                dietary.append("Vegetarian")
            if item.get("vegan"):
                dietary.append("Vegan")
            if item.get("gluten_free"):
                dietary.append("Gluten-Free")
            if dietary:
                results += f"  *{', '.join(dietary)}*\n"
            results += "\n"
            
        return results
    except Exception as e:
        print(f"Search error: {e}")
        traceback.print_exc()
        return f"Error searching menu: {str(e)}"


def get_store_hours():
    """Get store hours information."""
    return """
**Neo Cafe Hours:**

Monday - Friday: 7:00 AM to 8:00 PM
Saturday - Sunday: 8:00 AM to 6:00 PM

Location: 123 Coffee Street, Downtown
Phone: (555) 123-4567
Email: info@neocafe.com
"""

def parse_order_text(text):
    """
    Parse natural language order text into structured order data with improved matching.
    Args:
        text (str): Natural language order description.
    Returns:
        dict: Structured order data.
    """
    try:
        context = cl.user_session.get("context", {})
        order_items = []
        special_instructions_global = ""
        
        # Extract items and quantities
        text_lower = text.lower()
        print(f"Parsing order text: {text_lower}")
        
        # Extract global special instructions
        if "with " in text_lower and " and " in text_lower.split("with ")[1]:
            parts = text_lower.split("with ")
            special_parts = parts[1].split(" and ")
            if len(special_parts) > 1:
                special_instructions_global = f"With {parts[1]}"
        
        # Process each menu item
        for item in menu_items:
            item_name_lower = item["name"].lower()
            
            # Try different ways the item might appear in text
            variations = [
                item_name_lower,
                item_name_lower.replace(" ", ""),  # No spaces
                item_name_lower.replace("-", ""),  # No hyphens
                item_name_lower.replace(" ", "-"),  # Spaces as hyphens
                # Add common spelling variations if needed
            ]
            
            found = False
            for variation in variations:
                if variation in text_lower:
                    found = True
                    break
                    
            if found:
                # Try to find quantity before item name
                quantity = 1
                # Look for numeric quantities
                item_index = text_lower.find(item_name_lower)
                before_item = text_lower[:item_index].strip()
                words_before = before_item.split()
                
                if words_before and words_before[-1].isdigit():
                    quantity = int(words_before[-1])
                else:
                    # Look for written numbers
                    number_words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, 
                                    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
                    for word, value in number_words.items():
                        if f"{word} {item_name_lower}" in text_lower:
                            quantity = value
                            break
                
                # Special instruction handling for this specific item
                special_instructions = ""
                item_pos = text_lower.find(item_name_lower)
                if item_pos >= 0:
                    after_item = text_lower[item_pos + len(item_name_lower):]
                    if "with " in after_item:
                        with_part = after_item.split("with ")[1].split(".")[0].split(",")[0]
                        if len(with_part) < 100:  # Reasonable length check
                            special_instructions = f"With {with_part}"
                
                order_items.append({
                    "item_id": item["id"],
                    "quantity": quantity,
                    "special_instructions": special_instructions
                })
                print(f"Found item: {item['name']}, quantity: {quantity}")
        
        if not order_items:
            # Try fuzzy matching for items
            words = text_lower.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    best_match = None
                    best_score = 0
                    
                    for menu_item in menu_items:
                        menu_name = menu_item["name"].lower()
                        
                        # Simple fuzzy matching
                        if word in menu_name or any(word in part for part in menu_name.split()):
                            score = len(word) / len(menu_name)  # Longer matches = better
                            if score > best_score:
                                best_score = score
                                best_match = menu_item
                    
                    if best_match and best_score > 0.3:  # Threshold for match quality
                        print(f"Fuzzy match: '{word}' -> '{best_match['name']}'")
                        order_items.append({
                            "item_id": best_match["id"],
                            "quantity": 1,
                            "special_instructions": ""
                        })
        
        if not order_items:
            raise ValueError("No menu items found in order text")
            
        # Determine delivery type
        delivery_type = "table"
        if "delivery" in text_lower:
            delivery_type = "delivery"
            
        # Extract delivery details
        delivery_details = ""
        if "to table" in text_lower:
            table_index = text_lower.find("to table")
            if table_index != -1:
                after_table = text_lower[table_index+8:].strip()
                table_parts = after_table.split()
                if table_parts and table_parts[0].isdigit():
                    delivery_details = f"Table {table_parts[0]}"
                elif len(table_parts) > 0:
                    delivery_details = f"Table area: {' '.join(table_parts[:3])}"
        
        # Build the order structure
        return {
            "user_id": context.get("user_id", "guest"),
            "items": order_items,
            "delivery_type": delivery_type,
            "delivery_details": delivery_details,
            "special_instructions": special_instructions_global
        }
    except Exception as e:
        print(f"Parse order error details: {e}")
        raise ValueError(f"Could not parse order text: {str(e)}")

def query_knowledge_base(query):
    """
    Query the vector store for relevant information.
    Args:
        query (str): Query string.
    Returns:
        str: Knowledge base response.
    """
    try:
        vector_store = cl.user_session.get("vector_store")
        if not vector_store:
            return "Knowledge base not initialized. Please try again later."
            
        docs = vector_store.similarity_search(query, k=3)
        if not docs:
            return "I couldn't find information about that in our knowledge base."
            
        results = "Here's what I found:\n\n"
        for doc in docs:
            results += f"{doc.page_content}\n\n"
            
        return results
    except Exception as e:
        print(f"Knowledge base error: {e}")
        return "Sorry, I encountered an error when searching our information database."

# ----- Authentication and User Management -----

def verify_auth_token(token):
    """
    Verify authentication token with enhanced debugging
    Args:
        token (str): Authentication token
    Returns:
        tuple: (user_id, is_authenticated, user_data)
    """
    if not token:
        logger.debug("No authentication token provided")
        return "guest", False, {}
        
    logger.debug(f"Verifying auth token: {token[:20]}...")
    
    try:
        # First try to decode if it's base64 encoded JSON
        import base64
        import json
        
        try:
            # Try to decode base64 token - handle potential padding issues
            token_bytes = token.encode('utf-8')
            # Add padding if needed
            missing_padding = len(token_bytes) % 4
            if missing_padding:
                token_bytes += b'=' * (4 - missing_padding)
                
            decoded_bytes = base64.b64decode(token_bytes)
            user_data = json.loads(decoded_bytes)
            
            if isinstance(user_data, dict) and 'username' in user_data:
                logger.debug(f"Successfully decoded auth token for user: {user_data['username']}")
                # Also pass the full name if available
                if 'first_name' in user_data or 'last_name' in user_data:
                    full_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
                    if full_name:
                        user_data['full_name'] = full_name
                return user_data['username'], True, user_data
        except Exception as decode_err:
            logger.debug(f"Not a base64 token: {str(decode_err)}")
            
        # If not base64, check if it's a simple token format
        if '-' in token:
            parts = token.split('-')
            username = parts[0]
            
            if username and username != "guest":
                logger.debug(f"Using simple token format for user: {username}")
                return username, True, {"username": username}
                
        # Last resort: Try API verification
        try:
            response = requests.get(
                f"{DASHBOARD_URL}/api/verify-token",
                headers={"Authorization": f"Bearer {token}"},
                timeout=3
            )
            if response.ok:
                data = response.json()
                logger.debug(f"API verified user: {data.get('user_id', 'unknown')}")
                return data.get("user_id", "guest"), True, data
        except Exception as api_err:
            logger.debug(f"API verification failed: {str(api_err)}")
    
    except Exception as e:
        logger.error(f"Auth token verification error: {str(e)}")
        
    logger.debug("Auth verification failed, defaulting to guest")
    return "guest", False, {}

def load_conversation_history(session_id):
    """
    Load previous conversation from database.
    Args:
        session_id (str): Session identifier.
    Returns:
        list: List of message dictionaries.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT content, is_user, timestamp FROM messages
                     WHERE session_id = ?
                     ORDER BY timestamp ASC''', (session_id,))
        results = c.fetchall()
        conn.close()
        
        return [{
            "content": row[0],
            "is_user": bool(row[1]),
            "timestamp": row[2]
        } for row in results]
    except Exception as e:
        print(f"Error loading conversation history: {e}")
        return []

def save_conversation_message(session_id, content, is_user=False):
    """
    Save a conversation message to the database.
    Args:
        session_id (str): Session identifier.
        content (str): Message content.
        is_user (bool): Whether the message is from the user.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO messages
                     (session_id, content, is_user, timestamp)
                     VALUES (?, ?, ?, ?)''',
                  (session_id, content, is_user, datetime.now()))
        
        # Update session last active timestamp
        c.execute('''UPDATE conversations
                     SET last_active = ?
                     WHERE session_id = ?''',
                  (datetime.now(), session_id))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving conversation message: {e}")

# ----- LangChain Agent Setup -----

def initialize_agent_safely(context):
    """
    Initialize the LangChain agent with better error handling
    
    Args:
        context (dict): The user session context
        
    Returns:
        object or None: The initialized agent or None if initialization failed
    """
    try:
        logger.debug("Starting agent initialization")
        
        # Create knowledge base
        vector_store = create_knowledge_base()
        cl.user_session.set("vector_store", vector_store)
        logger.debug("Knowledge base created successfully")
        
        # Initialize memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Load conversation history if available
        if "session_id" in context:
            history = load_conversation_history(context["session_id"])
            for msg in history:
                if msg["is_user"]:
                    memory.chat_memory.add_user_message(msg["content"])
                else:
                    memory.chat_memory.add_ai_message(msg["content"])
            logger.debug(f"Loaded {len(history)} messages from history")
        
        # Define tools
        tools = [
            Tool(
                name="NavigateTool",
                func=navigate_to_page,
                description="Navigate to a page in the Neo Cafe app. Valid destinations are: menu, orders, delivery, profile, dashboard"
            ),
            Tool(
                name="SearchMenuTool",
                func=search_menu,
                description="Search the menu for specific items, categories, or dietary restrictions"
            ),
            Tool(
                name="PlaceOrderTool",
                func=OrderManager.place_order,
                description="Place an order with Neo Cafe. Expects either a JSON string or natural language order description"
            ),
            Tool(
                name="GetOrderStatusTool",
                func=OrderManager.get_order_status,
                description="Check the status of an order by order ID"
            ),
            Tool(
                name="StoreHoursTool",
                func=get_store_hours,
                description="Get information about Neo Cafe's operating hours and location"
            ),
            Tool(
                name="KnowledgeBaseTool",
                func=query_knowledge_base,
                description="Search Neo Cafe's knowledge base for general information"
            )
        ]
        logger.debug(f"Created {len(tools)} tools for the agent")
        
        # Create personalized system message
        is_auth = context.get("is_authenticated", False)
        username = context.get("username", "guest")
        current_page = context.get("current_page", "home")
        floating = context.get("is_floating", False)
        has_active_order = "active_order" in context
        
        # System message with enhanced personalization
        system_message = f"""You are BaristaBot, the friendly AI assistant for Neo Cafe. 
Your goal is to help customers with orders, menu information, and general inquiries.

CURRENT CONTEXT:
- User: {username if is_auth else "Guest"} {f"({context.get('email', '')})" if context.get('email') else ""}
- Authentication Status: {"Authenticated" if is_auth else "Guest"}
- Current Page: {current_page}
- Interface: {"Floating Chat" if floating else "Full Chat"}
- Active Order: {"Yes - " + context.get('active_order', {}).get('id', 'Unknown') if has_active_order else "No"}

IMPORTANT GUIDELINES:
1. Be helpful, friendly, and concise
2. Use appropriate tools for accurate information
3. For menu inquiries, use SearchMenuTool
4. For placing orders, use PlaceOrderTool
5. For checking order status, use GetOrderStatusTool
6. For navigation, use NavigateTool
7. Always address the user by name ({username}) if they are authenticated
8. Remember their preferences and past orders when making recommendations
9. If they have an active order, offer to check its status

If in floating chat mode, keep responses brief and focused."""
        
        # Initialize LLM with error handling
        try:
            llm = ChatOpenAI(temperature=0.7, model="gpt-4o")
            logger.debug("LLM initialized successfully")
        except Exception as llm_err:
            logger.error(f"Error initializing LLM: {llm_err}")
            # Fallback to older model or simpler configuration
            try:
                llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
                logger.debug("Fallback LLM initialized")
            except Exception as fallback_err:
                logger.error(f"Fallback LLM also failed: {fallback_err}")
                return None
        
        # Try to initialize agent
        try:
            agent = initialize_agent(
                tools,
                llm,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=True,
                memory=memory,
                handle_parsing_errors=True,
                agent_kwargs={
                    'prefix': system_message,
                    'system_message': SystemMessage(content=system_message)
                }
            )
            logger.debug("Agent initialized successfully")
            return agent
        except Exception as agent_err:
            logger.error(f"Error initializing agent: {agent_err}")
            return None
            
    except Exception as e:
        logger.error(f"Unexpected error in agent initialization: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# Update the setup_langchain_agent function in chainlit_app/app.py

def setup_langchain_agent(context):
    """
    Set up LangChain agent with tools for interacting with Neo Cafe.
    Args:
        context (dict): Session context.
    Returns:
        object: Initialized LangChain agent.
    """
    try:
        # Create knowledge base
        vector_store = create_knowledge_base()
        cl.user_session.set("vector_store", vector_store)
        
        # Initialize memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Load conversation history if available
        if "session_id" in context:
            history = load_conversation_history(context["session_id"])
            for msg in history:
                if msg["is_user"]:
                    memory.chat_memory.add_user_message(msg["content"])
                else:
                    memory.chat_memory.add_ai_message(msg["content"])
        
        # Define tools
        tools = [
            Tool(
                name="NavigateTool",
                func=navigate_to_page,
                description="Navigate to a page in the Neo Cafe app. Valid destinations are: menu, orders, delivery, profile, dashboard"
            ),
            Tool(
                name="ListMenuTool",
                func=lambda _: list_menu_items(),
                description="List all available menu items"
            ),
            Tool(
                name="SearchMenuTool",
                func=search_menu,
                description="Search the menu for specific items, categories, or dietary restrictions"
            ),
            Tool(
                name="PlaceOrderTool",
                func=OrderManager.place_order,
                description="Place an order with Neo Cafe. Expects either a JSON string or natural language order description"
            ),
            Tool(
                name="GetOrderStatusTool",
                func=OrderManager.get_order_status,
                description="Check the status of an order by order ID"
            ),
            Tool(
                name="UpdateOrderTool",
                func=lambda x: OrderManager.update_order(*json.loads(x)),
                description="Update an existing order. Format: JSON string with order_id and updates object"
            ),
            Tool(
                name="StoreHoursTool",
                func=get_store_hours,
                description="Get information about Neo Cafe's operating hours and location"
            ),
            Tool(
                name="KnowledgeBaseTool",
                func=query_knowledge_base,
                description="Search Neo Cafe's knowledge base for general information"
            )
        ]
        
        # Create personalized system message
        is_auth = context.get("is_authenticated", False)
        username = context.get("username", "guest")
        current_page = context.get("current_page", "home")
        floating = context.get("is_floating", False)
        has_active_order = "active_order" in context
        
        # System message with enhanced personalization
        system_message = f"""You are BaristaBot, the friendly AI assistant for Neo Cafe. 
Your goal is to help customers with orders, menu information, and general inquiries.

CURRENT CONTEXT:
- User: {username if is_auth else "Guest"} {f"({context.get('email', '')})" if context.get('email') else ""}
- Authentication Status: {"Authenticated" if is_auth else "Guest"}
- Current Page: {current_page}
- Interface: {"Floating Chat" if floating else "Full Chat"}
- Active Order: {"Yes - " + context.get('active_order', {}).get('id', 'Unknown') if has_active_order else "No"}

IMPORTANT GUIDELINES:
1. Be helpful, friendly, and concise
2. Use appropriate tools for accurate information
3. For menu inquiries, use SearchMenuTool
4. For placing orders, use PlaceOrderTool
5. For checking order status, use GetOrderStatusTool
6. For navigation, use NavigateTool
7. Always address the user by name ({username}) if they are authenticated
8. Remember their preferences and past orders when making recommendations
9. If they have an active order, offer to check its status

If in floating chat mode, keep responses brief and focused."""
        
        # Define custom prefix using system_message
        custom_prefix = system_message
        
        # Initialize LLM
        llm = ChatOpenAI(temperature=0.7, model="gpt-4o")
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            ai_prefix="BaristaBot"
        )
        
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=memory,
            handle_parsing_errors=True,
            agent_kwargs={
                'prefix': custom_prefix,
                'system_message': SystemMessage(content=system_message)
            }
        )
        return agent
    except Exception as e:
        print(f"Error setting up agent: {e}")
        raise

# Add this new function to generate personalized welcome messages
def get_personalized_welcome(context):
    """Generate a personalized welcome message based on user context"""
    # Base greeting with personalization if authenticated
    if context['is_authenticated']:
        greeting = f"Welcome back, {context.get('username', 'valued customer')}! "
    else:
        greeting = "Welcome to Neo Cafe! "
    
    # Page-specific additions
    current_page = context.get('current_page', 'home')
    
    page_messages = {
        'menu': "I can help you browse our menu or suggest items based on your preferences.",
        'order': "Ready to place an order? Just tell me what you'd like!",
        'status': "Looking to check on an order? I can help with that!",
        'dashboard': "Here to help with your Neo Cafe experience!",
        'profile': "Need help with your account or previous orders?"
    }
    
    page_specific = page_messages.get(current_page, "How can I assist you today?")
    
    # Order-specific content if available
    order_content = ""
    if 'active_order' in context:
        order_id = context['active_order'].get('id', 'Unknown')
        order_content = f"\n\nI see you have an active order (#{order_id}). Would you like to check its status?"
    
    return greeting + page_specific + order_content

# ----- Chainlit Handlers -----@cl.on_chat_start
async def start():
    """Initialize chat session with detailed logging"""
    # Get URL query parameters safely - with better error handling
    try:
        url_query = ""
        # First try the new way (safer)
        if hasattr(cl.context, 'request') and hasattr(cl.context.request, 'query_string'):
            url_query = cl.context.request.query_string.decode('utf-8')
            logger.debug(f"URL query from request: {url_query}")
        # Fallback to session dict (may cause the error)
        elif hasattr(cl.context, 'session') and isinstance(cl.context.session, dict):
            url_query = cl.context.session.get('url_query', '')
            logger.debug(f"URL query from session dict: {url_query}")
        # Final fallback in case session is an object with get method
        elif hasattr(cl.context, 'session') and hasattr(cl.context.session, 'get'):
            try:
                # Try with one argument to avoid signature mismatch
                url_query = cl.context.session.get('url_query')
                logger.debug(f"URL query from session object (1 arg): {url_query}")
            except TypeError:
                logger.debug("Session.get() caused TypeError, trying alternate access")
                if hasattr(cl.context.session, '__dict__'):
                    url_query = cl.context.session.__dict__.get('url_query', '')
                    logger.debug(f"URL query from session.__dict__: {url_query}")
        logger.debug(f"Final URL query: {url_query}")

        query_dict = {}
        if url_query:
            query_dict = urllib.parse.parse_qs(url_query)
        logger.debug(f"Parsed query dict: {query_dict}")
    except Exception as e:
        logger.error(f"Error parsing URL query: {e}")
        query_dict = {}

    # Add a fallback for detecting login status via cookies
    is_fallback_auth = False
    try:
        if hasattr(cl.context, 'request') and hasattr(cl.context.request, 'cookies'):
            cookies = cl.context.request.cookies
            logger.debug(f"Found cookies: {list(cookies.keys())}")
            auth_cookie_names = ['session', 'auth', 'token', 'user', 'sid']
            for name in auth_cookie_names:
                if any(name in cookie_name.lower() for cookie_name in cookies):
                    is_fallback_auth = True
                    logger.debug(f"Found potential auth cookie: {name}")
    except Exception as e:
        logger.error(f"Error checking cookies: {e}")

    # Authentication context with enhanced logging and fallbacks
    auth_token = query_dict.get('token', [None])[0]
    logger.debug(f"Raw auth token: {auth_token[:20] if auth_token else 'None'}")

    # Get direct user param
    direct_user = query_dict.get('user', [None])[0]
    logger.debug(f"Direct user param: {direct_user}")

    # Immediately check and inject URL parameters as an emergency fix
    # This is a bit of a hack but will ensure parameters are captured on startup
    if 'token' in query_dict or 'user' in query_dict:
        # Force immediate authentication update
        logger.debug("Direct URL parameters found, injecting authentication immediately")
        
        # Extract parameters
        auth_token = query_dict.get('token', [None])[0]
        username = query_dict.get('user', [None])[0]
        
        # Process username directly if available (highest priority)
        if username:
            logger.debug(f"Setting authenticated username from URL: {username}")
            user_id = username
            is_authenticated = True
            user_data = {"username": username}
            
            # Try to decode token if available
            if auth_token:
                try:
                    temp_id, temp_auth, temp_data = verify_auth_token(auth_token)
                    if temp_auth and isinstance(temp_data, dict):
                        # Use additional fields from token while keeping username
                        user_data.update({k: v for k, v in temp_data.items() 
                                         if k != 'username'})
                        logger.debug(f"Added token data to user: {user_data}")
                except Exception as e:
                    logger.error(f"Error decoding direct token: {e}")

    # Extract username from referer header if present
    parent_username = None
    try:
        if hasattr(cl.context, 'request') and hasattr(cl.context.request, 'headers'):
            referer = cl.context.request.headers.get('referer', '')
            if 'user=' in referer:
                parent_username = referer.split('user=')[1].split('&')[0]
                logger.debug(f"Found username in referer: {parent_username}")
    except Exception as e:
        logger.error(f"Error extracting username from referer: {e}")

    # Prepare verification
    username_candidates = [direct_user, parent_username]
    username_candidates = [u for u in username_candidates if u]

    user_id, is_authenticated, user_data = "guest", False, {}
    # Verify token if present
    if auth_token:
        try:
            user_id, is_authenticated, user_data = verify_auth_token(auth_token)
        except Exception as e:
            logger.error(f"Error verifying auth token: {e}")
    # Fallback to username or cookie-based auth
    if not is_authenticated and username_candidates:
        user_id = username_candidates[0]
        is_authenticated = True
        user_data = {"username": user_id}
        logger.debug(f"Using direct username as fallback: {user_id}")
    elif not is_authenticated and is_fallback_auth:
        user_id = "authenticated_user"
        is_authenticated = True
        user_data = {"username": "Valued Customer"}
        logger.debug("Using cookie-based auth fallback")

    logger.debug(f"Authentication result: user_id={user_id}, authenticated={is_authenticated}")
    logger.debug(f"User data: {user_data}")

    # Build enhanced context
    context = {
        "current_page": query_dict.get('tab', ['home'])[0],
        "user_id": user_id,
        "username": user_data.get('username', user_id),
        "email": user_data.get('email', ''),
        "first_name": user_data.get('first_name', ''),
        "last_name": user_data.get('last_name', ''),
        "full_name": user_data.get('full_name', ''),
        "is_authenticated": is_authenticated,
        "session_id": query_dict.get('session_id', [str(uuid.uuid4())])[0],
        "is_floating": query_dict.get('floating', ['false'])[0].lower() == 'true'
    }
    # Check for active order
    order_id = query_dict.get('order_id', [None])[0]
    if order_id:
        context["active_order"] = {"id": order_id}

    # Handle authentication from URL parameters
    auth_token = query_dict.get('token', [None])[0]
    direct_user = query_dict.get('user', [None])[0]
    
    logger.debug(f"Auth token from URL: {auth_token[:20] if auth_token else 'None'}")
    logger.debug(f"User from URL: {direct_user}")
    
    # Process token if present
    if auth_token and direct_user:
        try:
            import base64
            import json
            
            # Try to decode the token
            try:
                # Add padding if needed
                missing_padding = len(auth_token) % 4
                if missing_padding:
                    auth_token += '=' * (4 - missing_padding)
                    
                decoded_bytes = base64.b64decode(auth_token)
                user_data = json.loads(decoded_bytes)
                
                if isinstance(user_data, dict) and user_data.get('username') == direct_user:
                    # Update authentication in context
                    context.update({
                        "user_id": direct_user,
                        "username": direct_user,
                        "email": user_data.get("email", ""),
                        "first_name": user_data.get("first_name", ""),
                        "last_name": user_data.get("last_name", ""),
                        "is_authenticated": True
                    })
                    
                    # Add full name if available
                    first_name = user_data.get("first_name", "")
                    last_name = user_data.get("last_name", "")
                    if first_name or last_name:
                        full_name = f"{first_name} {last_name}".strip()
                        context["full_name"] = full_name
                    
                    logger.debug(f"Updated context from URL token: {context}")
                    
                    # Send auth status back to parent window
                    try:
                        cl.send_to_parent({
                            "type": "auth_status",
                            "status": "authenticated",
                            "user": direct_user
                        })
                    except:
                        logger.debug("Could not send auth status to parent")
            except Exception as decode_err:
                logger.error(f"Error decoding token from URL: {decode_err}")
        except Exception as e:
            logger.error(f"Error processing auth from URL: {e}")

    # Save to session
    cl.user_session.set("context", context)
    logger.debug(f"Saved context to session: {context}")

    # Set up the agent
    try:
        agent = initialize_agent_safely(context)
        if agent:
            cl.user_session.set("agent", agent)
            logger.debug("Agent setup complete")
        else:
            logger.warning("Agent initialization failed, using fallback responses")
        # agent = setup_langchain_agent(context)
        # cl.user_session.set("agent", agent)
        # logger.debug("Agent setup complete")
    except Exception as e:
        logger.error(f"Error setting up agent: {e}")

    # Send personalized welcome
    try:
        welcome_msg = ""
        if is_authenticated and context.get('full_name'):
            welcome_msg = f"Welcome back, {context['full_name']}! How can I assist you today?"
        elif is_authenticated:
            welcome_msg = f"Welcome back, {context['username']}! How can I assist you today?"
        else:
            welcome_msg = "Welcome to Neo Cafe! How can I help you today?"
        if order_id:
            welcome_msg += f"\n\nI see you have an active order (#{order_id}). Would you like to check its status?"
        logger.debug(f"Sending welcome message: {welcome_msg}")
        await cl.Message(content=welcome_msg).send()
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")
        await cl.Message(content="Welcome to Neo Cafe! How can I help you today?").send()


@cl.on_window_message
async def handle_window_message(message):
    """
    Handle messages from the parent window (Dash app).
    Args:
        message: Message content (string or dict).
    """
    print(f"Received window message: {message}")
    actual_message = None
    message_id = f"window_{time.time()}"
    
    if isinstance(message, dict):
        if 'message' in message:
            actual_message = message['message']
            if 'id' in message:
                message_id = f"window_{message['id']}"
        elif 'kind' in message and message.get('kind') == 'user_message':
            if 'data' in message and 'content' in message['data']:
                actual_message = message['data']['content']
    elif isinstance(message, str):
        actual_message = message
        
    if actual_message:
        print(f"Extracted message from window: {actual_message}")
        await process_message(actual_message, message_id=message_id, source="window")
    else:
        print(f"Could not extract message from: {message}")

# async def process_message(message, message_id=None, source=None):
#     """
#     Process a user message and generate a response using the LangChain agent.
#     Args:
#         message (str): The user's input message.
#         message_id (str, optional): Unique identifier for the message.
#         source (str, optional): Source of the message.
#     """
#     global processed_message_ids
#     context = cl.user_session.get("context", {})
    
#     if not message_id:
#         message_id = f"msg_{time.time()}"
#     if message_id in processed_message_ids:
#         print(f"Skipping already processed message: {message_id}")
#         return
#     processed_message_ids.add(message_id)

#     agent = cl.user_session.get("agent")
#     if not agent:
#         await cl.Message(content="I'm still initializing. Please try again in a moment.").send()
#         return

#     try:
#         # Build chat history from memory
#         memory = agent.memory
#         chat_history = "\n".join(
#             [f"{msg.type}: {msg.content}" 
#              for msg in memory.buffer
#              if isinstance(msg, (HumanMessage, AIMessage))]
#         )
        
#         prompt = (
#             f"Conversation history:\n{chat_history}\n\n"
#             f"Current page: {context.get('current_page', 'home')}\n"
#             f"User: {message}\n"
#             f"Assistant:"
#         )
        
#         print(f"Processing message with prompt:\n{prompt}")
#         response = await cl.make_async(agent.run)(prompt)
#         await cl.Message(content=response).send()
        
#         # Log updated conversation memory
#         print("Updated conversation memory:")
#         for msg in memory.buffer:
#             print(f"{msg.type}: {msg.content}")
            
#     except Exception as e:
#         print(f"Error processing message: {e}")
#         await cl.Message(
#             content="I'm having trouble processing your request. Could you try rephrasing?"
#         ).send()

async def process_message(message, message_id=None, source=None):
    """
    Process a user message and generate a response with improved error handling
    
    Args:
        message (str): The user's input message.
        message_id (str, optional): Unique identifier for the message.
        source (str, optional): Source of the message.
    """
    global processed_message_ids
    context = cl.user_session.get("context", {})
    
    if not message_id:
        message_id = f"msg_{time.time()}"
    if message_id in processed_message_ids:
        print(f"Skipping already processed message: {message_id}")
        return
    processed_message_ids.add(message_id)

    # First, track the user message
    track_message(message, is_user=True)
    
    # Get the agent, if available
    agent = cl.user_session.get("agent")
    
    # If agent is not available, try to reinitialize it
    if not agent:
        print("Agent not available, attempting to initialize")
        agent = initialize_agent_safely(context)
        if agent:
            cl.user_session.set("agent", agent)
            print("Agent successfully reinitialized")
        else:
            print("Could not initialize agent, using fallback response")
            await cl.Message(content="I'm having trouble connecting to my knowledge base. Let me try to answer your question more directly.").send()
            
            # Provide a simple fallback response
            if "menu" in message.lower() or "order" in message.lower():
                await cl.Message(content="I can help with our menu and orders. You can check out our coffee, pastries, and other items. Would you like more specific information?").send()
            elif "hour" in message.lower() or "open" in message.lower():
                await cl.Message(content="Neo Cafe is open Monday-Friday from 7am to 8pm, and Saturday-Sunday from 8am to 6pm.").send()
            else:
                await cl.Message(content="I'm still initializing my systems. Please try again in a moment, or you can navigate to our menu page to see what we offer.").send()
            return

    try:
        # Build chat history from memory
        memory = agent.memory
        chat_history = "\n".join(
            [f"{msg.type}: {msg.content}" 
             for msg in memory.buffer
             if isinstance(msg, (HumanMessage, AIMessage))]
        )
        
        prompt = (
            f"Conversation history:\n{chat_history}\n\n"
            f"Current page: {context.get('current_page', 'home')}\n"
            f"User: {message}\n"
            f"Assistant:"
        )
        
        print(f"Processing message with prompt:\n{prompt}")
        
        # Add a timeout for agent.run to prevent hanging
        from concurrent.futures import TimeoutError
        import asyncio
        
        try:
            # Try to get a response with a timeout
            response = await asyncio.wait_for(
                cl.make_async(agent.run)(prompt),
                timeout=30  # 30 second timeout
            )
            
            # Track and send the response
            track_message(response, is_user=False)
            await cl.Message(content=response).send()
            
        except TimeoutError:
            print("Agent response timed out")
            await cl.Message(content="I'm taking longer than expected to process your request. Let me provide a simpler response.").send()
            
            # Provide a fallback response for timeout
            if "menu" in message.lower():
                await cl.Message(content="Our menu includes various coffee drinks, teas, and pastries. You can view the full menu on our menu page.").send()
            elif "order" in message.lower():
                await cl.Message(content="You can place an order by telling me what items you'd like, or by using our menu page to select items.").send()
            else:
                await cl.Message(content="I'm here to help with orders, menu information, and general inquiries about Neo Cafe. How can I assist you?").send()
            
        # Log updated conversation memory
        print("Updated conversation memory:")
        for msg in memory.buffer:
            print(f"{msg.type}: {msg.content}")
            
    except Exception as e:
        print(f"Error processing message: {e}")
        import traceback
        traceback.print_exc()
        
        track_message("I'm having trouble processing your request. Could you try rephrasing?", is_user=False)
        await cl.Message(
            content="I'm having trouble processing your request. Could you try rephrasing?"
        ).send()





# @cl.on_chat_end
# def on_chat_end():
#     """Save conversation history when chat ends"""
#     context = cl.user_session.get("context", {})
#     if not context:
#         return
#     messages = cl.user_session.get("chat_history", [])
    
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
    
#     # Update session
#     c.execute('''INSERT OR REPLACE INTO conversations
#                  (session_id, user_id, created_at, last_active)
#                  VALUES (?, ?, ?, ?)''',
#               (context['session_id'], context['user_id'],
#                datetime.now(), datetime.now()))
    
#     # Save messages
#     for msg in messages:
#         c.execute('''INSERT INTO messages
#                      (session_id, content, is_user, timestamp)
#                      VALUES (?, ?, ?, ?)''',
#                   (context['session_id'], msg['content'],
#                    msg['is_user'], datetime.now()))
    
#     conn.commit()
#     conn.close()

@cl.on_chat_end
def on_chat_end():
    """Save conversation history when chat ends with better error handling"""
    try:
        context = cl.user_session.get("context", {})
        if not context:
            print("Warning: No context available in on_chat_end")
            return
        
        # Check for required keys
        session_id = context.get('session_id')
        user_id = context.get('user_id', 'guest')
        
        if not session_id:
            print("Warning: No session_id in context during on_chat_end")
            # Generate a temporary session ID if needed
            import uuid
            session_id = str(uuid.uuid4())
        
        messages = cl.user_session.get("chat_history", [])
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Update session - use INSERT OR REPLACE to handle both new and existing sessions
        c.execute('''INSERT OR REPLACE INTO conversations
                     (session_id, user_id, created_at, last_active)
                     VALUES (?, ?, ?, ?)''',
                  (session_id, user_id,
                   datetime.now(), datetime.now()))
        
        # Save messages if we have any
        if messages:
            for msg in messages:
                try:
                    c.execute('''INSERT INTO messages
                                 (session_id, content, is_user, timestamp)
                                 VALUES (?, ?, ?, ?)''',
                              (session_id, msg.get('content', ''),
                               msg.get('is_user', False), datetime.now()))
                except Exception as msg_err:
                    print(f"Error saving message: {msg_err}")
        
        conn.commit()
        conn.close()
        print(f"Chat session {session_id} saved successfully")
    except Exception as e:
        print(f"Error in on_chat_end: {e}")
        import traceback
        traceback.print_exc()



@cl.on_message
async def on_message(message: cl.Message):
    """Process messages with improved error handling"""
    try:
        # Process through centralized message handler
        await process_message(
            message=message.content,
            message_id=f"chat_{message.id}",
            source="chat"
        )
    except Exception as e:
        print(f"Error in on_message: {e}")
        import traceback
        traceback.print_exc()
        error_response = f"I apologize, but I'm having trouble responding right now. Please try again in a moment."
        track_message(error_response, is_user=False)
        await cl.Message(content=error_response).send()

# @cl.on_message
# async def on_message(message: cl.Message):
#     """Process messages with full context handling"""
#     # Track user message first
#     track_message(message.content, is_user=True)
    
#     try:
#         # Process through centralized message handler
#         response = await process_message(
#             message=message.content,
#             message_id=f"chat_{message.id}",
#             source="chat"
#         )
        
#         # Only send and track if we got a response
#         if response:
#             track_message(response, is_user=False)
#             await cl.Message(content=response).send()
            
#     except Exception as e:
#         error_response = f"Sorry, I need help with that: {str(e)}"
#         track_message(error_response, is_user=False)
#         await cl.Message(content=error_response).send()

@cl.on_window_message
async def handle_auth_message(message):
    """
    Handle authentication messages from the parent window (Dash app)
    """
    logger.debug(f"Received window message: {message}")
    
    # Check if this is an auth update message
    if isinstance(message, dict) and message.get('type') == 'auth_update':
        try:
            # Extract user and token
            user = message.get('user')
            token = message.get('token')
            auth_status = message.get('auth_status', False)
            
            logger.debug(f"Received auth update for user: {user}")
            
            if user and token and auth_status:
                # Verify token
                try:
                    # Try to decode the token
                    import base64
                    import json
                    decoded_bytes = base64.b64decode(token)
                    user_data = json.loads(decoded_bytes)
                    
                    if isinstance(user_data, dict) and user_data.get('username') == user:
                        # Get current context
                        context = cl.user_session.get("context", {})
                        
                        # Update context with authenticated user
                        context.update({
                            "user_id": user,
                            "username": user,
                            "email": user_data.get("email", ""),
                            "first_name": user_data.get("first_name", ""),
                            "last_name": user_data.get("last_name", ""),
                            "is_authenticated": True
                        })
                        
                        # Add full name if available
                        first_name = user_data.get("first_name", "")
                        last_name = user_data.get("last_name", "")
                        if first_name or last_name:
                            full_name = f"{first_name} {last_name}".strip()
                            context["full_name"] = full_name
                        
                        # Save updated context
                        cl.user_session.set("context", context)
                        logger.debug(f"Updated context from token: {context}")
                        
                        # Re-initialize the agent with the updated context
                        try:
                            agent = setup_langchain_agent(context)
                            cl.user_session.set("agent", agent)
                            logger.debug("Re-initialized agent with auth context")
                            
                            # Send acknowledgment message
                            await cl.Message(content=f"Welcome, {context.get('full_name') or user}! How can I help you today?").send()
                        except Exception as agent_err:
                            logger.error(f"Error re-initializing agent: {agent_err}")
                    else:
                        logger.warning(f"Invalid token for user {user}")
                except Exception as decode_err:
                    logger.error(f"Error decoding token: {decode_err}")
            else:
                logger.warning("Incomplete auth data received")
        except Exception as e:
            logger.error(f"Error processing auth message: {e}")

# ----- Enhanced Features -----

def load_conversation_history(session_id: str) -> list:
    """Load previous conversation from database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT content, is_user FROM messages
                 WHERE session_id = ?
                 ORDER BY timestamp ASC''', (session_id,))
    results = c.fetchall()
    conn.close()
    
    return [{
        "content": row[0],
        "is_user": bool(row[1])
    } for row in results]

def track_message(content: str, is_user: bool):
    """Store messages in session history"""
    history = cl.user_session.get("chat_history", [])
    history.append({
        "content": content,
        "is_user": is_user,
        "timestamp": datetime.now()
    })
    cl.user_session.set("chat_history", history)

def get_welcome_message(context: dict) -> str:
    """Generate personalized welcome message"""
    if context['is_authenticated']:
        base = f"Welcome back, valued customer! "
    else:
        base = "Welcome to Neo Cafe! "
    
    page_specific = {
        'menu': "Browse our menu below or ask for recommendations!",
        'order': "Ready to place an order? Just tell me what you'd like!",
        'history': "Viewing order history... ask about any previous order!"
    }
    return base + page_specific.get(context['current_page'], "How can I assist you today?")

# ----- Data Management -----

def load_menu_data():
    """Load menu with enhanced validation"""
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        possible_paths = [
            os.path.join(base_dir, 'data', 'menu.json'),
            os.path.join(base_dir, 'app', 'data', 'menu.json')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path) as f:
                    data = json.load(f)
                    validate_menu_data(data)
                    return data
        return default_menu()
    except Exception as e:
        print(f"Menu error: {e}")
        return default_menu()

def validate_menu_data(data: list):
    """Updated validation for menu items"""
    required = ['id', 'name', 'price', 'category']
    optional = ['description', 'vegetarian', 'vegan', 'gluten_free', 'popular']
    
    for item in data:
        # Check required fields
        if not all(key in item for key in required):
            raise ValueError(f"Missing required field in item: {item}")
            
        # Validate field types
        if not isinstance(item['price'], (int, float)):
            raise ValueError(f"Invalid price format in item: {item['id']}")

def default_menu():
    """Updated default menu with all required fields"""
    return [
        {
            "id": 1,
            "name": "Espresso",
            "description": "Rich espresso blend",
            "price": 2.95,
            "category": "coffee",
            "vegetarian": True,
            "vegan": False,
            "gluten_free": True
        },
        {
            "id": 2,
            "name": "Croissant",
            "description": "Buttery pastry",
            "price": 3.25,
            "category": "pastries",
            "vegetarian": True,
            "vegan": False,
            "gluten_free": False
        }
    ]

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="🛎️ Place Order",
            message="I'd like to order a latte and croissant",
            description="Start a new order"
        ),
        cl.Starter(
            label="📦 Track Order",
            message="Status of order ORD-123ABC",
            description="Check order progress"
        ),
        cl.Starter(
            label="📝 Modify Order",
            message="Update order ORD-123ABC to add a cappuccino",
            description="Change existing order"
        ),
        cl.Starter(
            label="⏳ Opening Hours",
            message="When do you open today?",
            description="Check store schedule"
        )
    ]