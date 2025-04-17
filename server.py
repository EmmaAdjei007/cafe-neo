# Updated server.py with new API endpoints for Chainlit

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
    
    # New API endpoints for Chainlit to call back
    
    @server.route('/api/navigate', methods=['POST'])
    def api_navigate():
        """API endpoint for navigation requests from Chainlit"""
        try:
            data = request.get_json()
            destination = data.get('destination')
            
            # Validate destination
            valid_destinations = ['menu', 'orders', 'delivery', 'profile', 'dashboard', 'home']
            if destination not in valid_destinations:
                return jsonify({'status': 'error', 'message': 'Invalid destination'})
            
            # Emit socket event to trigger navigation
            socketio.emit('navigate_to', {'destination': destination})
            
            return jsonify({
                'status': 'success', 
                'message': f'Navigation to {destination} requested',
                'destination': destination
            })
        except Exception as e:
            print(f"Error in navigation API: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)})
    
    @server.route('/api/place-order', methods=['POST'])
    def api_place_order():
        """API endpoint for placing orders from Chainlit"""
        try:
            order_data = request.get_json()
            
            # Validate order data
            if not order_data or not order_data.get('items'):
                return jsonify({'status': 'error', 'message': 'Invalid order data'})
            
            # Generate order ID if not provided
            if 'id' not in order_data:
                timestamp = int(time.time())
                order_data['id'] = f"ORD-{timestamp}"
            
            # Emit socket event with order data
            socketio.emit('order_update', order_data)
            
            return jsonify({
                'status': 'success', 
                'message': 'Order placed successfully',
                'order_id': order_data['id']
            })
        except Exception as e:
            print(f"Error in place-order API: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)})
    
    @server.route('/api/verify-token', methods=['GET'])
    def verify_token():
        """API endpoint to verify authentication tokens"""
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            try:
                # In a real app, you'd verify the token properly
                # Here's a simple implementation for demo purposes
                if '-' in token:
                    user_id = token.split('-')[0]
                    return jsonify({
                        'status': 'success',
                        'user_id': user_id, 
                        'is_authenticated': True
                    })
            except Exception as e:
                print(f"Error verifying token: {e}")
        
        return jsonify({
            'status': 'error',
            'message': 'Invalid token'
        }), 401


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
    
    # Enhanced direct message handler
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
            
            # Also emit a specific message for the Chainlit iframe
            socketio.emit('message_to_chainlit', {
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

    @socketio.on('chat_message_from_dashboard')
    def handle_chat_message_from_dashboard(data):
        """Handle chat messages from the dashboard"""
        try:
            message = data.get('message')
            session_id = data.get('session_id', str(uuid.uuid4()))
            
            print(f"Received chat message from dashboard: {message}")
            print(f"Session ID: {session_id}")
            
            # Broadcast to all clients to ensure the iframe gets it
            socketio.emit('chat_message_from_dashboard', {
                'message': message,
                'session_id': session_id
            }, broadcast=True)
            
            # Also update the chat message listener for compatibility
            socketio.emit('update_chat_message_listener', json.dumps({
                'type': 'user_message',
                'message': message,
                'session_id': session_id
            }))
            
            return {'status': 'success', 'message': 'Message broadcast successfully'}
        except Exception as e:
            print(f"Error in handle_chat_message_from_dashboard: {e}")
            return {'status': 'error', 'message': str(e)}
        
    # Update this in server.py to improve order handling

    # Enhanced order update handler
    # Enhanced order update handler
    @socketio.on('order_update')
    def handle_order_update(data):
        """
        Handle order updates from any source and broadcast to all clients
        
        Args:
            data (dict): Order data
        """
        try:
            print(f"Order update received: {data}")
            
            # Ensure data is in the right format
            if not isinstance(data, dict):
                print(f"Invalid order data format: {type(data)}")
                return {"status": "error", "message": "Invalid data format"}
                
            # Make sure there's an order ID
            if 'id' not in data:
                print("Order update missing ID")
                return {"status": "error", "message": "Order ID is required"}
            
            # Store the order in the database if it's a new order or update an existing one
            try:
                from app.data.database import create_order, update_order
                
                # Check if order already exists
                from app.data.database import get_order_by_id
                existing_order = get_order_by_id(data['id'])
                
                if existing_order:
                    # Update existing order
                    update_order(data['id'], data)
                    print(f"Updated existing order {data['id']}")
                else:
                    # Create new order
                    create_order(data)
                    print(f"Created new order {data['id']}")
            except Exception as db_error:
                print(f"Database error: {db_error}")
            
            # Broadcast the order update to all clients
            socketio.emit('order_update', data)
            
            # Also update the hidden div for compatibility with Dash callbacks
            socketio.emit('update_order_status', json.dumps(data))
            
            # Return success
            return {"status": "success", "message": "Order update broadcast successfully"}
        except Exception as e:
            print(f"Error handling order update: {e}")
            return {"status": "error", "message": str(e)}

    # Also add a specific handler for new orders from Chainlit
    @socketio.on('new_order')
    def handle_new_order(data):
        """
        Handle new orders specifically from Chainlit
        
        Args:
            data (dict): Order data
        """
        try:
            print(f"New order received from Chainlit: {data}")
            
            # Process through the main order update handler
            result = handle_order_update(data)
            
            # Additional processing specific to new orders
            # Update user's active order if applicable
            if 'user_id' in data:
                # This would update the user's active order in your user management system
                pass
            
            return result
        except Exception as e:
            print(f"Error handling new order: {e}")
            return {"status": "error", "message": str(e)}