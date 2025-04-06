# # File: chainlit_app/app.py (Updated with OpenAI integration)

# """
# Enhanced Chainlit integration for Neo Cafe with OpenAI-powered intelligence
# """
# import os
# import sys
# import json
# import time
# import urllib.parse
# import requests
# import asyncio
# import threading
# from typing import Dict, List, Optional
# from datetime import datetime
# import openai
# import re

# import chainlit as cl
# from chainlit.element import Element

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# # Import state management classes
# from chainlit_app.states import VoiceState, OrderState, RobotState

# # Constants
# DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:8050')
# ROBOT_SIMULATOR_URL = os.environ.get('ROBOT_SIMULATOR_URL', 'http://localhost:8051')
# OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# # Initialize OpenAI API
# openai.api_key = OPENAI_API_KEY

# # Global variables
# menu_items = []  # Will be populated in the on_chat_start function

# # ----- OpenAI Integration Functions -----

# async def analyze_intent(message: str) -> Dict:
#     """
#     Use OpenAI to analyze user intent from their message
    
#     Args:
#         message (str): User message
        
#     Returns:
#         dict: Intent analysis
#     """
#     if not OPENAI_API_KEY:
#         # Fallback to rule-based intent detection if API key not available
#         return analyze_intent_rule_based(message)
    
#     try:
#         system_prompt = """
#         You are an assistant for a coffee shop application called Neo Cafe.
#         Analyze the customer's message and identify their intent.
        
#         Possible intents include:
#         - greeting: Customer is saying hello
#         - menu: Customer wants to see the menu or specific menu items
#         - order: Customer wants to place an order or add items to their order
#         - order_status: Customer wants to check on their order
#         - robot_status: Customer wants to check the robot delivery status
#         - help: Customer needs help or information
#         - profile: Customer wants to access their profile
#         - hours: Customer wants to know business hours
#         - navigation: Customer wants to navigate to a specific part of the app
#         - casual: General casual conversation
        
#         Also extract any specific entities mentioned such as:
#         - menu_items: Specific items from the menu
#         - order_id: Any order identification
#         - location: Any mentioned location
#         - quantity: Any mentioned quantities
        
#         Respond with a JSON structure containing:
#         {
#             "intent": "one of the intent types above",
#             "entities": {"entity_type": "entity_value"},
#             "confidence": 0.0 to 1.0,
#             "navigate_to": null or page name (e.g., "menu", "orders", "profile", etc.)
#         }
#         """
        
#         response = await openai.Completion.acreate(
#             model="gpt-3.5-turbo",
#             prompt=system_prompt,
#             temperature=0.7,
#             max_tokens=150
#         )

        
#         content = response.choices[0].message.content
        
#         # Extract JSON from response
#         json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
#         if json_match:
#             content = json_match.group(1)
        
#         intent_data = json.loads(content)
#         return intent_data
    
#     except Exception as e:
#         print(f"Error analyzing intent with OpenAI: {e}")
#         # Fallback to rule-based analysis
#         return analyze_intent_rule_based(message)

# def analyze_intent_rule_based(message: str) -> Dict:
#     """
#     Analyze user intent using rule-based approach (fallback when OpenAI is unavailable)
    
#     Args:
#         message (str): User message
        
#     Returns:
#         dict: Intent analysis
#     """
#     message_lower = message.lower()
    
#     # Initialize result
#     result = {
#         "intent": "casual",
#         "entities": {},
#         "confidence": 0.7,
#         "navigate_to": None
#     }
    
#     # Check for greetings
#     greeting_patterns = ["hello", "hi ", "hey", "greetings", "morning", "afternoon", "evening"]
#     if any(pattern in message_lower for pattern in greeting_patterns):
#         result["intent"] = "greeting"
#         result["confidence"] = 0.9
    
#     # Check for menu-related intents
#     menu_patterns = ["menu", "what do you have", "what do you offer", "show me", "what can i order", "what's available"]
#     if any(pattern in message_lower for pattern in menu_patterns):
#         result["intent"] = "menu"
#         result["confidence"] = 0.85
#         result["navigate_to"] = "menu"
    
