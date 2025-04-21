/**
 * Direct message handler for Neo Cafe
 * Manages communication between Dash and Chainlit
 */

(function() {
    // Store references
    const frameSelector = 'floating-chainlit-frame';
    let chatFrame = null;
    let authData = null;
    let sessionId = null;

    // Set up page load listener
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Direct message handler initialized');
        setupFrameWatcher();
    });

    // Watch for the iframe to be available
    function setupFrameWatcher() {
        // Check immediately
        chatFrame = document.getElementById(frameSelector);
        if (chatFrame) {
            console.log('Chat frame found immediately');
            initializeWithFrame(chatFrame);
            return;
        }

        // Set up mutations observer to detect when frame is added
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    chatFrame = document.getElementById(frameSelector);
                    if (chatFrame) {
                        console.log('Chat frame found via observer');
                        initializeWithFrame(chatFrame);
                        observer.disconnect();
                    }
                }
            });
        });

        // Start observing the document for frame addition
        observer.observe(document.body, { childList: true, subtree: true });
    }

    // Initialize communication when the frame is available
    function initializeWithFrame(frame) {
        // Listen for messages from iframe
        window.addEventListener('message', receiveMessage);

        // Get session information from localStorage
        sessionId = localStorage.getItem('chainlit_session_id');
        if (sessionId) {
            console.log('Loaded session ID:', sessionId);
        }

        // Get auth data from dashboard state
        try {
            const userStoreData = JSON.parse(localStorage.getItem('user-store'));
            if (userStoreData && userStoreData.username) {
                authData = {
                    user: userStoreData.username,
                    id: userStoreData.id || '',
                    token: btoa(JSON.stringify(userStoreData))
                };
                
                // Send auth data to frame
                setTimeout(function() {
                    sendAuthToFrame(frame, authData);
                }, 1000);
            }
        } catch (e) {
            console.error('Error getting user store data:', e);
        }
    }

    // Handler for messages from Chainlit iframe
    function receiveMessage(event) {
        // Verify the message source
        if (chatFrame && event.source === chatFrame.contentWindow) {
            // Handle session ID message
            if (event.data && event.data.type === 'session_id') {
                console.log('Received session ID from Chainlit:', event.data.session_id);
                sessionId = event.data.session_id;
                localStorage.setItem('chainlit_session_id', sessionId);
            }
            
            // Handle ready message
            if (event.data && event.data.type === 'iframe_ready') {
                console.log('Chainlit iframe is ready');
                if (authData) {
                    sendAuthToFrame(chatFrame, authData);
                }
            }
            
            // Handle auth status message
            if (event.data && event.data.type === 'auth_status') {
                console.log('Received auth status from Chainlit:', event.data.status);
                if (event.data.status === 'authenticated') {
                    console.log('Chainlit authentication successful');
                } else {
                    console.warn('Chainlit authentication failed');
                    // Retry auth if we have the data
                    if (authData) {
                        setTimeout(function() {
                            sendAuthToFrame(chatFrame, authData);
                        }, 2000);
                    }
                }
            }
            
            // Handle navigation requests
            if (event.data && event.data.type === 'navigation') {
                console.log('Navigation request from Chainlit:', event.data.destination);
                handleNavigation(event.data.destination);
            }
        }
    }

    // Handle navigation requests
    function handleNavigation(destination) {
        // Map destination to URLs
        const urlMap = {
            'menu': '/menu',
            'orders': '/orders',
            'order': '/orders',
            'delivery': '/delivery',
            'profile': '/profile',
            'dashboard': '/dashboard',
            'home': '/'
        };
        
        if (destination in urlMap) {
            window.location.pathname = urlMap[destination];
        }
    }

    // Send auth data to the frame
    function sendAuthToFrame(frame, data) {
        try {
            const authMessage = {
                type: 'auth_update',
                user: data.user,
                token: data.token || btoa(JSON.stringify({
                    username: data.user,
                    id: data.id || ''
                })),
                auth_status: true
            };
            
            console.log('Sending auth data to Chainlit iframe');
            frame.contentWindow.postMessage(authMessage, '*');
            
            // Try socket.io as well if available
            if (window.socket && window.socket.emit) {
                window.socket.emit('auth_update', authMessage);
            }
        } catch (e) {
            console.error('Error sending auth to frame:', e);
        }
    }

    // Expose send message function globally
    window.sendDirectMessageToChainlit = function(message) {
        if (!chatFrame) {
            console.error('Cannot send message: Chat frame not available');
            chatFrame = document.getElementById(frameSelector);
            if (!chatFrame) {
                return false;
            }
        }
        
        try {
            // Direct message format
            chatFrame.contentWindow.postMessage({
                type: 'userMessage',
                message: message
            }, '*');
            
            // Alternative formats for compatibility
            chatFrame.contentWindow.postMessage({
                kind: 'user_message',
                data: { content: message }
            }, '*');
            
            console.log('Sent message to Chainlit:', message);
            return true;
        } catch (e) {
            console.error('Error sending message to Chainlit:', e);
            return false;
        }
    };
})();