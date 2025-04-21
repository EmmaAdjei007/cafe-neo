// // assets/js/chat_messenger.js

// // Create socket.io connection when document is loaded
// document.addEventListener('DOMContentLoaded', function() {
//     console.log('Initializing NeoCafe chat messenger');
//     initializeChatMessenger();
// });

// function initializeChatMessenger() {
//     // Initialize Socket.IO connection if not already done
//     if (!window.chatSocket && io) {
//         window.chatSocket = io.connect();
//         console.log('Socket.IO connection initialized');
        
//         // Set up socket event listeners
//         setupSocketListeners();
//     } else if (!io) {
//         console.warn('Socket.IO not loaded, will retry in 1 second');
//         setTimeout(initializeChatMessenger, 1000);
//         return;
//     } else {
//         console.log('Chat socket already initialized');
//     }
    
//     // Create message bridge to share between components
//     if (!window.messageBridge) {
//         window.messageBridge = {
//             sendMessage: sendDirectMessageToChainlit,
//             receiveMessage: function(callback) {
//                 if (typeof callback === 'function') {
//                     this.messageCallback = callback;
//                 }
//             },
//             messageCallback: null,
//             navigation: {
//                 navigate: navigateFromChat,
//                 callback: null
//             },
//             orderUpdate: {
//                 updateOrder: updateOrderFromChat,
//                 callback: null
//             }
//         };
//     }
    
//     // Expose functions globally for other components to use
//     window.sendDirectMessageToChainlit = sendDirectMessageToChainlit;
//     window.navigateFromChat = navigateFromChat;
//     window.updateOrderFromChat = updateOrderFromChat;
// }

// function setupSocketListeners() {
//     // Skip if socket not available
//     if (!window.chatSocket) return;
    
//     // Ensure we're not adding duplicate listeners
//     window.chatSocket.off('message_to_chainlit');
//     window.chatSocket.off('chat_message_from_dashboard');
//     window.chatSocket.off('navigation_command');
//     window.chatSocket.off('order_update');
    
//     // Listen for messages to Chainlit
//     window.chatSocket.on('message_to_chainlit', function(data) {
//         console.log('Received message_to_chainlit:', data);
//         forwardMessageToChainlitIframe(data.message);
//     });
    
//     // Listen for chat messages from dashboard
//     window.chatSocket.on('chat_message_from_dashboard', function(data) {
//         console.log('Received chat_message_from_dashboard:', data);
//         forwardMessageToChainlitIframe(data.message);
//     });
    
//     // Listen for navigation commands
//     window.chatSocket.on('navigate_to', function(data) {
//         console.log('Received navigate_to:', data);
//         if (data && data.destination) {
//             navigateFromChat(data.destination);
//         }
//     });
    
//     // Listen for order updates
//     window.chatSocket.on('order_update', function(data) {
//         console.log('Received order_update:', data);
//         if (data && data.id) {
//             updateOrderFromChat(data);
//         }
//     });
    
//     console.log('Socket listeners setup complete');
// }

// function getSessionId() {
//     // Try to get from localStorage
//     let sessionId = localStorage.getItem('neocafe_session_id');
//     if (!sessionId) {
//         // Generate random ID
//         sessionId = Math.random().toString(36).substring(2, 15) + 
//                    Math.random().toString(36).substring(2, 15);
//         localStorage.setItem('neocafe_session_id', sessionId);
//     }
//     return sessionId;
// }

// function sendDirectMessageToChainlit(message) {
//     console.log('Sending message to Chainlit:', message);
    
//     // Check if message is empty
//     if (!message || message.trim() === '') {
//         console.warn('Attempted to send empty message to Chainlit');
//         return false;
//     }
    
//     // Try multiple methods to send message to ensure delivery
//     let successCount = 0;
    
//     // Method 1: Socket.IO
//     if (window.chatSocket) {
//         try {
//             window.chatSocket.emit('direct_message_to_chainlit', {
//                 message: message,
//                 session_id: getSessionId()
//             });
//             console.log('Message sent via Socket.IO');
//             successCount++;
//         } catch (err) {
//             console.error('Failed to send message via Socket.IO:', err);
//         }
//     }
    
