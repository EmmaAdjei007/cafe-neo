/**
 * Direct Message Handler for communicating with Chainlit iframe
 * This file handles sending messages directly to the Chainlit iframe using postMessage
 */

(function() {
    // Debug mode - set to true to see debug messages in console
    const DEBUG = window.DEBUG_MODE || false;
    
    // Debug log helper
    function debugLog(...args) {
        if (DEBUG) {
            console.log('[DirectMessageHandler]', ...args);
        }
    }
    
    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        debugLog('Initializing Direct Message Handler');
        
        // Store a reference to the Chainlit iframe
        const getChainlitIframe = () => document.getElementById('floating-chainlit-frame');
        
        // Function to send message to the iframe
        window.sendDirectMessageToChainlit = function(message) {
            debugLog('Attempting to send message to Chainlit:', message);
            
            const iframe = getChainlitIframe();
            if (!iframe) {
                debugLog('Error: Chainlit iframe not found in DOM');
                return false;
            }
            
            try {
                // Try to send via postMessage in the format Chainlit expects
                iframe.contentWindow.postMessage({
                    type: 'userMessage',
                    message: message
                }, '*');
                
                // Also try older/alternate Chainlit format as fallback
                iframe.contentWindow.postMessage({
                    kind: 'user_message',
                    data: {
                        content: message
                    }
                }, '*');
                
                debugLog('Message sent via postMessage');
                return true;
            } catch (e) {
                debugLog('Error sending via postMessage:', e);
                return false;
            }
        };
        
        // Function to open the chat panel and send a message
        window.sendAndOpenChat = function(message) {
            debugLog('Opening chat panel and sending message:', message);
            
            // First make sure the chat panel is visible
            const chatPanel = document.getElementById('floating-chat-panel');
            if (chatPanel) {
                // Show the panel
                chatPanel.style.display = 'flex';
                
                // Set a class to ensure it's fully visible
                chatPanel.className = 'floating-chat-panel';
                
                // Create a small delay to ensure the iframe is loaded
                setTimeout(() => {
                    window.sendDirectMessageToChainlit(message);
                }, 500);
                
                return true;
            }
            
            debugLog('Error: Chat panel not found');
            return false;
        };
        
        // Listen for messages from the iframe
        window.addEventListener('message', function(event) {
            // Filter messages from the Chainlit iframe
            const iframe = getChainlitIframe();
            if (iframe && event.source === iframe.contentWindow) {
                debugLog('Received message from Chainlit iframe:', event.data);
                
                // Process specific message types
                if (event.data && event.data.type === 'navigation') {
                    debugLog('Navigation requested:', event.data.destination);
                    // Handle navigation requests from the iframe
                    if (event.data.destination) {
                        window.location.href = '/' + event.data.destination;
                    }
                }
            }
        });
    });
})();