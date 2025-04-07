/**
 * Clientside callback functions for Neo Cafe
 * This file must be placed in the assets/js directory
 */

// Create the clientside namespace if it doesn't exist
if (!window.dash_clientside) {
    window.dash_clientside = {};
}

// Create the clientside namespace
window.dash_clientside.clientside = {
    /**
     * Listen for events in the chat and update the chat message listener
     * This function is called by a Dash clientside callback
     * 
     * @returns {string} Message JSON to update the hidden div
     */
    updateChatListener: function() {
        console.log('Initializing chat message listener');
        
        // Initialize the message handler only once
        if (!window._chatListenerInitialized) {
            window._chatListenerInitialized = true;
            
            // Listen for message events from the socket
            if (window.socket) {
                console.log('Found socket object, setting up listener');
                window.socket.on('update_chat_message_listener', function(data) {
                    console.log('Received update_chat_message_listener:', data);
                    window._lastChatMessage = data;
                });
            } else {
                console.log('Socket not found, will set up listener when socket connects');
                // Wait for socket to be available
                window._socketCheckInterval = setInterval(function() {
                    if (window.socket) {
                        console.log('Socket now available, setting up listener');
                        window.socket.on('update_chat_message_listener', function(data) {
                            console.log('Received update_chat_message_listener:', data);
                            window._lastChatMessage = data;
                        });
                        clearInterval(window._socketCheckInterval);
                    }
                }, 1000);
            }
            
            // Also listen for postMessage events from the iframe
            window.addEventListener('message', function(event) {
                // Check if it's a message we care about
                if (event.data && (event.data.type === 'navigation' || 
                                   event.data.type === 'order_update' ||
                                   event.data.type === 'chat_message')) {
                    console.log('Received postMessage event:', event.data);
                    window._lastChatMessage = JSON.stringify(event.data);
                }
            });
        }
        
        // Return the last message if available
        return window._lastChatMessage || null;
    }
};

// Initialize socket listener as soon as DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing socket listener');
    
    // Set up an interval to check if socket is available
    const socketCheck = setInterval(function() {
        // Check if socket.io is loaded and connected
        if (typeof io !== 'undefined') {
            console.log('Socket.io found, connecting');
            // Store socket in window object so it's accessible to callback
            window.socket = io.connect();
            
            // Set up listener for update events
            window.socket.on('update_chat_message_listener', function(data) {
                console.log('Received update_chat_message_listener:', data);
                window._lastChatMessage = data;
            });
            
            // Clear the interval once we've set up the listener
            clearInterval(socketCheck);
        }
    }, 1000);
});