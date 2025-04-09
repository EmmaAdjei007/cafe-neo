"""
Enhanced Chainlit integration for Neo Cafe with reliable communication and intelligent processing
"""
import os
import sys
import json
import time
import urllib.parse
import requests
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import re

import chainlit as cl
from chainlit.element import Element

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import state management classes
from chainlit_app.states import VoiceState, OrderState, RobotState

# Constants
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:8050')
ROBOT_SIMULATOR_URL = os.environ.get('ROBOT_SIMULATOR_URL', 'http://localhost:8051')

# Global variables
menu_items = []  # Will be populated in the on_chat_start function
is_floating_chat = False  # Flag to check if running in floating mode
processed_message_ids = set()  # Track processed message IDs to avoid duplicates

# ----- Helper Functions -----

def analyze_intent_rule_based(message: str) -> Dict:
    """
    Analyze user intent using rule-based approach
    
    Args:
        message (str): User message
        
    Returns:
        dict: Intent analysis
    """
    message_lower = message.lower()
    
    # Initialize result
    result = {
        "intent": "casual",
        "entities": {},
        "confidence": 0.7,
        "navigate_to": None
    }
    
    # Check for greetings
    greeting_patterns = ["hello", "hi ", "hey", "greetings", "morning", "afternoon", "evening"]
    if any(pattern in message_lower for pattern in greeting_patterns):
        result["intent"] = "greeting"
        result["confidence"] = 0.9
    
    # Check for menu-related intents
    menu_patterns = ["menu", "what do you have", "what do you offer", "show me", "what can i order", "what's available"]
    if any(pattern in message_lower for pattern in menu_patterns):
        result["intent"] = "menu"
        result["confidence"] = 0.85
        result["navigate_to"] = "menu"
    
    # Check for specific menu items
    menu_items_global = ["coffee", "latte", "espresso", "cappuccino", "mocha", "tea", "sandwich", "croissant", "muffin", "pastry"]
    found_items = [item for item in menu_items_global if item in message_lower]
    if found_items:
        result["entities"]["menu_items"] = found_items
        if "order" in message_lower or any(word in message_lower for word in ["get", "have", "want", "like", "give"]):
            result["intent"] = "order"
            result["confidence"] = 0.8
    
    # Check for ordering intent
    order_patterns = ["order", "buy", "purchase", "get me", "i'd like", "i want", "i'll have", "add to my order", "add to cart"]
    if any(pattern in message_lower for pattern in order_patterns):
        result["intent"] = "order"
        result["confidence"] = 0.85
        result["navigate_to"] = "orders"
    
    # Check for order status intent
    status_patterns = ["status", "where is my order", "how long", "track", "follow", "my order"]
    if any(pattern in message_lower for pattern in status_patterns):
        result["intent"] = "order_status"
        result["confidence"] = 0.8
        result["navigate_to"] = "orders"
    
    # Check for robot status intent
    robot_patterns = ["robot", "delivery", "deliveries", "where is the robot", "delivery status"]
    if any(pattern in message_lower for pattern in robot_patterns):
        result["intent"] = "robot_status"
        result["confidence"] = 0.8
        result["navigate_to"] = "delivery"
    
    # Check for profile intent
    profile_patterns = ["profile", "account", "my information", "my details", "settings"]
    if any(pattern in message_lower for pattern in profile_patterns):
        result["intent"] = "profile"
        result["confidence"] = 0.85
        result["navigate_to"] = "profile"
    
    # Check for help intent
    help_patterns = ["help", "support", "assist", "how do i", "how to", "guide"]
    if any(pattern in message_lower for pattern in help_patterns):
        result["intent"] = "help"
        result["confidence"] = 0.8
    
    # Check for hours intent
    hours_patterns = ["hours", "open", "close", "when", "time", "operating"]
    if any(pattern in message_lower for pattern in hours_patterns):
        result["intent"] = "hours"
        result["confidence"] = 0.8
    
    # Extract quantities
    quantity_matches = re.findall(r'(\d+)\s+([a-zA-Z]+)', message_lower)
    if quantity_matches:
        quantities = {}
        for quantity, item in quantity_matches:
            quantities[item] = int(quantity)
        result["entities"]["quantity"] = quantities
    
    return result

