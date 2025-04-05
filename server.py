# File: app/server.py
# This file adds custom routes to the Flask server for integration

import uuid
from flask import Flask, render_template, redirect, session, request, jsonify
import requests
import os
from flask_socketio import SocketIO


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
        chainlit_url = os.environ.get('CHAINLIT_URL', 'http://localhost:8000')
        
        # Create a session ID if one doesn't exist
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        # Pass along any query parameters
        query_string = request.query_string.decode('utf-8')
        if query_string:
            chainlit_url = f"{chainlit_url}?{query_string}"
        
        return render_template('chainlit_embed.html', chainlit_url=chainlit_url)
    
    # API endpoints for Chainlit integration
    @server.route('/api/place-order', methods=['POST'])
    def place_order_api():
        """API endpoint to place an order"""
        try:
            # Get order data from request
            order_data = request.json
            
            # Validate order data
            if not order_data or 'items' not in order_data:
                return jsonify({'status': 'error', 'message': 'Invalid order data'}), 400
            
            # Save order to database (would be implemented in production)
            # For demo purposes, we'll just return success
            
            # Broadcast new order via SocketIO
            socketio.emit('new_order', order_data)
            
            return jsonify({
                'status': 'success',
                'message': 'Order placed successfully',
                'order_id': order_data.get('id')
            })
        
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @server.route('/api/robot/<order_id>', methods=['GET'])
    def get_robot_status_api(order_id):
        """API endpoint to get robot status for an order"""
        try:
            # In production, this would query the robot service or database
            # For demo purposes, we'll return simulated data
            import random
            
            # Simulate different statuses
            statuses = ['preparing', 'in transit', 'delivered', 'returning']
            status = random.choice(statuses)
            
            # If it's in transit, generate a random progress percentage
            progress = random.randint(10, 90) if status == 'in transit' else None
            
            return jsonify({
                'status': status,
                'order_id': order_id,
                'progress': progress,
                'estimated_delivery_time': '10 minutes' if status == 'in transit' else None,
                'robot_id': 'R-' + str(random.randint(100, 999))
            })
        
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    # Add a simple health check route
    @server.route('/chainlit-status')
    def chainlit_status():
        """Check if Chainlit is running"""
        chainlit_url = os.environ.get('CHAINLIT_URL', 'http://localhost:8000')
        try:
            response = requests.get(f"{chainlit_url}/health", timeout=2)
            if response.status_code == 200:
                return jsonify({"status": "ok"})
            else:
                return jsonify({"status": "error", "message": f"Chainlit returned status code {response.status_code}"}), 503
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 503