#     # Check for specific menu items
#     menu_items_global = ["coffee", "latte", "espresso", "cappuccino", "mocha", "tea", "sandwich", "croissant", "muffin", "pastry"]
#     found_items = [item for item in menu_items_global if item in message_lower]
#     if found_items:
#         result["entities"]["menu_items"] = found_items
#         if "order" in message_lower or any(word in message_lower for word in ["get", "have", "want", "like", "give"]):
#             result["intent"] = "order"
#             result["confidence"] = 0.8
    
#     # Check for ordering intent
#     order_patterns = ["order", "buy", "purchase", "get me", "i'd like", "i want", "i'll have", "add to my order", "add to cart"]
#     if any(pattern in message_lower for pattern in order_patterns):
#         result["intent"] = "order"
#         result["confidence"] = 0.85
#         result["navigate_to"] = "orders"
    
#     # Check for order status intent
#     status_patterns = ["status", "where is my order", "how long", "track", "follow", "my order"]
#     if any(pattern in message_lower for pattern in status_patterns):
#         result["intent"] = "order_status"
#         result["confidence"] = 0.8
#         result["navigate_to"] = "orders"
    
#     # Check for robot status intent
#     robot_patterns = ["robot", "delivery", "deliveries", "where is the robot", "delivery status"]
#     if any(pattern in message_lower for pattern in robot_patterns):
#         result["intent"] = "robot_status"
#         result["confidence"] = 0.8
#         result["navigate_to"] = "delivery"
    
#     # Check for profile intent
#     profile_patterns = ["profile", "account", "my information", "my details", "settings"]
#     if any(pattern in message_lower for pattern in profile_patterns):
#         result["intent"] = "profile"
#         result["confidence"] = 0.85
#         result["navigate_to"] = "profile"
    
#     # Check for help intent
#     help_patterns = ["help", "support", "assist", "how do i", "how to", "guide"]
#     if any(pattern in message_lower for pattern in help_patterns):
#         result["intent"] = "help"
#         result["confidence"] = 0.8
    
#     # Check for hours intent
#     hours_patterns = ["hours", "open", "close", "when", "time", "operating"]
#     if any(pattern in message_lower for pattern in hours_patterns):
#         result["intent"] = "hours"
#         result["confidence"] = 0.8
    
#     # Extract quantities
#     quantity_matches = re.findall(r'(\d+)\s+([a-zA-Z]+)', message_lower)
#     if quantity_matches:
#         quantities = {}
#         for quantity, item in quantity_matches:
#             quantities[item] = int(quantity)
#         result["entities"]["quantity"] = quantities
    
#     return result

# async def generate_response(user_message: str, intent_data: Dict, context: Dict) -> str:
#     """
#     Generate a natural language response based on intent and context
    
#     Args:
#         user_message (str): User's message
#         intent_data (dict): Intent analysis from OpenAI
#         context (dict): Conversation context
        
#     Returns:
#         str: Generated response
#     """
#     if not OPENAI_API_KEY:
#         # Return a simple response if OpenAI is not available
#         return get_default_response(intent_data)
    
#     try:
#         # Build system prompt with context
#         system_prompt = f"""
#         You are BaristaBot, the virtual assistant for Neo Cafe, a coffee shop application.
        
#         Current context:
#         - User is logged in: {context.get('is_logged_in', False)}
#         - Current page: {context.get('current_page', 'unknown')}
#         - Has active order: {context.get('has_active_order', False)}
#         - Order items: {', '.join(context.get('order_items', []))}
        
#         Intent identified: {intent_data.get('intent')}
        
#         Your task is to provide a helpful, friendly response that addresses the user's intent.
#         Keep your response concise, under 150 words, and conversational.
#         If they want to order something, help them place the order.
#         If they want to navigate, tell them you'll take them there.
#         If they want information, provide it in a friendly way.
        
