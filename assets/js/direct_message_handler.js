// Create a new file: assets/js/direct_message_handler.js

/**
 * Direct Message Handler
 * Handles messages directly between the dashboard and Chainlit
 */

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Direct message handler initialized');
    
    // Connect to socket.io
    if (typeof io !== 'undefined') {
        const socket = io.connect();
        
        // Log connection
        socket.on('connect', function() {
            console.log('Connected to Socket.IO for direct messaging');
        });
        
        // Handle open_chat_panel event
        socket.on('open_chat_panel', function(data) {
            console.log('Received open_chat_panel event:', data);
            
            // Find and click the chat button to open the panel
            const chatButton = document.getElementById('floating-chat-button');
            if (chatButton) {
                console.log('Opening chat panel');
                chatButton.click();
            }
        });
        
        // Handle direct message events
        socket.on('chat_message_from_dashboard', function(data) {
            console.log('Received direct message from dashboard:', data);
            
            // Wait a moment for the panel to open if needed
            setTimeout(function() {
                forwardMessageToChainlit(data.message);
            }, 500);
        });
        
        // Handle voice toggle
        socket.on('toggle_voice_mode', function(data) {
            console.log('Received voice toggle event:', data);
            
            // Here you would toggle voice mode if implemented
        });
    } else {
        console.error('Socket.IO not available for direct message handler');
    }
    
    // Function to forward message to Chainlit
    function forwardMessageToChainlit(message) {
        console.log('Forwarding message to Chainlit:', message);
        
        // Find the Chainlit iframe
        const iframe = document.getElementById('floating-chainlit-frame');
        if (!iframe) {
            console.error('Chainlit iframe not found');
            return false;
        }
        
        try {
            // Method 1: Post a message to the iframe
            iframe.contentWindow.postMessage({
                type: 'direct_message',
                message: message
            }, '*');
            
            // Method 2: Use the chat_message_from_dashboard event which may be handled in the iframe
            const chatEvent = new CustomEvent('chat_message_from_dashboard', { 
                detail: { message: message } 
            });
            iframe.dispatchEvent(chatEvent);
            
            return true;
        } catch (error) {
            console.error('Error forwarding message to Chainlit:', error);
            return false;
        }
    }
});