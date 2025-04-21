if (!window.dash_clientside) {
    window.dash_clientside = {};
}

window.dash_clientside.clientside = {
    /**
     * Listen for messages from the Chainlit iframe
     * @returns {null}
     */
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
    },

    /**
     * Update chat authentication when user logs in
     * 
     * @param {Object} userData - User data from user-store
     * @returns {null} - No return value needed
     */
    updateChatAuth: function(userData) {
        console.log('Auth update received:', userData);
        
        if (!userData || !userData.username) {
            return null;
        }
        
        // Find chat iframe
        const chatFrame = document.getElementById('floating-chainlit-frame');
        if (!chatFrame || !chatFrame.contentWindow) {
            console.log('Chat frame not found, auth update skipped');
            return null;
        }
        
        // Create auth token
        const authData = {
            username: userData.username,
            id: userData.id || '',
            email: userData.email || '',
            first_name: userData.first_name || '',
            last_name: userData.last_name || ''
        };
        
        // Convert to base64 token
        let authToken;
        try {
            const jsonData = JSON.stringify(authData);
            authToken = btoa(jsonData);
        } catch (e) {
            console.error('Error creating auth token:', e);
            return null;
        }
        
        // Send auth data to chat iframe
        console.log('Sending auth data to chat frame:', authData.username);
        
        // Try multiple message formats to ensure it's received
        try {
            chatFrame.contentWindow.postMessage({
                type: 'auth_update',
                user: authData.username,
                token: authToken,
                auth_status: true
            }, '*');
            
            // Also try credentials format
            chatFrame.contentWindow.postMessage({
                type: 'credentials',
                user: authData.username,
                token: authToken
            }, '*');
            
            // Also try direct parameter format
            let params = new URLSearchParams();
            params.append('user', authData.username);
            params.append('token', authToken);
            
            // Try to update the iframe src with auth params
            const currentSrc = chatFrame.src;
            const baseUrl = currentSrc.split('?')[0];
            chatFrame.src = baseUrl + '?' + params.toString();
            
            console.log('Auth data sent to chat frame');
        } catch (e) {
            console.error('Error sending auth data to chat frame:', e);
        }
        
        return null;
    }
};