def get_default_response(intent_data: Dict) -> str:
    """
    Get a default response based on intent
    
    Args:
        intent_data (dict): Intent analysis
        
    Returns:
        str: Default response
    """
    intent = intent_data.get("intent", "casual")
    
    # Default responses by intent
    responses = {
        "greeting": "👋 Hello! Welcome to Neo Cafe. How can I help you today?",
        "menu": "📋 I'd be happy to show you our menu. Is there something specific you're looking for or would you like to see the full menu?",
        "order": "🛒 I'd be happy to help you place an order. What would you like to have?",
        "order_status": "📊 Let me check on the status of your order for you. Do you have an order ID or would you like to check your most recent order?",
        "robot_status": "🤖 I'll check on the robot delivery status for you. One moment please.",
        "help": "❓ I'm here to help! You can ask about our menu, place orders, track deliveries, or learn about our coffee shop. What would you like help with?",
        "profile": "👤 I can help you with your profile information. Would you like to see your account details, order history, or preferences?",
        "hours": "🕒 Neo Cafe is open Monday through Friday from 7:00 AM to 8:00 PM, and weekends from 8:00 AM to 6:00 PM.",
        "navigation": "🧭 I'll help you navigate to that section of the app.",
        "casual": "I'm here to help with your Neo Cafe experience. You can ask about our menu, place an order, or check delivery status."
    }
    
    return responses.get(intent, responses["casual"])

# ----- Chainlit Event Handlers -----

