# File: server.py (Enhanced with improved error handling)
import uuid
from flask import Flask, render_template, redirect, session, request, jsonify
from datetime import datetime
import time
import requests
import os
from flask_socketio import SocketIO, emit
import json

# Error handler for Socket.IO
def handle_socketio_error(e):
    """
    Handle Socket.IO errors gracefully
    
    Args:
        e (Exception): The exception that was raised
    """
    print(f"Socket.IO error: {str(e)}")
    # No need to re-raise, just log the error

def configure_server(server, socketio):
    """
    Configure the Flask server with custom routes for integration
    
    Args:
        server (Flask): Flask server instance
        socketio (SocketIO): SocketIO instance
    """
    # Chainlit proxy route
    @server.route('/chainlit')
    def chainlit_proxy():
        """Proxy page that embeds the Chainlit app in an iframe"""
        chainlit_url = os.environ.get('CHAINLIT_URL', 'http://localhost:8001')
        
        # Create a session ID if one doesn't exist
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            print(f"Created new session_id: {session['session_id']}")
        else:
            print(f"Using existing session_id: {session['session_id']}")
        
        # Pass along any query parameters
        query_string = request.query_string.decode('utf-8')
        full_url = chainlit_url
        if query_string:
            full_url = f"{chainlit_url}?{query_string}"
            print(f"Redirecting to Chainlit with query params: {query_string}")
        
        print(f"Rendering Chainlit embed with URL: {full_url}")
        return render_template('chainlit_embed.html', chainlit_url=full_url)
    
    # Debug endpoint to check if server is responding
    @server.route('/api/ping', methods=['GET'])
    def ping():
        """Simple ping endpoint to check if server is responding"""
        return jsonify({
            'status': 'success',
            'message': 'Pong from server',
            'time': str(datetime.now())
        })
    
    # SocketIO event handlers
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print(f'Client connected to Socket.IO: {request.sid}')
        return {'status': 'connected', 'sid': request.sid}
    
    @socketio.on('disconnect')
    def handle_disconnect(sid=None):
        """Handle client disconnection"""
        sid_value = sid or request.sid or "unknown"
        print(f'Client disconnected from Socket.IO: {sid_value}')
    
    @socketio.on('ping')
    def handle_ping(data):
        """Handle ping messages for testing"""
        print(f"Received ping from client {request.sid}: {data}")
        return {'status': 'success', 'message': 'pong', 'received': data}
    
    @socketio.on('send_chat_message')
    def handle_send_chat_message(data):
        """Handle sending messages to Chainlit"""
        try:
            message = data.get('message')
            session_id = data.get('session_id')
            
            print(f"Received message to send to Chainlit via Socket.IO: {message}")
            print(f"From session: {session_id}")
            
            # Forward the message to all clients (including the Chainlit iframe)
            print(f"Broadcasting chat_message_from_dashboard to all clients")
            
            # Make sure the data is properly formatted
            emit_data = {
                'message': message,
                'session_id': session_id
            }
            
            # Emit to everyone
            socketio.emit('chat_message_from_dashboard', emit_data, broadcast=True)
            
            # For debugging - also emit to update listener
            socketio.emit('update_chat_message_listener', json.dumps({
                'type': 'user_message',
                'message': message,
                'session_id': session_id
            }))
            
            # Acknowledge receipt
            return {'status': 'success', 'message': f'Message broadcast successfully: {message}'}
        except Exception as e:
            print(f"Error in handle_send_chat_message: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    # Add a new route to handle direct messages to Chainlit
    @socketio.on('direct_message_to_chainlit')
    def handle_direct_message(data):
        """Handle direct messages to Chainlit"""
        try:
            message = data.get('message')
            session_id = data.get('session_id', str(uuid.uuid4()))
            
            print(f"Received direct message for Chainlit: {message}")
            
            # Broadcast to all clients to ensure the iframe gets it
            socketio.emit('chat_message_from_dashboard', {
                'message': message,
                'session_id': session_id
            })
            
            return {'status': 'success', 'message': 'Direct message sent'}
        except Exception as e:
            print(f"Error in handle_direct_message: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    # Handle messages from open_chat_panel
    @socketio.on('open_chat_panel')
    def handle_open_panel(data):
        """Handle request to open chat panel"""
        try:
            message = data.get('message_sent')
            print(f"Request to open chat panel received. Message to send: {message}")
            
            # Emit a special event to open the chat panel
            socketio.emit('update_chat_message_listener', json.dumps({
                'type': 'open_chat',
                'message': message
            }))
            
            # Also emit a general open_floating_chat event
            socketio.emit('open_floating_chat', {'message': message})
            
            return {'status': 'success'}
        except Exception as e:
            print(f"Error in handle_open_panel: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    # Set up proper Socket.IO error handlers
    @socketio.on_error()
    def handle_error(e):
        """Handle Socket.IO errors"""
        handle_socketio_error(e)
    
    @socketio.on_error_default
    def handle_default_error(e):
        """Handle default Socket.IO errors"""
        handle_socketio_error(e)
    
    # Error handler for specific events
    @socketio.on_error('send_chat_message')
    def handle_send_chat_message_error(e):
        """Handle errors in send_chat_message event"""
        handle_socketio_error(e)
    
    @socketio.on_error('direct_message_to_chainlit')
    def handle_direct_message_error(e):
        """Handle errors in direct_message_to_chainlit event"""
        handle_socketio_error(e)