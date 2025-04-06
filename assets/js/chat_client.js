// // File: assets/js/chat_client.js

// /**
//  * Simplified chat client that focuses on direct iframe communication
//  * without relying on Socket.IO
//  */

// // Define the clientside namespace for Dash callbacks
// if (!window.clientside) {
//     window.clientside = {};
// }

// // Track if the iframe is ready
// let iframeReady = false;

// /**
//  * Update chat listener for messages from the Chainlit iframe
//  */
// window.clientside.updateChatListener = function() {
//     console.log("Setting up message listener for Chainlit iframe");
    
//     // Set up message listener for communication from iframe
//     window.addEventListener('message', function(event) {
//         // Only handle messages from the Chainlit iframe
//         const iframe = document.getElementById('floating-chainlit-frame');
//         if (iframe && event.source === iframe.contentWindow) {
//             console.log("Received message from Chainlit iframe:", event.data);
            
//             // Mark iframe as ready when we receive any message from it
//             iframeReady = true;
            
//             // Store the message data in the hidden div
//             const chatListener = document.getElementById('chat-message-listener');
//             if (chatListener) {
//                 chatListener.textContent = JSON.stringify(event.data);
                
//                 // Trigger a custom event to ensure callbacks pick up the change
//                 chatListener.dispatchEvent(new Event('change'));
//             }
//         }
//     });
    
//     return "";  // Return empty string as output
// };

// /**
//  * Send a message directly to the Chainlit iframe
//  */
// function sendMessageToChainlit(message) {
//     console.log("Attempting to send message to Chainlit:", message);
//     const iframe = document.getElementById('floating-chainlit-frame');
    
//     if (!iframe) {
//         console.error("Chainlit iframe not found");
//         alert("Chat interface not loaded. Please refresh the page and try again.");
//         return false;
//     }
    
//     if (!iframe.contentWindow) {
//         console.error("Iframe contentWindow not available");
//         alert("Cannot communicate with chat interface. Please refresh the page.");
//         return false;
//     }
    
//     // Type can be different depending on Chainlit implementation
//     // Try all known message formats
//     const messagePayloads = [
//         // Format 1: Standard userMessage format
//         {
//             type: 'userMessage',
//             message: message
//         },
//         // Format 2: Direct message format
//         {
//             message: message,
//             type: 'message'
//         },
//         // Format 3: Chat message format
//         {
//             type: 'chat_message',
//             content: message
//         }
//     ];
    
//     // Try each format
//     for (const payload of messagePayloads) {
//         try {
//             iframe.contentWindow.postMessage(payload, '*');
//             console.log(`Sent message using format: ${JSON.stringify(payload)}`);
//         } catch (e) {
//             console.error(`Error sending format ${JSON.stringify(payload)}:`, e);
//         }
//     }
    
//     // Show indicator that the message was sent
//     showFloatingFeedback(`Message sent: ${message}`);
    
//     // Also ensure the chat panel is visible
//     showChatPanel();
    
//     return true;
// }

// /**
//  * Show a floating feedback message 
//  */
// function showFloatingFeedback(message, duration = 3000) {
//     // Create or find the feedback element
//     let feedback = document.getElementById('chat-feedback-popup');
//     if (!feedback) {
//         feedback = document.createElement('div');
//         feedback.id = 'chat-feedback-popup';
//         feedback.style.position = 'fixed';
//         feedback.style.bottom = '150px';
//         feedback.style.right = '20px';
//         feedback.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
//         feedback.style.color = 'white';
//         feedback.style.padding = '10px 15px';
//         feedback.style.borderRadius = '5px';
//         feedback.style.zIndex = '9999';
//         feedback.style.transition = 'opacity 0.3s ease';
//         feedback.style.opacity = '0';
//         document.body.appendChild(feedback);
//     }
    
//     // Set message and show
//     feedback.textContent = message;
//     feedback.style.opacity = '1';
    
//     // Hide after duration
//     setTimeout(() => {
//         feedback.style.opacity = '0';
//     }, duration);
// }

