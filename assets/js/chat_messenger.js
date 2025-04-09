/**
 * Robust Chat Messenger for Neo Cafe
 * This file provides robust message sending between the dashboard and Chainlit
 * with multiple fallback mechanisms and automatic retries.
 */

(function() {
    // Debug mode
    const DEBUG = window.DEBUG_MODE || true;
    
    // Configuration
    const MAX_RETRIES = 3;
    const RETRY_DELAY = 500; // ms
    const IFRAME_LOAD_TIMEOUT = 5000; // ms
    
    // Debug log helper
    function debugLog(...args) {
        if (DEBUG) {
            console.log('[ChatMessenger]', ...args);
        }
    }
    
    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        debugLog('Initializing robust chat messenger');
        
        // Keep track of iframe ready state
        let iframeReady = false;
        let iframeLoaded = false;
        let socketConnected = false;
        let messagePendingQueue = [];
        
        // Get references to key elements
        const getIframe = () => document.getElementById('floating-chainlit-frame');
        const getChatPanel = () => document.getElementById('floating-chat-panel');
        
        // Monitor socket connection status
        function checkSocketStatus() {
            if (window.socket) {
                socketConnected = window.socket.connected;
                return socketConnected;
            }
            return false;
        }
        
        // Function to safely send a message using all available methods
        function sendMessage(message, options = {}) {
            const defaultOptions = {
                sessionId: null,
                retry: 0,
                openPanel: false,
                showLog: true
            };
            
            const config = {...defaultOptions, ...options};
            
            if (config.showLog) {
                debugLog(`Sending message: "${message}" (retry: ${config.retry})`);
            }
            
            // If we need to open the panel, do that first
            if (config.openPanel) {
                const panel = getChatPanel();
                if (panel) {
                    panel.style.display = 'flex';
                    panel.className = 'floating-chat-panel';
                    
                    // If we're opening the panel, give it time to initialize
                    if (config.retry === 0) {
                        setTimeout(() => {
                            sendMessage(message, {...config, retry: 0, openPanel: false});
                        }, 500);
                        return;
                    }
                }
            }
            
            // If the iframe isn't ready yet, queue the message
            if (!iframeReady && config.retry === 0) {
                debugLog('Iframe not ready, queueing message');
                messagePendingQueue.push({message, options: config});
                
                // Wait for iframe to be ready
                waitForIframe();
                return;
            }
            
            // Track whether any method succeeded
            let methodSucceeded = false;
            
            // 1. Try direct postMessage to iframe
            try {
                const iframe = getIframe();
                if (iframe && iframe.contentWindow) {
                    // Try multiple message formats to ensure compatibility
                    
                    // Format 1: Standard message object
                    iframe.contentWindow.postMessage({
                        type: 'userMessage',
                        message: message
                    }, '*');
                    
                    // Format 2: Another possible format
                    iframe.contentWindow.postMessage({
                        kind: 'user_message',
                        data: {
                            content: message
                        }
                    }, '*');
                    
                    // Format 3: Direct string
                    iframe.contentWindow.postMessage(message, '*');
                    
                    methodSucceeded = true;
                    debugLog('Message sent via postMessage');
                }
            } catch (e) {
                debugLog('Error sending via postMessage:', e);
            }
            
            // 2. Try via Socket.IO if available
            if (checkSocketStatus()) {
                try {
                    window.socket.emit('send_chat_message', {
                        message: message,
                        session_id: config.sessionId || window.sessionId || localStorage.getItem('chatSessionId') || undefined
                    });
                    methodSucceeded = true;
                    debugLog('Message sent via Socket.IO');
                } catch (e) {
                    debugLog('Error sending via Socket.IO:', e);
                }
            }
            
            // 3. Try via chatClient
            if (window.chatClient && window.chatClient.sendMessage) {
                try {
                    window.chatClient.sendMessage(message, config.sessionId);
                    methodSucceeded = true;
                    debugLog('Message sent via chatClient');
                } catch (e) {
                    debugLog('Error sending via chatClient:', e);
                }
            }
            
            // 4. Try via direct_message_to_chainlit Socket.IO event
            if (checkSocketStatus()) {
                try {
                    window.socket.emit('direct_message_to_chainlit', {
                        message: message,
                        session_id: config.sessionId
                    });
                    methodSucceeded = true;
                    debugLog('Message sent via direct_message_to_chainlit');
                } catch (e) {
                    debugLog('Error sending via direct_message_to_chainlit:', e);
                }
            }
            
            // 5. If no method succeeded and we haven't exceeded max retries, try again
            if (!methodSucceeded && config.retry < MAX_RETRIES) {
                debugLog(`All message methods failed, retrying (${config.retry + 1}/${MAX_RETRIES})...`);
                setTimeout(() => {
                    sendMessage(message, {...config, retry: config.retry + 1});
                }, RETRY_DELAY * (config.retry + 1)); // Exponential backoff
            } else if (!methodSucceeded) {
                debugLog('All message methods failed after maximum retries');
                
                // Last resort: Try to reload the iframe
                if (config.retry >= MAX_RETRIES) {
                    debugLog('Attempting to reload iframe as last resort');
                    const iframe = getIframe();
                    if (iframe) {
                        const currentSrc = iframe.src;
                        iframe.src = currentSrc; // Reload
                        
                        // Re-queue the message after reload
                        setTimeout(() => {
                            sendMessage(message, {...config, retry: 0});
                        }, 2000);
                    }
                }
            }
            
            return methodSucceeded;
        }
        
        // Wait for iframe to be ready with timeout
        function waitForIframe() {
            if (iframeReady) return;
            
            const iframe = getIframe();
            if (!iframe) {
                debugLog('Iframe element not found in DOM');
                return;
            }
            
            // Set up load event listener
            if (!iframeLoaded) {
                iframeLoaded = true;
                
                iframe.onload = function() {
                    debugLog('Iframe loaded');
                    iframeReady = true;
                    
                    // Process queued messages
                    processMessageQueue();
                };
                
                // Set up timeout
                setTimeout(() => {
                    if (!iframeReady) {
                        debugLog('Iframe load timeout, forcing ready state');
                        iframeReady = true;
                        
                        // Process queued messages even though iframe might not be fully ready
                        processMessageQueue();
                    }
                }, IFRAME_LOAD_TIMEOUT);
            }
            
            // Check if iframe is already loaded (happens when this script loads after iframe)
            if (iframe.contentDocument && 
                iframe.contentDocument.readyState === 'complete') {
                debugLog('Iframe already loaded');
                iframeReady = true;
                processMessageQueue();
            }
        }
        
        // Process queued messages
        function processMessageQueue() {
            debugLog(`Processing ${messagePendingQueue.length} queued messages`);
            
            // Process each message with a delay between them
            messagePendingQueue.forEach((item, index) => {
                setTimeout(() => {
                    sendMessage(item.message, {...item.options, retry: 0});
                }, index * 300); // Stagger the messages
            });
            
            // Clear the queue
            messagePendingQueue = [];
        }
        
        // Listen for iframe ready message
        window.addEventListener('message', function(event) {
            // Check if it's the ready message from iframe
            if (event.data && event.data.type === 'iframe_ready') {
                debugLog('Received iframe_ready message');
                iframeReady = true;
                processMessageQueue();
            }
        });
        
        // Check Socket.IO connection at intervals
        setInterval(checkSocketStatus, 5000);
        
        // Generate a session ID if needed
        if (!window.sessionId) {
            const storedSessionId = localStorage.getItem('chatSessionId');
            if (storedSessionId) {
                window.sessionId = storedSessionId;
            } else {
                // Generate a new UUID
                window.sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    const r = Math.random() * 16 | 0;
                    const v = c === 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                });
                localStorage.setItem('chatSessionId', window.sessionId);
            }
            debugLog('Session ID:', window.sessionId);
        }
        
        // Expose the API
        window.chatMessenger = {
            sendMessage: sendMessage,
            
            openChatAndSendMessage: function(message, sessionId) {
                return sendMessage(message, {
                    sessionId: sessionId || window.sessionId,
                    openPanel: true,
                    retry: 0
                });
            },
            
            // Helper to check status
            getStatus: function() {
                return {
                    iframeReady,
                    socketConnected: checkSocketStatus(),
                    queueLength: messagePendingQueue.length,
                    sessionId: window.sessionId
                };
            }
        };
        
        // Make sendDirectMessageToChainlit use our robust implementation
        window.sendDirectMessageToChainlit = function(message) {
            return window.chatMessenger.sendMessage(message);
        };
        
        // Make sendAndOpenChat use our robust implementation
        window.sendAndOpenChat = function(message) {
            return window.chatMessenger.openChatAndSendMessage(message);
        };
        
        debugLog('Chat messenger initialized');
    });
})();