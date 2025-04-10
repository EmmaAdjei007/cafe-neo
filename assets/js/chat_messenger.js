// assets/js/chat_messenger.js

// Create socket.io connection when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing NeoCafe chat messenger');
    initializeChatMessenger();
});

function initializeChatMessenger() {
    // Initialize Socket.IO connection if not already done
    if (!window.chatSocket && io) {
        window.chatSocket = io.connect();
        console.log('Socket.IO connection initialized');
        
        // Set up socket event listeners
        setupSocketListeners();
    } else if (!io) {
        console.warn('Socket.IO not loaded, will retry in 1 second');
        setTimeout(initializeChatMessenger, 1000);
        return;
    } else {
        console.log('Chat socket already initialized');
    }
    
    // Create message bridge to share between components
    if (!window.messageBridge) {
        window.messageBridge = {
            sendMessage: sendDirectMessageToChainlit,
            receiveMessage: function(callback) {
                if (typeof callback === 'function') {
                    this.messageCallback = callback;
                }
            },
            messageCallback: null,
            navigation: {
                navigate: navigateFromChat,
                callback: null
            },
            orderUpdate: {
                updateOrder: updateOrderFromChat,
                callback: null
            }
        };
    }
    
    // Expose functions globally for other components to use
    window.sendDirectMessageToChainlit = sendDirectMessageToChainlit;
    window.navigateFromChat = navigateFromChat;
    window.updateOrderFromChat = updateOrderFromChat;
}

function setupSocketListeners() {
    // Skip if socket not available
    if (!window.chatSocket) return;
    
    // Ensure we're not adding duplicate listeners
    window.chatSocket.off('message_to_chainlit');
    window.chatSocket.off('chat_message_from_dashboard');
    window.chatSocket.off('navigation_command');
    window.chatSocket.off('order_update');
    
    // Listen for messages to Chainlit
    window.chatSocket.on('message_to_chainlit', function(data) {
        console.log('Received message_to_chainlit:', data);
        forwardMessageToChainlitIframe(data.message);
    });
    
    // Listen for chat messages from dashboard
    window.chatSocket.on('chat_message_from_dashboard', function(data) {
        console.log('Received chat_message_from_dashboard:', data);
        forwardMessageToChainlitIframe(data.message);
    });
    
    // Listen for navigation commands
    window.chatSocket.on('navigate_to', function(data) {
        console.log('Received navigate_to:', data);
        if (data && data.destination) {
            navigateFromChat(data.destination);
        }
    });
    
    // Listen for order updates
    window.chatSocket.on('order_update', function(data) {
        console.log('Received order_update:', data);
        if (data && data.id) {
            updateOrderFromChat(data);
        }
    });
    
    console.log('Socket listeners setup complete');
}

function getSessionId() {
    // Try to get from localStorage
    let sessionId = localStorage.getItem('neocafe_session_id');
    if (!sessionId) {
        // Generate random ID
        sessionId = Math.random().toString(36).substring(2, 15) + 
                   Math.random().toString(36).substring(2, 15);
        localStorage.setItem('neocafe_session_id', sessionId);
    }
    return sessionId;
}

function sendDirectMessageToChainlit(message) {
    console.log('Sending message to Chainlit:', message);
    
    // Check if message is empty
    if (!message || message.trim() === '') {
        console.warn('Attempted to send empty message to Chainlit');
        return false;
    }
    
    // Try multiple methods to send message to ensure delivery
    let successCount = 0;
    
    // Method 1: Socket.IO
    if (window.chatSocket) {
        try {
            window.chatSocket.emit('direct_message_to_chainlit', {
                message: message,
                session_id: getSessionId()
            });
            console.log('Message sent via Socket.IO');
            successCount++;
        } catch (err) {
            console.error('Failed to send message via Socket.IO:', err);
        }
    }
    
    // Method 2: iframe postMessage
    try {
        const iframe = document.getElementById('floating-chainlit-frame');
        if (iframe && iframe.contentWindow) {
            iframe.contentWindow.postMessage({
                type: 'userMessage',
                message: message
            }, '*');
            console.log('Message sent via iframe postMessage');
            successCount++;
        }
    } catch (err) {
        console.error('Failed to send message via iframe postMessage:', err);
    }
    
    // Method 3: Direct message to window.sendMessage if available
    try {
        const iframe = document.getElementById('floating-chainlit-frame');
        if (iframe && iframe.contentWindow && iframe.contentWindow.sendMessage) {
            iframe.contentWindow.sendMessage(message);
            console.log('Message sent via iframe.contentWindow.sendMessage');
            successCount++;
        }
    } catch (err) {
        console.error('Failed to send message via iframe.contentWindow.sendMessage:', err);
    }
    
    // Check if message was sent successfully through any method
    return successCount > 0;
}

