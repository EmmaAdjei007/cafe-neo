// Add or update assets/js/auth_bridge.js

/**
 * Neo Cafe Authentication Bridge
 * This script helps maintain authentication state between the Dash app and Chainlit
 */

// Store for current auth state
window.neoCafeAuth = window.neoCafeAuth || {
    isAuthenticated: false,
    username: null,
    token: null,
    userData: null
};

// Initialize from localStorage
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Auth Bridge] Initializing');
    
    // Try to load from localStorage
    if (window.localStorage) {
        try {
            const storedAuth = localStorage.getItem('neo_cafe_auth');
            if (storedAuth) {
                const authData = JSON.parse(storedAuth);
                window.neoCafeAuth = authData;
                console.log('[Auth Bridge] Loaded auth from localStorage:', 
                    authData.username);
                
                // Apply auth state to any Chainlit iframe
                setTimeout(applyAuthToChainlit, 500);
            }
        } catch (e) {
            console.error('[Auth Bridge] Error loading from localStorage:', e);
        }
    }
    
    // Set up auth update listener
    window.addEventListener('storage', handleStorageChange);
    
    // Set up message listener for iframe communication
    window.addEventListener('message', handleIframeMessage);
});

// Handle storage changes (for multi-tab sync)
function handleStorageChange(event) {
    if (event.key === 'neo_cafe_auth') {
        console.log('[Auth Bridge] Auth changed in another tab');
        try {
            if (event.newValue) {
                const authData = JSON.parse(event.newValue);
                window.neoCafeAuth = authData;
                applyAuthToChainlit();
            }
        } catch (e) {
            console.error('[Auth Bridge] Error handling storage change:', e);
        }
    }
}

// Handle messages from iframes
function handleIframeMessage(event) {
    // Only accept messages from known sources
    if (event.origin !== window.location.origin) {
        return;
    }
    
    const data = event.data;
    
    // Handle auth requests from iframes
    if (data && data.type === 'request_auth') {
        console.log('[Auth Bridge] Received auth request from iframe');
        if (window.neoCafeAuth.isAuthenticated) {
            event.source.postMessage({
                type: 'auth_response',
                auth: window.neoCafeAuth
            }, '*');
        }
    }
}

// Update auth state from user data
function updateAuthState(userData) {
    if (!userData || !userData.username) {
        console.log('[Auth Bridge] No valid user data provided');
        return;
    }
    
    console.log('[Auth Bridge] Updating auth state for', userData.username);
    
    // Create token if needed
    let token = userData.token;
    if (!token) {
        try {
            token = btoa(JSON.stringify({
                username: userData.username,
                id: userData.id || '',
                email: userData.email || '',
                first_name: userData.first_name || '',
                last_name: userData.last_name || ''
            }));
        } catch (e) {
            console.error('[Auth Bridge] Error creating token:', e);
        }
    }
    
    // Update global auth state
    window.neoCafeAuth = {
        isAuthenticated: true,
        username: userData.username,
        token: token,
        userData: userData
    };
    
    // Save to localStorage
    if (window.localStorage) {
        try {
            localStorage.setItem('neo_cafe_auth', JSON.stringify(window.neoCafeAuth));
        } catch (e) {
            console.error('[Auth Bridge] Error saving to localStorage:', e);
        }
    }
    
    // Apply to Chainlit iframes
    applyAuthToChainlit();
}

// Apply auth state to Chainlit iframes
function applyAuthToChainlit() {
    if (!window.neoCafeAuth.isAuthenticated) {
        console.log('[Auth Bridge] Not authenticated, skipping iframe update');
        return;
    }
    
    console.log('[Auth Bridge] Applying auth to Chainlit iframes');
    
    const auth = window.neoCafeAuth;
    
    // Find all iframes that might be Chainlit
    const iframes = document.querySelectorAll('iframe');
    iframes.forEach(iframe => {
        try {
            if (iframe.id.includes('chainlit') || 
                (iframe.src && iframe.src.includes('chainlit'))) {
                
                console.log('[Auth Bridge] Updating iframe:', iframe.id);
                
                // 1. Update src with auth parameters if possible
                if (iframe.src) {
                    const url = new URL(iframe.src);
                    url.searchParams.set('token', auth.token);
                    url.searchParams.set('user', auth.username);
                    url.searchParams.set('t', Date.now()); // Force refresh
                    
                    // Only update if different to avoid reload loops
                    if (url.toString() !== iframe.src) {
                        console.log('[Auth Bridge] Updating iframe src with auth params');
                        iframe.src = url.toString();
                    }
                }
                
                // 2. Try postMessage for already loaded iframes
                if (iframe.contentWindow) {
                    console.log('[Auth Bridge] Sending auth via postMessage');
                    iframe.contentWindow.postMessage({
                        type: 'auth_update',
                        user: auth.username,
                        token: auth.token,
                        auth_status: true
                    }, '*');
                    
                    // Also send in alternative format
                    iframe.contentWindow.postMessage({
                        type: 'auth_data',
                        auth: auth
                    }, '*');
                }
            }
        } catch (e) {
            console.error('[Auth Bridge] Error updating iframe:', e);
        }
    });
}

// Set up Dash clientside callback
if (!window.dash_clientside) {
    window.dash_clientside = {};
}

if (!window.dash_clientside.clientside) {
    window.dash_clientside.clientside = {};
}

// Add this to other clientside callbacks
window.dash_clientside.clientside.updateAuthState = function(userData) {
    if (userData) {
        updateAuthState(userData);
    }
    return userData;
};

// Export key functions for external use
window.neoCafeAuthBridge = {
    updateAuthState: updateAuthState,
    applyAuthToChainlit: applyAuthToChainlit
};

// Auto-refresh auth every 5 seconds (helps with timing issues)
setInterval(function() {
    if (window.neoCafeAuth.isAuthenticated) {
        applyAuthToChainlit();
    }
}, 5000);