// /**
//  * Show the chat panel if it's hidden
//  */
// function showChatPanel() {
//     const chatPanel = document.getElementById('floating-chat-panel');
//     if (chatPanel && chatPanel.style.display === 'none') {
//         chatPanel.style.display = 'flex';
//     }
// }

// // Add manual message handling for all quick action buttons
// document.addEventListener('DOMContentLoaded', function() {
//     console.log("DOM loaded, setting up quick action button handlers");
    
//     // Map of button IDs to message text
//     const messageMap = {
//         'quick-order-btn': 'I\'d like to place an order',
//         'quick-track-btn': 'Track my order',
//         'quick-popular-btn': 'What are your popular items?',
//         'quick-hours-btn': 'What are your operating hours?',
//         'faq-menu-btn': 'Show me the menu',
//         'faq-hours-btn': 'When are you open?',
//         'faq-robot-btn': 'How does robot delivery work?',
//         'faq-popular-btn': "What\'s your most popular coffee?",
//         'menu-faq-btn': 'Show me the menu',
//         'hours-faq-btn': 'When are you open?',
//         'robot-faq-btn': 'How does robot delivery work?',
//         'popular-faq-btn': "What\'s your most popular coffee?",
//         'voice-toggle-btn': 'Toggle voice mode'
//     };
    
//     // Helper to ensure we have all buttons
//     function setupDirectHandlers() {
//         console.log("Setting up direct button handlers");
        
//         // Add handlers to all potential buttons
//         Object.keys(messageMap).forEach(buttonId => {
//             const button = document.getElementById(buttonId);
//             if (button) {
//                 console.log(`Found button: ${buttonId}`);
                
//                 // Add direct click handling
//                 button.addEventListener('click', function(e) {
//                     e.preventDefault();
//                     const message = messageMap[buttonId];
//                     console.log(`Button ${buttonId} clicked, sending: "${message}"`);
//                     sendMessageToChainlit(message);
//                     return false;
//                 });
//             }
//         });
//     }
    
//     // First attempt when DOM is ready
//     setupDirectHandlers();
    
//     // Second attempt after a delay to ensure all elements are rendered
//     setTimeout(setupDirectHandlers, 2000);
    
//     // Add additional handlers whenever the chat panel is shown
//     const chatButton = document.getElementById('floating-chat-button');
//     if (chatButton) {
//         chatButton.addEventListener('click', function() {
//             setTimeout(setupDirectHandlers, 500);
//         });
//     }
    
//     // Add debug button
//     const debugButton = document.createElement('button');
//     debugButton.id = 'debug-chat-button';
//     debugButton.textContent = 'Debug Chat';
//     debugButton.style.position = 'fixed';
//     debugButton.style.bottom = '90px';
//     debugButton.style.right = '20px';
//     debugButton.style.zIndex = '9999';
//     debugButton.style.padding = '5px 10px';
//     debugButton.style.backgroundColor = '#666';
//     debugButton.style.color = 'white';
//     debugButton.style.border = 'none';
//     debugButton.style.borderRadius = '4px';
//     debugButton.style.cursor = 'pointer';
//     document.body.appendChild(debugButton);
    
//     // Add debug functionality
//     debugButton.addEventListener('click', function() {
//         // Create debug panel if it doesn't exist
//         let debugPanel = document.getElementById('debug-panel');
//         if (!debugPanel) {
//             debugPanel = document.createElement('div');
//             debugPanel.id = 'debug-panel';
//             debugPanel.style.position = 'fixed';
//             debugPanel.style.top = '20px';
//             debugPanel.style.right = '20px';
//             debugPanel.style.width = '400px';
//             debugPanel.style.padding = '10px';
//             debugPanel.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
//             debugPanel.style.color = 'white';
//             debugPanel.style.zIndex = '10000';
//             debugPanel.style.borderRadius = '5px';
//             debugPanel.style.fontFamily = 'monospace';
//             debugPanel.style.fontSize = '12px';
//             document.body.appendChild(debugPanel);
            
