// assets/js/chat_client.js

// Initialize everything once the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // ========================
    // Socket.IO initialization
    // ========================
    if (typeof io === 'undefined') {
        console.error('Socket.IO not loaded! Make sure the script is included.');
        return;
    }

    console.log('Initializing chat client...');

    // Connect to the Socket.IO server
    const socket = io.connect();
    // Expose socket globally in case it's needed elsewhere (e.g., for quick action fallback)
    window.socket = socket;

    // Log connection status
    socket.on('connect', function() {
        console.log('Connected to Socket.IO server');
        socket.emit('ping', { data: 'Chat client connected' });
    });

    socket.on('disconnect', function() {
        console.log('Disconnected from Socket.IO server');
    });

    // Debug helper to log all events
    socket.onAny((eventName, ...args) => {
        console.log(`[Socket Event] ${eventName}:`, args);
    });

    // ========================
    // Message forwarding logic
    // ========================
    socket.on('chat_message_from_dashboard', function(data) {
        console.log('Received chat message to forward to Chainlit:', data);

        // If the chat panel is hidden, open it first
        const panel = document.getElementById('floating-chat-panel');
        if (panel && panel.style.display === 'none') {
            const chatButton = document.getElementById('floating-chat-button');
            if (chatButton) {
                console.log('Opening chat panel first...');
                chatButton.click();

                // Wait a moment for the panel to open, then send the message
                setTimeout(function() {
                    sendMessageToChainlit(data.message);
                }, 500);
                return;
            }
        }
        // Otherwise, send the message directly
        sendMessageToChainlit(data.message);
    });

    // Unified function to send messages to the Chainlit iframe
    function sendMessageToChainlit(message) {
        console.log('Sending message to Chainlit:', message);
        const iframe = document.getElementById('floating-chainlit-frame');
        if (!iframe || !iframe.contentWindow) {
            console.error('Chainlit iframe not found or not accessible');
            return false;
        }

        try {
            // Method 1: Direct postMessage (format 1)
            iframe.contentWindow.postMessage(message, '*');

            // Method 2: Use the standard userMessage format
            iframe.contentWindow.postMessage({
                type: 'userMessage',
                message: message
            }, '*');

            // Method 3: If an explicit sendMessage function is exposed, use it
            if (iframe.contentWindow.sendMessageToChainlit) {
                iframe.contentWindow.sendMessageToChainlit(message);
            }

            return true;
        } catch (e) {
            console.error('Error sending message to Chainlit iframe:', e);
            return false;
        }
    }

    // Function to open the chat panel (if closed) and then send a message via Socket.IO
    window.openChatWithMessage = function(message) {
        const panel = document.getElementById('floating-chat-panel');
        if (panel && panel.style.display === 'none') {
            const chatButton = document.getElementById('floating-chat-button');
            if (chatButton) {
                chatButton.click();
                // Wait for the panel to open before sending the message
                setTimeout(function() {
                    socket.emit('send_chat_message', {
                        message: message,
                        session_id: localStorage.getItem('chainlit_session_id') || 'default_session'
                    });
                }, 500);
                return;
            }
        }
        // If the panel is already open, send directly
        socket.emit('send_chat_message', {
            message: message,
            session_id: localStorage.getItem('chainlit_session_id') || 'default_session'
        });
    };

    // ========================
    // Quick action buttons setup
    // ========================
    console.log('Setting up direct click handlers for quick action buttons');

    // Mapping button IDs to their associated messages
    const buttonMessages = {
        'quick-order-btn': 'I\'d like to place an order',
        'quick-track-btn': 'Track my order',
        'quick-popular-btn': 'What are your popular items?',
        'quick-hours-btn': 'What are your operating hours?',
        'faq-menu-btn': 'Show me the menu',
        'faq-hours-btn': 'When are you open?',
        'faq-robot-btn': 'How does robot delivery work?',
        'faq-popular-btn': "What's your most popular coffee?",
        'menu-faq-btn': 'Show me the menu',
        'hours-faq-btn': 'When are you open?',
        'robot-faq-btn': 'How does robot delivery work?',
        'popular-faq-btn': "What's your most popular coffee?",
        'voice-toggle-btn': 'Toggle voice mode'
    };

    // Set up click handlers for the buttons
    function setupButtonHandlers() {
        Object.keys(buttonMessages).forEach(function(buttonId) {
            const button = document.getElementById(buttonId);
            if (button) {
                console.log('Setting up handler for button:', buttonId);
                button.addEventListener('click', function(e) {
                    console.log('Button clicked:', buttonId);
                    const message = buttonMessages[buttonId];

                    // Ensure the chat panel is open before sending the message
                    const chatPanel = document.getElementById('floating-chat-panel');
                    const chatButton = document.getElementById('floating-chat-button');
                    if (chatPanel && chatPanel.style.display === 'none' && chatButton) {
                        chatButton.click();
                        setTimeout(function() {
                            // Use our unified send function
                            sendMessageToChainlit(message);
                        }, 500);
                    } else {
                        // Send immediately if already open
                        sendMessageToChainlit(message);
                    }
                });
            }
        });
    }

    // Call setup once on initial load
    setupButtonHandlers();

    // Use a MutationObserver to catch any buttons added dynamically to the page
    const observer = new MutationObserver(function(mutations) {
        let shouldSetup = false;
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                for (let i = 0; i < mutation.addedNodes.length; i++) {
                    const node = mutation.addedNodes[i];
                    if (node.nodeType === 1 && (node.id in buttonMessages || node.querySelector)) {
                        shouldSetup = true;
                        break;
                    }
                }
            }
        });
        if (shouldSetup) {
            setupButtonHandlers();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
});