//     // Method 2: iframe postMessage
//     try {
//         const iframe = document.getElementById('floating-chainlit-frame');
//         if (iframe && iframe.contentWindow) {
//             iframe.contentWindow.postMessage({
//                 type: 'userMessage',
//                 message: message
//             }, '*');
//             console.log('Message sent via iframe postMessage');
//             successCount++;
//         }
//     } catch (err) {
//         console.error('Failed to send message via iframe postMessage:', err);
//     }
    
//     // Method 3: Direct message to window.sendMessage if available
//     try {
//         const iframe = document.getElementById('floating-chainlit-frame');
//         if (iframe && iframe.contentWindow && iframe.contentWindow.sendMessage) {
//             iframe.contentWindow.sendMessage(message);
//             console.log('Message sent via iframe.contentWindow.sendMessage');
//             successCount++;
//         }
//     } catch (err) {
//         console.error('Failed to send message via iframe.contentWindow.sendMessage:', err);
//     }
    
//     // Check if message was sent successfully through any method
//     return successCount > 0;
// }

// function forwardMessageToChainlitIframe(message) {
//     // Method 1: Try using iframe postMessage
//     try {
//         const iframe = document.getElementById('floating-chainlit-frame');
//         if (iframe && iframe.contentWindow) {
//             iframe.contentWindow.postMessage({
//                 type: 'userMessage',
//                 message: message
//             }, '*');
//             console.log('Message forwarded to Chainlit iframe via postMessage');
//             return true;
//         }
//     } catch (err) {
//         console.error('Failed to forward message via iframe postMessage:', err);
//     }
    
//     // Method 2: Try using sendMessage function in iframe if available
//     try {
//         const iframe = document.getElementById('floating-chainlit-frame');
//         if (iframe && iframe.contentWindow && iframe.contentWindow.sendMessage) {
//             iframe.contentWindow.sendMessage(message);
//             console.log('Message forwarded to Chainlit iframe via sendMessage function');
//             return true;
//         }
//     } catch (err) {
//         console.error('Failed to forward message via iframe sendMessage function:', err);
//     }
    
//     console.warn('Failed to forward message to Chainlit iframe');
//     return false;
// }

// function navigateFromChat(destination) {
//     console.log('Navigating from chat to:', destination);
    
//     // Validate destination
//     const validDestinations = ['menu', 'orders', 'delivery', 'profile', 'dashboard', 'home'];
    
//     if (!validDestinations.includes(destination.toLowerCase())) {
//         console.warn('Invalid navigation destination:', destination);
//         return false;
//     }
    
//     // Map destination to URL
//     const destinationMap = {
//         'menu': '/menu',
//         'orders': '/orders',
//         'delivery': '/delivery',
//         'profile': '/profile',
//         'dashboard': '/dashboard',
//         'home': '/'
//     };
    
//     const targetUrl = destinationMap[destination.toLowerCase()] || '/';
    
//     // Check if we need to navigate
//     if (window.location.pathname === targetUrl) {
//         console.log('Already on the requested page');
//         return true;
//     }
    
//     // Trigger navigation
//     if (window.messageBridge && window.messageBridge.navigation.callback) {
//         // Use callback if available
//         window.messageBridge.navigation.callback(destination);
//         return true;
//     } else {
//         // Fallback to direct navigation
//         window.location.href = targetUrl;
//         return true;
//     }
// }

// function updateOrderFromChat(orderData) {
//     console.log('Updating order from chat:', orderData);
    
//     // Validate order data
//     if (!orderData || !orderData.items) {
//         console.warn('Invalid order data received');
//         return false;
//     }
    
//     // Store in localStorage for persistence
//     localStorage.setItem('current_order', JSON.stringify(orderData));
    
//     // Call callback if available
//     if (window.messageBridge && window.messageBridge.orderUpdate.callback) {
//         window.messageBridge.orderUpdate.callback(orderData);
//         return true;
//     }
    
//     // Dispatch custom event for components to listen for
//     const updateEvent = new CustomEvent('neo-cafe-order-update', {
//         detail: orderData,
//         bubbles: true
//     });
//     document.dispatchEvent(updateEvent);
    
