# File: app/utils/robot_api_utils.py

import requests
import json
import os
import logging
from functools import wraps
import time
from urllib.parse import urljoin

# Configure logging
logger = logging.getLogger('neo_cafe')

# Get the base URL for the robot API from environment variable or use default
# Replace localhost with your specific IP address
ROBOT_API_BASE_URL = os.environ.get('ROBOT_API_BASE_URL', 'http://172.29.104.124:8001/api')

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
def start_robot_delivery(interface_name="en7", order_id=None, delivery_location=None):
    """
    Start a robot delivery by calling the robot API
    
    Args:
        interface_name (str): Network interface name for the robot
        order_id (str, optional): The ID of the order being delivered
        delivery_location (str, optional): The delivery destination address
        
    Returns:
        dict: Response from the robot API
    """
    try:
        # Construct the API endpoint URL
        endpoint = urljoin(ROBOT_API_BASE_URL, "delivery/start")
        
        # Prepare the payload
        payload = {
            "interface_name": interface_name
        }
        
        # Add order details if provided
        if order_id:
            payload["order_id"] = order_id
        if delivery_location:
            payload["delivery_location"] = delivery_location
            
        # Log the request
        logger.info(f"Starting robot delivery: {json.dumps(payload)}")
        
        # Make the API call
        response = requests.post(
            endpoint,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=10  # 10 second timeout
        )
        
        # Check if the request was successful
        if response.status_code in (200, 201, 202):
            result = response.json()
            logger.info(f"Robot delivery started successfully: {result}")
            return {
                "status": "success",
                "data": result,
                "message": "Robot delivery started successfully"
            }
        else:
            error_msg = f"Failed to start robot delivery. Status code: {response.status_code}"
            logger.error(error_msg)
            logger.error(f"Response: {response.text}")
            return {
                "status": "error",
                "error": error_msg,
                "details": response.text
            }
    
    except Exception as e:
        error_msg = f"Error starting robot delivery: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }

@retry_request()
def get_robot_delivery_status(delivery_id=None, order_id=None):
    """
    Get the status of a robot delivery
    
    Args:
        delivery_id (str, optional): The ID of the delivery
        order_id (str, optional): The ID of the order
        
    Returns:
        dict: Status of the robot delivery
    """
    try:
        # Construct the API endpoint URL
        endpoint = urljoin(ROBOT_API_BASE_URL, "delivery/status")
        
        # Add query parameters if provided
        params = {}
        if delivery_id:
            params["delivery_id"] = delivery_id
        if order_id:
            params["order_id"] = order_id
            
        # Log the request
        logger.info(f"Getting robot delivery status: {params}")
        
        # Make the API call
        response = requests.get(
            endpoint,
            params=params,
            timeout=5  # 5 second timeout
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Robot delivery status retrieved: {result}")
            return {
                "status": "success",
                "data": result
            }
        else:
            error_msg = f"Failed to get robot delivery status. Status code: {response.status_code}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "details": response.text
            }
    
    except Exception as e:
        error_msg = f"Error getting robot delivery status: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }

@retry_request()
def cancel_robot_delivery(delivery_id=None, order_id=None):
    """
    Cancel a robot delivery
    
    Args:
        delivery_id (str, optional): The ID of the delivery
        order_id (str, optional): The ID of the order
        
    Returns:
        dict: Result of the cancellation request
    """
    try:
        # Construct the API endpoint URL
        endpoint = urljoin(ROBOT_API_BASE_URL, "delivery/cancel")
        
        # Prepare the payload
        payload = {}
        if delivery_id:
            payload["delivery_id"] = delivery_id
        if order_id:
            payload["order_id"] = order_id
            
        # Log the request
        logger.info(f"Cancelling robot delivery: {json.dumps(payload)}")
        
        # Make the API call
        response = requests.post(
            endpoint,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=5  # 5 second timeout
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Robot delivery cancelled: {result}")
            return {
                "status": "success",
                "data": result,
                "message": "Robot delivery cancelled successfully"
            }
        else:
            error_msg = f"Failed to cancel robot delivery. Status code: {response.status_code}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "details": response.text
            }
    
    except Exception as e:
        error_msg = f"Error cancelling robot delivery: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }