// File: assets/js/chat_client.js

/**
 * Simplified chat client that focuses on direct iframe communication
 * without relying on Socket.IO
 */

// Define the clientside namespace for Dash callbacks
if (!window.clientside) {
    window.clientside = {};
}

// Track if the iframe is ready
let iframeReady = false;

/**
 * Update chat listener for messages from the Chainlit iframe
 */
window.clientside.updateChatListener = function() {
    console.log("Setting up message listener for Chainlit iframe");
    
    // Set up message listener for communication from iframe
    window.addEventListener('message', function(event) {
        // Only handle messages from the Chainlit iframe
        const iframe = document.getElementById('floating-chainlit-frame');
        if (iframe && event.source === iframe.contentWindow) {
            console.log("Received message from Chainlit iframe:", event.data);
            
            // Mark iframe as ready when we receive any message from it
            iframeReady = true;
            
            // Store the message data in the hidden div
            const chatListener = document.getElementById('chat-message-listener');
            if (chatListener) {
                chatListener.textContent = JSON.stringify(event.data);
                
                // Trigger a custom event to ensure callbacks pick up the change
                chatListener.dispatchEvent(new Event('change'));
            }
        }
    });
    
    return "";  // Return empty string as output
};

/**
 * Send a message directly to the Chainlit iframe
 */
function sendMessageToChainlit(message) {
    console.log("Attempting to send message to Chainlit:", message);
    const iframe = document.getElementById('floating-chainlit-frame');
    
    if (!iframe) {
        console.error("Chainlit iframe not found");
        alert("Chat interface not loaded. Please refresh the page and try again.");
        return false;
    }
    
    if (!iframe.contentWindow) {
        console.error("Iframe contentWindow not available");
        alert("Cannot communicate with chat interface. Please refresh the page.");
        return false;
    }
    
    // Type can be different depending on Chainlit implementation
    // Try all known message formats
    const messagePayloads = [
        // Format 1: Standard userMessage format
        {
            type: 'userMessage',
            message: message
        },
        // Format 2: Direct message format
        {
            message: message,
            type: 'message'
        },
        // Format 3: Chat message format
        {
            type: 'chat_message',
            content: message
        }
    ];
    
    // Try each format
    for (const payload of messagePayloads) {
        try {
            iframe.contentWindow.postMessage(payload, '*');
            console.log(`Sent message using format: ${JSON.stringify(payload)}`);
        } catch (e) {
            console.error(`Error sending format ${JSON.stringify(payload)}:`, e);
        }
    }
    
    // Show indicator that the message was sent
    showFloatingFeedback(`Message sent: ${message}`);
    
    // Also ensure the chat panel is visible
    showChatPanel();
    
    return true;
}

/**
 * Show a floating feedback message 
 */
function showFloatingFeedback(message, duration = 3000) {
    // Create or find the feedback element
    let feedback = document.getElementById('chat-feedback-popup');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.id = 'chat-feedback-popup';
        feedback.style.position = 'fixed';
        feedback.style.bottom = '150px';
        feedback.style.right = '20px';
        feedback.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        feedback.style.color = 'white';
        feedback.style.padding = '10px 15px';
        feedback.style.borderRadius = '5px';
        feedback.style.zIndex = '9999';
        feedback.style.transition = 'opacity 0.3s ease';
        feedback.style.opacity = '0';
        document.body.appendChild(feedback);
    }
    
    // Set message and show
    feedback.textContent = message;
    feedback.style.opacity = '1';
    
    // Hide after duration
    setTimeout(() => {
        feedback.style.opacity = '0';
    }, duration);
}

/**
 * Show the chat panel if it's hidden
 */
function showChatPanel() {
    const chatPanel = document.getElementById('floating-chat-panel');
    if (chatPanel && chatPanel.style.display === 'none') {
        chatPanel.style.display = 'flex';
    }
}