//     return true;
// }

// // Set up listener for messages from Chainlit iframe
// window.addEventListener('message', function(event) {
//     // Check if message is from our Chainlit iframe
//     const iframe = document.getElementById('floating-chainlit-frame');
//     if (iframe && event.source === iframe.contentWindow) {
//         console.log('Received message from Chainlit iframe:', event.data);
        
//         // Handle different message types
//         if (event.data && event.data.type) {
//             switch (event.data.type) {
//                 case 'navigation':
//                     if (event.data.destination) {
//                         navigateFromChat(event.data.destination);
//                     }
//                     break;
                    
//                 case 'order_update':
//                     if (event.data.order) {
//                         updateOrderFromChat(event.data.order);
//                     }
//                     break;
                    
//                 case 'iframe_ready':
//                     console.log('Chainlit iframe is ready');
//                     // You can add initialization code here if needed
//                     break;
                    
//                 default:
//                     console.log('Unhandled message type from Chainlit iframe:', event.data.type);
//             }
//         }
//     }
// });

//===============================================================================================================================================

// assets/js/chat_messenger.js

// Create the clientside namespace for Dash if it doesn't exist
if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside.clientside = window.dash_clientside.clientside || {};

// Main initialization when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing NeoCafe chat messenger');
    initializeChatMessenger();
    setupChainlitMessageListeners();
});

function initializeChatMessenger() {
    // Initialize Socket.IO connection if not already done
    if (!window.chatSocket && io) {
        window.chatSocket = io.connect();
        console.log('Socket.IO connection initialized');
        setupSocketListeners();
    } else if (!io) {
        console.warn('Socket.IO not loaded, will retry in 1 second');
        setTimeout(initializeChatMessenger, 1000);
        return;
    } else {
        console.log('Chat socket already initialized');
    }
    
    // Create message bridge if not exists
    if (!window.messageBridge) {
        window.messageBridge = {
            sendMessage: sendDirectMessageToChainlit,
            receiveMessage: function(callback) {
                this.messageCallback = callback;
            },
            messageCallback: null,
            navigation: {
                navigate: navigateFromChat,
                callback: null
            },
            orderUpdate: {
                updateOrder: updateOrderFromChat,
                callback: null
            }
        };
    }
    
    // Expose global functions
    window.sendDirectMessageToChainlit = sendDirectMessageToChainlit;
    window.navigateFromChat = navigateFromChat;
    window.updateOrderFromChat = updateOrderFromChat;
}

function setupSocketListeners() {
    if (!window.chatSocket) return;
    
    // Remove existing listeners to prevent duplicates
    window.chatSocket.off('message_to_chainlit');
    window.chatSocket.off('chat_message_from_dashboard');
    window.chatSocket.off('navigation_command');
    window.chatSocket.off('order_update');
    
    // Configure new listeners
    window.chatSocket.on('message_to_chainlit', handleChainlitMessage);
    window.chatSocket.on('chat_message_from_dashboard', handleDashboardMessage);
    window.chatSocket.on('navigate_to', handleNavigationCommand);
    window.chatSocket.on('order_update', handleOrderUpdate);
    
    console.log('Socket listeners setup complete');
}

// Socket event handlers
function handleChainlitMessage(data) {
    console.log('Received message_to_chainlit:', data);
    forwardMessageToChainlitIframe(data.message);
}

function handleDashboardMessage(data) {
    console.log('Received chat_message_from_dashboard:', data);
    forwardMessageToChainlitIframe(data.message);
}

function handleNavigationCommand(data) {
    console.log('Received navigate_to:', data);
    if (data?.destination) navigateFromChat(data.destination);
}

function handleOrderUpdate(data) {
    console.log('Received order_update:', data);
    if (data?.id) updateOrderFromChat(data);
}

// Authentication functions
window.dash_clientside.clientside.updateChatAuth = function(userData) {
    console.log('updateChatAuth called with:', userData);
    
    if (!userData) {
        console.log('No user data, skipping auth update');
        return '';
    }
    
    const chatFrame = document.getElementById('floating-chainlit-frame');
    if (!chatFrame) {
        handlePendingAuthData(userData);
        return '';
    }
    
    sendAuthToFrame(chatFrame, userData);
    return 'auth-updated';
};