#         Relevant details:
#         - Hours: Monday-Friday 7am-8pm, Saturday-Sunday 8am-6pm
#         - Location: 123 Coffee Street, Downtown
#         - Delivery done by robots within 1 mile radius
#         """

#         response = await openai.Completion.acreate(
#             model="gpt-3.5-turbo",
#             prompt=system_prompt + "\n" + user_message,
#             temperature=0.7,
#             max_tokens=150
#         )
        
#         return response.choices[0].message.content
    
#     except Exception as e:
#         print(f"Error generating response with OpenAI: {e}")
#         # Fallback to default responses
#         return get_default_response(intent_data)

# def get_default_response(intent_data: Dict) -> str:
#     """
#     Get a default response based on intent (used as fallback when OpenAI is unavailable)
    
#     Args:
#         intent_data (dict): Intent analysis
        
#     Returns:
#         str: Default response
#     """
#     intent = intent_data.get("intent", "casual")
    
#     # Default responses by intent
#     responses = {
#         "greeting": "👋 Hello! Welcome to Neo Cafe. How can I help you today?",
#         "menu": "📋 I'd be happy to show you our menu. Is there something specific you're looking for or would you like to see the full menu?",
#         "order": "🛒 I'd be happy to help you place an order. What would you like to have?",
#         "order_status": "📊 Let me check on the status of your order for you. Do you have an order ID or would you like to check your most recent order?",
#         "robot_status": "🤖 I'll check on the robot delivery status for you. One moment please.",
#         "help": "❓ I'm here to help! You can ask about our menu, place orders, track deliveries, or learn about our coffee shop. What would you like help with?",
#         "profile": "👤 I can help you with your profile information. Would you like to see your account details, order history, or preferences?",
#         "hours": "🕒 Neo Cafe is open Monday through Friday from 7:00 AM to 8:00 PM, and weekends from 8:00 AM to 6:00 PM.",
#         "navigation": "🧭 I'll help you navigate to that section of the app.",
#         "casual": "I'm here to help with your Neo Cafe experience. You can ask about our menu, place an order, or check delivery status."
#     }
    
#     return responses.get(intent, responses["casual"])

# # ----- Chainlit Event Handlers -----

# @cl.on_chat_start
# async def start():
#     """Initialize chat session"""
#     global menu_items
    
#     # Load menu data
#     menu_items = await load_menu_data()
    
#     # Initialize state objects
#     voice_state = VoiceState()
#     order_state = OrderState()
#     robot_state = RobotState()
    
#     # Store state in user session
#     cl.user_session.set("voice_state", voice_state)
#     cl.user_session.set("order_state", order_state)
#     cl.user_session.set("robot_state", robot_state)
    
#     # Parse URL query parameters
#     query = cl.context.session.get('url_query')
#     query_dict = {}
#     current_page = "home"
    
#     if query:
#         query_dict = urllib.parse.parse_qs(query)
#         if 'tab' in query_dict:
#             current_page = query_dict['tab'][0]
    
#     # Set initial context
#     is_logged_in = 'user' in query_dict
#     has_active_order = 'order_id' in query_dict
#     order_id = query_dict.get('order_id', [''])[0]
    
#     # Store context in session
#     context = {
#         "is_logged_in": is_logged_in,
#         "current_page": current_page,
#         "has_active_order": has_active_order,
#         "order_id": order_id,
#         "order_items": []
#     }
#     cl.user_session.set("context", context)
    
#     # Personalized welcome based on context
#     welcome_message = ""
    
#     if is_logged_in:
#         username = query_dict.get('user', ['customer'])[0]
#         welcome_message = f"👋 Welcome back, {username}! I'm BaristaBot, your Neo Cafe assistant."
#     else:
#         welcome_message = "👋 Welcome to Neo Cafe! I'm BaristaBot, your virtual barista assistant."
    