@cl.on_chat_start
async def start():
    """Initialize chat session"""
    global menu_items, is_floating_chat
    
    # Load menu data
    menu_items = await load_menu_data()
    
    # Initialize state objects
    voice_state = VoiceState()
    order_state = OrderState()
    robot_state = RobotState()
    
    # Store state in user session
    cl.user_session.set("voice_state", voice_state)
    cl.user_session.set("order_state", order_state)
    cl.user_session.set("robot_state", robot_state)
    
    # Parse URL query parameters
    query = cl.context.session.get('url_query')
    query_dict = {}
    current_page = "home"
    
    if query:
        query_dict = urllib.parse.parse_qs(query) if isinstance(query, str) else query
        
        # Extract values from query parameters
        if 'tab' in query_dict:
            current_page = query_dict['tab'][0]
        
        # Check if this is a floating chat instance
        if 'floating' in query_dict:
            is_floating_chat = query_dict['floating'][0].lower() == 'true'
    
    # Set initial context
    is_logged_in = 'user' in query_dict
    has_active_order = 'order_id' in query_dict
    order_id = query_dict.get('order_id', [''])[0] if query_dict.get('order_id') else ''
    
    # Store context in session
    context = {
        "is_logged_in": is_logged_in,
        "current_page": current_page,
        "has_active_order": has_active_order,
        "order_id": order_id,
        "order_items": [],
        "is_floating": is_floating_chat
    }
    cl.user_session.set("context", context)
    
    # Personalized welcome based on context
    welcome_message = ""
    
    if is_logged_in:
        username = query_dict.get('user', ['customer'])[0] if query_dict.get('user') else 'customer'
        welcome_message = f"👋 Welcome back, {username}! I'm BaristaBot, your Neo Cafe assistant."
    else:
        welcome_message = "👋 Welcome to Neo Cafe! I'm BaristaBot, your virtual barista assistant."
    
    # Add context-specific welcome additions
    if current_page == "menu":
        welcome_message += " I see you're browsing our menu. Can I help you find something specific or make a recommendation?"
    elif current_page == "order":
        welcome_message += " I can help you place an order. Just tell me what you'd like to have!"
    elif current_page == "status":
        if has_active_order:
            welcome_message += f" I see you're tracking order {order_id}. I can provide updates on its status."
        else:
            welcome_message += " I can help you track your orders. Do you have an order you'd like to check on?"
    else:
        welcome_message += " I can help you with our menu, placing orders, tracking deliveries, and answering questions."
    
    # Keep welcome message more concise for floating chat
    if is_floating_chat:
        welcome_message = welcome_message.split(".")[0] + "."
    
    await cl.Message(content=welcome_message).send()
    
    # Only show quick menu if not in a specific context and not in floating chat
    if current_page == "home" and not is_floating_chat:
        quick_menu = """
**📋 Quick Actions**
* Browse the menu
* Place an order
* Check order status
* Track delivery
* Learn about our coffee

Feel free to ask in natural language - I'm here to help!
"""
        await cl.Message(content=quick_menu).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages from the chat interface"""
    await process_message(message.content, message_id=message.id)

# Window messaging is a completely separate channel from normal messages
@cl.on_window_message
async def handle_window_message(message):
    """
    Handle messages sent from the parent window (Dash app)
    
    Args:
        message: Message content (can be string or dictionary)
    """
    print(f"Received window message: {message}")
    
    # Extract the actual message content
    actual_message = None
    message_id = f"window_{time.time()}"  # Create a unique ID for window messages
    
    # Check type of message
    if isinstance(message, dict):
        # Dictionary format (most common from our JS code)
        if 'message' in message:
            actual_message = message['message']
            # If there's an ID in the message, use it
            if 'id' in message:
                message_id = f"window_{message['id']}"
        elif 'kind' in message and message.get('kind') == 'user_message':
            if 'data' in message and 'content' in message['data']:
                actual_message = message['data']['content']
    elif isinstance(message, str):
        # Direct string format
        actual_message = message
    
    # If we extracted a valid message, process it
    if actual_message:
        print(f"Extracted message from window: {actual_message}")
        await process_message(actual_message, message_id=message_id, source="window")
    else:
        # Could not extract a message, log the error
        print(f"Could not extract message from: {message}")

async def process_message(message, message_id=None, source=None):
    """
    Process user message and generate response
    
    Args:
        message (str): User message
        message_id (str, optional): Unique ID for this message
        source (str, optional): Source of the message (window, user)
    """
    global processed_message_ids
    
    # Generate a message ID if none provided
    if not message_id:
        message_id = f"msg_{time.time()}"
    
    # Check if this message has already been processed (prevent duplicates)
    if message_id in processed_message_ids:
        print(f"Skipping already processed message: {message_id}")
        return
    
    # Mark as processed
    processed_message_ids.add(message_id)
    
    # Log the processing
    print(f"Processing message: '{message}' (ID: {message_id}, Source: {source})")
    
    # Get state objects and context
    voice_state = cl.user_session.get("voice_state")
    order_state = cl.user_session.get("order_state")
    robot_state = cl.user_session.get("robot_state")
    context = cl.user_session.get("context", {})
    is_floating_chat = context.get("is_floating", False)
    
    # Initialize if not present
    if not order_state:
        order_state = OrderState()
        cl.user_session.set("order_state", order_state)
    
    if not robot_state:
        robot_state = RobotState()
        cl.user_session.set("robot_state", robot_state)
    
    # Update context with current order information
    context["order_items"] = [item["name"] for item in order_state.items]
    context["has_active_order"] = order_state.order_confirmed
    context["order_id"] = order_state.order_id
    cl.user_session.set("context", context)
    
    # Check if voice mode is enabled
    should_speak = voice_state and voice_state.is_enabled()
    
    # Analyze user intent using rule-based approach (more reliable than OpenAI for this use case)
    intent_data = analyze_intent_rule_based(message)
    
    # Get response based on intent
    response = get_default_response(intent_data)
    
    # Handle navigation if needed
    navigate_to = intent_data.get("navigate_to")
    if navigate_to:
        # Only include navigation message if we're going to a different page
        if navigate_to != context.get("current_page"):
            # Add navigation text to response
            response += f"\n\nI'll take you to the {navigate_to} section."
            
            # Try to send navigation event to parent window
            try:
                print(f"Attempting to navigate to: {navigate_to}")
                await cl.send_to_parent({
                    "type": "navigation",
                    "destination": navigate_to
                })
                
                # Also try the older post_to_parent method
                try:
                    cl.context.session.post_to_parent({
                        "type": "navigation",
                        "destination": navigate_to
                    })
                except Exception as e:
                    print(f"Could not use post_to_parent: {e}")
                    
            except Exception as e:
                print(f"Error sending navigation to parent: {e}")
    
    # Send the response
    response_msg = await cl.Message(content=response).send()
    
    # If voice is enabled, speak the response
    if should_speak:
        voice_state.speak_text(response.replace("*", ""))
    
    # Handle specific intents with actions
    intent = intent_data.get("intent")
    
    # Process menu requests
    if intent == "menu":
        menu_category = None
        if "entities" in intent_data and "menu_category" in intent_data["entities"]:
            menu_category = intent_data["entities"]["menu_category"]
        
        # For floating chat, show a more compact menu
        if is_floating_chat:
            await show_compact_menu(category=menu_category)
        else:
            await show_menu(category=menu_category)
    
    # Process order requests
    elif intent == "order":
        # Check for specific menu items mentioned
        if "entities" in intent_data and "menu_items" in intent_data["entities"]:
            menu_items_to_add = intent_data["entities"]["menu_items"]
            quantities = intent_data.get("entities", {}).get("quantity", {})
            
            added_items = []
            for item_name in menu_items_to_add:
                # Default to quantity 1 if not specified
                quantity = quantities.get(item_name, 1)
                result = order_state.add_item(item_name, quantity)
                
                # Only add to confirmation if successfully added
                if "added" in result.lower():
                    added_items.append(f"{quantity}x {item_name}")
            
            # If items were added, show confirmation and order summary
            if added_items:
                items_text = ", ".join(added_items)
                await cl.Message(content=f"🛒 I've added {items_text} to your order.").send()
                await display_order_summary()
                
                # Try to notify parent window about order update
                try:
                    await cl.send_to_parent({
                        "type": "orderUpdate",
                        "order": order_state.get_order_data()
                    })
                except Exception as e:
                    print(f"Error sending order update to parent: {e}")
    
    # Process order status requests
    elif intent == "order_status":
        if order_state.order_confirmed and order_state.order_id:
            # Show order status
            status_msg = robot_state.format_status_message(order_state.order_id)
            await cl.Message(content=status_msg).send()
        else:
            # No active order
            await cl.Message(content="You don't have any active orders to track. Would you like to place an order?").send()
    
    # Process robot status requests
    elif intent == "robot_status":
        # Show general robot status
        status_msg = robot_state.format_status_message()
        await cl.Message(content=status_msg).send()
    
    # Process help requests
    elif intent == "help":
        # Show help based on context
        help_text = """
