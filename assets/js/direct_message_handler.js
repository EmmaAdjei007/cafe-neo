/**
 * Direct Message Handler for Neo Cafe
 * Handles sending messages from the dashboard to the Chainlit chatbot
 */

// Track if the Chainlit iframe has been loaded
let chainlitFrameLoaded = false;
let messageQueue = [];

// Define the global function to send messages to Chainlit
window.sendDirectMessageToChainlit = function(message) {
    console.log("Attempting to send message to Chainlit:", message);
    
    // First, make sure the chat panel is visible
    const panel = document.getElementById('floating-chat-panel');
    if (panel) {
        panel.style.display = 'flex';
        panel.className = 'floating-chat-panel';
    }
    
    // Find the Chainlit iframe
    const iframe = document.getElementById('floating-chainlit-frame');
    if (!iframe || !iframe.contentWindow) {
        console.error("Chainlit iframe not found or not accessible");
        queueMessage(message);
        return false;
    }
    
    // If iframe is not loaded yet, queue the message
    if (!chainlitFrameLoaded) {
        console.log("Chainlit iframe not yet loaded, queueing message");
        queueMessage(message);
        return false;
    }
    
    // If message is not a string, JSON stringify it
    if (typeof message !== 'string') {
        message = JSON.stringify(message);
    }
    
    // Try to send the message using multiple formats to ensure it works
    try {
        // Based on the messages you're seeing in Chainlit, this format is working:
        iframe.contentWindow.postMessage({
            type: 'direct_message',
            message: message
        }, '*');
        
        // Also try these alternative formats
        iframe.contentWindow.postMessage({
            type: 'userMessage',
            message: message
        }, '*');
        
        iframe.contentWindow.postMessage({
            kind: 'user_message',
            data: {
                content: message
            }
        }, '*');
        
        // Try simple string format as last resort
        iframe.contentWindow.postMessage(message, '*');
        
        console.log("Message sent to Chainlit iframe using multiple formats");
        return true;
    } catch (e) {
        console.error("Error sending message to Chainlit:", e);
        return false;
    }
};