#     if current_page == "menu":
#         welcome_message += " I see you're browsing our menu. Can I help you find something specific or make a recommendation?"
#     elif current_page == "order":
#         welcome_message += " I can help you place an order. Just tell me what you'd like to have!"
#     elif current_page == "status":
#         if has_active_order:
#             welcome_message += f" I see you're tracking order {order_id}. I can provide updates on its status."
#         else:
#             welcome_message += " I can help you track your orders. Do you have an order you'd like to check on?"
#     else:
#         welcome_message += " I can help you with our menu, placing orders, tracking deliveries, and answering questions."
    
#     await cl.Message(content=welcome_message).send()
    
#     # Only show quick menu if not in a specific context
#     if current_page == "home":
#         quick_menu = """
# ## 📋 Quick Actions

# - Browse the menu
# - Place an order
# - Check order status
# - Track delivery
# - Learn about our coffee

# Feel free to ask in natural language - I'm here to help!
# """
#         await cl.Message(content=quick_menu).send()
    
#     # Check if there's a query in the URL
#     initial_query = cl.context.session.get('url_query')
#     if initial_query:
#         # Extract actual query if it's in the format query=XXX
#         if "query=" in initial_query:
#             actual_query = initial_query.split("query=")[1].split("&")[0]
#             actual_query = urllib.parse.unquote_plus(actual_query)
#             await process_message(actual_query)

# @cl.on_message
# async def on_message(message: cl.Message):
#     """Handle user messages"""
#     await process_message(message.content)

# async def process_message(message):
#     """
#     Process user message and generate response
    
#     Args:
#         message (str): User message
#     """
#     # Get state objects
#     voice_state = cl.user_session.get("voice_state")
#     order_state = cl.user_session.get("order_state")
#     robot_state = cl.user_session.get("robot_state")
#     context = cl.user_session.get("context", {})
    
#     # Initialize if not present
#     if not order_state:
#         order_state = OrderState()
#         cl.user_session.set("order_state", order_state)
    
#     if not robot_state:
#         robot_state = RobotState()
#         cl.user_session.set("robot_state", robot_state)
    
#     # Update context with current order information
#     context["order_items"] = [item["name"] for item in order_state.items]
#     context["has_active_order"] = order_state.order_confirmed
#     context["order_id"] = order_state.order_id
#     cl.user_session.set("context", context)
    
#     # Check if voice mode is enabled
#     should_speak = voice_state and voice_state.is_enabled()
    
#     # Analyze user intent
#     intent_data = await analyze_intent(message)
    
#     # Generate a natural language response
#     response = await generate_response(message, intent_data, context)
    
#     # Determine if navigation is needed
#     navigate_to = intent_data.get("navigate_to")
#     if navigate_to:
#         # Inform the user about navigation
#         if navigate_to != context.get("current_page"):
#             response += f"\n\nI'll take you to the {navigate_to} section."
            
#             # Notify the parent window about navigation
#             try:
#                 cl.context.session.post_to_parent({
#                     "type": "navigation",
#                     "destination": navigate_to
#                 })
#             except Exception as e:
#                 print(f"Error navigating to {navigate_to}: {e}")
    
#     # Send the response
#     await cl.Message(content=response).send()
    
#     # If voice is enabled, speak the response
#     if should_speak:
#         voice_state.speak_text(response.replace("*", ""))
    
#     # Handle specific intents with actions
#     intent = intent_data.get("intent")
    
#     if intent == "menu":
#         # Show menu based on context
#         menu_category = None
#         if "entities" in intent_data and "menu_category" in intent_data["entities"]:
#             menu_category = intent_data["entities"]["menu_category"]
#         await show_menu(category=menu_category)
    
#     elif intent == "order":
#         # Extract menu items and quantities from intent
#         if "entities" in intent_data and "menu_items" in intent_data["entities"]:
#             menu_items_to_add = intent_data["entities"]["menu_items"]
#             quantities = intent_data.get("entities", {}).get("quantity", {})
            
