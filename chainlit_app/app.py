# chainlit_app/app.py
import os
import sys
import json
import time
import urllib.parse
import requests
from typing import Dict, List, Optional
from datetime import datetime

import chainlit as cl
from chainlit.element import Element
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Constants
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:8050')
ROBOT_SIMULATOR_URL = os.environ.get('ROBOT_SIMULATOR_URL', 'http://localhost:8051')

# Global variables
is_floating_chat = False  # Flag to check if running in floating mode
menu_items = []  # Will be populated in the on_chat_start function
processed_message_ids = set()  # Track processed message IDs to avoid duplicates

# ----- Knowledge Base Setup -----

def create_knowledge_base():
    """
    Create vector store knowledge base for menu items and other information
    
    Returns:
        FAISS: Vector store
    """
    # Load menu data
    menu_data = load_menu_data()
    global menu_items
    menu_items = menu_data
    
    # Prepare text chunks for vector store
    documents = []
    for item in menu_data:
        # Create menu item document
        doc_text = f"Menu Item: {item['name']}\n"
        doc_text += f"Description: {item['description']}\n"
        doc_text += f"Price: ${item['price']:.2f}\n"
        doc_text += f"Category: {item['category']}\n"
        doc_text += f"Dietary Info: "
        dietary = []
        if item.get('vegetarian'):
            dietary.append('Vegetarian')
        if item.get('vegan'):
            dietary.append('Vegan')
        if item.get('gluten_free'):
            dietary.append('Gluten-Free')
        doc_text += ', '.join(dietary) if dietary else 'None specified'
        
        # Add as document
        documents.append(doc_text)
    
    # Add operating hours and general info
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
    
    # Add ordering process info
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
    
    # Create vector store from documents
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_texts(documents, embeddings)
    
    return vector_store

def load_menu_data():
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
        
        # Return a fallback menu with some basic items if no file found
        print("Warning: Could not find menu.json, using fallback menu")
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

# ----- API Integration Tools -----

def navigate_to_page(destination):
    """
    Send navigation request to the Dash app
    
    Args:
        destination (str): Navigation destination
        
    Returns:
        str: Response message
    """
    try:
        print(f"Attempting to navigate to: {destination}")
        
        # Try to send navigation event to parent window
        try:
            cl.send_to_parent({
                "type": "navigation",
                "destination": destination
            })
        except Exception as e:
            print(f"Error sending navigation via cl.send_to_parent: {e}")
        
        # Also try direct HTTP API call
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
        return f"Failed to navigate: {str(e)}"

def place_order(order_data_str):
    """
    Place an order with the Dash app
    
    Args:
        order_data_str (str): JSON string with order data
        
    Returns:
        str: Response message
    """
    try:
        # Parse order data
        order_data = json.loads(order_data_str)
        
        # Generate order ID if not present
        if "id" not in order_data:
            timestamp = int(time.time())
            order_data["id"] = f"ORD-{timestamp}"
        
        print(f"Attempting to place order: {order_data}")
        
        # Try to send order to parent window
        try:
            cl.send_to_parent({
                "type": "order_update",
                "order": order_data
            })
        except Exception as e:
            print(f"Error sending order via cl.send_to_parent: {e}")
        
        # Also try direct HTTP API call
        try:
            response = requests.post(
                f"{DASHBOARD_URL}/api/place-order",
                json=order_data,
                timeout=5
            )
            print(f"Place order API response: {response.status_code}")
        except Exception as e:
            print(f"Error calling place-order API: {e}")
        
        return f"Order placed successfully! Your order ID is {order_data['id']}."
    except Exception as e:
        return f"Failed to place order: {str(e)}"

def search_menu(query):
    """
    Search menu items based on query
    
    Args:
        query (str): Search query
        
    Returns:
        str: Search results
    """
    try:
        # Convert query to lowercase for case-insensitive matching
        query_lower = query.lower()
        
        # Find matching items
        matching_items = []
        for item in menu_items:
            # Check name, description, and category
            if (query_lower in item["name"].lower() or 
                query_lower in item["description"].lower() or 
                query_lower in item["category"].lower()):
                matching_items.append(item)
        
        # Format results
        if not matching_items:
            return "No menu items found matching your query."
        
        results = "Here are the menu items matching your query:\n\n"
        for item in matching_items:
            results += f"• **{item['name']}** - ${item['price']:.2f}\n"
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
        return f"Error searching menu: {str(e)}"

def get_store_hours():
    """Get store hours information"""
    return """
**Neo Cafe Hours:**

Monday - Friday: 7:00 AM to 8:00 PM
Saturday - Sunday: 8:00 AM to 6:00 PM

Location: 123 Coffee Street, Downtown
Phone: (555) 123-4567
"""

# ----- LangChain Setup -----

def setup_langchain_agent():
    """
    Set up LangChain agent with tools for interacting with Neo Cafe
    
    Returns:
        dict: Agent configuration
    """
    # Create knowledge base
    kb = create_knowledge_base()
    
    # Set up retriever
    retriever = kb.as_retriever(search_kwargs={"k": 5})
    
    # Create memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    # Create tools
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
            func=place_order,
            description="Place an order with Neo Cafe. Expects a JSON string with order details"
        ),
        Tool(
            name="StoreHoursTool",
            func=get_store_hours,
            description="Get information about Neo Cafe's operating hours"
        )
    ]
    
    # Create LLM
    llm = ChatOpenAI(temperature=0.2)
    
    # Create agent
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory
    )
    
    return {
        "agent": agent,
        "tools": tools,
        "retriever": retriever,
        "memory": memory
    }

# ----- Chainlit Event Handlers -----

@cl.on_chat_start
async def start():
    """Initialize chat session"""
    global is_floating_chat
    
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
    
    # Set up LangChain agent
    try:
        agent_config = setup_langchain_agent()
        cl.user_session.set("agent_config", agent_config)
        print("LangChain agent setup complete")
    except Exception as e:
        print(f"Error setting up LangChain agent: {e}")
    
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
    
    # Get agent configuration and context
    agent_config = cl.user_session.get("agent_config")
    context = cl.user_session.get("context", {})
    
    if not agent_config:
        await cl.Message(content="I'm still initializing. Please try again in a moment.").send()
        return
    
    try:
        # Get agent
        agent = agent_config["agent"]
        
        # Run the message through the agent
        message_with_context = f"Current page: {context.get('current_page', 'home')}. User says: {message}"
        response = await cl.make_async(agent.run)(message_with_context)
        
        # Send the response
        await cl.Message(content=response).send()
        
    except Exception as e:
        print(f"Error processing message: {e}")
        await cl.Message(content="I'm having trouble processing your request. Could you please try again or rephrase your question?").send()

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

def set_starters():
    """
    This function returns starter messages for the chat interface.
    The @cl.set_starters decorator takes the list of starters directly.
    """
    pass  # Using the decorator with direct list argument, so function body is empty