# 📚 BaristaBot Help

## 🛍️ What I Can Do:
- Show you our menu and make recommendations
- Help you place and customize orders
- Track your order status and delivery
- Provide information about Neo Cafe
- Answer questions about our products

## 💬 Try These Examples:
- "I'd like to order a latte and a croissant"
- "What's on the menu?"
- "Where's my order?"
- "Tell me about your coffee beans"
- "When are you open?"
- "Take me to my profile"

Just chat naturally - I understand regular language!
"""
        await cl.Message(content=help_text).send()

# ----- Data Management Functions -----

async def load_menu_data():
    """
    Load menu data from menu.json
    
    Returns:
        list: Menu items
    """
    try:
        # Try multiple possible paths for the menu file
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'data', 'seed_data', 'menu.json'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'seed_data', 'menu.json'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'menu.json')
        ]
        
        # Try each path
        for menu_path in possible_paths:
            if os.path.exists(menu_path):
                print(f"Found menu file at: {menu_path}")
                with open(menu_path, 'r') as f:
                    return json.load(f)
        
        # If we get here, no file was found
        print("Warning: Could not find menu.json in any expected location")
        
        # Return a fallback menu with some basic items
        return [
            {
                "id": 1,
                "name": "Espresso",
                "description": "Rich and complex espresso with notes of cocoa and caramel.",
                "price": 2.95,
                "category": "coffee",
                "popular": True
            },
            {
                "id": 2,
                "name": "Latte",
                "description": "Smooth espresso with steamed milk and a light layer of foam.",
                "price": 4.50,
                "category": "coffee",
                "popular": True
            },
            {
                "id": 3,
                "name": "Cappuccino",
                "description": "Espresso with steamed milk and a deep layer of foam.",
                "price": 4.25,
                "category": "coffee",
                "popular": True
            },
            {
                "id": 7,
                "name": "Croissant",
                "description": "Buttery, flaky pastry made with pure butter.",
                "price": 3.25,
                "category": "pastries",
                "popular": True
            }
        ]
            
    except Exception as e:
        print(f"Error loading menu data: {e}")
        return []

# ----- Menu Display Functions -----

async def show_menu(category=None):
    """
    Show the menu, optionally filtered by category
    
    Args:
        category (str, optional): Category to filter by
    """
    await cl.Message(content="📋 **Neo Cafe Menu**").send()
    
    # Group menu items by category
    items_by_category = {}
    for item in menu_items:
        item_category = item.get("category", "Other")
        if item_category not in items_by_category:
            items_by_category[item_category] = []
        items_by_category[item_category].append(item)
    
    # If category specified, only show that category
    categories_to_show = [category] if category and category in items_by_category else items_by_category.keys()
    
    # Show ordering instructions
    ordering_instructions = """
