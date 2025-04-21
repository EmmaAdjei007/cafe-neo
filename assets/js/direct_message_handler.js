/**
 * Direct message handler for Neo Cafe
 * Manages communication between Dash and Chainlit with improved stability
 */

(function() {
    // Store references
    const frameSelector = 'floating-chainlit-frame';
    let chatFrame = null;
    let authData = null;
    let sessionId = null;
    let frameReloadCount = 0;
    const MAX_RELOADS = 3;
    let lastAuthTime = 0;
    const AUTH_COOLDOWN = 5000; // 5 seconds between auth attempts

    // Set up page load listener
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Improved direct message handler initialized');
        setupFrameWatcher();
        setupSocketListener();
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

    // Set up socket.io listener for auth updates
    function setupSocketListener() {
        // Wait for socket to be available
        const checkSocket = setInterval(function() {
            if (window.socket && window.socket.on) {
                console.log('Socket.IO found, setting up auth listener');
                
                // Listen for auth_confirmed events from Chainlit
                window.socket.on('auth_confirmed', function(data) {
                    console.log('Received auth confirmation:', data);
                    
                    // Store session ID if provided
                    if (data.session_id) {
                        sessionId = data.session_id;
                        localStorage.setItem('chainlit_session_id', sessionId);
                        console.log('Stored session ID from auth confirmation:', sessionId);
                    }
                });
                
                clearInterval(checkSocket);
            }
        }, 1000);
    }

    // Initialize communication when the frame is available
    function initializeWithFrame(frame) {
        // Watch for frame load/reload events
        frame.addEventListener('load', function() {
            console.log('Chat frame loaded/reloaded');
            frameReloadCount++;
            
            if (frameReloadCount > MAX_RELOADS) {
                console.warn(`Frame has reloaded ${frameReloadCount} times, this may indicate stability issues`);
            }
            
            // Wait a moment for the frame to fully initialize
            setTimeout(function() {
                if (authData) {
                    console.log('Sending auth data after frame reload');
                    sendAuthToFrame(frame, authData);
                }
            }, 1000);
        });
        
        // Listen for messages from iframe
        window.addEventListener('message', receiveMessage);

        // Get session information from localStorage
        sessionId = localStorage.getItem('chainlit_session_id');
        if (sessionId) {
            console.log('Loaded session ID from localStorage:', sessionId);
        }

        // Get auth data from dashboard state
        try {
            // Try localStorage first for session persistence
            const userStoreData = JSON.parse(localStorage.getItem('user-store') || '{}');
            
            if (userStoreData && userStoreData.username) {
                authData = {
                    user: userStoreData.username,
                    id: userStoreData.id || '',
                    token: btoa(JSON.stringify(userStoreData))
                };
                
                // Send auth data to frame with random delay to prevent race conditions
                const randomDelay = 800 + Math.random() * 1000;
                setTimeout(function() {
                    sendAuthToFrame(frame, authData);
                }, randomDelay);
            }
        } catch (e) {
            console.error('Error getting user store data:', e);
        }
    }

    // Handler for messages from Chainlit iframe
    function receiveMessage(event) {
        // Skip messages from other sources
        if (!chatFrame || event.source !== chatFrame.contentWindow) {
            return;
        }
        
        console.log('Received message from Chainlit:', event.data);
        
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
                const now = Date.now();
                if (now - lastAuthTime > AUTH_COOLDOWN) {
                    sendAuthToFrame(chatFrame, authData);
                    lastAuthTime = now;
                } else {
                    console.log('Skipping auth send due to cooldown');
                }
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
                    const now = Date.now();
                    if (now - lastAuthTime > AUTH_COOLDOWN) {
                        setTimeout(function() {
                            sendAuthToFrame(chatFrame, authData);
                            lastAuthTime = now;
                        }, 2000);
                    }
                }
            }
        }
        
        // Handle chat_ready message
        if (event.data && event.data.type === 'chat_ready') {
            console.log('Chainlit reports chat is ready');
            
            // If session ID is provided, save it
            if (event.data.session_id) {
                sessionId = event.data.session_id;
                localStorage.setItem('chainlit_session_id', sessionId);
                console.log('Stored session ID from chat_ready event:', sessionId);
            }
        }
        
        // Handle navigation requests
        if (event.data && event.data.type === 'navigation') {
            console.log('Navigation request from Chainlit:', event.data.destination);
            handleNavigation(event.data.destination);
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

    // Send auth data to the frame with stability improvements
    function sendAuthToFrame(frame, data) {
        try {
            const now = Date.now();
            lastAuthTime = now;
            
            const authMessage = {
                type: 'auth_update',
                user: data.user,
                token: data.token || btoa(JSON.stringify({
                    username: data.user,
                    id: data.id || ''
                })),
                auth_status: true,
                timestamp: now,  // Add timestamp to differentiate messages
                session_id: sessionId  // Include session ID if available
            };
            
            console.log('Sending auth data to Chainlit iframe for user:', data.user);
            
            // Send session ID if available to maintain conversation history
            if (sessionId) {
                authMessage.session_id = sessionId;
                console.log('Including session ID in auth message:', sessionId);
            }
            
            // Try postMessage first - the most reliable method
            try {
                frame.contentWindow.postMessage(authMessage, '*');
            } catch (pm_err) {
                console.error('Error with postMessage:', pm_err);
            }
            
            // Also try socket.io if available - backup method
            try {
                if (window.socket && window.socket.emit) {
                    console.log('Sending auth update via socket.io');
                    window.socket.emit('auth_update', authMessage);
                }
            } catch (socket_err) {
                console.error('Error with socket.io emit:', socket_err);
            }
            
            // Try credentials format as well for maximum compatibility
            try {
                frame.contentWindow.postMessage({
                    type: 'credentials',
                    user: data.user,
                    token: data.token
                }, '*');
            } catch (cred_err) {
                console.error('Error sending credentials format:', cred_err);
            }
        } catch (e) {
            console.error('Error sending auth to frame:', e);
        }
    }

    // Expose send message function globally with stability enhancements
    window.sendDirectMessageToChainlit = function(message) {
        if (!chatFrame) {
            console.error('Cannot send message: Chat frame not available');
            chatFrame = document.getElementById(frameSelector);
            if (!chatFrame) {
                return false;
            }
        }
        
        try {
            // Generate message ID for tracing
            const messageId = Date.now().toString(36) + Math.random().toString(36).substring(2);
            
            // Direct message format
            chatFrame.contentWindow.postMessage({
                type: 'userMessage',
                message: message,
                id: messageId,
                session_id: sessionId
            }, '*');
            
            // Alternative formats for compatibility
            chatFrame.contentWindow.postMessage({
                kind: 'user_message',
                data: { 
                    content: message,
                    id: messageId,
                    session_id: sessionId
                }
            }, '*');
            
            // Also try socket.io if available
            if (window.socket && window.socket.emit) {
                window.socket.emit('send_chat_message', {
                    message: message,
                    id: messageId,
                    session_id: sessionId
                });
            }
            
            console.log('Sent message to Chainlit:', message, 'with ID:', messageId);
            return true;
        } catch (e) {
            console.error('Error sending message to Chainlit:', e);
            return false;
        }
    };
    
    // Add a heartbeat to detect iframe crashes and recover if needed
    setInterval(function() {
        if (chatFrame) {
            try {
                // Check if iframe is accessible
                if (chatFrame.contentWindow) {
                    // Send a heartbeat message
                    chatFrame.contentWindow.postMessage({
                        type: 'heartbeat',
                        timestamp: Date.now()
                    }, '*');
                } else {
                    console.warn('Chat frame content window not accessible, possible crash');
                    // Attempt recovery - reload the iframe if it seems inaccessible
                    if (frameReloadCount < MAX_RELOADS) {
                        console.log('Attempting to recover chat frame');
                        const parentElement = chatFrame.parentElement;
                        if (parentElement) {
                            const currentSrc = chatFrame.src;
                            chatFrame.remove();
                            chatFrame = document.createElement('iframe');
                            chatFrame.id = frameSelector;
                            chatFrame.src = currentSrc;
                            chatFrame.style.width = '100%';
                            chatFrame.style.height = '100%';
                            chatFrame.style.border = 'none';
                            parentElement.appendChild(chatFrame);
                            console.log('Chat frame reloaded');
                            
                            // Reinitialize with the new frame
                            initializeWithFrame(chatFrame);
                        }
                    }
                }
            } catch (e) {
                console.error('Error in heartbeat check:', e);
            }
        }
    }, 30000); // Check every 30 seconds
})();