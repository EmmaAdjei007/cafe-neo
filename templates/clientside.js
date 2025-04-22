//# Update this in templates/clientside.js or in your assets/js directory

if (!window.dash_clientside) {
    window.dash_clientside = {};
}

window.dash_clientside.clientside = {
    /**
     * Update chat authentication - use data property instead of className
     */
    updateChatAuth: function(userData) {
        console.log('Updating chat authentication with user data:', userData);
        
        // Your existing auth update code here...
        
        return userData; // Return the data instead of modifying className
    },
    
    /**
     * Listen for events in the chat and update the chat message listener
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