function forwardMessageToChainlitIframe(message) {
    // Method 1: Try using iframe postMessage
    try {
        const iframe = document.getElementById('floating-chainlit-frame');
        if (iframe && iframe.contentWindow) {
            iframe.contentWindow.postMessage({
                type: 'userMessage',
                message: message
            }, '*');
            console.log('Message forwarded to Chainlit iframe via postMessage');
            return true;
        }
    } catch (err) {
        console.error('Failed to forward message via iframe postMessage:', err);
    }
    
    // Method 2: Try using sendMessage function in iframe if available
    try {
        const iframe = document.getElementById('floating-chainlit-frame');
        if (iframe && iframe.contentWindow && iframe.contentWindow.sendMessage) {
            iframe.contentWindow.sendMessage(message);
            console.log('Message forwarded to Chainlit iframe via sendMessage function');
            return true;
        }
    } catch (err) {
        console.error('Failed to forward message via iframe sendMessage function:', err);
    }
    
    console.warn('Failed to forward message to Chainlit iframe');
    return false;
}

function navigateFromChat(destination) {
    console.log('Navigating from chat to:', destination);
    
    // Validate destination
    const validDestinations = ['menu', 'orders', 'delivery', 'profile', 'dashboard', 'home'];
    
    if (!validDestinations.includes(destination.toLowerCase())) {
        console.warn('Invalid navigation destination:', destination);
        return false;
    }
    
    // Map destination to URL
    const destinationMap = {
        'menu': '/menu',
        'orders': '/orders',
        'delivery': '/delivery',
        'profile': '/profile',
        'dashboard': '/dashboard',
        'home': '/'
    };
    
    const targetUrl = destinationMap[destination.toLowerCase()] || '/';
    
    // Check if we need to navigate
    if (window.location.pathname === targetUrl) {
        console.log('Already on the requested page');
        return true;
    }
    
    // Trigger navigation
    if (window.messageBridge && window.messageBridge.navigation.callback) {
        // Use callback if available
        window.messageBridge.navigation.callback(destination);
        return true;
    } else {
        // Fallback to direct navigation
        window.location.href = targetUrl;
        return true;
    }
}

function updateOrderFromChat(orderData) {
    console.log('Updating order from chat:', orderData);
    
    // Validate order data
    if (!orderData || !orderData.items) {
        console.warn('Invalid order data received');
        return false;
    }
    
    // Store in localStorage for persistence
    localStorage.setItem('current_order', JSON.stringify(orderData));
    
    // Call callback if available
    if (window.messageBridge && window.messageBridge.orderUpdate.callback) {
        window.messageBridge.orderUpdate.callback(orderData);
        return true;
    }
    
    // Dispatch custom event for components to listen for
    const updateEvent = new CustomEvent('neo-cafe-order-update', {
        detail: orderData,
        bubbles: true
    });
    document.dispatchEvent(updateEvent);
    
    return true;
}

// Set up listener for messages from Chainlit iframe
window.addEventListener('message', function(event) {
    // Check if message is from our Chainlit iframe
    const iframe = document.getElementById('floating-chainlit-frame');
    if (iframe && event.source === iframe.contentWindow) {
        console.log('Received message from Chainlit iframe:', event.data);
        
        // Handle different message types
        if (event.data && event.data.type) {
            switch (event.data.type) {
                case 'navigation':
                    if (event.data.destination) {
                        navigateFromChat(event.data.destination);
                    }
                    break;
                    
                case 'order_update':
                    if (event.data.order) {
                        updateOrderFromChat(event.data.order);
                    }
                    break;
                    
                case 'iframe_ready':
                    console.log('Chainlit iframe is ready');
                    // You can add initialization code here if needed
                    break;
                    
                default:
                    console.log('Unhandled message type from Chainlit iframe:', event.data.type);
            }
        }
    }
});