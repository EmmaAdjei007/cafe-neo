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

// Global auth data store (from second code)
window.neoCafeAuth = {
    isAuthenticated: false,
    username: null,
    token: null,
    userData: null
};

// Function to update auth data (from second code with original modifications)
function updateAuthData(userData) {
    console.log('Updating auth data:', userData);
    
    if (!userData || !userData.username) {
        console.log('No valid user data provided');
        window.neoCafeAuth = {
            isAuthenticated: false,
            username: null,
            token: null,
            userData: null
        };
        return;
    }
    
    // Create a token from user data if not provided
    let token = userData.token;
    if (!token && userData.username) {
        try {
            // Simple base64 encoding of user data (matches original code's approach)
            token = btoa(JSON.stringify({
                username: userData.username,
                id: userData.id || userData.user_id || '',
                email: userData.email || '',
                first_name: userData.first_name || '',
                last_name: userData.last_name || ''
            }));
        } catch (e) {
            console.error('Error creating token:', e);
        }
    }
    
    // Update global auth data
    window.neoCafeAuth = {
        isAuthenticated: true,
        username: userData.username,
        token: token,
        userData: userData
    };
    
    // Store in localStorage for persistence (from second code)
    if (window.localStorage) {
        localStorage.setItem('auth_token', token);
        localStorage.setItem('auth_user', userData.username);
        localStorage.setItem('auth_data', JSON.stringify(userData));
    }
    
    // Notify any iframes (combined approach)
    notifyIframesOfAuth();
}

// Function to pass auth data to all iframes (combined from both codes)
function notifyIframesOfAuth() {
    const auth = window.neoCafeAuth;
    if (!auth.isAuthenticated) return;

    // Find all iframes (from second code)
    const iframes = document.querySelectorAll('iframe');
    iframes.forEach(iframe => {
        try {
            console.log(`Sending auth data to iframe: ${iframe.id || 'unnamed'}`);
            
            // Format the data (combines both approaches)
            const authData = {
                type: 'auth_update',  // Original code's type
                user: auth.username,
                token: auth.token,
                auth_status: true,
                userData: auth.userData  // From second code
            };
            
            // Send using both postMessage approaches
            iframe.contentWindow.postMessage(authData, '*');
            
            // Original code's socket.io approach
            if (window.socket && window.socket.emit) {
                console.log('Sending auth update via socket.io');
                window.socket.emit('auth_update', authData);
            }
        } catch (e) {
            console.error(`Error sending auth to iframe ${iframe.id || 'unnamed'}:`, e);
        }
    });
}

// Original code's MutationObserver approach with second code's localStorage
document.addEventListener('DOMContentLoaded', function() {
    console.log('Setting up chat message event listeners');
    
    // Initialize from localStorage if available (from second code)
    if (window.localStorage) {
        const storedToken = localStorage.getItem('auth_token');
        const storedUser = localStorage.getItem('auth_user');
        const storedData = localStorage.getItem('auth_data');
        
        if (storedToken && storedUser) {
            try {
                const userData = storedData ? JSON.parse(storedData) : { username: storedUser };
                updateAuthData({
                    ...userData,
                    token: storedToken
                });
                console.log('Restored auth data from localStorage');
            } catch (e) {
                console.error('Error restoring auth data:', e);
            }
        }
    }

    // Original code's message listener with second code's enhancements
    window.addEventListener('message', function(event) {
        // Check if it's from the Chainlit iframe
        const chatFrame = document.getElementById('floating-chainlit-frame');
        if (chatFrame && event.source === chatFrame.contentWindow) {
            console.log('Received message from Chainlit iframe:', event.data);
            
            // Handle iframe_ready event (original code)
            if (event.data && event.data.type === 'iframe_ready') {
                console.log('Chainlit iframe is ready');
                notifyIframesOfAuth();
            }
            
            // Handle session_id event (original code)
            if (event.data && event.data.type === 'session_id' && event.data.session_id) {
                console.log('Received session_id from Chainlit:', event.data.session_id);
                localStorage.setItem('chainlit_session_id', event.data.session_id);
            }
            
            // Handle auth data requests (from second code)
            if (event.data && event.data.type === 'request_auth_data') {
                console.log('Received auth data request from iframe');
                if (window.neoCafeAuth.isAuthenticated) {
                    event.source.postMessage({
                        type: 'auth_data',
                        token: window.neoCafeAuth.token,
                        user: window.neoCafeAuth.username,
                        userData: window.neoCafeAuth.userData
                    }, '*');
                }
            }
        }
    });
});

// Combined interval check approach
setInterval(function() {
    if (window.neoCafeAuth && window.neoCafeAuth.isAuthenticated) {
        const iframe = document.getElementById('floating-chainlit-frame');
        if (iframe) {
            console.log('Periodic auth check - notifying iframes');
            notifyIframesOfAuth();
        }
    }
}, 5000);

// Original code's updateChatAuth function modified
window.dash_clientside.clientside.updateChatAuth = function(userData) {
    console.log('Dash callback: updateChatAuth called with:', userData);
    
    if (!userData) {
        console.log('No user data, skipping auth update');
        return '';
    }
    
    updateAuthData(userData);
    
    // Original code's iframe refresh logic
    setTimeout(function() {
        const iframe = document.getElementById('floating-chainlit-frame');
        if (iframe) {
            console.log('Refreshing Chainlit iframe with auth');
            const src = new URL(iframe.src);
            src.searchParams.set('token', window.neoCafeAuth.token);
            src.searchParams.set('user', window.neoCafeAuth.username);
            src.searchParams.set('t', Date.now());
            iframe.src = src.toString();
        }
    }, 500);
    
    return 'auth-updated';
};

// Preserve original message sending functionality
window.sendDirectMessageToChainlit = function(message) {
    console.log('Sending direct message to Chainlit:', message);
    
    try {
        const chatFrame = document.getElementById('floating-chainlit-frame');
        if (!chatFrame) {
            console.error('Chat frame not found');
            return false;
        }
        
        // Include auth data with messages
        const messageData = {
            type: 'userMessage',
            message: message,
            auth: window.neoCafeAuth.token ? {
                user: window.neoCafeAuth.username,
                token: window.neoCafeAuth.token
            } : null
        };
        
        chatFrame.contentWindow.postMessage(messageData, '*');
        
        if (window.socket && window.socket.emit) {
            console.log('Sending message via socket.io');
            window.socket.emit('send_chat_message', {
                message: message,
                session_id: localStorage.getItem('chainlit_session_id') || '',
                auth: window.neoCafeAuth.token
            });
        }
        
        return true;
    } catch (e) {
        console.error('Error sending message to Chainlit:', e);
        return false;
    }
};

// Preserve original MutationObserver logic for pending auth
if (!window._chatFrameObserver) {
    window._chatFrameObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                const chatFrame = document.getElementById('floating-chainlit-frame');
                if (chatFrame && window.neoCafeAuth.isAuthenticated) {
                    console.log('Chat frame now available, sending auth data');
                    notifyIframesOfAuth();
                }
            }
        });
    });
    window._chatFrameObserver.observe(document.body, { childList: true, subtree: true });
}