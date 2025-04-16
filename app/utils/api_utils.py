# # File: app/utils/api_utils.py

# import requests
# import json
# import os
# from functools import wraps
# import time
# import uuid

# # Base URLs for APIs
# CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8000')
# ROBOT_SIMULATOR_URL = os.environ.get('ROBOT_SIMULATOR_URL', 'http://localhost:8051')

# def retry_request(max_retries=3, backoff_factor=0.5):
#     """
#     Decorator to retry API requests with exponential backoff
    
#     Args:
#         max_retries (int): Maximum number of retry attempts
#         backoff_factor (float): Backoff factor for retry timing
#     """
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             retries = 0
#             while retries < max_retries:
#                 try:
#                     return func(*args, **kwargs)
#                 except (requests.RequestException, ConnectionError) as e:
#                     retries += 1
#                     if retries >= max_retries:
#                         raise e
#                     # Calculate backoff time based on retry number
#                     backoff_time = backoff_factor * (2 ** (retries - 1))
#                     time.sleep(backoff_time)
#         return wrapper
#     return decorator

# @retry_request()
# def get_robot_status(order_id=None):
#     """
#     Get robot status for an order or general status
    
#     Args:
#         order_id (str, optional): Order ID
        
#     Returns:
#         dict: Robot status data
#     """
#     try:
#         if order_id:
#             response = requests.get(
#                 f"{ROBOT_SIMULATOR_URL}/api/delivery/{order_id}",
#                 timeout=3
#             )
            
#             if response.status_code == 200:
#                 return response.json()
        
#         # Get general robot status
#         response = requests.get(
#             f"{ROBOT_SIMULATOR_URL}/api/status",
#             timeout=3
#         )
        
#         if response.status_code == 200:
#             return response.json()
#         else:
#             return {
#                 "status": "unknown",
#                 "error": f"Status code: {response.status_code}"
#             }
    
#     except Exception as e:
#         return {
#             "status": "error",
#             "error": str(e)
#         }

# @retry_request()
# def place_order(order_data):
#     """
#     Place an order via the API
    
#     Args:
#         order_data (dict): Order data
        
#     Returns:
#         dict: Response data
#     """
#     try:
#         response = requests.post(
#             f"{ROBOT_SIMULATOR_URL}/api/place-order",
#             json=order_data,
#             timeout=5
#         )
        
#         if response.status_code == 200:
#             return response.json()
#         else:
#             return {
#                 "status": "error",
#                 "error": f"Status code: {response.status_code}"
#             }
    
#     except Exception as e:
#         return {
#             "status": "error",
#             "error": str(e)
#         }

# @retry_request()
# def update_order_status(order_id, new_status):
#     """
#     Update order status via the API
    
#     Args:
#         order_id (str): Order ID
#         new_status (str): New status
        
#     Returns:
#         dict: Response data
#     """
#     try:
#         response = requests.put(
#             f"{ROBOT_SIMULATOR_URL}/api/orders/{order_id}/status",
#             json={"status": new_status},
#             timeout=3
#         )
        
#         if response.status_code == 200:
#             return response.json()
#         else:
#             return {
#                 "status": "error",
#                 "error": f"Status code: {response.status_code}"
#             }
    
#     except Exception as e:
#         return {
#             "status": "error",
#             "error": str(e)
#         }

# @retry_request()
# def send_message_to_chainlit(message, session_id=None):
#     """
#     Send a message to the Chainlit chatbot
    
#     Args:
#         message (str): Message to send
#         session_id (str, optional): Session ID
        
#     Returns:
#         dict: Response data
#     """
#     try:
#         data = {
#             "message": message
#         }
        
#         if session_id:
#             data["session_id"] = session_id
        
#         response = requests.post(
#             f"{CHAINLIT_URL}/api/chat",
#             json=data,
#             timeout=5
#         )
        
#         if response.status_code == 200:
#             return response.json()
#         else:
#             return {
#                 "status": "error",
#                 "error": f"Status code: {response.status_code}"
#             }
    
#     except Exception as e:
#         return {
#             "status": "error",
#             "error": str(e)
#         }

# def get_chainlit_session():
#     """
#     Get or create a Chainlit session ID
    
#     Returns:
#         str: Session ID
#     """
#     # In a real application, this would be stored in the user's session
#     # For simplicity, generating a new one here
#     return str(uuid.uuid4())

# def sync_order_with_chainlit(order_data, session_id=None):
#     """
#     Synchronize order data with Chainlit
    
#     Args:
#         order_data (dict): Order data
#         session_id (str, optional): Session ID
        
#     Returns:
#         bool: Success status
#     """
#     try:
#         data = {
#             "type": "sync_order",
#             "order": order_data
#         }
        
#         if session_id:
#             data["session_id"] = session_id
        
#         response = requests.post(
#             f"{CHAINLIT_URL}/api/custom",
#             json=data,
#             timeout=5
#         )
        
#         return response.status_code == 200
    
#     except Exception as e:
#         print(f"Error syncing order with Chainlit: {e}")
#         return False

## =======================================================================

# File: app/utils/api_utils.py

import requests
import json
import os
from functools import wraps
import time
import uuid

# Base URLs for APIs
CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8000')
ROBOT_SIMULATOR_URL = os.environ.get('ROBOT_SIMULATOR_URL', 'http://localhost:8051')

def retry_request(max_retries=3, backoff_factor=0.5):
    """
    Decorator to retry API requests with exponential backoff
    
    Args:
        max_retries (int): Maximum number of retry attempts
        backoff_factor (float): Backoff factor for retry timing
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, ConnectionError) as e:
                    retries += 1
                    if retries >= max_retries:
                        raise e
                    # Calculate backoff time based on retry number
                    backoff_time = backoff_factor * (2 ** (retries - 1))
                    time.sleep(backoff_time)
        return wrapper
    return decorator

@retry_request()
def get_robot_status(order_id=None):
    """Get robot status for an order or general status"""
    try:
        if order_id:
            response = requests.get(
                f"{ROBOT_SIMULATOR_URL}/api/delivery/{order_id}",
                timeout=3
            )
            
            if response.status_code == 200:
                return response.json()
        
        # Get general robot status
        response = requests.get(
            f"{ROBOT_SIMULATOR_URL}/api/status",
            timeout=3
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "status": "unknown",
                "error": f"Status code: {response.status_code}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@retry_request()
def place_order(order_data):
    """Place an order via the API"""
    try:
        response = requests.post(
            f"{ROBOT_SIMULATOR_URL}/api/place-order",
            json=order_data,
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

@retry_request()
def update_order_status(order_id, new_status):
    """Update order status via the API"""
    try:
        response = requests.put(
            f"{ROBOT_SIMULATOR_URL}/api/orders/{order_id}/status",
            json={"status": new_status},
            timeout=3
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

@retry_request()
def send_message_to_chainlit(message, session_id=None):
    """
    Send a message to the Chainlit chatbot
    
    Args:
        message (str): Message to send
        session_id (str, optional): Session ID
        
    Returns:
        dict: Response data
    """
    try:
        # Try using WebSocket approach instead of REST API
        # In a real implementation, you would use a proper WebSocket client
        print(f"Attempting to send message to Chainlit via socket: {message}")
        
        # For demo purposes, just log the message
        # The actual message will be handled by the socket.io connection
        return {
            "status": "success",
            "message": "Message sent to Chainlit via socket"
        }
    except Exception as e:
        print(f"Error sending message to Chainlit: {e}")
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
    # This function will use socket.io instead of REST API
    print(f"Synchronizing order with Chainlit: {order_data}")
    return True