//             // Add test buttons
//             const testMessageBtn = document.createElement('button');
//             testMessageBtn.textContent = 'Send Test Message';
//             testMessageBtn.style.padding = '5px 10px';
//             testMessageBtn.style.margin = '5px';
//             testMessageBtn.style.border = 'none';
//             testMessageBtn.style.backgroundColor = '#4CAF50';
//             testMessageBtn.style.color = 'white';
//             testMessageBtn.style.borderRadius = '3px';
//             testMessageBtn.style.cursor = 'pointer';
//             testMessageBtn.addEventListener('click', function() {
//                 sendMessageToChainlit('Test message');
//             });
//             debugPanel.appendChild(testMessageBtn);
            
//             // Add button to check iframe
//             const checkIframeBtn = document.createElement('button');
//             checkIframeBtn.textContent = 'Check Iframe';
//             checkIframeBtn.style.padding = '5px 10px';
//             checkIframeBtn.style.margin = '5px';
//             checkIframeBtn.style.border = 'none';
//             checkIframeBtn.style.backgroundColor = '#2196F3';
//             checkIframeBtn.style.color = 'white';
//             checkIframeBtn.style.borderRadius = '3px';
//             checkIframeBtn.style.cursor = 'pointer';
//             checkIframeBtn.addEventListener('click', function() {
//                 const iframe = document.getElementById('floating-chainlit-frame');
//                 if (!iframe) {
//                     logToDebug('Iframe not found');
//                 } else {
//                     logToDebug(`Iframe found: ${iframe.src}`);
//                     if (iframe.contentWindow) {
//                         logToDebug('ContentWindow available');
//                     } else {
//                         logToDebug('ContentWindow NOT available');
//                     }
//                 }
//             });
//             debugPanel.appendChild(checkIframeBtn);
            
//             // Add clear button
//             const clearBtn = document.createElement('button');
//             clearBtn.textContent = 'Clear Log';
//             clearBtn.style.padding = '5px 10px';
//             clearBtn.style.margin = '5px';
//             clearBtn.style.border = 'none';
//             clearBtn.style.backgroundColor = '#f44336';
//             clearBtn.style.color = 'white';
//             clearBtn.style.borderRadius = '3px';
//             clearBtn.style.cursor = 'pointer';
//             clearBtn.addEventListener('click', function() {
//                 const logArea = document.getElementById('debug-log-area');
//                 if (logArea) {
//                     logArea.innerHTML = '';
//                 }
//             });
//             debugPanel.appendChild(clearBtn);
            
//             // Add log area
//             const logArea = document.createElement('div');
//             logArea.id = 'debug-log-area';
//             logArea.style.marginTop = '10px';
//             logArea.style.height = '200px';
//             logArea.style.overflow = 'auto';
//             logArea.style.padding = '5px';
//             logArea.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
//             logArea.style.borderRadius = '3px';
//             debugPanel.appendChild(logArea);
//         } else {
//             // Toggle visibility
//             debugPanel.style.display = debugPanel.style.display === 'none' ? 'block' : 'none';
//         }
//     });
    
//     // Helper to log to debug panel
//     window.logToDebug = function(message) {
//         console.log(message);
//         const logArea = document.getElementById('debug-log-area');
//         if (logArea) {
//             const logEntry = document.createElement('div');
//             logEntry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
//             logEntry.style.marginBottom = '3px';
//             logEntry.style.borderBottom = '1px solid #333';
//             logArea.appendChild(logEntry);
//             logArea.scrollTop = logArea.scrollHeight;
//         }
//     };
// });


// File: assets/js/chat_client.js

/**
 * Chat client using synthetic input to directly interact with the Chainlit UI
 */

// Define the clientside namespace for Dash callbacks
if (!window.clientside) {
    window.clientside = {};
}

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

/**
 * This is the key function that finds the input field and send button in Chainlit
 * and directly triggers them with synthetic input
 */