function handlePendingAuthData(userData) {
    window._pendingAuthData = userData;
    
    if (!window._chatFrameObserver) {
        window._chatFrameObserver = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.addedNodes.length) {
                    const frame = document.getElementById('floating-chainlit-frame');
                    if (frame && window._pendingAuthData) {
                        console.log('Chat frame available, sending pending auth');
                        sendAuthToFrame(frame, window._pendingAuthData);
                        window._pendingAuthData = null;
                    }
                }
            });
        });
        
        window._chatFrameObserver.observe(document.body, { 
            childList: true, 
            subtree: true 
        });
    }
}

function sendAuthToFrame(frame, userData) {
    try {
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
        
        // Send via postMessage
        frame.contentWindow.postMessage(authData, '*');
        
        // Send via Socket.IO if available
        if (window.chatSocket) {
            window.chatSocket.emit('auth_update', authData);
        }
        
        // Store and retry if needed
        window._lastAuthData = authData;
        setupAuthRetryInterval();
    } catch (e) {
        console.error('Error sending auth to frame:', e);
    }
}

function setupAuthRetryInterval() {
    if (window._authInterval) return;
    
    let attempts = 0;
    window._authInterval = setInterval(() => {
        const frame = document.getElementById('floating-chainlit-frame');
        if (frame && window._lastAuthData && attempts < 5) {
            console.log('Resending auth (attempt ' + (attempts + 1) + ')');
            frame.contentWindow.postMessage(window._lastAuthData, '*');
            attempts++;
        } else {
            clearInterval(window._authInterval);
            window._authInterval = null;
        }
    }, 2000);
}

// Message handling functions
function sendDirectMessageToChainlit(message) {
    console.log('Sending message to Chainlit:', message);
    if (!message?.trim()) {
        console.warn('Empty message blocked');
        return false;
    }
    
    let successCount = 0;
    const iframe = document.getElementById('floating-chainlit-frame');
    
    // Socket.IO method
    if (window.chatSocket) {
        try {
            window.chatSocket.emit('direct_message_to_chainlit', {
                message: message,
                session_id: getSessionId()
            });
            successCount++;
        } catch (err) {
            console.error('Socket.IO send error:', err);
        }
    }
    
    // postMessage methods
    if (iframe?.contentWindow) {
        try {
            const formats = [
                { type: 'userMessage', message: message },
                { kind: 'user_message', data: { content: message } },
                message // Fallback format
            ];
            
            formats.forEach(format => {
                iframe.contentWindow.postMessage(format, '*');
            });
            successCount++;
        } catch (err) {
            console.error('postMessage error:', err);
        }
    }
    
    // Direct function call
    if (iframe?.contentWindow?.sendMessage) {
        try {
            iframe.contentWindow.sendMessage(message);
            successCount++;
        } catch (err) {
            console.error('Direct sendMessage error:', err);
        }
    }
    
    return successCount > 0;
}

function forwardMessageToChainlitIframe(message) {
    const iframe = document.getElementById('floating-chainlit-frame');
    if (!iframe) return false;

    try {
        iframe.contentWindow.postMessage({
            type: 'userMessage',
            message: message
        }, '*');
        return true;
    } catch (err) {
        console.error('Message forwarding failed:', err);
        return false;
    }
}

// Utility functions
function getSessionId() {
    let sessionId = localStorage.getItem('neocafe_session_id');
    if (!sessionId) {
        sessionId = Math.random().toString(36).substring(2, 15) + 
                   Math.random().toString(36).substring(2, 15);
        localStorage.setItem('neocafe_session_id', sessionId);
    }
    return sessionId;
}

