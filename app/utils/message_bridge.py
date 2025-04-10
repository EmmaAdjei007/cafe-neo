# app/utils/message_bridge.py

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
            MessageBridge._send_via_socket,
            MessageBridge._send_via_websocket,
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
    def _send_via_socket(message, session_id):
        """Send message via Socket.IO"""
        try:
            # This is a placeholder - in a real implementation,
            # you would use a Socket.IO client to send the message
            
            # Import here to avoid circular imports
            from flask import current_app
            socketio = current_app.extensions.get('socketio')
            
            if socketio:
                socketio.emit('chat_message_from_dashboard', {
                    'message': message,
                    'session_id': session_id
                })
                logger.info(f"Message sent via Socket.IO: {message}")
                return {
                    'status': 'success',
                    'method': 'socket'
                }
            else:
                return {
                    'status': 'error',
                    'error': "Socket.IO not available"
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def _send_via_websocket(message, session_id):
        """Send message via WebSocket directly (not using API)"""
        try:
            # This uses a different mechanism than the API
            # No REST API call here, so no 405 error
            
            # Import the socketio instance
            try:
                from app import socketio
                
                # Directly emit through imported socketio
                socketio.emit('message_to_chainlit', {
                    'message': message,
                    'session_id': session_id
                })
                
                logger.info(f"Message sent via direct WebSocket: {message}")
                return {
                    'status': 'success',
                    'method': 'websocket'
                }
            except ImportError:
                return {
                    'status': 'error',
                    'error': "Could not import socketio"
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