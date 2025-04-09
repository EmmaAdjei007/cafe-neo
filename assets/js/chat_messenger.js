/**
 * Chat Messenger for Neo Cafe
 * A client-side utility for sending messages to the Chainlit chatbot
 */

// Create a namespace for the chat client
window.chatClient = (function() {
    // Internal variables
    let isConnected = false;
    let messageQueue = [];
    let retryCount = 0;
    const MAX_RETRIES = 5;
    
    // Find all possible iframe paths
    function findChatIframe() {
        const iframes = [
            document.getElementById('floating-chainlit-frame'),
            document.getElementById('chatframe'),
            ...Array.from(document.querySelectorAll('iframe')).filter(
                iframe => iframe.src && iframe.src.includes('chainlit')
            )
        ].filter(Boolean);
        
        return iframes.length > 0 ? iframes[0] : null;
    }
    
    // Process queued messages
    function processQueue() {
        console.log(`[ChatClient] Processing ${messageQueue.length} queued messages`);
        
        // Create a copy of the queue and clear it
        const queueCopy = [...messageQueue];
        messageQueue = [];
        
        // Process each message
        queueCopy.forEach(message => {
            sendMessage(message, true);
        });
    }
    
    // Send a message using any available method
    function sendMessage(message, isFromQueue = false) {
        console.log(`[ChatClient] Sending message: ${message}`);
        
        // If message is not a string, try to convert it
        if (typeof message !== 'string') {
            try {
                message = JSON.stringify(message);
            } catch (e) {
                console.error('[ChatClient] Could not convert message to string:', e);
                return false;
            }
        }
        
        // Try different methods in order of preference
        
        // Method 1: Use the direct message handler
        if (window.sendDirectMessageToChainlit) {
            console.log('[ChatClient] Using directMessageToChainlit');
            const success = window.sendDirectMessageToChainlit(message);
            if (success) return true;
        }
        
        // Method 2: Post directly to iframe
        const iframe = findChatIframe();
        if (iframe && iframe.contentWindow) {
            try {
                console.log('[ChatClient] Using iframe postMessage');
                
                // Try different message formats
                const formats = [
                    { type: 'direct_message', message },
                    { type: 'userMessage', message },
                    { kind: 'user_message', data: { content: message } },
                    message // Plain string as fallback
                ];
                
                // Send all formats
                formats.forEach(format => {
                    iframe.contentWindow.postMessage(format, '*');
                });
                
                return true;
            } catch (e) {
                console.error('[ChatClient] Error posting to iframe:', e);
            }
        }
        
        // Method 3: Use Socket.IO if available
        if (window.socket && window.socket.emit) {
            try {
                console.log('[ChatClient] Using Socket.IO');
                window.socket.emit('chat_message_from_dashboard', {
                    message: message,
                    session_id: Date.now().toString()
                });
                return true;
            } catch (e) {
                console.error('[ChatClient] Error sending via Socket.IO:', e);
            }
        }
        
        // If we get here, no method succeeded
        if (!isFromQueue) {
            // Queue the message for retry if it's not already from the queue
            messageQueue.push(message);
            
            // Try again after a delay if we haven't exceeded the retry limit
            if (retryCount < MAX_RETRIES) {
                retryCount++;
                console.log(`[ChatClient] Message queued, will retry in ${retryCount}s`);
                setTimeout(processQueue, retryCount * 1000);
            }
        }
        
        return false;
    }
    
    // Initialize the chat client
    function init() {
        console.log('[ChatClient] Initializing');
        
        // Listen for iframe ready events
        window.addEventListener('message', function(event) {
            // Check if it's a ready message
            if (event.data && 
                (event.data === 'ready' || 
                 (typeof event.data === 'object' && event.data.type === 'iframe_ready'))) {
                console.log('[ChatClient] Iframe reported ready');
                isConnected = true;
                retryCount = 0;
                processQueue();
            }
        });
        
        // Set up retry logic
        setTimeout(function checkConnection() {
            if (!isConnected && messageQueue.length > 0) {
                console.log('[ChatClient] Trying to process queue...');
                processQueue();
            }
            setTimeout(checkConnection, 5000); // Check every 5 seconds
        }, 5000);
        
        return {
            sendMessage,
            getQueueLength: () => messageQueue.length,
            isConnected: () => isConnected
        };
    }
    
    // Return the public API
    return init();
})();

// Make sure chat panel is visible when needed
document.addEventListener('DOMContentLoaded', function() {
    // Add click listeners to quick action buttons
    const quickActionButtons = [
        'quick-order-btn', 'quick-track-btn', 'quick-popular-btn', 'quick-hours-btn',
        'faq-menu-btn', 'faq-hours-btn', 'faq-robot-btn', 'faq-popular-btn',
        'menu-faq-btn', 'hours-faq-btn', 'robot-faq-btn', 'popular-faq-btn'
    ];
    
    quickActionButtons.forEach(btnId => {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.addEventListener('click', function() {
                // Show chat panel
                const panel = document.getElementById('floating-chat-panel');
                if (panel) {
                    panel.style.display = 'flex';
                    panel.className = 'floating-chat-panel';
                }
            });
        }
    });
});