#             added_items = []
#             for item_name in menu_items_to_add:
#                 quantity = quantities.get(item_name, 1)
#                 result = order_state.add_item(item_name, quantity)
#                 if "added" in result.lower():
#                     added_items.append(f"{quantity}x {item_name}")
            
#             if added_items:
#                 items_text = ", ".join(added_items)
#                 await cl.Message(content=f"🛒 I've added {items_text} to your order.").send()
#                 await display_order_summary()
                
#                 # Notify the parent window about the order update
#                 try:
#                     cl.context.session.post_to_parent({
#                         "type": "orderUpdate",
#                         "order": order_state.get_order_data()
#                     })
#                 except Exception as e:
#                     print(f"Error sending order update to parent: {e}")
    
#     elif intent == "order_status":
#         if order_state.order_confirmed and order_state.order_id:
#             # Show order status
#             status_msg = robot_state.format_status_message(order_state.order_id)
#             await cl.Message(content=status_msg).send()
            
#             # Add a simulated map view
#             await cl.Message(
#                 content="**📍 Live Tracking Map**\n\nYou can see the robot's current location on the map.",
#                 elements=[
#                     cl.Image(
#                         name="tracking_map",
#                         display="inline",
#                         url="https://via.placeholder.com/600x400?text=Robot+Location+Map",
#                         size="large"
#                     )
#                 ]
#             ).send()
#         else:
#             # No active order
#             await cl.Message(content="You don't have any active orders to track. Would you like to place an order?").send()
    
#     elif intent == "robot_status":
#         # Show general robot status
#         status_msg = robot_state.format_status_message()
#         await cl.Message(content=status_msg).send()
    
#     elif intent == "help":
#         # Show help based on context
#         help_text = """
# # 📚 BaristaBot Help

# ## 🛍️ What I Can Do:
# - Show you our menu and make recommendations
# - Help you place and customize orders
# - Track your order status and delivery
# - Provide information about Neo Cafe
# - Answer questions about our products

# ## 💬 Try These Examples:
# - "I'd like to order a latte and a croissant"
# - "What's on the menu?"
# - "Where's my order?"
# - "Tell me about your coffee beans"
# - "When are you open?"
# - "Take me to my profile"

# Just chat naturally - I understand regular language!
# """
#         await cl.Message(content=help_text).send()

# # ----- Data Loading and Management -----

# async def load_menu_data():
#     """
#     Load menu data from menu.json
    
#     Returns:
#         list: Menu items
#     """
#     try:
#         # Try to get the menu file path
#         menu_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'menu.json')
        
#         # Check if the file exists
#         if not os.path.exists(menu_path):
#             return []
            
#         # Load the data
#         with open(menu_path, 'r') as f:
#             return json.load(f)
            
#     except Exception as e:
#         print(f"Error loading menu data: {e}")
#         return []

# # ----- Menu Display Function -----

# async def show_menu(category=None):
#     """
#     Show the menu, optionally filtered by category
    
#     Args:
#         category (str, optional): Category to filter by
#     """
#     await cl.Message(content="📋 **Neo Cafe Menu**").send()
    
#     # Group menu items by category
#     items_by_category = {}
#     for item in menu_items:
#         item_category = item.get("category", "Other")
#         if item_category not in items_by_category:
#             items_by_category[item_category] = []
#         items_by_category[item_category].append(item)
    
#     # If category specified, only show that category
#     categories_to_show = [category] if category and category in items_by_category else items_by_category.keys()
    
#     # Show ordering instructions
#     ordering_instructions = """
# ### 📝 How to Order:
# - Say "I'd like [item]" to add to your order
# - Ask me about any item for more information
# - Say "View my order" to see your current selections
# """
#     await cl.Message(content=ordering_instructions).send()
    
