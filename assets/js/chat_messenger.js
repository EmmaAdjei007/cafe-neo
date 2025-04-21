/**
 * Chat messenger functionality for Neo Cafe
 * This file provides communication between the dashboard and the Chainlit chat
 */

// Create the clientside namespace if it doesn't exist
if (!window.dash_clientside) {
    window.dash_clientside = {};
}

// Create the clientside namespace
window.dash_clientside.clientside = window.dash_clientside.clientside || {};

// Add the updateChatAuth function
window.dash_clientside.clientside.updateChatAuth = function(userData) {
    console.log('updateChatAuth called with:', userData);
    
    if (!userData) {
        console.log('No user data, skipping auth update');
        return '';
    }
    
    try {
        // Find the chat iframe
        const chatFrame = document.getElementById('floating-chainlit-frame');
        if (!chatFrame) {
            console.log('Chat frame not found, possibly not loaded yet');
            
            // Store for later use when frame becomes available
            window._pendingAuthData = userData;
            
            // Set up a MutationObserver to watch for the iframe being added to the DOM
            if (!window._chatFrameObserver) {
                window._chatFrameObserver = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        if (mutation.addedNodes.length) {
                            const chatFrame = document.getElementById('floating-chainlit-frame');
                            if (chatFrame && window._pendingAuthData) {
                                console.log('Chat frame now available, sending pending auth data');
                                sendAuthToFrame(chatFrame, window._pendingAuthData);
                                window._pendingAuthData = null;
                            }
                        }
                    });
                });
                
                // Start observing the document body for changes
                window._chatFrameObserver.observe(document.body, { childList: true, subtree: true });
            }
            
            return '';
        }
        
        // Send auth data to the iframe
        sendAuthToFrame(chatFrame, userData);
        
        return 'auth-updated'; // Class name change to trigger update
    } catch (e) {
        console.error('Error in updateChatAuth:', e);
        return '';
    }
};

// Function to send authentication data to an iframe
function sendAuthToFrame(frame, userData) {
    try {
        // Format the data
        const authData = {
            type: 'auth_update',
            user: userData.username,
            token: btoa(JSON.stringify({
                username: userData.username,
                id: userData.id || '',
                email: userData.email || '',
                first_name: userData.first_name || '',
                last_name: userData.last_name || ''
            })),
            auth_status: true
        };
        
        console.log('Sending auth data to chat frame:', authData.user);
        
        // Try direct postMessage
        frame.contentWindow.postMessage(authData, '*');
        
        // Also try socket.io if available
        if (window.socket && window.socket.emit) {
            console.log('Sending auth update via socket.io');
            window.socket.emit('auth_update', authData);
        }
        
        // Store auth data for reuse (e.g., after iframe reload)
        window._lastAuthData = authData;
        
        // Set up an interval to repeatedly send auth data to ensure it's received
        // This helps when the iframe loads after the auth data is first sent
        if (!window._authInterval) {
            let attempts = 0;
            window._authInterval = setInterval(function() {
                const frameExists = document.getElementById('floating-chainlit-frame');
                if (frameExists && window._lastAuthData && attempts < 5) {
                    console.log('Resending auth data (attempt ' + (attempts + 1) + ')');
                    frameExists.contentWindow.postMessage(window._lastAuthData, '*');
                    attempts++;
                } else {
                    clearInterval(window._authInterval);
                    window._authInterval = null;
                }
            }, 2000); // Try every 2 seconds
        }
    } catch (e) {
        console.error('Error sending auth to frame:', e);
    }
}

// Function to send a direct message to Chainlit
window.sendDirectMessageToChainlit = function(message) {
    console.log('Sending direct message to Chainlit:', message);
    
    try {
        // Find the chat iframe
        const chatFrame = document.getElementById('floating-chainlit-frame');
        if (!chatFrame) {
            console.error('Chat frame not found');
            return false;
        }
        
        // Try multiple message formats to ensure compatibility
        
        // Format 1: Standard format
        chatFrame.contentWindow.postMessage({
            type: 'userMessage',
            message: message
        }, '*');
        
        // Format 2: Alternative format
        chatFrame.contentWindow.postMessage({
            kind: 'user_message',
            data: {
                content: message
            }
        }, '*');
        
        // Format 3: Simple message (fallback)
        chatFrame.contentWindow.postMessage(message, '*');
        
        // Also try socket.io if available
        if (window.socket && window.socket.emit) {
            console.log('Sending message via socket.io');
            window.socket.emit('send_chat_message', {
                message: message,
                session_id: localStorage.getItem('chainlit_session_id') || ''
            });
        }
        
        return true;
    } catch (e) {
        console.error('Error sending message to Chainlit:', e);
        return false;
    }
};

// Setup event listeners when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Setting up chat message event listeners');
    
    // Listen for messages from the Chainlit iframe
    window.addEventListener('message', function(event) {
        // Check if it's from the Chainlit iframe
        const chatFrame = document.getElementById('floating-chainlit-frame');
        if (chatFrame && event.source === chatFrame.contentWindow) {
            console.log('Received message from Chainlit iframe:', event.data);
            
            // Handle iframe_ready event
            if (event.data && event.data.type === 'iframe_ready') {
                console.log('Chainlit iframe is ready');
                
                // If we have stored auth data, send it now
                if (window._lastAuthData) {
                    console.log('Sending stored auth data to ready iframe');
                    chatFrame.contentWindow.postMessage(window._lastAuthData, '*');
                }
            }
            
            // Handle session_id event
            if (event.data && event.data.type === 'session_id' && event.data.session_id) {
                console.log('Received session_id from Chainlit:', event.data.session_id);
                localStorage.setItem('chainlit_session_id', event.data.session_id);
            }
        }
    });
});