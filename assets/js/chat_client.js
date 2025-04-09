/**
 * Client-side Socket.IO handler for Neo Cafe chatbot integration
 */

(function() {
    // Debug mode
    const DEBUG = window.DEBUG_MODE || false;
    
    // Debug log helper
    function debugLog(...args) {
        if (DEBUG) {
            console.log('[ChatClient]', ...args);
        }
    }
    
    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        debugLog('Initializing chat client');
        
        // Check if socket.io is available
        if (!window.io) {
            console.error('Socket.IO not loaded. Make sure to include socket.io.js before this script.');
            return;
        }
        
        // Initialize Socket.IO
        let socket;
        try {
            socket = io.connect();
            window.socket = socket; // Store for global access
            debugLog('Socket.IO connected');
        } catch (e) {
            console.error('Error connecting to Socket.IO:', e);
            return;
        }
        
        // Set up event listeners
        socket.on('connect', function() {
            debugLog('Socket.IO connection established');
            
            // Send a ping to test connection
            socket.emit('ping', 'Chat client initialized');
        });
        
        socket.on('disconnect', function() {
            debugLog('Socket.IO connection lost');
        });
        
        socket.on('chat_message_from_dashboard', function(data) {
            debugLog('Received chat_message_from_dashboard:', data);
            
            // Try to forward to the Chainlit iframe
            try {
                const iframe = document.getElementById('floating-chainlit-frame');
                if (iframe && iframe.contentWindow) {
                    // Send the message to the iframe
                    iframe.contentWindow.postMessage({
                        type: 'direct_message',
                        message: data.message
                    }, '*');
                    debugLog('Message forwarded to iframe');
                }
            } catch (e) {
                debugLog('Error forwarding message to iframe:', e);
            }
        });
        
        socket.on('open_floating_chat', function(data) {
            debugLog('Received open_floating_chat:', data);
            
            // Open the floating chat panel
            const chatPanel = document.getElementById('floating-chat-panel');
            if (chatPanel) {
                chatPanel.style.display = 'flex';
                chatPanel.className = 'floating-chat-panel';
                
                // If a message is provided, forward it after a short delay
                if (data && data.message) {
                    setTimeout(() => {
                        if (window.sendDirectMessageToChainlit) {
                            window.sendDirectMessageToChainlit(data.message);
                        }
                    }, 500);
                }
            }
        });
        
        // Handle errors
        socket.on('error', function(error) {
            console.error('Socket.IO error:', error);
        });
        
        // Debug events - log all events
        socket.onAny((event, ...args) => {
            debugLog(`Event '${event}' received:`, args);
        });
        
        // Expose methods globally
        window.chatClient = {
            sendMessage: function(message, sessionId) {
                debugLog('Sending message via Socket.IO:', message);
                
                socket.emit('send_chat_message', {
                    message: message,
                    session_id: sessionId || window.sessionId || undefined
                });
            },
            
            openChatWithMessage: function(message) {
                debugLog('Opening chat with message:', message);
                
                // First try client-side method
                if (window.sendAndOpenChat) {
                    window.sendAndOpenChat(message);
                    return;
                }
                
                // Fallback to Socket.IO
                socket.emit('open_chat_panel', {
                    message_sent: message
                });
            }
        };
    });
})();