#     # Display items by category
#     for category in categories_to_show:
#         # Capitalize category name and add emoji
#         category_emoji = "☕"
#         if "coffee" in category.lower():
#             category_emoji = "☕"
#         elif "tea" in category.lower():
#             category_emoji = "🍵"
#         elif "pastry" in category.lower() or "bakery" in category.lower():
#             category_emoji = "🥐"
#         elif "breakfast" in category.lower():
#             category_emoji = "🍳"
#         elif "sandwich" in category.lower():
#             category_emoji = "🥪"
#         elif "dessert" in category.lower():
#             category_emoji = "🍰"
#         elif "drink" in category.lower() or "beverage" in category.lower():
#             category_emoji = "🥤"
        
#         category_name = category.capitalize()
        
#         await cl.Message(content=f"## {category_emoji} {category_name}").send()
        
#         # Show items in an attractive format
#         items = items_by_category[category]
#         for item in items:
#             await create_menu_card(item)

# async def create_menu_card(item):
#     """
#     Create a card for a menu item
    
#     Args:
#         item (dict): Menu item
#     """
#     # Create card content with enhanced formatting
#     content = f"""
# ### 🔸 {item['name']} - ${item['price']:.2f}

# {item['description']}

# **Quick Actions:**
# - "I'd like a {item['name']}"
# - "Tell me more about the {item['name']}"
# """
    
#     # Create elements (image)
#     elements = []
#     if "image" in item and item["image"]:
#         # Try to get the absolute path to the image
#         image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'images', item['image'])
#         if os.path.exists(image_path):
#             elements = [
#                 cl.Image(
#                     name=item["name"],
#                     display="inline", 
#                     path=image_path,
#                     size="medium"
#                 )
#             ]
    
#     # Send the card
#     await cl.Message(
#         content=content,
#         elements=elements
#     ).send()

# async def display_order_summary():
#     """Display the current order summary"""
#     order_state = cl.user_session.get("order_state")
#     if not order_state:
#         return
    
#     summary = order_state.get_order_summary()
    
#     # Create a fancy order display
#     if order_state.items:
#         # Add emoji and styling
#         header = "🛍️ **Your Order Summary**\n\n"
        
#         # Send detailed order summary
#         await cl.Message(content=header + summary).send()
        
#         # Add suggested next actions based on order state
#         if not order_state.order_confirmed:
#             next_actions = """
# **What would you like to do next?**
# - "Confirm my order"
# - "Add more items"
# - "Clear my order"
# - "Add special instructions: [your notes]"
# - "Deliver to [location]"
# """
#             await cl.Message(content=next_actions).send()
#         else:
#             # Order is already confirmed
#             tracking_actions = """
# **Order Confirmed!**
# - "Track my order"
# - "Start a new order"
# """
#             await cl.Message(content=tracking_actions).send()
#     else:
#         # Empty order
#         await cl.Message(content="🛒 Your order is currently empty. Browse our menu to add items!").send()
        
#         # Suggest viewing the menu
#         await cl.Message(content="Would you like to see our menu?").send()

# # ----- Chainlit Set Starters -----

# @cl.set_starters
# async def set_starters():
#     """Define starter messages for the chat"""
#     return [
#         cl.Starter(
#             label="☕️ Show Menu",
#             message="Show me the menu",
#             icon="🍽️",
#         ),
#         cl.Starter(
#             label="⭐ What's Popular?",
#             message="What are your most popular items?",
#             icon="⭐",
#         ),
#         cl.Starter(
#             label="🛍️ Place an Order",
#             message="I'd like to place an order",
#             icon="☕",
#         ),
#         cl.Starter(
#             label="🤖 Track Delivery",
#             message="Where is my order?",
#             icon="🤖",
#         ),
#         cl.Starter(
#             label="❓ Help",
#             message="What can you help me with?",
#             icon="❓",
#         ),
#     ]

# ==================================================================================

# File: chainlit_app/app.py (Updated for floating chat integration)

"""
Enhanced Chainlit integration for Neo Cafe with OpenAI-powered intelligence and floating chat support
"""
import os
import sys
import json
import time
import urllib.parse
import requests
import asyncio
import threading
from typing import Dict, List, Optional
from datetime import datetime
import openai
import re

