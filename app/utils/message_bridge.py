import os
import json
import requests
import time
import uuid
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URLs for APIs
CHAINLIT_URL = os.environ.get('CHAINLIT_URL', 'http://localhost:8001')

class MessageBridge:
    """Class to handle sending messages to Chainlit"""
    
    @staticmethod
    def send_message(message, session_id=None):
        """
        Send a message to Chainlit via whatever means available
        
        Args:
            message (str): Message to send
            session_id (str, optional): Session ID
            
        Returns:
            dict: Result status
        """
        # Try multiple methods in sequence
        methods = [
            MessageBridge._send_via_api,
            MessageBridge._send_via_custom_api,
            MessageBridge._send_via_file
        ]
        
        # Get session ID
        if not session_id:
            session_id = str(uuid.uuid4())
            
        # Try each method
        for method in methods:
            try:
                result = method(message, session_id)
                if result.get('status') == 'success':
                    return result
                logger.warning(f"Method {method.__name__} failed with: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error in {method.__name__}: {str(e)}")
                continue
        
        # If all methods fail, return error
        return {
            'status': 'error',
            'error': 'All message delivery methods failed'
        }
    
    @staticmethod
    def _send_via_api(message, session_id):
        """Send message via standard Chainlit API"""
        try:
            data = {
                "message": message,
                "session_id": session_id
            }
            
            response = requests.post(
                f"{CHAINLIT_URL}/api/chat",
                json=data,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in (200, 201, 202):
                logger.info(f"Message sent to Chainlit API: {message}")
                return {
                    'status': 'success',
                    'method': 'api'
                }
            else:
                return {
                    'status': 'error',
                    'error': f"API error: {response.status_code}"
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def _send_via_custom_api(message, session_id):
        """Send message via custom API endpoint"""
        try:
            data = {
                "message": message,
                "session_id": session_id
            }
            
            response = requests.post(
                f"{CHAINLIT_URL}/api/custom_message",
                json=data,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in (200, 201, 202):
                logger.info(f"Message sent to custom API: {message}")
                return {
                    'status': 'success',
                    'method': 'custom_api'
                }
            else:
                return {
                    'status': 'error',
                    'error': f"Custom API error: {response.status_code}"
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def _send_via_file(message, session_id):
        """Write message to a file that Chainlit can monitor"""
        try:
            # Create messages directory if it doesn't exist
            os.makedirs('messages', exist_ok=True)
            
            # Create a unique filename
            filename = f"messages/message_{session_id}_{int(time.time())}.json"
            
            # Write message to file
            with open(filename, 'w') as f:
                json.dump({
                    'message': message,
                    'session_id': session_id,
                    'timestamp': time.time()
                }, f)
            
            logger.info(f"Message written to file: {filename}")
            return {
                'status': 'success',
                'method': 'file',
                'filename': filename
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }