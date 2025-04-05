// ChatComponent.js - Converted from JSX to plain JavaScript

// Create shorthand for React.createElement
const e = React.createElement;

// ChatComponent function
const ChatComponent = () => {
  const [messages, setMessages] = React.useState([
    { id: 1, sender: 'bot', content: 'Hello! Welcome to Neo Cafe. How can I assist you today?' }
  ]);
  const [inputValue, setInputValue] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const messagesEndRef = React.useRef(null);
  const [connectionStatus, setConnectionStatus] = React.useState('checking');

  // Scroll to bottom of messages
  React.useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Check connection to Chainlit server
  React.useEffect(() => {
    const checkConnection = async () => {
        try {
          // Try to check connection status
          let response;
          try {
            // First try relative URL
            response = await fetch('/chainlit-status');
          } catch (error) {
            // If that fails, try with window.location.origin
            const baseUrl = window.location.origin;
            response = await fetch(`${baseUrl}/chainlit-status`);
          }
          
          if (response.ok) {
            setConnectionStatus('connected');
          } else {
            setConnectionStatus('error');
          }
        } catch (error) {
          console.error('Connection check failed:', error);
          setConnectionStatus('error');
        }
      };

    checkConnection();
    const intervalId = setInterval(checkConnection, 30000); // Check every 30 seconds
    return () => clearInterval(intervalId);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage = { id: Date.now(), sender: 'user', content: inputValue };
    setMessages([...messages, userMessage]);
    
    // Clear input and set loading
    setInputValue('');
    setIsLoading(true);

    // Simulate bot response (in a real app, this would call the actual API)
    setTimeout(() => {
      if (connectionStatus === 'connected') {
        // Make actual API call to Chainlit
        fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userMessage.content })
        })
          .then(res => res.json())
          .then(data => {
            setMessages(prev => [...prev, { 
              id: Date.now(), 
              sender: 'bot', 
              content: data.response || 'Sorry, I encountered an issue processing your request.'
            }]);
            setIsLoading(false);
          })
          .catch(err => {
            console.error('Error calling chat API:', err);
            // Fallback response if API fails
            handleFallbackResponse(userMessage.content);
          });
      } else {
        // Use fallback responses if not connected
        handleFallbackResponse(userMessage.content);
      }
    }, 500);
  };

  const handleFallbackResponse = (userMessage) => {
    // Simple fallback responses when Chainlit is not available
    let response = "I'm having trouble connecting to my backend. Please try again later.";
    
    const lowerMsg = userMessage.toLowerCase();
    
    if (lowerMsg.includes('hello') || lowerMsg.includes('hi')) {
      response = "Hello! I'm BaristaBot. I'm currently operating in fallback mode but I'll try to help you.";
    } else if (lowerMsg.includes('menu')) {
      response = "Our menu includes espresso, latte, cappuccino, cold brew, and various pastries. For the full menu, please check the Menu tab.";
    } else if (lowerMsg.includes('hours')) {
      response = "Neo Cafe is open Monday-Friday 7am-8pm and Saturday-Sunday 8am-6pm.";
    } else if (lowerMsg.includes('order')) {
      response = "To place an order, please visit the Orders tab or try again when our chat service is back online.";
    }
    
    setMessages(prev => [...prev, { id: Date.now(), sender: 'bot', content: response }]);
    setIsLoading(false);
  };

  // Quick action buttons
  const quickActions = [
    { label: 'Place Order', action: () => setInputValue('I want to place an order') },
    { label: 'Today\'s Special', action: () => setInputValue('What\'s your special today?') },
    { label: 'Track Order', action: () => setInputValue('Track my order') },
    { label: 'Hours', action: () => setInputValue('What are your hours?') },
  ];

  // Create connection status element if needed
  let connectionStatusElement = null;
  if (connectionStatus !== 'connected') {
    connectionStatusElement = e('div', { 
      className: "p-2 bg-yellow-100 text-yellow-800 text-center text-sm" 
    }, connectionStatus === 'checking' ? 'Connecting to chat service...' : 'Chat service is not available. Using fallback mode.');
  }

  // Create loading indicator element
  const loadingIndicator = isLoading ? e('div', { 
    className: "flex justify-start mb-4" 
  }, e('div', { 
    className: "bg-gray-200 p-3 rounded-lg rounded-bl-none" 
  }, e('div', { 
    className: "flex space-x-1" 
  }, [
    e('div', { key: 1, className: "w-2 h-2 bg-gray-500 rounded-full animate-bounce" }),
    e('div', { key: 2, className: "w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" }),
    e('div', { key: 3, className: "w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" })
  ]))) : null;

  // Create message elements
  const messageElements = messages.map(message => 
    e('div', { 
      key: message.id, 
      className: `mb-4 flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`
    }, e('div', { 
      className: `max-w-3/4 p-3 rounded-lg ${
        message.sender === 'user' 
          ? 'bg-blue-600 text-white rounded-br-none' 
          : 'bg-gray-200 text-gray-800 rounded-bl-none'
      }`
    }, message.content))
  );

  // Create quick action buttons
  const quickActionButtons = quickActions.map((action, index) => 
    e('button', {
      key: index,
      onClick: action.action,
      className: "bg-gray-200 hover:bg-gray-300 text-gray-800 px-3 py-1 rounded-full text-sm"
    }, action.label)
  );

  // Create SVG icon for send button
  const sendIcon = e('svg', {
    xmlns: "http://www.w3.org/2000/svg",
    className: "h-5 w-5",
    fill: "none",
    viewBox: "0 0 24 24",
    stroke: "currentColor"
  }, e('path', {
    strokeLinecap: "round",
    strokeLinejoin: "round",
    strokeWidth: 2,
    d: "M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
  }));

  // Return the component structure
  return e('div', { className: "flex flex-col h-full bg-white rounded-lg shadow-lg overflow-hidden" }, [
    // Connection Status
    connectionStatusElement,
    
    // Messages Container
    e('div', { className: "flex-1 p-4 overflow-y-auto" }, [
      ...messageElements,
      loadingIndicator,
      e('div', { ref: messagesEndRef })
    ]),
    
    // Quick Actions
    e('div', { className: "px-4 py-2 border-t border-gray-200" }, 
      e('div', { className: "flex flex-wrap gap-2 mb-2" }, quickActionButtons)
    ),
    
    // Input Area
    e('form', { 
      onSubmit: handleSubmit, 
      className: "p-4 border-t border-gray-200" 
    }, e('div', { 
      className: "flex space-x-2" 
    }, [
      e('input', {
        type: "text",
        value: inputValue,
        onChange: (e) => setInputValue(e.target.value),
        placeholder: "Type your message...",
        className: "flex-1 border border-gray-300 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
      }),
      e('button', {
        type: "submit",
        className: "bg-blue-600 text-white rounded-full w-10 h-10 flex items-center justify-center",
        disabled: isLoading
      }, sendIcon)
    ]))
  ]);
};

// Initialize the ChatComponent when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const mountPoint = document.getElementById('chat-component-mount-point');
  if (mountPoint) {
    ReactDOM.render(e(ChatComponent), mountPoint);
  }
});