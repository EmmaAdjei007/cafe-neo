/**
 * Order message handler for Neo Cafe
 * This file must be placed in the assets/js directory
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Order handler initialized');
    
    // Function to process order updates from Chainlit
    function processOrderUpdate(data) {
        console.log('Processing order update:', data);
        
        // If we have a socket connection, relay the order update
        if (window.socket) {
            try {
                window.socket.emit('order_update', data);
                console.log('Order update sent to server via socket');
            } catch (e) {
                console.error('Error sending order update via socket:', e);
            }
        } else {
            console.warn('Socket not available, cannot send order update');
        }
        
        // Update local storage as a backup mechanism
        try {
            // Save the current order
            localStorage.setItem('currentOrder', JSON.stringify(data));
            
            // Add to order history
            let orderHistory = JSON.parse(localStorage.getItem('orderHistory') || '[]');
            
            // Check if this order is already in history
            const existingOrderIndex = orderHistory.findIndex(order => order.id === data.id);
            if (existingOrderIndex >= 0) {
                // Update existing order
                orderHistory[existingOrderIndex] = data;
            } else {
                // Add new order
                orderHistory.unshift(data);
            }
            
            // Limit history size
            if (orderHistory.length > 20) {
                orderHistory = orderHistory.slice(0, 20);
            }
            
            localStorage.setItem('orderHistory', JSON.stringify(orderHistory));
            console.log('Order saved to local storage');
        } catch (e) {
            console.error('Error saving order to local storage:', e);
        }
        
        // Update UI directly where possible
        updateOrderUI(data);
    }
    
    // Function to update order UI elements directly
    function updateOrderUI(orderData) {
        try {
            // Update current order status in chat panel if it exists
            const currentOrderStatus = document.getElementById('current-order-status');
            if (currentOrderStatus) {
                // Format items into readable text
                let itemsText = '';
                if (orderData.items && Array.isArray(orderData.items)) {
                    const itemCount = orderData.items.length;
                    itemsText = `${itemCount} item${itemCount !== 1 ? 's' : ''}`;
                }
                
                // Format currency
                const totalText = `$${(orderData.total || 0).toFixed(2)}`;
                
                // Get appropriate status color
                const statusColors = {
                    'New': 'secondary',
                    'In Progress': 'primary',
                    'Ready': 'info',
                    'Completed': 'success',
                    'Delivered': 'success',
                    'Cancelled': 'danger'
                };
                const statusColor = statusColors[orderData.status] || 'secondary';
                
                // Create HTML for order status
                currentOrderStatus.innerHTML = `
                    <h6 class="card-subtitle mb-2">Order #${orderData.id}</h6>
                    <p><strong>Status: </strong><span class="text-${statusColor}">${orderData.status}</span></p>
                    <p><strong>Items: </strong><span>${itemsText}</span></p>
                    <p><strong>Total: </strong><span>${totalText}</span></p>
                    <p><strong>Delivery: </strong><span>${orderData.delivery_location || 'Not specified'}</span></p>
                    <button id="view-order-details-btn" class="btn btn-primary btn-sm mt-2">View Details</button>
                `;
                
                console.log('Current order status UI updated');
            } else {
                console.log('Current order status element not found');
            }
        } catch (e) {
            console.error('Error updating order UI:', e);
        }
    }
    
    // Listen for message events from the Chainlit iframe
    window.addEventListener('message', function(event) {
        // Validate source for security
        if (event.source === document.getElementById('floating-chainlit-frame')?.contentWindow ||
            event.source === document.getElementById('chainlit-frame')?.contentWindow) {
            
            const data = event.data;
            
            // Check for order-related messages
            if (data && typeof data === 'object') {
                // Check various formats that Chainlit might send
                if (data.type === 'order_update' || data.type === 'new_order') {
                    processOrderUpdate(data);
                } else if (data.kind === 'order' && data.data) {
                    processOrderUpdate(data.data);
                } else if (data.message_type === 'order' && data.content) {
                    processOrderUpdate(data.content);
                }
            }
        }
    });
    
    // Check for order data in local storage on page load
    try {
        const savedOrder = localStorage.getItem('currentOrder');
        if (savedOrder) {
            const orderData = JSON.parse(savedOrder);
            console.log('Found saved order in local storage:', orderData);
            
            // Update UI with saved order
            updateOrderUI(orderData);
            
            // Send to server if socket is available
            if (window.socket) {
                window.socket.emit('order_update', orderData);
                console.log('Sent saved order to server');
            }
        }
    } catch (e) {
        console.error('Error loading saved order:', e);
    }
});