### 📝 How to Order:
- Say "I'd like [item]" to add to your order
- Ask me about any item for more information
- Say "View my order" to see your current selections
"""
    await cl.Message(content=ordering_instructions).send()
    
    # Display items by category
    for category in categories_to_show:
        # Capitalize category name and add emoji
        category_emoji = "☕"
        if "coffee" in category.lower():
            category_emoji = "☕"
        elif "tea" in category.lower():
            category_emoji = "🍵"
        elif "pastry" in category.lower() or "bakery" in category.lower():
            category_emoji = "🥐"
        elif "breakfast" in category.lower():
            category_emoji = "🍳"
        elif "sandwich" in category.lower():
            category_emoji = "🥪"
        elif "dessert" in category.lower():
            category_emoji = "🍰"
        elif "drink" in category.lower() or "beverage" in category.lower():
            category_emoji = "🥤"
        
        category_name = category.capitalize()
        
        await cl.Message(content=f"## {category_emoji} {category_name}").send()
        
        # Show items in a compact list format
        item_messages = []
        items = items_by_category[category]
        
        # Create a formatted list for each item
        for item in items:
            item_msg = f"### {item['name']} - ${item['price']:.2f}\n"
            item_msg += f"{item.get('description', '')}\n"
            if item.get('popular'):
                item_msg += "**Popular!** ⭐\n"
            
            item_messages.append(item_msg)
        
        # Send items in groups to reduce message count
        for i in range(0, len(item_messages), 3):
            group = item_messages[i:i+3]
            await cl.Message(content="\n\n".join(group)).send()

async def show_compact_menu(category=None):
    """
    Show a compact menu version for the floating chat
    
    Args:
        category (str, optional): Category to filter by
    """
    await cl.Message(content="📋 **Neo Cafe Menu**").send()
    
    # Group menu items by category
    items_by_category = {}
    for item in menu_items:
        item_category = item.get("category", "Other")
        if item_category not in items_by_category:
            items_by_category[item_category] = []
        items_by_category[item_category].append(item)
    
    # If category specified, only show that category
    categories_to_show = [category] if category and category in items_by_category else items_by_category.keys()
    
    # For each category, create a compact display
    for category in categories_to_show:
        category_name = category.capitalize()
        
        # Create a compact list of items in this category
        items = items_by_category[category]
        items_text = f"## {category_name}\n\n"
        
        for item in items:
            # Compact item display with popularity mark
            popular_mark = "⭐ " if item.get("popular") else ""
            items_text += f"• **{popular_mark}{item['name']}** - ${item['price']:.2f}\n"
        
        # Add simple ordering instructions
        items_text += "\n*Say 'I'd like [item]' to order*"
        
        # Send as a single message
        await cl.Message(content=items_text).send()

async def display_order_summary():
    """Display the current order summary"""
    order_state = cl.user_session.get("order_state")
    if not order_state:
        return
    
    # Check if there are items in the order
    if not order_state.items:
        await cl.Message(content="🛒 Your order is currently empty. Browse our menu to add items!").send()
        await cl.Message(content="Would you like to see our menu?").send()
        return
    
    # Create summary header
    summary = "🛍️ **Your Order Summary**\n\n"
    
    # Add items
    for item in order_state.items:
        name = item.get('name', 'Unknown item')
        price = item.get('price', 0)
        quantity = item.get('quantity', 1)
        subtotal = price * quantity
        summary += f"- {quantity}x {name} (${subtotal:.2f})\n"
    
    # Add special instructions if any
    if order_state.special_instructions:
        summary += f"\n**Special Instructions:** {order_state.special_instructions}\n"
    
    # Add delivery location and payment method
    summary += f"\n**Delivery Location:** {order_state.delivery_location}\n"
    summary += f"**Payment Method:** {order_state.payment_method}\n"
    
    # Add total
    summary += f"**Total:** ${order_state.total_price:.2f}"
    
    # Add order status if confirmed
    if order_state.order_confirmed:
        summary += f"\n\n**Status:** Confirmed ✅ (Order ID: {order_state.order_id})"
        
    # Send the summary
    await cl.Message(content=summary).send()
    
    # Add suggested next actions based on order state
    if not order_state.order_confirmed:
        next_actions = """
**What would you like to do next?**
- "Confirm my order"
- "Add more items"
- "Clear my order"
- "Add special instructions: [your notes]"
- "Deliver to [location]"
"""
        await cl.Message(content=next_actions).send()
    else:
        # Order is already confirmed
        tracking_actions = """
**Order Confirmed!**
- "Track my order"
- "Start a new order"
"""
        await cl.Message(content=tracking_actions).send()

# ----- Chainlit Set Starters -----

@cl.set_starters
async def set_starters():
    """Define starter messages for the chat"""
    return [
        cl.Starter(
            label="☕️ Show Menu",
            message="Show me the menu",
            icon="🍽️",
        ),
        cl.Starter(
            label="⭐ What's Popular?",
            message="What are your most popular items?",
            icon="⭐",
        ),
        cl.Starter(
            label="🛍️ Place an Order",
            message="I'd like to place an order",
            icon="☕",
        ),
        cl.Starter(
            label="🤖 Track Delivery",
            message="Where is my order?",
            icon="🤖",
        ),
        cl.Starter(
            label="❓ Help",
            message="What can you help me with?",
            icon="❓",
        ),
    ]