function sendMessageViaUI(message) {
    console.log("Attempting to send message via UI:", message);
    
    // Show the chat panel
    showChatPanel();
    
    // Get the iframe
    const iframe = document.getElementById('floating-chainlit-frame');
    if (!iframe || !iframe.contentWindow) {
        console.error("Cannot find iframe or contentWindow");
        showFloatingFeedback("Error: Chat interface not available");
        return false;
    }
    
    // Get the iframe document
    let iframeDoc;
    try {
        iframeDoc = iframe.contentWindow.document;
    } catch (e) {
        console.error("Cannot access iframe document:", e);
        showFloatingFeedback("Error: Cannot access chat interface");
        return false;
    }
    
    // First approach: Try to use the UI directly by finding the input and submit button
    try {
        // Look for the Chainlit chatbox using various selectors
        // We'll try multiple selectors since different Chainlit versions might use different classes/ids
        const possibleInputSelectors = [
            // Default Chainlit classes
            'input[type="text"]',
            '.chakra-input',
            'textarea.chakra-textarea',
            // Common chat input classes
            'input.chat-input',
            'textarea.chat-input',
            // Input with placeholder about questions
            'input[placeholder*="question"]',
            'textarea[placeholder*="question"]',
            'input[placeholder*="message"]',
            'textarea[placeholder*="message"]',
            // Any input inside a form
            'form input[type="text"]',
            'form textarea',
            // Last resort: any input or textarea
            'input',
            'textarea'
        ];
        
        // Try to find the input element
        let inputElement = null;
        for (const selector of possibleInputSelectors) {
            const elements = iframeDoc.querySelectorAll(selector);
            for (const el of elements) {
                // Check if it's visible
                if (el.offsetParent !== null) {
                    inputElement = el;
                    console.log(`Found input using selector: ${selector}`);
                    break;
                }
            }
            if (inputElement) break;
        }
        
        if (!inputElement) {
            throw new Error("Could not find chat input field");
        }
        
        // Now find the submit button
        const possibleButtonSelectors = [
            // Default Chainlit classes
            'button[type="submit"]',
            'button.chakra-button',
            // Common button classes
            'button.send-button',
            'button.submit-button',
            // Buttons with send or arrow icons
            'button:has(svg)',
            'button:has(i)',
            // Last resort: any button
            'button'
        ];
        
        // Try to find the submit button
        let submitButton = null;
        for (const selector of possibleButtonSelectors) {
            try {
                const elements = iframeDoc.querySelectorAll(selector);
                for (const el of elements) {
                    // Check if it's visible and near the input
                    if (el.offsetParent !== null) {
                        submitButton = el;
                        console.log(`Found button using selector: ${selector}`);
                        break;
                    }
                }
                if (submitButton) break;
            } catch (e) {
                // Some selectors might not be supported in all browsers
                console.log(`Selector failed: ${selector}`, e);
            }
        }
        
        // Set the input value
        inputElement.value = message;
        
        // Dispatch input event to trigger any listeners
        inputElement.dispatchEvent(new Event('input', { bubbles: true }));
        
        // Give a slight delay for the input to register
        setTimeout(() => {
            // If we found a submit button, click it
            if (submitButton) {
                submitButton.click();
                showFloatingFeedback(`Message sent: "${message}"`);
                console.log("Message sent via button click");
            } else {
                // Otherwise try to submit the form directly
                const form = inputElement.closest('form');
                if (form) {
                    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
                    showFloatingFeedback(`Message sent: "${message}"`);
                    console.log("Message sent via form submit");
                } else {
                    // Last resort: try to trigger Enter key on the input
                    const enterEvent = new KeyboardEvent('keydown', {
                        bubbles: true,
                        cancelable: true,
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13
                    });
                    inputElement.dispatchEvent(enterEvent);
                    showFloatingFeedback(`Message sent: "${message}"`);
                    console.log("Message sent via Enter key");
                }
            }
        }, 100);
        
        return true;
    } catch (error) {
        console.error("Error sending message via UI:", error);
        
        // Fallback: create a visible debug button inside the iframe
        try {
            const debugBtn = iframeDoc.createElement('button');
            debugBtn.style.position = 'fixed';
            debugBtn.style.top = '10px';
            debugBtn.style.right = '10px';
            debugBtn.style.zIndex = '9999';
            debugBtn.style.padding = '5px 10px';
            debugBtn.style.backgroundColor = 'red';
            debugBtn.style.color = 'white';
            debugBtn.textContent = 'Manual Send';
            debugBtn.onclick = function() {
                alert(`Please manually enter: "${message}"`);
            };
            iframeDoc.body.appendChild(debugBtn);
            
            showFloatingFeedback("Error sending message automatically. Click 'Manual Send' in the top-right of the chat.");
        } catch (e) {
            console.error("Failed to create debug button:", e);
            showFloatingFeedback("Failed to send message. Please type it manually.");
        }
        
        return false;
    }
}

