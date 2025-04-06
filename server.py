# File: app/server.py (Enhanced with debugging)
import uuid
from flask import Flask, render_template, redirect, session, request, jsonify
from datetime import datetime
import requests
import os
from flask_socketio import SocketIO, emit
import json


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
    
    # API endpoints for Chainlit integration
    @server.route('/api/place-order', methods=['POST'])
    def place_order_api():
        """API endpoint to place an order"""
        try:
            # Get order data from request
            order_data = request.json
            print(f"Received order data: {json.dumps(order_data)}")
            
            # Validate order data
            if not order_data or 'items' not in order_data:
                print("Invalid order data")
                return jsonify({'status': 'error', 'message': 'Invalid order data'}), 400
            
            # Broadcast new order via SocketIO
            print(f"Broadcasting new order via SocketIO: {order_data.get('id')}")
            socketio.emit('new_order', order_data)
            
            return jsonify({
                'status': 'success',
                'message': 'Order placed successfully',
                'order_id': order_data.get('id')
            })
        
        except Exception as e:
            print(f"Error in place_order_api: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
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
    def handle_disconnect():
        """Handle client disconnection"""
        print(f'Client disconnected from Socket.IO: {request.sid}')
    
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
            socketio.emit('chat_message_from_dashboard', {
                'message': message,
                'session_id': session_id
            })
            
            # Acknowledge receipt
            return {'status': 'success', 'message': 'Message sent to Chainlit'}
        except Exception as e:
            print(f"Error in handle_send_chat_message: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @socketio.on('chainlit_message')
    def handle_chainlit_message(data):
        """Handle messages from Chainlit"""
        try:
            message_type = data.get('type')
            
            print(f"Received message from Chainlit: {message_type}")
            print(f"Full data: {json.dumps(data)}")
            
            # Forward the message to all clients
            socketio.emit('update_chat_message_listener', json.dumps(data))
            
            # For demo purposes, log all events
            socketio.emit('debug_log', {
                'source': 'chainlit',
                'type': message_type,
                'data': data
            })
            
            # Acknowledge receipt
            return {'status': 'success', 'message': 'Message received from Chainlit'}
        except Exception as e:
            print(f"Error in handle_chainlit_message: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @socketio.on_error()
    def handle_error(e):
        """Handle Socket.IO errors"""
        print(f"Socket.IO error: {str(e)}")

# Import datetime only needed for the ping endpoint