// Add manual message handling for all quick action buttons
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, setting up quick action button handlers");
    
    // Map of button IDs to message text
    const messageMap = {
        'quick-order-btn': 'I\'d like to place an order',
        'quick-track-btn': 'Track my order',
        'quick-popular-btn': 'What are your popular items?',
        'quick-hours-btn': 'What are your operating hours?',
        'faq-menu-btn': 'Show me the menu',
        'faq-hours-btn': 'When are you open?',
        'faq-robot-btn': 'How does robot delivery work?',
        'faq-popular-btn': "What\'s your most popular coffee?",
        'menu-faq-btn': 'Show me the menu',
        'hours-faq-btn': 'When are you open?',
        'robot-faq-btn': 'How does robot delivery work?',
        'popular-faq-btn': "What\'s your most popular coffee?",
        'voice-toggle-btn': 'Toggle voice mode'
    };
    
    // Helper to ensure we have all buttons
    function setupDirectHandlers() {
        console.log("Setting up direct button handlers");
        
        // Add handlers to all potential buttons
        Object.keys(messageMap).forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                console.log(`Found button: ${buttonId}`);
                
                // Add direct click handling
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const message = messageMap[buttonId];
                    console.log(`Button ${buttonId} clicked, sending: "${message}"`);
                    sendMessageToChainlit(message);
                    return false;
                });
            }
        });
    }
    
    // First attempt when DOM is ready
    setupDirectHandlers();
    
    // Second attempt after a delay to ensure all elements are rendered
    setTimeout(setupDirectHandlers, 2000);
    
    // Add additional handlers whenever the chat panel is shown
    const chatButton = document.getElementById('floating-chat-button');
    if (chatButton) {
        chatButton.addEventListener('click', function() {
            setTimeout(setupDirectHandlers, 500);
        });
    }
    
    // Add debug button
    const debugButton = document.createElement('button');
    debugButton.id = 'debug-chat-button';
    debugButton.textContent = 'Debug Chat';
    debugButton.style.position = 'fixed';
    debugButton.style.bottom = '90px';
    debugButton.style.right = '20px';
    debugButton.style.zIndex = '9999';
    debugButton.style.padding = '5px 10px';
    debugButton.style.backgroundColor = '#666';
    debugButton.style.color = 'white';
    debugButton.style.border = 'none';
    debugButton.style.borderRadius = '4px';
    debugButton.style.cursor = 'pointer';
    document.body.appendChild(debugButton);
    
    // Add debug functionality
    debugButton.addEventListener('click', function() {
        // Create debug panel if it doesn't exist
        let debugPanel = document.getElementById('debug-panel');
        if (!debugPanel) {
            debugPanel = document.createElement('div');
            debugPanel.id = 'debug-panel';
            debugPanel.style.position = 'fixed';
            debugPanel.style.top = '20px';
            debugPanel.style.right = '20px';
            debugPanel.style.width = '400px';
            debugPanel.style.padding = '10px';
            debugPanel.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            debugPanel.style.color = 'white';
            debugPanel.style.zIndex = '10000';
            debugPanel.style.borderRadius = '5px';
            debugPanel.style.fontFamily = 'monospace';
            debugPanel.style.fontSize = '12px';
            document.body.appendChild(debugPanel);
            
            // Add test buttons
            const testMessageBtn = document.createElement('button');
            testMessageBtn.textContent = 'Send Test Message';
            testMessageBtn.style.padding = '5px 10px';
            testMessageBtn.style.margin = '5px';
            testMessageBtn.style.border = 'none';
            testMessageBtn.style.backgroundColor = '#4CAF50';
            testMessageBtn.style.color = 'white';
            testMessageBtn.style.borderRadius = '3px';
            testMessageBtn.style.cursor = 'pointer';
            testMessageBtn.addEventListener('click', function() {
                sendMessageToChainlit('Test message');
            });
            debugPanel.appendChild(testMessageBtn);
            
            // Add button to check iframe
            const checkIframeBtn = document.createElement('button');
            checkIframeBtn.textContent = 'Check Iframe';
            checkIframeBtn.style.padding = '5px 10px';
            checkIframeBtn.style.margin = '5px';
            checkIframeBtn.style.border = 'none';
            checkIframeBtn.style.backgroundColor = '#2196F3';
            checkIframeBtn.style.color = 'white';
            checkIframeBtn.style.borderRadius = '3px';
            checkIframeBtn.style.cursor = 'pointer';
            checkIframeBtn.addEventListener('click', function() {
                const iframe = document.getElementById('floating-chainlit-frame');
                if (!iframe) {
                    logToDebug('Iframe not found');
                } else {
                    logToDebug(`Iframe found: ${iframe.src}`);
                    if (iframe.contentWindow) {
                        logToDebug('ContentWindow available');
                    } else {
                        logToDebug('ContentWindow NOT available');
                    }
                }
            });
            debugPanel.appendChild(checkIframeBtn);
            
            // Add clear button
            const clearBtn = document.createElement('button');
            clearBtn.textContent = 'Clear Log';
            clearBtn.style.padding = '5px 10px';
            clearBtn.style.margin = '5px';
            clearBtn.style.border = 'none';
            clearBtn.style.backgroundColor = '#f44336';
            clearBtn.style.color = 'white';
            clearBtn.style.borderRadius = '3px';
            clearBtn.style.cursor = 'pointer';
            clearBtn.addEventListener('click', function() {
                const logArea = document.getElementById('debug-log-area');
                if (logArea) {
                    logArea.innerHTML = '';
                }
            });
            debugPanel.appendChild(clearBtn);
            
            // Add log area
            const logArea = document.createElement('div');
            logArea.id = 'debug-log-area';
            logArea.style.marginTop = '10px';
            logArea.style.height = '200px';
            logArea.style.overflow = 'auto';
            logArea.style.padding = '5px';
            logArea.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
            logArea.style.borderRadius = '3px';
            debugPanel.appendChild(logArea);
        } else {
            // Toggle visibility
            debugPanel.style.display = debugPanel.style.display === 'none' ? 'block' : 'none';
        }
    });
    
    // Helper to log to debug panel
    window.logToDebug = function(message) {
        console.log(message);
        const logArea = document.getElementById('debug-log-area');
        if (logArea) {
            const logEntry = document.createElement('div');
            logEntry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
            logEntry.style.marginBottom = '3px';
            logEntry.style.borderBottom = '1px solid #333';
            logArea.appendChild(logEntry);
            logArea.scrollTop = logArea.scrollHeight;
        }
    };
});