import chainlit as cl
from chainlit.element import Element

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import state management classes
from chainlit_app.states import VoiceState, OrderState, RobotState

# Constants
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:8050')
ROBOT_SIMULATOR_URL = os.environ.get('ROBOT_SIMULATOR_URL', 'http://localhost:8051')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

# Global variables
menu_items = []  # Will be populated in the on_chat_start function
is_floating_chat = False  # Flag to check if running in floating mode

# ----- OpenAI Integration Functions -----
# Note: These functions are already implemented in your code, so they are omitted here

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
        query_dict = urllib.parse.parse_qs(query)
        if 'tab' in query_dict:
            current_page = query_dict['tab'][0]
        
        # Check if this is a floating chat instance
        if 'floating' in query_dict:
            is_floating_chat = query_dict['floating'][0].lower() == 'true'
    
    # Set initial context
    is_logged_in = 'user' in query_dict
    has_active_order = 'order_id' in query_dict
    order_id = query_dict.get('order_id', [''])[0]
    
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
        username = query_dict.get('user', ['customer'])[0]
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
## 📋 Quick Actions

- Browse the menu
- Place an order
- Check order status
- Track delivery
- Learn about our coffee

Feel free to ask in natural language - I'm here to help!
"""
        await cl.Message(content=quick_menu).send()
    
    # Check if there's a query in the URL
    initial_query = cl.context.session.get('url_query')
    if initial_query:
        # Extract actual query if it's in the format query=XXX
        if "query=" in initial_query:
            actual_query = initial_query.split("query=")[1].split("&")[0]
            actual_query = urllib.parse.unquote_plus(actual_query)
            await process_message(actual_query)

@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages"""
    await process_message(message.content)

async def process_message(message):
    """
    Process user message and generate response
    
    Args:
        message (str): User message
    """
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
    
    # Analyze user intent
    intent_data = await analyze_intent(message)
    
    # Generate a natural language response
    response = await generate_response(message, intent_data, context)
    
    # Determine if navigation is needed
    navigate_to = intent_data.get("navigate_to")
    if navigate_to:
        # Inform the user about navigation
        if navigate_to != context.get("current_page"):
            # For floating chat, be more concise
            if is_floating_chat:
                response += f"\n\nNavigating to {navigate_to}..."
            else:
                response += f"\n\nI'll take you to the {navigate_to} section."
            
            # Notify the parent window about navigation
            try:
                cl.context.session.post_to_parent({
                    "type": "navigation",
                    "destination": navigate_to
                })
            except Exception as e:
                print(f"Error navigating to {navigate_to}: {e}")
    
    # Send the response
    await cl.Message(content=response).send()
    
    # If voice is enabled, speak the response
    if should_speak:
        voice_state.speak_text(response.replace("*", ""))
    
    # Handle specific intents with actions
    intent = intent_data.get("intent")
    
    if intent == "menu":
        # Show menu based on context
        menu_category = None
        if "entities" in intent_data and "menu_category" in intent_data["entities"]:
            menu_category = intent_data["entities"]["menu_category"]
        
        # For floating chat, show a more compact menu
        if is_floating_chat:
            await show_compact_menu(category=menu_category)
        else:
            await show_menu(category=menu_category)
    
    elif intent == "order":
        # Handle order intent
        # Processing as in original code
        # This part is already implemented in your code, so it's omitted here
        pass
    
    # Other intent handlers remain the same
    # This part is already implemented in your code, so it's omitted here

# ----- Data Loading and Menu Display -----

async def load_menu_data():
    """
    Load menu data from menu.json
    
    Returns:
        list: Menu items
    """
    # This function is already implemented in your code, so it's omitted here
    pass

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
            # Compact item display
            items_text += f"• **{item['name']}** - ${item['price']:.2f}\n"
        
        # Add simple ordering instructions
        items_text += "\n*Say 'I'd like [item]' to order*"
        
        # Send as a single message
        await cl.Message(content=items_text).send()