function navigateFromChat(destination) {
    const validDestinations = ['menu', 'orders', 'delivery', 'profile', 'dashboard', 'home'];
    const targetUrl = {
        'menu': '/menu',
        'orders': '/orders',
        'delivery': '/delivery',
        'profile': '/profile',
        'dashboard': '/dashboard',
        'home': '/'
    }[destination?.toLowerCase()] || '/';
    
    if (!validDestinations.includes(destination?.toLowerCase())) {
        console.warn('Invalid navigation destination:', destination);
        return false;
    }
    
    if (window.messageBridge?.navigation?.callback) {
        window.messageBridge.navigation.callback(destination);
    } else {
        window.location.href = targetUrl;
    }
    return true;
}

function updateOrderFromChat(orderData) {
    if (!orderData?.items) {
        console.warn('Invalid order data');
        return false;
    }
    
    localStorage.setItem('current_order', JSON.stringify(orderData));
    
    if (window.messageBridge?.orderUpdate?.callback) {
        window.messageBridge.orderUpdate.callback(orderData);
    } else {
        document.dispatchEvent(new CustomEvent('neo-cafe-order-update', {
            detail: orderData,
            bubbles: true
        }));
    }
    return true;
}

// Message listener setup
function setupChainlitMessageListeners() {
    window.addEventListener('message', function(event) {
        const iframe = document.getElementById('floating-chainlit-frame');
        if (!iframe || event.source !== iframe.contentWindow) return;
        
        console.log('Chainlit message:', event.data);
        
        if (event.data?.type) {
            switch (event.data.type) {
                case 'navigation':
                    if (event.data.destination) navigateFromChat(event.data.destination);
                    break;
                case 'order_update':
                    if (event.data.order) updateOrderFromChat(event.data.order);
                    break;
                case 'iframe_ready':
                    console.log('Chainlit iframe ready');
                    if (window._lastAuthData) {
                        iframe.contentWindow.postMessage(window._lastAuthData, '*');
                    }
                    break;
                case 'session_id':
                    if (event.data.session_id) {
                        localStorage.setItem('chainlit_session_id', event.data.session_id);
                    }
                    break;
                default:
                    console.log('Unhandled message type:', event.data.type);
            }
        }
    });
}


// //===============================================================================================================================================
// /**
//  * Chat messenger functionality for Neo Cafe
//  * This file provides communication between the dashboard and the Chainlit chat
//  */

// // Create the clientside namespace if it doesn't exist
// if (!window.dash_clientside) {
//     window.dash_clientside = {};
// }

// // Create the clientside namespace
// window.dash_clientside.clientside = window.dash_clientside.clientside || {};

// // Add the updateChatAuth function
// window.dash_clientside.clientside.updateChatAuth = function(userData) {
//     console.log('updateChatAuth called with:', userData);
    
//     if (!userData) {
//         console.log('No user data, skipping auth update');
//         return '';
//     }
    
//     try {
//         // Find the chat iframe
//         const chatFrame = document.getElementById('floating-chainlit-frame');
//         if (!chatFrame) {
//             console.log('Chat frame not found, possibly not loaded yet');
            
//             // Store for later use when frame becomes available
//             window._pendingAuthData = userData;
            
//             // Set up a MutationObserver to watch for the iframe being added to the DOM
//             if (!window._chatFrameObserver) {
//                 window._chatFrameObserver = new MutationObserver(function(mutations) {
//                     mutations.forEach(function(mutation) {
//                         if (mutation.addedNodes.length) {
//                             const chatFrame = document.getElementById('floating-chainlit-frame');
//                             if (chatFrame && window._pendingAuthData) {
//                                 console.log('Chat frame now available, sending pending auth data');
//                                 sendAuthToFrame(chatFrame, window._pendingAuthData);
//                                 window._pendingAuthData = null;
//                             }
//                         }
//                     });
//                 });
                
//                 // Start observing the document body for changes
//                 window._chatFrameObserver.observe(document.body, { childList: true, subtree: true });
//             }
            
//             return '';
//         }
        
//         // Send auth data to the iframe
//         sendAuthToFrame(chatFrame, userData);
        
//         return 'auth-updated'; // Class name change to trigger update
//     } catch (e) {
//         console.error('Error in updateChatAuth:', e);
//         return '';
//     }
// };

