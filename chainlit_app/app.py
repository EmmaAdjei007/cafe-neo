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
from langchain_openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
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


# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Constants
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:8050')
ROBOT_SIMULATOR_URL = os.environ.get('ROBOT_SIMULATOR_URL', 'http://localhost:8051')
DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'neo_cafe.db'))
logger.debug(f"Using database at: {DB_PATH}")
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
    
    # Create table for order state tracking
    c.execute('''CREATE TABLE IF NOT EXISTS user_state
                 (session_id TEXT,
                  state_type TEXT,
                  state_data TEXT,
                  updated_at TIMESTAMP,
                  PRIMARY KEY (session_id, state_type))''')
    
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
        Place an order with the Neo Cafe system with improved detail collection.
        Args:
            order_data (dict or str): Order information in various formats.
        Returns:
            dict: Order details with ID or a response requesting more information.
        """
        try:
            # Step 1: Better input handling for various formats
            print(f"Original order data: {order_data}")
            
            # Check for confirmation messages
            if isinstance(order_data, str):
                # Check for confirmation phrases
                confirmation_phrases = [
                    "that's all", "thats all", "nothing else", "finalize", "place order",
                    "confirm", "that is all", "looks good", "proceed", "yes", "complete",
                    "finish", "done", "good to go", "fine", "perfect", "correct", "ok", 
                    "okay", "sure", "yeah", "yep", "sounds good", "just that", "that's it",
                    "that will be it", "finalize it", "that's correct"
                ]
                
                order_data_lower = order_data.lower().strip()
                if any(phrase == order_data_lower or phrase in order_data_lower for phrase in confirmation_phrases) and len(order_data_lower.split()) <= 6:
                    print("Detected confirmation message, returning verification status")
                    return {
                        "status": "confirmation_only",
                        "message": "Please confirm that you want to finalize your order as is.",
                        "order_so_far": None
                    }
                    
            # Continue with normal parsing logic
            if isinstance(order_data, str):
                try:
                    # Try to parse as JSON first
                    order_data = json.loads(order_data)
                    print(f"Parsed order data from JSON: {order_data}")
                    
                    # Map 'location' or 'address' to 'delivery_location' if needed
                    if 'location' in order_data and 'delivery_location' not in order_data:
                        order_data['delivery_location'] = order_data['location']
                        print(f"Mapped location field to delivery_location: {order_data['delivery_location']}")
                    elif 'address' in order_data and 'delivery_location' not in order_data:
                        order_data['delivery_location'] = order_data['address']
                        print(f"Mapped address field to delivery_location: {order_data['delivery_location']}")
                except json.JSONDecodeError:
                    # If not valid JSON, try to parse as text
                    try:
                        parsed_data = parse_order_text(order_data)
                        
                        # Check if this was just a confirmation message
                        if isinstance(parsed_data, dict) and parsed_data.get("is_confirmation", False):
                            print("Parse_order_text detected confirmation-only message")
                            return {
                                "status": "confirmation_only",
                                "message": "Please confirm that you want to finalize your order as is.",
                                "order_so_far": None
                            }
                        
                        # Normal parsed order data
                        order_data = parsed_data
                        print(f"Parsed order data from text: {order_data}")
                        
                    except Exception as parse_err:
                        print(f"Error in text parsing: {parse_err}")
                        # Additional fallback - try to extract menu items directly
                        items = []
                        text_lower = order_data.lower()
                        
                        # Special handling for "classic latte" in direct text
                        if "classic latte" in text_lower:
                            # Find latte in menu
                            latte_item = None
                            for menu_item in menu_items:
                                if menu_item["name"].lower() == "latte":
                                    latte_item = menu_item
                                    break
                            
                            if latte_item:
                                # Create a special order for classic latte
                                order_data = {
                                    "items": [{
                                        "item_id": latte_item["id"],
                                        "quantity": 1,
                                        "special_instructions": "Classic style"
                                    }],
                                    "user_id": "guest",
                                    "delivery_type": ""  # Empty to trigger the conversation flow
                                }
                                print(f"Created special classic latte order: {order_data}")
                            else:
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
                                        "delivery_type": ""  # Empty to trigger the conversation flow
                                    }
                                else:
                                    raise ValueError("No menu items found in text and couldn't parse as JSON")
            
            # Step 2: Check for required details
            # Check for items first
            if not isinstance(order_data, dict):
                raise ValueError(f"Invalid order data type: {type(order_data)}")
                
            if "items" not in order_data or not order_data["items"]:
                return {
                    "status": "incomplete",
                    "message": "I don't see any items in your order. What would you like to order?",
                    "missing_field": "items"
                }
                
            # Convert items to standard format if needed
            standardized_items = []
            for item in order_data["items"]:
                if isinstance(item, dict):
                    if "item_id" in item:
                        standardized_items.append(item)
                    elif "id" in item:
                        standardized_items.append({
                            "item_id": item["id"],
                            "quantity": item.get("quantity", 1),
                            "special_instructions": item.get("special_instructions", "")
                        })
                    elif "name" in item:
                        # Find item by name
                        found = False
                        for menu_item in menu_items:
                            # Handle "Classic Latte" case specially
                            if "classic" in item["name"].lower() and "latte" in item["name"].lower() and menu_item["name"].lower() == "latte":
                                standardized_items.append({
                                    "item_id": menu_item["id"],
                                    "quantity": item.get("quantity", 1),
                                    "special_instructions": "Classic style"
                                })
                                found = True
                                break
                            # Regular case
                            elif menu_item["name"].lower() == item["name"].lower():
                                standardized_items.append({
                                    "item_id": menu_item["id"],
                                    "quantity": item.get("quantity", 1),
                                    "special_instructions": item.get("special_instructions", "")
                                })
                                found = True
                                break
                        
                        # If not found, try fuzzy matching
                        if not found:
                            best_match = None
                            best_score = 0
                            item_name_lower = item["name"].lower()
                            
                            for menu_item in menu_items:
                                menu_name = menu_item["name"].lower()
                                # Check if item name contains menu item name or vice versa
                                if menu_name in item_name_lower or item_name_lower in menu_name:
                                    score = len(menu_name) if menu_name in item_name_lower else len(item_name_lower)
                                    if score > best_score:
                                        best_score = score
                                        best_match = menu_item
                            
                            if best_match:
                                print(f"Fuzzy matched '{item['name']}' to '{best_match['name']}'")
                                standardized_items.append({
                                    "item_id": best_match["id"],
                                    "quantity": item.get("quantity", 1),
                                    "special_instructions": item.get("special_instructions", "")
                                })
                elif isinstance(item, str):
                    # Find item by name
                    found = False
                    for menu_item in menu_items:
                        # Special case for Classic Latte
                        if "classic latte" == item.lower() and menu_item["name"].lower() == "latte":
                            standardized_items.append({
                                "item_id": menu_item["id"],
                                "quantity": 1,
                                "special_instructions": "Classic style"
                            })
                            found = True
                            break
                        # Regular case
                        elif menu_item["name"].lower() == item.lower():
                            standardized_items.append({
                                "item_id": menu_item["id"],
                                "quantity": 1,
                                "special_instructions": ""
                            })
                            found = True
                            break
                    
                    # If not found, try fuzzy matching
                    if not found:
                        best_match = None
                        best_score = 0
                        item_lower = item.lower()
                        
                        for menu_item in menu_items:
                            menu_name = menu_item["name"].lower()
                            # Check if item name contains menu item name or vice versa
                            if menu_name in item_lower or item_lower in menu_name:
                                score = len(menu_name) if menu_name in item_lower else len(item_lower)
                                if score > best_score:
                                    best_score = score
                                    best_match = menu_item
                        
                        if best_match:
                            print(f"Fuzzy matched '{item}' to '{best_match['name']}'")
                            standardized_items.append({
                                "item_id": best_match["id"],
                                "quantity": 1,
                                "special_instructions": ""
                            })
                            
            if standardized_items:
                order_data["items"] = standardized_items
            
            # Step 3: Check for missing required details to create conversational flow
            
            # Check for delivery type (dine-in, pickup, delivery)
            if not order_data.get("delivery_type"):
                return {
                    "status": "incomplete",
                    "message": "Is this order for dine-in, pickup, or delivery?",
                    "missing_field": "delivery_type",
                    "order_so_far": order_data
                }
                
            # Check for delivery location based on type
            if not order_data.get("delivery_location"):
                delivery_type_lower = order_data.get("delivery_type").lower()
                if delivery_type_lower in ["dine-in", "dine in", "dinein"]:
                    # Check if table number is already in delivery_type description
                    # Extract table number if possible
                    if "table" in delivery_type_lower:
                        table_parts = delivery_type_lower.split("table")
                        if len(table_parts) > 1 and table_parts[1].strip().isdigit():
                            order_data["delivery_location"] = f"Table {table_parts[1].strip()}"
                            print(f"Extracted table number from delivery_type: {order_data['delivery_location']}")
                    # If still no delivery_location, prompt for table number
                    if not order_data.get("delivery_location"):
                        return {
                            "status": "incomplete",
                            "message": "Which table number are you sitting at?",
                            "missing_field": "delivery_location",
                            "order_so_far": order_data
                        }
                elif delivery_type_lower in ["delivery", "deliver"]:
                    return {
                        "status": "incomplete",
                        "message": "What address would you like your order delivered to?",
                        "missing_field": "delivery_location",
                        "order_so_far": order_data
                    }
                elif delivery_type_lower in ["pickup", "pick-up", "pick up", "takeout", "take-out", "take out"]:
                    # For pickup, use default location
                    order_data["delivery_location"] = "Pickup Counter"
            
            # Check for payment method
            if not order_data.get("payment_method"):
                return {
                    "status": "incomplete",
                    "message": "How would you like to pay? We accept Credit Card, Cash, or Mobile Payment.",
                    "missing_field": "payment_method",
                    "order_so_far": order_data
                }
                
            

            # Add verification step if all required fields are present but verification_complete is not set
            if not order_data.get("verification_complete", False):
                # Generate order ID during verification if not present
                if "id" not in order_data:
                    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
                    order_data["id"] = order_id
                    print(f"Generated order ID for verification: {order_id}")
                
                # Format order summary for verification
                items_summary = []
                total_price = 0
                
                for item in order_data.get("items", []):
                    # Find item details for display
                    item_id = item.get("item_id")
                    quantity = item.get("quantity", 1)
                    
                    # Find menu item details
                    menu_item = next((mi for mi in menu_items if mi["id"] == item_id), None)
                    
                    if menu_item:
                        item_name = menu_item["name"]
                        item_price = menu_item.get("price", 0) * quantity
                        items_summary.append(f"{quantity}x {item_name} (${item_price:.2f})")
                        total_price += item_price
                    else:
                        items_summary.append(f"{quantity}x Item #{item_id}")
                
                # Format delivery details
                delivery_type = order_data.get("delivery_type", "").capitalize()
                delivery_location = order_data.get("delivery_location", "")
                payment_method = order_data.get("payment_method", "")
                
                # Create verification message
                verification_message = f"Your order summary:\n\n"
                verification_message += "• " + "\n• ".join(items_summary) + "\n\n"
                verification_message += f"Total: ${total_price:.2f}\n"
                verification_message += f"Type: {delivery_type}\n"
                verification_message += f"Location: {delivery_location}\n"
                verification_message += f"Payment: {payment_method}\n\n"
                verification_message += "Would you like to add anything else to your order, confirm it as is, or cancel the order?"
                
                # IMPORTANT: Update cart items for Dash app during verification
                try:
                    # REPLACE EVERYTHING FROM HERE...
                    # Calculate the total price
                    total_price = 0
                    for item in order_data["items"]:
                        item_id = item.get("item_id")
                        quantity = item.get("quantity", 1)
                        # Find item price
                        for menu_item in menu_items:
                            if menu_item["id"] == item_id:
                                total_price += menu_item.get("price", 0) * quantity
                                break
                    
                    # Store total in order_data for future use
                    order_data["total"] = total_price
                    
                    # Format order summary
                    items_summary = []
                    for item in order_data.get("items", []):
                        # Find item details for display
                        item_id = item.get("item_id")
                        quantity = item.get("quantity", 1)
                        
                        # Find menu item details
                        menu_item = next((mi for mi in menu_items if mi["id"] == item_id), None)
                        
                        if menu_item:
                            item_name = menu_item["name"]
                            item_price = menu_item.get("price", 0) * quantity
                            items_summary.append(f"{quantity}x {item_name} (${item_price:.2f})")
                        else:
                            items_summary.append(f"{quantity}x Item #{item_id}")
                    
                    # Format delivery details
                    delivery_type = order_data.get("delivery_type", "").capitalize()
                    delivery_location = order_data.get("delivery_location", "")
                    payment_method = order_data.get("payment_method", "")
                    
                    # Create verification message
                    verification_message = f"Your order summary:\n\n"
                    verification_message += "• " + "\n• ".join(items_summary) + "\n\n"
                    verification_message += f"Total: ${total_price:.2f}\n"
                    verification_message += f"Type: {delivery_type}\n"
                    verification_message += f"Location: {delivery_location}\n"
                    verification_message += f"Payment: {payment_method}\n\n"
                    verification_message += "Would you like to add anything else to your order, confirm it as is, or cancel the order?"
                    
                    # CRITICAL FIX: Create cart-friendly format with total included
                    cart_items = []
                    for item in order_data["items"]:
                        item_id = item.get("item_id")
                        quantity = item.get("quantity", 1)
                        
                        # Find menu item details
                        menu_item = next((m for m in menu_items if m["id"] == item_id), None)
                        if menu_item:
                            cart_items.append({
                                "id": item_id,
                                "name": menu_item["name"],
                                "price": menu_item.get("price", 0),
                                "quantity": quantity,
                                "special_instructions": item.get("special_instructions", "")
                            })
                    
                    # Create cart-specific message WITH TOTAL
                    cart_update = {
                        "type": "cart_update",
                        "items": cart_items,
                        "order_id": order_data.get("id", str(uuid.uuid4())),
                        "username": order_data.get("username", "guest"),
                        "user_id": order_data.get("user_id", "guest"),
                        "total": total_price  # CRITICAL: Include the total here
                    }
                    
                    # Use the updated helper function to update the UI with the total
                    update_chat_ui_with_order(order_data)
                    # ...TO HERE
                except Exception as cart_err:
                    print(f"Error updating cart during verification: {cart_err}")
                
                # Return verification request
                return {
                    "status": "verification",
                    "message": verification_message,
                    "order_so_far": order_data
                }
                
            # Step 4: All details are present, continue with order processing
            
            # Generate order ID if not present
            if "id" not in order_data:
                order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
                order_data["id"] = order_id
            
            # Add context data
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
                
            # Add timestamp
            order_data["timestamp"] = datetime.now().isoformat()
            
            # Calculate total if not provided
            if "total" not in order_data:
                total = 0
                for item in order_data["items"]:
                    item_id = item.get("item_id")
                    quantity = item.get("quantity", 1)
                    # Find item price
                    for menu_item in menu_items:
                        if menu_item["id"] == item_id:
                            total += menu_item.get("price", 0) * quantity
                            break
                order_data["total"] = total
            
            # Step 5: Save to database
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
            
            # Step 6: Notify dashboard and update cart
            success = False
            try:
                # CRITICAL: Update cart items for Dash app - this is required for cart integration
                # Create cart-friendly format
                cart_items = []
                for item in order_data["items"]:
                    item_id = item.get("item_id")
                    quantity = item.get("quantity", 1)
                    
                    # Find menu item details
                    menu_item = next((m for m in menu_items if m["id"] == item_id), None)
                    if menu_item:
                        cart_items.append({
                            "id": item_id,
                            "name": menu_item["name"],
                            "price": menu_item.get("price", 0),
                            "quantity": quantity,
                            "special_instructions": item.get("special_instructions", "")
                        })
                
                # Create cart-specific message
                cart_update = {
                    "type": "cart_update",
                    "items": cart_items,
                    "order_id": order_data["id"],
                    "username": order_data.get("username", "guest"),
                    "user_id": order_data.get("user_id", "guest"),
                    "total": order_data.get("total", 0)  # Add the total from order_data
                }
                
                # METHOD 1: Try Socket.IO first
                try:
                    import socketio
                    sio = socketio.Client()
                    sio.connect(DASHBOARD_URL)
                    # Send both general order update and specific cart update
                    sio.emit('order_update', order_data)
                    sio.emit('cart_update', cart_update)
                    sio.disconnect()
                    print("Order sent via Socket.IO")
                    success = True
                except Exception as e:
                    print(f"Error sending order via Socket.IO: {e}")
                    success = False
                
                # METHOD 2: Try parent window messaging
                try:
                    # Send order update to parent window
                    cl.send_to_parent({
                        "type": "order_update", 
                        "order": order_data
                    })
                    
                    # CRITICAL: Also send cart_update event specifically
                    cl.send_to_parent({
                        "type": "cart_update",
                        "items": cart_items,
                        "order_id": order_data["id"],
                        "total": order_data.get("total", 0)  # IMPORTANT: Include the total here
                    })
                    
                    print("Order notification sent to parent")
                    success = True
                except Exception as e:
                    print(f"Error sending order via cl.send_to_parent: {e}")
                
                # METHOD 3: Try REST API approach
                if not success:
                    try:
                        # Call the place-order API endpoint
                        order_response = requests.post(
                            f"{DASHBOARD_URL}/api/place-order", 
                            json=order_data,
                            timeout=5
                        )
                        
                        # Call the update-cart API endpoint
                        cart_response = requests.post(
                            f"{DASHBOARD_URL}/api/update-cart", 
                            json=cart_update,
                            timeout=5
                        )
                        
                        if order_response.status_code == 200 or cart_response.status_code == 200:
                            print(f"Order API response: {order_response.status_code}, Cart API response: {cart_response.status_code}")
                            success = True
                        else:
                            print(f"REST API call failed - Order: {order_response.status_code}, Cart: {cart_response.status_code}")
                    except Exception as api_err:
                        print(f"Error calling REST API: {api_err}")
                
                # METHOD 4: Also try the file-based approach as last resort
                try:
                    os.makedirs('order_data', exist_ok=True)
                    with open(f"order_data/order_{order_data['id']}.json", 'w') as f:
                        json.dump(order_data, f)
                    with open(f"order_data/cart_{order_data['id']}.json", 'w') as f:
                        json.dump(cart_update, f)
                    print(f"Order saved to file: order_{order_data['id']}.json")
                except Exception as e:
                    print(f"Error saving order to file: {e}")
                
                # Update session context
                context = cl.user_session.get("context", {})
                context["active_order"] = order_data
                context["delivery_location"] = order_data.get("delivery_location", "Table 1")
                cl.user_session.set("context", context)
                
                # Important: Clear the order_in_progress state now that order is complete
                cl.user_session.set("order_in_progress", None)
                
                # Return success message
                return {
                    "status": "success",
                    "message": f"Your order has been placed! Order #{order_data['id']}. Your {order_data.get('delivery_type', 'order')} will be ready soon.",
                    "order": order_data
                }
            
            except Exception as e:
                print(f"Error in notification: {e}")
                # Return basic order info
                return {
                    "status": "success",
                    "message": f"Order placed! Your total is ${order_data.get('total', 0):.2f}",
                    "order": order_data
                }
                
        except Exception as e:
            print(f"Unexpected error placing order: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"I'm sorry, I couldn't process your order: {str(e)}"
            }
        
    @staticmethod
    def handle_order_response(order_response):
        """
        Handle responses from the place_order method, especially for incomplete orders
        Args:
            order_response (dict): Response from place_order
        Returns:
            str: User-friendly message to display
        """
        # Check response type
        if not isinstance(order_response, dict):
            return f"There was a problem with your order: {order_response}"
            
        status = order_response.get("status", "unknown")
        
        # Handle verification status (new)
        if status == "verification":
            # Just return the verification message directly
            return order_response.get("message", "Please review your order. Would you like to add anything else?")
            
        elif status == "confirmation_only":
            # Process confirmation
            return order_response.get("message", "Please confirm that you want to finalize your order.")

        elif status == "incomplete":
            # Order needs more details
            message = order_response.get("message", "I need more information to complete your order.")
            missing_field = order_response.get("missing_field", "")
            
            # Customize prompts based on missing field
            if missing_field == "delivery_type":
                return (f"{message} Would you prefer dine-in, pickup, or delivery?")
            elif missing_field == "delivery_location":
                if order_response.get("order_so_far", {}).get("delivery_type") == "dine-in":
                    return (f"{message} Which table number are you sitting at?")
                else:
                    return (f"{message} Please provide your delivery address.")
            elif missing_field == "payment_method":
                return (f"{message} We accept Credit Card, Cash, and Mobile Payment.")
            else:
                return message
        
        elif status == "success":
            # Order placed successfully
            message = order_response.get("message", "Your order has been placed successfully!")
            order = order_response.get("order", {})
            
            # Format order summary
            summary = f"{message}\n\n"
            
            if order:
                if "id" in order:
                    summary += f"Order ID: {order['id']}\n"
                
                if "items" in order and order["items"]:
                    summary += "Items:\n"
                    try:
                        # Try to display proper item names
                        menu_lookup = {item["id"]: item for item in menu_items}
                        
                        for item in order["items"]:
                            item_id = item.get("item_id")
                            quantity = item.get("quantity", 1)
                            menu_item = menu_lookup.get(item_id, {})
                            item_name = menu_item.get("name", f"Item #{item_id}")
                            item_price = menu_item.get("price", 0) * quantity
                            summary += f"- {quantity}x {item_name} (${item_price:.2f})\n"
                    except Exception:
                        # Fallback display
                        summary += f"- {len(order['items'])} item(s)\n"
                
                if "total" in order:
                    summary += f"\nTotal: ${order['total']:.2f}\n"
                
                if "delivery_type" in order:
                    summary += f"Order type: {order['delivery_type'].title()}\n"
                
                if "delivery_location" in order:
                    summary += f"Location: {order['delivery_location']}\n"
                    
                if "payment_method" in order:
                    summary += f"Payment: {order['payment_method']}\n"
                
            return summary
        
        elif status == "error":
            # Order processing error
            message = order_response.get("message", "There was a problem processing your order.")
            return f"I'm sorry, but {message} Please try again."
        
        else:
            # Unknown response type
            return "I'm not sure what happened with your order. Can you try again please?"
    
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
    Parse natural language order text into structured order data with improved detail extraction.
    Args:
        text (str): Natural language order description.
    Returns:
        dict: Structured order data.
    """
    try:
        # Quick check if this is just a confirmation message, not a new order
        text_lower = text.lower().strip()
        confirmation_phrases = [
            "that's all", "thats all", "nothing else", "finalize", "place order",
            "confirm", "that is all", "looks good", "proceed", "yes", "complete",
            "finish", "done", "good to go", "fine", "perfect", "correct", "ok", 
            "okay", "sure", "yeah", "yep", "sounds good", "just that", "that's it",
            "that looks right", "place my order", "go ahead", "that's correct",
            "that will be it", "that will be all", "finalize it", "that'll be it"
        ]
        
        # If this is just a confirmation message with no menu items, raise a special error
        if any(phrase == text_lower or phrase in text_lower for phrase in confirmation_phrases) and len(text_lower.split()) <= 5:
            return {
                "is_confirmation": True,
                "items": []  # Empty items list
            }
            
        context = cl.user_session.get("context", {})
        order_items = []
        special_instructions_global = ""
        
        # Extract global special instructions
        if "with " in text_lower and " and " in text_lower.split("with ")[1]:
            parts = text_lower.split("with ")
            special_parts = parts[1].split(" and ")
            if len(special_parts) > 1:
                special_instructions_global = f"With {parts[1]}"
        
        # Extract delivery type
        delivery_type = ""  # Empty to trigger follow-up question
        delivery_terms = {
            "dine in": "dine-in",
            "dine-in": "dine-in", 
            "dinein": "dine-in",
            "table": "dine-in",
            "sit": "dine-in",
            "restaurant": "dine-in",
            "pickup": "pickup",
            "pick up": "pickup",
            "pick-up": "pickup",
            "takeout": "pickup",
            "take out": "pickup",
            "take-out": "pickup",
            "to go": "pickup",
            "delivery": "delivery",
            "deliver": "delivery", 
            "bring to": "delivery",
            "send to": "delivery"
        }
        
        for term, dtype in delivery_terms.items():
            if term in text_lower:
                delivery_type = dtype
                break
        
        # Extract delivery location
        delivery_location = ""
        
        # IMPROVED TABLE EXTRACTION for dine-in
        if "table" in text_lower:
            # Use regex to find table numbers more reliably
            import re
            table_matches = re.findall(r'table\s*(\d+)', text_lower)
            if table_matches:
                delivery_location = f"Table {table_matches[0]}"
                print(f"Extracted table number from text: {delivery_location}")
            elif any(part.isdigit() for part in text_lower.split()):
                for i, part in enumerate(text_lower.split()):
                    if part.isdigit() and i > 0 and text_lower.split()[i-1] in ["table", "number", "#"]:
                        delivery_location = f"Table {part}"
                        print(f"Found table number with context: {delivery_location}")
                        break
                    elif part.isdigit():
                        delivery_location = f"Table {part}"
                        print(f"Found possible table number: {delivery_location}")
                        break
        
        # IMPROVED ADDRESS EXTRACTION for delivery
        elif delivery_type == "delivery":
            address_indicators = ["deliver to", "delivery to", "send to", "bring to", "address", "location", "at"]
            for indicator in address_indicators:
                if indicator in text_lower:
                    idx = text_lower.find(indicator) + len(indicator)
                    # Get everything after the indicator
                    address_part = text_lower[idx:].strip()
                    
                    # Handle multiple sentences
                    if any(end_char in address_part for end_char in ['.', ',', ';', '!', '?']):
                        for end_char in ['.', ',', ';', '!', '?']:
                            if end_char in address_part:
                                address_part = address_part.split(end_char)[0].strip()
                                break
                    
                    # Filter out payment info
                    payment_terms = ["pay", "cash", "credit", "card", "apple pay", "google pay"]
                    for term in payment_terms:
                        if term in address_part:
                            address_part = address_part.split(term)[0].strip()
                    
                    if len(address_part) > 3 and not any(word in address_part for word in ["my order", "it", "this"]):
                        delivery_location = address_part.capitalize()
                        print(f"Extracted delivery address: {delivery_location}")
                        break
            
            # Fallback address extraction - look for common address patterns
            if not delivery_location:
                # Look for numeric addresses (e.g. "123 Main St")
                import re
                address_match = re.search(r'\b\d+\s+[a-zA-Z\s]+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|circle|cir|court|ct|place|pl|boulevard|blvd)\b', text_lower, re.IGNORECASE)
                if address_match:
                    delivery_location = address_match.group().capitalize()
                    print(f"Found address with street number: {delivery_location}")
                else:
                    # Try simpler pattern - just a number followed by words
                    address_match = re.search(r'\b\d+\s+[a-zA-Z\s]{5,30}\b', text_lower)
                    if address_match:
                        delivery_location = address_match.group().capitalize()
                        print(f"Found potential address: {delivery_location}")
        
        # Extract payment method with improved detection
        payment_method = ""
        payment_terms = {
            "credit card": "Credit Card",
            "credit": "Credit Card",
            "card": "Credit Card",
            "visa": "Credit Card",
            "mastercard": "Credit Card",
            "debit": "Credit Card",
            "cash": "Cash",
            "money": "Cash",
            "bills": "Cash",
            "dollars": "Cash",
            "mobile payment": "Mobile Payment",
            "mobile": "Mobile Payment",
            "apple pay": "Mobile Payment",
            "google pay": "Mobile Payment",
            "samsung pay": "Mobile Payment",
            "phone": "Mobile Payment",
            "venmo": "Mobile Payment",
            "paypal": "Mobile Payment"
        }
        
        for term, method in payment_terms.items():
            if term in text_lower:
                payment_method = method
                break
        
        # Special handling for "classic latte" case
        if "classic latte" in text_lower or "classic" in text_lower and "latte" in text_lower:
            for menu_item in menu_items:
                if menu_item["name"].lower() == "latte":
                    print(f"Found special case: Classic Latte")
                    order_items.append({
                        "item_id": menu_item["id"],
                        "quantity": 1,
                        "special_instructions": "Classic style"
                    })
                    break
        
        # If we haven't found a "classic latte", continue with regular parsing
        if not order_items:
            # Process menu items with improved matching for other items
            for item in menu_items:
                item_name_lower = item["name"].lower()
                
                # Skip if we already have this item (e.g., classic latte)
                if item_name_lower == "latte" and any(item["item_id"] == item_id for item_id in [i["item_id"] for i in order_items]):
                    continue
                
                # Try different ways the item might appear in text
                variations = [
                    item_name_lower,
                    item_name_lower.replace(" ", ""),  # No spaces
                    item_name_lower.replace("-", ""),  # No hyphens
                    item_name_lower.replace(" ", "-"),  # Spaces as hyphens
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
        
        # Try fuzzy matching if no items found
        if not order_items:
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
        
        # Build the order structure with enhanced details
        return {
            "user_id": context.get("user_id", "guest"),
            "items": order_items,
            "delivery_type": delivery_type,
            "delivery_location": delivery_location,
            "payment_method": payment_method,
            "special_instructions": special_instructions_global
        }
    except ValueError as e:
        print(f"Parse order error details: {e}")
        raise ValueError(f"Could not parse order text: {str(e)}")
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
    Verify authentication token with enhanced debugging and users.json lookup
    
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
                username = user_data['username']
                logger.debug(f"Successfully decoded auth token for user: {username}")
                
                # Try to get more user data from users.json
                stored_user_data = get_user_from_file(username)
                if stored_user_data:
                    # Merge data from token with data from file
                    merged_data = {**user_data, **stored_user_data}
                    logger.debug(f"Enhanced user data with info from users.json")
                    
                    # Ensure full_name is set if available
                    if 'first_name' in merged_data or 'last_name' in merged_data:
                        full_name = f"{merged_data.get('first_name', '')} {merged_data.get('last_name', '')}".strip()
                        if full_name:
                            merged_data['full_name'] = full_name
                    
                    return username, True, merged_data
                
                # If no stored data, use token data
                if 'first_name' in user_data or 'last_name' in user_data:
                    full_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
                    if full_name:
                        user_data['full_name'] = full_name
                
                return username, True, user_data
        except Exception as decode_err:
            logger.debug(f"Not a base64 token: {str(decode_err)}")
        
        # If not base64, try direct username match
        # This could be just the username coming through
        direct_user = token
        stored_user_data = get_user_from_file(direct_user)
        if stored_user_data:
            logger.debug(f"Found user via direct username match: {direct_user}")
            return direct_user, True, stored_user_data
    
    except Exception as e:
        logger.error(f"Auth token verification error: {str(e)}")
        
    logger.debug("Auth verification failed, defaulting to guest")
    return "guest", False, {}

def get_user_from_file(username):
    """
    Retrieve user data from users.json file
    
    Args:
        username (str): Username to look for
        
    Returns:
        dict: User data or None if not found
    """
    try:
        # Look for users.json in multiple possible locations
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        possible_paths = [
            os.path.join(base_dir, 'app', 'data', 'seed_data', 'users.json'),
            os.path.join(base_dir, 'data', 'seed_data', 'users.json'),
            os.path.join(base_dir, 'app', 'data', 'users.json')
        ]
        
        users_file = None
        for path in possible_paths:
            if os.path.exists(path):
                users_file = path
                break
        
        if not users_file:
            logger.warning(f"Users file not found in any standard location")
            return None
        
        logger.debug(f"Reading user data from: {users_file}")
        with open(users_file, 'r') as f:
            users = json.load(f)
        
        # Log available usernames for debugging
        usernames = [user.get('username') for user in users if 'username' in user]
        logger.debug(f"Available users: {usernames}")
        
        # Find the user by username (case-insensitive match)
        for user in users:
            if user.get('username', '').lower() == username.lower():
                # Remove sensitive data
                user_data = {k: v for k, v in user.items() if k != 'password_hash'}
                logger.debug(f"Found user in users.json: {username}")
                return user_data
        
        logger.warning(f"User not found in users.json: {username}")
        return None
    except Exception as e:
        logger.error(f"Error reading users.json: {e}")
        traceback.print_exc()
        return None


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
                func=lambda x: OrderManager.handle_order_response(OrderManager.place_order(x)),
                description="""Place an order with Neo Cafe. Expects either a JSON string or natural language order description.
                            IMPORTANT: You must gather all the required details before placing an order:
                            1. Items to order (what food/drinks)
                            2. Delivery type (dine-in, pickup, or delivery)
                            3. Location (table number for dine-in, address for delivery)
                            4. Payment method (Credit Card, Cash, or Mobile Payment)
                            If any of these details are missing, you must ask the customer before proceeding."""
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

4. FOR PLACING ORDERS, FOLLOW THIS EXACT PROCESS:
   a. First ask what items they would like to order and use SearchMenuTool if needed
   b. Then ask if the order is for dine-in, pickup, or delivery
   c. If dine-in, ask which table number they're sitting at
   d. If delivery, ask for the delivery address
   e. Always ask for payment method preference (Credit Card, Cash, Mobile Payment)
   f. ONLY after collecting ALL these details should you use PlaceOrderTool
   g. If the PlaceOrderTool returns a message about missing details, ask the customer for that specific information

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

# ----- Chainlit Handlers -----

@cl.on_chat_start
async def start():
    """Initialize chat session with persistent user data"""
    # Initialize order tracking
    cl.user_session.set("order_in_progress", None)
    
    # Get URL query parameters
    try:
        url_query = ""
        if hasattr(cl.context, 'request') and hasattr(cl.context.request, 'query_string'):
            url_query = cl.context.request.query_string.decode('utf-8')
            logger.debug(f"URL query from request: {url_query}")
        
        query_dict = {}
        if url_query:
            query_dict = urllib.parse.parse_qs(url_query)
        logger.debug(f"Parsed query dict: {query_dict}")
    except Exception as e:
        logger.error(f"Error parsing URL query: {e}")
        query_dict = {}

    # Extract session_id and user parameters
    session_id = query_dict.get('session_id', [None])[0]
    auth_token = query_dict.get('token', [None])[0]
    direct_user = query_dict.get('user', [None])[0]
    
    # IMPORTANT: First check for existing session in database
    # This helps maintain authentication across page reloads
    persisted_session_id, persisted_user_id, persisted_data, persisted_auth = get_persisted_auth()
    
    # Use persisted data as a fallback if URL doesn't have auth info
    if not session_id:
        session_id = persisted_session_id
        logger.debug(f"Using persisted session ID: {session_id}")
    
    if not direct_user and not auth_token and persisted_auth:
        direct_user = persisted_user_id
        logger.debug(f"Using persisted user ID: {direct_user}")

    # Verify token if present
    user_id, is_authenticated, user_data = "guest", False, {}
    
    if auth_token:
        try:
            user_id, is_authenticated, user_data = verify_auth_token(auth_token)
            logger.debug(f"Token verification result: user={user_id}, auth={is_authenticated}")
        except Exception as e:
            logger.error(f"Error verifying auth token: {e}")
            
            # Fall back to persisted data if token verification fails
            if persisted_auth:
                user_id = persisted_user_id
                is_authenticated = True
                user_data = persisted_data
                logger.debug(f"Falling back to persisted data for user: {user_id}")
    
    # Fall back to direct user if provided and token auth failed
    if not is_authenticated and direct_user:
        user_id = direct_user
        # Try to get user data from users.json
        stored_user_data = get_user_from_file(direct_user)
        if stored_user_data:
            user_data = stored_user_data
            is_authenticated = True
            logger.debug(f"Found user data for {direct_user} in users.json")
        elif persisted_auth and persisted_user_id == direct_user:
            # Fall back to persisted data if matching user
            user_data = persisted_data
            is_authenticated = True
            logger.debug(f"Using persisted data for user: {direct_user}")
        else:
            # Basic info if not in users.json or persisted
            user_data = {"username": user_id}
            is_authenticated = True
        
        logger.debug(f"Using direct username: {user_id}")
    
    # Use persisted data as final fallback
    if not is_authenticated and persisted_auth:
        user_id = persisted_user_id
        user_data = persisted_data
        is_authenticated = True
        logger.debug(f"Using persisted auth as final fallback: {user_id}")
    
    # Build context
    context = {
        "current_page": query_dict.get('tab', ['home'])[0],
        "user_id": user_id,
        "username": user_data.get('username', user_id),
        "email": user_data.get('email', ''),
        "first_name": user_data.get('first_name', ''),
        "last_name": user_data.get('last_name', ''),
        "full_name": user_data.get('full_name', ''),
        "is_authenticated": is_authenticated,
        "session_id": session_id,
        "is_floating": query_dict.get('floating', ['false'])[0].lower() == 'true'
    }
    
    # Check for active order
    order_id = query_dict.get('order_id', [None])[0]
    if order_id:
        context["active_order"] = {"id": order_id}
    
    # If authenticated, save the session to database
    if is_authenticated and user_id != "guest":
        save_user_session(user_id, context)
        logger.debug(f"Saved user session to database: {user_id}")
    
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
    except Exception as e:
        logger.error(f"Error setting up agent: {e}")

    # Send personalized welcome
    try:
        welcome_msg = ""
        if is_authenticated:
            if context.get('full_name'):
                welcome_msg = f"Welcome back, {context['full_name']}! How can I assist you today?"
            else:
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

async def process_message(message, message_id=None, source=None):
    """
    Process a user message and generate a response with improved order handling
    
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
    
    # Check if we're in the middle of an order flow
    order_in_progress = cl.user_session.get("order_in_progress", None)
    
    if order_in_progress:
        print(f"Continuing order in progress: {order_in_progress}")

        # Handle verification responses
        if order_in_progress.get("status") == "verification":
            print("Processing verification response for order")
            order_so_far = order_in_progress.get("order_so_far", {})
            msg_lower = message.lower()

            # Enhanced list of confirmation phrases for better recognition
            finalize_phrases = [
                "that's all", "thats all", "nothing else", "finalize", "place order",
                "confirm", "that is all", "looks good", "proceed", "yes", "complete",
                "finish", "done", "good to go", "fine", "perfect", "correct", "ok", 
                "okay", "sure", "yeah", "yep", "sounds good", "just that", "that's it",
                "that looks right", "place my order", "go ahead", "that's correct",
                "that will be it", "that will be all", "finalize it", "that'll be it",
                "confirm it", "confirmation", "order it", "submit", "send it", "order now"
            ]
            
            # Phrases indicating the user wants to add more items
            add_more_phrases = [
                "add", "also", "more", "another", "additional", "extra", "include", 
                "plus", "and", "with", "get", "want", "like", "would like", "i'd like",
                "include", "put in", "throw in", "add on", "as well"
            ]
            
            # Phrases indicating the user wants to cancel the order
            cancel_phrases = [
                "cancel", "never mind", "nevermind", "stop", "forget it", "don't want",
                "dont want", "remove", "delete", "clear", "no", "nope", "cancel order",
                "abandon", "scrap", "discard", "start over", "start again", "reset"
            ]

            # Check if user wants to cancel the order
            if any(phrase in msg_lower for phrase in cancel_phrases) and not any(
                phrase in msg_lower for phrase in add_more_phrases + finalize_phrases):
                # Clear order in progress
                cl.user_session.set("order_in_progress", None)
                
                # Send cancellation message
                await cl.Message(content="I've canceled your order. Is there anything else I can help you with?").send()
                return

            # Check if user is confirming the order without additions
            if any(phrase in msg_lower for phrase in finalize_phrases) and not any(phrase in msg_lower for phrase in add_more_phrases):
                # Mark order as verified before finalizing
                order_so_far["verification_complete"] = True
                
                try:
                    # Send a message to indicate we're processing
                    await cl.Message(content="Processing your order...").send()
                    
                    # Ensure the total is properly calculated and update UI
                    update_chat_ui_with_order(order_so_far)
                    
                    # Process the finalized order
                    response = OrderManager.place_order(order_so_far)
                    cl.user_session.set("order_in_progress", None)
                    user_message = OrderManager.handle_order_response(response)
                    track_message(user_message, is_user=False)
                    await cl.Message(content=user_message).send()
                    return
                except Exception as e:
                    print(f"Error finalizing order: {e}")
                    await cl.Message(content=f"I apologize, but there was an issue finalizing your order. Let me try again with a different approach.").send()
                    
                    # Try a simpler approach
                    try:
                        print("Attempting simpler direct order approach")
                        # Create a simplified order manually
                        simple_order = {
                            "items": order_so_far.get("items", [{"item_id": 2, "quantity": 1}]),
                            "delivery_type": order_so_far.get("delivery_type", "dine-in"),
                            "delivery_location": order_so_far.get("delivery_location", "Table 1"),
                            "payment_method": order_so_far.get("payment_method", "Credit Card"),
                            "verification_complete": True
                        }
                        # Process this simpler order
                        response = OrderManager.place_order(simple_order)
                        cl.user_session.set("order_in_progress", None)
                        user_message = OrderManager.handle_order_response(response)
                        track_message(user_message, is_user=False)
                        await cl.Message(content=user_message).send()
                    except Exception as backup_err:
                        print(f"Backup order approach also failed: {backup_err}")
                        await cl.Message(content="I'm very sorry, but I'm experiencing technical difficulties with our ordering system. Please try again in a moment or contact our staff directly for assistance.").send()
                    return

            # Check if user wants to add more items
            elif any(phrase in msg_lower for phrase in add_more_phrases):
                try:
                    # Find additional items
                    additional_items = []
                    
                    for menu_item in menu_items:
                        item_name_lower = menu_item["name"].lower()
                        if item_name_lower in msg_lower:
                            quantity = 1
                            for i in range(1, 10):
                                if f"{i} {item_name_lower}" in msg_lower or f"{i}{item_name_lower}" in msg_lower:
                                    quantity = i
                                    break
                            additional_items.append({
                                "item_id": menu_item["id"],
                                "quantity": quantity,
                                "special_instructions": ""
                            })
                            print(f"Adding additional item: {menu_item['name']}, quantity: {quantity}")

                    if additional_items:
                        # Add items to the order
                        order_so_far["items"].extend(additional_items)
                        updated_response = OrderManager.place_order(order_so_far)
                        cl.user_session.set("order_in_progress", updated_response)
                        user_message = OrderManager.handle_order_response(updated_response)
                        track_message(user_message, is_user=False)
                        await cl.Message(content=user_message).send()
                        return
                    else:
                        # Couldn't detect specific items - ask for clarification
                        await cl.Message(content="I'm not sure what you'd like to add. Could you specify which items you'd like to add to your order?").send()
                        return
                except Exception as e:
                    print(f"Error parsing additional items: {e}")
                    await cl.Message(content="I'm having trouble understanding what you'd like to add. Could you specify which items from our menu you'd like to add?").send()
                    return
            else:
                await cl.Message(content="I'm not sure what you'd like to do. Would you like to add more items to your order, confirm it as is, or cancel the order?").send()
                return
        
        # Handle other missing fields
        missing_field = order_in_progress.get("missing_field", "")
        order_so_far = order_in_progress.get("order_so_far", {})

        if missing_field == "delivery_type":
            # Update the delivery type based on user response
            delivery_type = ""
            msg_lower = message.lower()
            
            # Enhanced detection of delivery type
            if any(term in msg_lower for term in ["dine", "dine in", "dine-in", "eat in", "table", "sit", "dining", "restaurant"]):
                delivery_type = "dine-in"
            elif any(term in msg_lower for term in ["pickup", "pick up", "pick-up", "take out", "takeout", "take-out", "collect", "to go"]):
                delivery_type = "pickup"
            elif any(term in msg_lower for term in ["delivery", "deliver", "send", "bring", "ship", "transport"]):
                delivery_type = "delivery"

            if delivery_type:
                order_so_far["delivery_type"] = delivery_type
                response = OrderManager.place_order(order_so_far)
                if response.get("status") == "incomplete":
                    cl.user_session.set("order_in_progress", response)
                else:
                    cl.user_session.set("order_in_progress", None)
                user_message = OrderManager.handle_order_response(response)
                track_message(user_message, is_user=False)
                await cl.Message(content=user_message).send()
                return

        elif missing_field == "delivery_location":
            # Update the delivery location based on user response
            if order_so_far.get("delivery_type") == "delivery":
                order_so_far["delivery_location"] = message.strip()
                print(f"Set delivery address: {message.strip()}")
            else:
                # For dine-in: Better table number extraction
                if "table" in message.lower():
                    table_parts = message.lower().split("table")
                    if len(table_parts) > 1:
                        # Extract the first number after "table"
                        import re
                        number_match = re.search(r'\d+', table_parts[1])
                        if number_match:
                            table_number = number_match.group()
                            order_so_far["delivery_location"] = f"Table {table_number}"
                            print(f"Extracted table number from message: {order_so_far['delivery_location']}")
                        else:
                            # Use raw message if extraction fails
                            order_so_far["delivery_location"] = message.strip()
                    else:
                        # Use raw message if no table parts
                        order_so_far["delivery_location"] = message.strip()
                else:
                    # Better handling of numeric input
                    # First check if the message contains only digits
                    digits_only = ''.join(c for c in message if c.isdigit())
                    if digits_only and len(digits_only) <= 3:  # Reasonable table number
                        order_so_far["delivery_location"] = f"Table {digits_only}"
                        print(f"Interpreted as table number: {order_so_far['delivery_location']}")
                    else:
                        order_so_far["delivery_location"] = message.strip()

            # Try to continue the order processing
            response = OrderManager.place_order(order_so_far)
            
            # Update order state based on response
            if response.get("status") == "incomplete":
                cl.user_session.set("order_in_progress", response)
            else:
                # Clear order progress if completed or error
                cl.user_session.set("order_in_progress", None)
            
            # Prepare and send response message
            user_message = OrderManager.handle_order_response(response)
            track_message(user_message, is_user=False)
            await cl.Message(content=user_message).send()
            return
            
        elif missing_field == "payment_method":
            # Update the payment method based on user response - improved detection
            payment_method = ""
            msg_lower = message.lower()
            
            if any(term in msg_lower for term in ["credit", "card", "visa", "mastercard", "credit card", "debit", "amex", "american express"]):
                payment_method = "Credit Card"
            elif any(term in msg_lower for term in ["cash", "money", "notes", "bills", "currency", "dollar", "pay with cash"]):
                payment_method = "Cash"
            elif any(term in msg_lower for term in ["mobile", "phone", "apple pay", "google pay", "mobile payment", "venmo", "paypal", "electronic"]):
                payment_method = "Mobile Payment"
            else:
                # Default to Credit Card for unrecognized payment methods
                payment_method = "Credit Card"
                print(f"Unrecognized payment method '{message}', defaulting to Credit Card")
            
            # Update the order
            order_so_far["payment_method"] = payment_method
            
            # Try to complete the order
            response = OrderManager.place_order(order_so_far)
            
            # Check if order is actually complete now
            if response.get("status") == "incomplete":
                # Order still has missing fields
                cl.user_session.set("order_in_progress", response)
            else:
                # Order is complete or there was an error - either way, end the order flow
                cl.user_session.set("order_in_progress", None)
            
            # Send the response
            user_message = OrderManager.handle_order_response(response)
            track_message(user_message, is_user=False)
            await cl.Message(content=user_message).send()
            return
    
    # If we got here, either there's no order in progress or we didn't handle it directly
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
            
            # Check if this is an order response
            if "incomplete" in response.lower() and any(phrase in response.lower() for phrase in 
                ["dine-in, pickup, or delivery", "table number", "delivery address", "payment method"]):
                
                # Try to extract order info
                order_in_progress = None
                
                if "dine-in, pickup, or delivery" in response.lower():
                    order_in_progress = {
                        "status": "incomplete",
                        "missing_field": "delivery_type",
                        "order_so_far": {"items": parse_items_from_response(response)}
                    }
                elif "table number" in response.lower():
                    order_in_progress = {
                        "status": "incomplete",
                        "missing_field": "delivery_location",
                        "order_so_far": {
                            "items": parse_items_from_response(response),
                            "delivery_type": "dine-in"
                        }
                    }
                elif "delivery address" in response.lower():
                    order_in_progress = {
                        "status": "incomplete",
                        "missing_field": "delivery_location",
                        "order_so_far": {
                            "items": parse_items_from_response(response),
                            "delivery_type": "delivery"
                        }
                    }
                elif "payment method" in response.lower():
                    # Extract order details from response
                    items = parse_items_from_response(response)
                    delivery_type = parse_delivery_type(response)
                    delivery_location = parse_delivery_location(response)
                    
                    order_in_progress = {
                        "status": "incomplete",
                        "missing_field": "payment_method",
                        "order_so_far": {
                            "items": items,
                            "delivery_type": delivery_type,
                            "delivery_location": delivery_location
                        }
                    }
                
                if order_in_progress:
                    cl.user_session.set("order_in_progress", order_in_progress)
            
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

@cl.on_chat_end
def on_chat_end():
    """Save conversation history when chat ends with better error handling"""
    # Add this to the on_chat_end function to save order state
    save_order_state()

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
                        # First check if we already have this user session
                        existing_session = get_user_session(user)
                        
                        # Get current context (or create a new one)
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
                        
                        # Add token to context
                        context["token"] = token
                        
                        # Save updated context to session
                        cl.user_session.set("context", context)
                        logger.debug(f"Updated context from token: {context}")
                        
                        # Also save to database for persistence
                        save_user_session(user, context)
                        logger.debug(f"Updated user session in database: {user}")
                        
                        # If this is a new user (not in existing session), re-initialize the agent
                        if not existing_session:
                            try:
                                agent = setup_langchain_agent(context)
                                cl.user_session.set("agent", agent)
                                logger.debug("Re-initialized agent with auth context")
                                
                                # Send acknowledgment message only for new users
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
    
# Add these functions to chainlit_app/app.py

def save_user_session(user_id, user_data):
    """
    Save or update user session data in the database
    
    Args:
        user_id (str): User ID
        user_data (dict): User data to store
    
    Returns:
        bool: Success status
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Convert context to JSON string
        context_json = json.dumps(user_data)
        
        # Check if user session already exists
        c.execute('SELECT user_id FROM user_sessions WHERE user_id = ?', (user_id,))
        exists = c.fetchone() is not None
        
        if exists:
            # Update existing session
            c.execute('''UPDATE user_sessions 
                        SET username = ?, email = ?, first_name = ?, last_name = ?, 
                        token = ?, context = ?, last_active = ?
                        WHERE user_id = ?''',
                      (user_data.get('username', ''),
                       user_data.get('email', ''),
                       user_data.get('first_name', ''),
                       user_data.get('last_name', ''),
                       user_data.get('token', ''),
                       context_json,
                       datetime.now(),
                       user_id))
            logger.debug(f"Updated user session for {user_id}")
        else:
            # Create new session
            c.execute('''INSERT INTO user_sessions
                        (user_id, username, email, first_name, last_name, token, context, last_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (user_id,
                       user_data.get('username', ''),
                       user_data.get('email', ''),
                       user_data.get('first_name', ''),
                       user_data.get('last_name', ''),
                       user_data.get('token', ''),
                       context_json,
                       datetime.now()))
            logger.debug(f"Created new user session for {user_id}")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving user session: {e}")
        return False

def get_user_session(user_id):
    """
    Get user session data from the database
    
    Args:
        user_id (str): User ID
        
    Returns:
        dict: User session data or None
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''SELECT username, email, first_name, last_name, token, context
                    FROM user_sessions
                    WHERE user_id = ?''', (user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return None
            
        username, email, first_name, last_name, token, context_json = result
        
        # Parse context JSON
        try:
            context = json.loads(context_json)
        except:
            context = {}
            
        return {
            'user_id': user_id,
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'token': token,
            'context': context,
            'is_authenticated': True
        }
    except Exception as e:
        logger.error(f"Error getting user session: {e}")
        return None

def update_user_session_field(user_id, field, value):
    """
    Update a specific field in the user session
    
    Args:
        user_id (str): User ID
        field (str): Field name to update
        value: New value
        
    Returns:
        bool: Success status
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Validate field name to prevent SQL injection
        valid_fields = ['username', 'email', 'first_name', 'last_name', 'token', 'context']
        if field not in valid_fields:
            logger.error(f"Invalid field name: {field}")
            conn.close()
            return False
            
        # Special handling for context field (JSON)
        if field == 'context':
            value = json.dumps(value)
            
        # Update the field
        query = f"UPDATE user_sessions SET {field} = ?, last_active = ? WHERE user_id = ?"
        c.execute(query, (value, datetime.now(), user_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating user session field: {e}")
        return False
    

def parse_items_from_response(response):
    """
    Extract order items mentioned in a response with improved recognition.
    
    Args:
        response (str): The agent's response text
        
    Returns:
        list: List of item dictionaries
    """
    items = []
    
    # Convert response to lowercase for case-insensitive matching
    response_lower = response.lower()
    
    # First, handle the special case of "classic latte" (or other classic items)
    if "classic" in response_lower:
        for menu_item in menu_items:
            item_name_lower = menu_item["name"].lower()
            if "latte" == item_name_lower and "classic latte" in response_lower:
                # Found a classic latte reference
                items.append({
                    "item_id": menu_item["id"],
                    "quantity": 1,
                    "special_instructions": "Classic style"
                })
                print(f"Found classic version of: {menu_item['name']}")
                # Continue searching for other items
    
    # Now do the regular item search for any items not handled by the classic case
    for menu_item in menu_items:
        item_name_lower = menu_item["name"].lower()
        
        # Skip if we already added this item as a "classic" version
        if item_name_lower == "latte" and any(item["item_id"] == menu_item["id"] for item in items):
            continue
            
        # Try different variations of the item name
        variations = [
            item_name_lower,
            item_name_lower.replace(" ", ""),
            item_name_lower + "s",  # plural form
        ]
        
        found = False
        for variation in variations:
            if variation in response_lower:
                found = True
                break
                
        if found:
            # Try to extract quantity
            quantity = 1
            
            # Look for numeric quantities near the item name
            import re
            quantity_matches = re.findall(r'(\d+)\s*(?:x\s*)?(?:' + re.escape(item_name_lower) + r')', response_lower)
            if quantity_matches:
                try:
                    quantity = int(quantity_matches[0])
                except:
                    pass
            
            # Add the item
            items.append({
                "item_id": menu_item["id"],
                "quantity": quantity,
                "special_instructions": ""
            })
            print(f"Extracted item from response: {menu_item['name']}, quantity: {quantity}")
    
    if not items:
        # Default item if we couldn't find any
        print("No items found in response, using default item")
        if menu_items and len(menu_items) > 0:
            # Try to find a latte as default if mentioned
            if "latte" in response_lower:
                for menu_item in menu_items:
                    if menu_item["name"].lower() == "latte":
                        items.append({
                            "item_id": menu_item["id"],
                            "quantity": 1,
                            "special_instructions": ""
                        })
                        break
            # Otherwise use first menu item
            if not items:
                items.append({
                    "item_id": menu_items[0]["id"],
                    "quantity": 1,
                    "special_instructions": ""
                })
        else:
            # Fallback if menu_items is empty
            items.append({
                "item_id": 1,  # Assuming ID 1 is a valid item
                "quantity": 1,
                "special_instructions": ""
            })
    
    return items

def parse_delivery_type(response):
    """
    Extract delivery type from a response with improved recognition.
    
    Args:
        response (str): The agent's response text
        
    Returns:
        str: Detected delivery type
    """
    response_lower = response.lower()
    
    # Enhanced dictionary of delivery type keywords
    delivery_types = {
        "dine-in": ["dine-in", "dine in", "dining", "table", "sit", "restaurant", "eating in"],
        "pickup": ["pickup", "pick up", "pick-up", "takeout", "take out", "take-out", "to go", "collect"],
        "delivery": ["delivery", "deliver", "delivered", "bringing", "send to", "bring to", "bringing to"]
    }
    
    # Check for each type
    for dtype, keywords in delivery_types.items():
        if any(keyword in response_lower for keyword in keywords):
            return dtype
    
    # Look for strong indicators through context
    if "table number" in response_lower or "which table" in response_lower:
        return "dine-in"
    elif "pickup counter" in response_lower or "counter" in response_lower:
        return "pickup"
    elif "address" in response_lower or "location" in response_lower:
        return "delivery"
    
    return "dine-in"  # Default

def parse_delivery_location(response):
    """
    Extract delivery location from a response with improved extraction.
    
    Args:
        response (str): The agent's response text
        
    Returns:
        str: Detected delivery location
    """
    response_lower = response.lower()
    
    # Check if this is a dine-in order
    if "table" in response_lower:
        # Try to extract table number using regex
        import re
        table_matches = re.findall(r'table\s*(\d+)', response_lower)
        if table_matches:
            return f"Table {table_matches[0]}"
        
        # Try to find any number after "table"
        words = response_lower.split()
        for i, word in enumerate(words):
            if word == "table" and i+1 < len(words) and words[i+1].isdigit():
                return f"Table {words[i+1]}"
    
    # Check if this is a delivery order
    elif "address" in response_lower or "deliver to" in response_lower:
        # Try to extract an address
        import re
        # Look for common address patterns
        address_pattern = r'(\d+\s+[a-zA-Z\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|place|pl|blvd))'
        address_matches = re.findall(address_pattern, response_lower, re.IGNORECASE)
        if address_matches:
            return address_matches[0].capitalize()
    
    # Default values based on likely order type
    if "dine-in" in response_lower or "table" in response_lower:
        return "Table 1"  # Default table
    elif "delivery" in response_lower:
        return "Address needed"  # Placeholder for delivery
    elif "pickup" in response_lower or "take" in response_lower:
        return "Pickup Counter"  # Default for pickup
    
    return "Table 1"  # Default

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

# And add this function to save/restore order state if needed
def save_order_state():
    """Save current order state to database for persistence"""
    try:
        order_in_progress = cl.user_session.get("order_in_progress")
        session_id = cl.user_session.get("context", {}).get("session_id")
        
        if order_in_progress and session_id:
            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Save order state
            c.execute('''INSERT OR REPLACE INTO user_state
                        (session_id, state_type, state_data, updated_at)
                        VALUES (?, ?, ?, ?)''',
                     (session_id, 
                      "order_in_progress", 
                      json.dumps(order_in_progress), 
                      datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            print(f"Saved order state for session: {session_id}")
    except Exception as e:
        print(f"Error saving order state: {e}")

def restore_order_state():
    """Restore order state from database if available"""
    try:
        session_id = cl.user_session.get("context", {}).get("session_id")
        
        if session_id:
            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Get order state
            c.execute('''SELECT state_data FROM user_state
                        WHERE session_id = ? AND state_type = ?''',
                     (session_id, "order_in_progress"))
            
            result = c.fetchone()
            conn.close()
            
            if result:
                order_data = json.loads(result[0])
                cl.user_session.set("order_in_progress", order_data)
                print(f"Restored order state for session: {session_id}")
                return True
    except Exception as e:
        print(f"Error restoring order state: {e}")
    
    return False

def get_persisted_auth():
    """
    Get persisted authentication info from database
    
    Returns:
        tuple: (session_id, user_id, user_data, is_authenticated)
    """
    try:
        # First try to get auth from current request
        if hasattr(cl.context, 'request'):
            cookies = getattr(cl.context.request, 'cookies', {})
            if hasattr(cookies, 'get'):
                session_id = cookies.get('session_id')
                auth_token = cookies.get('auth_token')
                
                if session_id and auth_token:
                    logger.debug(f"Found auth in cookies: {session_id}")
                    user_id, is_auth, user_data = verify_auth_token(auth_token)
                    if is_auth:
                        return session_id, user_id, user_data, is_auth
        
        # If no session in cookies, check database for active sessions
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get most recent active session
        c.execute('''SELECT user_id, context FROM user_sessions
                     ORDER BY last_active DESC LIMIT 1''')
        result = c.fetchone()
        conn.close()
        
        if result:
            user_id, context_json = result
            try:
                context = json.loads(context_json)
                logger.debug(f"Found persisted session for user: {user_id}")
                return context.get('session_id', str(uuid.uuid4())), user_id, context, True
            except:
                logger.warning(f"Invalid context JSON for user: {user_id}")
                
    except Exception as e:
        logger.error(f"Error getting persisted auth: {e}")
    
    return str(uuid.uuid4()), "guest", {}, False


def update_chat_ui_with_order(order_data):
    """
    Helper function to update the chat UI with current order data.
    Uses the exact structure from the original code.
    
    Args:
        order_data (dict): Order data to display
    """
    try:
        # Calculate total if not already present
        if "total" not in order_data or order_data["total"] == 0:
            total = 0
            for item in order_data.get("items", []):
                item_id = item.get("item_id")
                quantity = item.get("quantity", 1)
                for menu_item in menu_items:
                    if menu_item["id"] == item_id:
                        total += menu_item.get("price", 0) * quantity
                        break
            order_data["total"] = total
            print(f"Calculated total: {total} for order: {order_data.get('id', 'unknown')}")
            
        # Create cart-friendly format exactly as in original code
        cart_items = []
        for item in order_data["items"]:
            item_id = item.get("item_id")
            quantity = item.get("quantity", 1)
            
            # Find menu item details
            menu_item = next((m for m in menu_items if m["id"] == item_id), None)
            if menu_item:
                cart_items.append({
                    "id": item_id,
                    "name": menu_item["name"],
                    "price": menu_item.get("price", 0),
                    "quantity": quantity,
                    "special_instructions": item.get("special_instructions", "")
                })
        
        # Create cart-specific message - add the total to cart_update
        cart_update = {
            "type": "cart_update",
            "items": cart_items,
            "order_id": order_data.get("id", str(uuid.uuid4())),
            "username": order_data.get("username", "guest"),
            "user_id": order_data.get("user_id", "guest"),
            "total": order_data.get("total", 0)  # Important: Include the total here
        }
        
        # METHOD 1: Try Socket.IO first
        try:
            import socketio
            sio = socketio.Client()
            sio.connect(DASHBOARD_URL)
            # Send both general order update and specific cart update
            print(f"Sending via Socket.IO. order_data total: {order_data.get('total')}")
            sio.emit('order_update', order_data)
            sio.emit('cart_update', cart_update)
            sio.disconnect()
            print("Order sent via Socket.IO")
        except Exception as e:
            print(f"Error sending order via Socket.IO: {e}")
        
        # METHOD 2: Try parent window messaging
        try:
            # Send order update to parent window
            print(f"Sending to parent window. order_data total: {order_data.get('total')}")
            cl.send_to_parent({
                "type": "order_update", 
                "order": order_data
            })
            
            # CRITICAL: Also send cart_update event specifically
            cl.send_to_parent({
                "type": "cart_update",
                "items": cart_items,
                "order_id": order_data.get("id", "unknown"),
                "total": order_data.get("total", 0)  # Important: Include the total here
            })
            
            print("Order notification sent to parent")
        except Exception as e:
            print(f"Error sending order via cl.send_to_parent: {e}")
            
        # METHOD 3: Try REST API approach as a fallback
        try:
            # Call the place-order API endpoint
            order_response = requests.post(
                f"{DASHBOARD_URL}/api/place-order", 
                json=order_data,
                timeout=5
            )
            
            # Call the update-cart API endpoint
            cart_response = requests.post(
                f"{DASHBOARD_URL}/api/update-cart", 
                json=cart_update,
                timeout=5
            )
            
            if order_response.status_code == 200 or cart_response.status_code == 200:
                print(f"Order API response: {order_response.status_code}, Cart API response: {cart_response.status_code}")
        except Exception as api_err:
            print(f"Error calling REST API: {api_err}")
            
    except Exception as e:
        print(f"Error in update_chat_ui_with_order: {e}")

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