// Add event listeners for all quick action buttons
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
        
        // Process all quick action buttons
        Object.keys(messageMap).forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                console.log(`Found button: ${buttonId}`);
                
                // Add direct click handling
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const message = messageMap[buttonId];
                    console.log(`Button ${buttonId} clicked, sending: "${message}"`);
                    sendMessageViaUI(message);
                    return false;
                });
            }
        });
    }
    
    // First attempt when DOM is loaded
    setupDirectHandlers();
    
    // Second attempt after a delay to ensure all elements are rendered
    setTimeout(setupDirectHandlers, 2000);
    
    // Add handler when chat panel is shown
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
        // Create modal for debugging
        const modal = document.createElement('div');
        modal.style.position = 'fixed';
        modal.style.top = '50%';
        modal.style.left = '50%';
        modal.style.transform = 'translate(-50%, -50%)';
        modal.style.backgroundColor = '#222';
        modal.style.padding = '20px';
        modal.style.borderRadius = '8px';
        modal.style.zIndex = '10000';
        modal.style.width = '80%';
        modal.style.maxWidth = '600px';
        modal.style.maxHeight = '80vh';
        modal.style.overflow = 'auto';
        modal.style.color = 'white';
        modal.style.boxShadow = '0 0 20px rgba(0,0,0,0.5)';
        
        // Add title
        const title = document.createElement('h2');
        title.textContent = 'Chat Debug Panel';
        title.style.marginTop = '0';
        modal.appendChild(title);
        
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '×';
        closeBtn.style.position = 'absolute';
        closeBtn.style.top = '10px';
        closeBtn.style.right = '10px';
        closeBtn.style.backgroundColor = 'transparent';
        closeBtn.style.border = 'none';
        closeBtn.style.color = 'white';
        closeBtn.style.fontSize = '24px';
        closeBtn.style.cursor = 'pointer';
        closeBtn.onclick = function() {
            document.body.removeChild(modal);
        };
        modal.appendChild(closeBtn);
        
        // Add message input
        const inputGroup = document.createElement('div');
        inputGroup.style.display = 'flex';
        inputGroup.style.marginBottom = '15px';
        
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'Enter message to send';
        input.style.flex = '1';
        input.style.padding = '8px';
        input.style.borderRadius = '4px 0 0 4px';
        input.style.border = 'none';
        
        const sendBtn = document.createElement('button');
        sendBtn.textContent = 'Send';
        sendBtn.style.padding = '8px 15px';
        sendBtn.style.backgroundColor = '#4CAF50';
        sendBtn.style.color = 'white';
        sendBtn.style.border = 'none';
        sendBtn.style.borderRadius = '0 4px 4px 0';
        sendBtn.style.cursor = 'pointer';
        sendBtn.onclick = function() {
            if (input.value) {
                sendMessageViaUI(input.value);
                input.value = '';
            }
        };
        
        inputGroup.appendChild(input);
        inputGroup.appendChild(sendBtn);
        modal.appendChild(inputGroup);
        
        // Add debug actions
        const actions = document.createElement('div');
        actions.style.marginBottom = '15px';
        
        const checkIframeBtn = document.createElement('button');
        checkIframeBtn.textContent = 'Check Iframe';
        checkIframeBtn.style.marginRight = '10px';
        checkIframeBtn.style.padding = '8px 15px';
        checkIframeBtn.style.backgroundColor = '#2196F3';
        checkIframeBtn.style.color = 'white';
        checkIframeBtn.style.border = 'none';
        checkIframeBtn.style.borderRadius = '4px';
        checkIframeBtn.style.cursor = 'pointer';
        checkIframeBtn.onclick = function() {
            const iframe = document.getElementById('floating-chainlit-frame');
            if (!iframe) {
                addLogEntry('Iframe not found', 'error');
            } else {
                addLogEntry(`Iframe found: ${iframe.src}`);
                if (iframe.contentWindow) {
                    addLogEntry('ContentWindow available');
                    
                    try {
                        const iframeDoc = iframe.contentWindow.document;
                        addLogEntry(`Document accessible: ${iframeDoc.title}`);
                        
                        // Try to find input and button
                        const inputs = iframeDoc.querySelectorAll('input, textarea');
                        addLogEntry(`Found ${inputs.length} inputs/textareas`);
                        
                        const buttons = iframeDoc.querySelectorAll('button');
                        addLogEntry(`Found ${buttons.length} buttons`);
                        
                        // Scan for forms
                        const forms = iframeDoc.querySelectorAll('form');
                        addLogEntry(`Found ${forms.length} forms`);
                    } catch (e) {
                        addLogEntry(`Error accessing document: ${e.message}`, 'error');
                    }
                } else {
                    addLogEntry('ContentWindow NOT available', 'error');
                }
            }
        };
        actions.appendChild(checkIframeBtn);
        
        const refreshIframeBtn = document.createElement('button');
        refreshIframeBtn.textContent = 'Refresh Iframe';
        refreshIframeBtn.style.marginRight = '10px';
        refreshIframeBtn.style.padding = '8px 15px';
        refreshIframeBtn.style.backgroundColor = '#FF9800';
        refreshIframeBtn.style.color = 'white';
        refreshIframeBtn.style.border = 'none';
        refreshIframeBtn.style.borderRadius = '4px';
        refreshIframeBtn.style.cursor = 'pointer';
        refreshIframeBtn.onclick = function() {
            const iframe = document.getElementById('floating-chainlit-frame');
            if (iframe) {
                const currentSrc = iframe.src;
                addLogEntry(`Refreshing iframe: ${currentSrc}`);
                iframe.src = 'about:blank';
                setTimeout(() => {
                    iframe.src = currentSrc;
                    addLogEntry('Iframe refresh initiated');
                }, 100);
            } else {
                addLogEntry('Iframe not found', 'error');
            }
        };
        actions.appendChild(refreshIframeBtn);
        
        const clearLogBtn = document.createElement('button');
        clearLogBtn.textContent = 'Clear Log';
        clearLogBtn.style.padding = '8px 15px';
        clearLogBtn.style.backgroundColor = '#F44336';
        clearLogBtn.style.color = 'white';
        clearLogBtn.style.border = 'none';
        clearLogBtn.style.borderRadius = '4px';
        clearLogBtn.style.cursor = 'pointer';
        clearLogBtn.onclick = function() {
            logArea.innerHTML = '';
        };
        actions.appendChild(clearLogBtn);
        
        modal.appendChild(actions);
        
        // Add log area
        const logArea = document.createElement('div');
        logArea.style.backgroundColor = '#111';
        logArea.style.padding = '10px';
        logArea.style.borderRadius = '4px';
        logArea.style.height = '200px';
        logArea.style.overflowY = 'auto';
        logArea.style.fontFamily = 'monospace';
        logArea.style.fontSize = '12px';
        modal.appendChild(logArea);
        
        // Function to add log entries
        function addLogEntry(message, type = 'info') {
            const entry = document.createElement('div');
            entry.style.marginBottom = '5px';
            entry.style.borderLeft = `3px solid ${type === 'error' ? '#F44336' : type === 'warn' ? '#FF9800' : '#4CAF50'}`;
            entry.style.paddingLeft = '5px';
            entry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
            logArea.appendChild(entry);
            logArea.scrollTop = logArea.scrollHeight;
            console.log(`[${type}] ${message}`);
        }
        
        // Add initial log entry
        addLogEntry('Debug panel initialized');
        
        // Add the modal to the page
        document.body.appendChild(modal);
    });
});