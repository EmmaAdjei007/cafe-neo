if (!window.dash_clientside) {
    window.dash_clientside = {};
}

window.dash_clientside.clientside = {
    updateChatListener: function() {
        // Listen for messages from iframe
        window.addEventListener('message', function(event) {
            // Process messages from Chainlit iframe
            if (event.data && event.data.type) {
                // Update the hidden div with the message data
                document.getElementById('chat-message-listener').textContent = JSON.stringify(event.data);
            }
        });
        
        return null;
    }
};