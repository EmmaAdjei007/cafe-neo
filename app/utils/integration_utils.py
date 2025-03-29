# File: app/utils/integration_utils.py

"""
Utilities for integrating Dash and Chainlit
"""
import requests
import json
import os
from urllib.parse import urlencode
import uuid

# Get Chainlit URL from environment
CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8001')

def generate_chainlit_url(params=None):
    """
    Generate a URL for the Chainlit application with optional parameters
    
    Args:
        params (dict, optional): Parameters to include in URL
        
    Returns:
        str: Chainlit URL with parameters
    """
    base_url = CHAINLIT_URL
    
    if params:
        query_string = urlencode(params)
        return f"{base_url}?{query_string}"
    
    return base_url

def send_message_to_chainlit(message, session_id=None):
    """
    Send a message to the Chainlit application
    
    Args:
        message (str): Message text
        session_id (str, optional): Session ID
        
    Returns:
        dict: Response data
    """
    try:
        data = {
            "message": message
        }
        
        if session_id:
            data["session_id"] = session_id
        
        response = requests.post(
            f"{CHAINLIT_URL}/api/chat",
            json=data,
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "status": "error",
                "error": f"Status code: {response.status_code}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def get_chainlit_session():
    """
    Get or create a Chainlit session ID
    
    Returns:
        str: Session ID
    """
    # In a real application, this would be stored in the user's session
    # For simplicity, generating a new one here
    return str(uuid.uuid4())

def sync_order_with_chainlit(order_data, session_id=None):
    """
    Synchronize order data with Chainlit
    
    Args:
        order_data (dict): Order data
        session_id (str, optional): Session ID
        
    Returns:
        bool: Success status
    """
    try:
        data = {
            "type": "sync_order",
            "order": order_data
        }
        
        if session_id:
            data["session_id"] = session_id
        
        response = requests.post(
            f"{CHAINLIT_URL}/api/custom",
            json=data,
            timeout=5
        )
        
        return response.status_code == 200
    
    except Exception as e:
        print(f"Error syncing order with Chainlit: {e}")
        return False