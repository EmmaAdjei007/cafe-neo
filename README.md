# Neo Cafe Dashboard

An integrated dashboard application for Neo Cafe, featuring a coffee-themed interface with order management, menu display, delivery tracking, and a robust AI-powered chatbot assistant.

## Features

- **Dashboard**: View sales analytics, inventory status, and real-time order tracking
- **Menu Management**: Interactive menu display with filtering, search, and dietary preferences
- **Order System**: Seamless order processing and status tracking
- **Delivery Tracking**: Real-time robot delivery tracking with map visualization
- **Integrated Chatbot**: AI-powered assistant with reliable cross-application communication

### Enhanced Communication Features

- **Multi-channel Communication**: Reliable message passing between Dash and Chainlit via:
  - Real-time Socket.IO events
  - Parent-child iframe messaging
  - HTTP API endpoints
  - File-based message exchange (fallback mechanism)
  
- **Robust Messaging**: Automatic retries, queuing, and fallbacks for all messages
- **Session Management**: Persistent sessions across application components
- **Comprehensive Error Handling**: Graceful error recovery for all communication channels

## Technologies

- **Dash**: Interactive web application framework for the main dashboard
- **Flask**: Backend web server with custom API endpoints
- **Socket.IO**: Real-time bidirectional communication
- **Chainlit**: AI chatbot integration with LangChain
- **LangChain**: Framework for LLM-powered applications
- **Plotly**: Interactive data visualization
- **Bootstrap**: Responsive UI styling
- **Eventlet**: WSGI server with Socket.IO support

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+ (for Chainlit)
- OpenAI API key (for LangChain)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/EmmaAdjei007/neo-cafe.git
cd neo-cafe
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env .env
# Edit .env file with your configuration, including OpenAI API key
```

### Running the application

There are three ways to run the application:

#### Option 1: Using the combined runner (recommended)

This starts both the Dash app and Chainlit chatbot simultaneously:

```bash
python run.py
```

#### Option 2: Using the eventlet runner for better Socket.IO performance

```bash
python run_with_eventlet.py
```

#### Option 3: Starting components separately

In one terminal, start the Chainlit chatbot:
```bash
cd chainlit_app
chainlit run app.py --port 8000
```

In another terminal, start the main dashboard:
```bash
python app.py
```

Then open your browser and navigate to:
```
http://localhost:8050
```

## Project Structure

- `app.py`: Main application entry point
- `run.py`: Combined runner for both Dash and Chainlit
- `run_with_eventlet.py`: Eventlet-optimized runner
- `server.py`: Flask server configuration
- `app/`: Core application modules
  - `layouts/`: Dash page layouts
  - `callbacks/`: Callback functions
  - `components/`: Reusable UI components
  - `data/`: Data management
  - `utils/`: Utility functions
    - `chat_bridge.py`: Robust communication bridge
    - `socketio_setup.py`: Socket.IO configuration utilities
- `chainlit_app/`: Chainlit chatbot integration
  - `app.py`: Chainlit application
  - `states.py`: State management for chat
- `assets/`: Static files (CSS, images, JavaScript)
  - `js/chat_messenger.js`: Client-side messaging handling
- `templates/`: HTML templates
  - `chainlit_embed.html`: Iframe integration template

## Troubleshooting

### Socket.IO Connection Issues

If you experience connection problems:

1. Make sure you're using the `run_with_eventlet.py` script which properly handles monkey patching
2. Check that port 8050 (Dash) and 8001 (Chainlit) are not in use
3. Verify that your firewall is not blocking WebSocket connections

### Chat Integration Problems

If the chat integration isn't working:

1. Clear your browser cache and cookies
2. Check browser console for JavaScript errors
3. Verify that the CHAINLIT_URL environment variable is set correctly
4. Try using the file-based message exchange by enabling DEBUG mode

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Coffee icons created by [Freepik](https://www.freepik.com)
- Dashboard template inspired by [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/)