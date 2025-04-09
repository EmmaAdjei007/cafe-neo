# File: app/callbacks/__init__.py

def register_all_callbacks(app, socketio):
    """
    Register all callbacks for the application
    
    Args:
        app: Dash application instance
        socketio: SocketIO instance for real-time communication
    """
    # Import and register callback modules
    from app.callbacks.auth_callbacks import register_callbacks as register_auth
    from app.callbacks.navigation_callbacks import register_callbacks as register_nav
    from app.callbacks.dashboard_callbacks import register_callbacks as register_dashboard
    from app.callbacks.menu_callbacks import register_callbacks as register_menu
    from app.callbacks.order_callbacks import register_callbacks as register_orders
    from app.callbacks.delivery_callbacks import register_callbacks as register_delivery
    from app.callbacks.chat_callbacks import register_callbacks as register_chat
    #==============================================================================
    from app.callbacks.direct_button_callbacks import register_callbacks as register_direct_buttons
    
    # Register all callback modules with the app
    register_auth(app)
    register_nav(app)
    register_dashboard(app, socketio)
    register_menu(app)
    register_orders(app, socketio)
    register_delivery(app, socketio)
    register_chat(app, socketio)
    
    # Register SocketIO event handlers
    register_socketio_handlers(socketio)
    #==============================================================================
    register_direct_buttons(app, socketio)
    
    print("All callbacks registered successfully!")


def register_socketio_handlers(socketio):
    """
    Register SocketIO event handlers for real-time communication
    
    Args:
        socketio: SocketIO instance
    """
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print('Client connected')
    
    # Fix: Add the sid parameter to handle_disconnect
    @socketio.on('disconnect')
    def handle_disconnect(sid=None):
        """Handle client disconnection"""
        print(f'Client disconnected: {sid}')
    
    @socketio.on('new_order')
    def handle_new_order(data):
        """
        Handle new order notification
        
        Args:
            data (dict): Order data
        """
        # Broadcast the new order to all connected clients
        socketio.emit('order_update', data)
    
    @socketio.on('order_status_change')
    def handle_status_change(data):
        """
        Handle order status change
        
        Args:
            data (dict): Status data
        """
        # Broadcast the status change to all connected clients
        socketio.emit('order_update', data)
    
    @socketio.on('robot_location_update')
    def handle_robot_update(data):
        """
        Handle robot location update
        
        Args:
            data (dict): Robot location data
        """
        # Broadcast the robot location update to all connected clients
        socketio.emit('robot_update', data)
        
    @socketio.on_error()
    def handle_error(e):
        """Handle Socket.IO errors"""
        print(f"Socket.IO error: {str(e)}")
        
    @socketio.on_error_default
    def handle_default_error(e):
        """Handle default Socket.IO errors"""
        print(f"Socket.IO default error: {str(e)}")