// // Function to send authentication data to an iframe
// function sendAuthToFrame(frame, userData) {
//     try {
//         // Format the data
//         const authData = {
//             type: 'auth_update',
//             user: userData.username,
//             token: btoa(JSON.stringify({
//                 username: userData.username,
//                 id: userData.id || '',
//                 email: userData.email || '',
//                 first_name: userData.first_name || '',
//                 last_name: userData.last_name || ''
//             })),
//             auth_status: true
//         };
        
//         console.log('Sending auth data to chat frame:', authData.user);
        
//         // Try direct postMessage
//         frame.contentWindow.postMessage(authData, '*');
        
//         // Also try socket.io if available
//         if (window.socket && window.socket.emit) {
//             console.log('Sending auth update via socket.io');
//             window.socket.emit('auth_update', authData);
//         }
        
//         // Store auth data for reuse (e.g., after iframe reload)
//         window._lastAuthData = authData;
        
//         // Set up an interval to repeatedly send auth data to ensure it's received
//         // This helps when the iframe loads after the auth data is first sent
//         if (!window._authInterval) {
//             let attempts = 0;
//             window._authInterval = setInterval(function() {
//                 const frameExists = document.getElementById('floating-chainlit-frame');
//                 if (frameExists && window._lastAuthData && attempts < 5) {
//                     console.log('Resending auth data (attempt ' + (attempts + 1) + ')');
//                     frameExists.contentWindow.postMessage(window._lastAuthData, '*');
//                     attempts++;
//                 } else {
//                     clearInterval(window._authInterval);
//                     window._authInterval = null;
//                 }
//             }, 2000); // Try every 2 seconds
//         }
//     } catch (e) {
//         console.error('Error sending auth to frame:', e);
//     }
// }

// // Function to send a direct message to Chainlit
// window.sendDirectMessageToChainlit = function(message) {
//     console.log('Sending direct message to Chainlit:', message);
    
//     try {
//         // Find the chat iframe
//         const chatFrame = document.getElementById('floating-chainlit-frame');
//         if (!chatFrame) {
//             console.error('Chat frame not found');
//             return false;
//         }
        
//         // Try multiple message formats to ensure compatibility
        
//         // Format 1: Standard format
//         chatFrame.contentWindow.postMessage({
//             type: 'userMessage',
//             message: message
//         }, '*');
        
//         // Format 2: Alternative format
//         chatFrame.contentWindow.postMessage({
//             kind: 'user_message',
//             data: {
//                 content: message
//             }
//         }, '*');
        
//         // Format 3: Simple message (fallback)
//         chatFrame.contentWindow.postMessage(message, '*');
        
//         // Also try socket.io if available
//         if (window.socket && window.socket.emit) {
//             console.log('Sending message via socket.io');
//             window.socket.emit('send_chat_message', {
//                 message: message,
//                 session_id: localStorage.getItem('chainlit_session_id') || ''
//             });
//         }
        
//         return true;
//     } catch (e) {
//         console.error('Error sending message to Chainlit:', e);
//         return false;
//     }
// };

// // Setup event listeners when the DOM is loaded
// document.addEventListener('DOMContentLoaded', function() {
//     console.log('Setting up chat message event listeners');
    
//     // Listen for messages from the Chainlit iframe
//     window.addEventListener('message', function(event) {
//         // Check if it's from the Chainlit iframe
//         const chatFrame = document.getElementById('floating-chainlit-frame');
//         if (chatFrame && event.source === chatFrame.contentWindow) {
//             console.log('Received message from Chainlit iframe:', event.data);
            
//             // Handle iframe_ready event
//             if (event.data && event.data.type === 'iframe_ready') {
//                 console.log('Chainlit iframe is ready');
                
//                 // If we have stored auth data, send it now
//                 if (window._lastAuthData) {
//                     console.log('Sending stored auth data to ready iframe');
//                     chatFrame.contentWindow.postMessage(window._lastAuthData, '*');
//                 }
//             }
            
//             // Handle session_id event
//             if (event.data && event.data.type === 'session_id' && event.data.session_id) {
//                 console.log('Received session_id from Chainlit:', event.data.session_id);
//                 localStorage.setItem('chainlit_session_id', event.data.session_id);
//             }
//         }
//     });
// });