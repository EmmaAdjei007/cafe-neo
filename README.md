# File: README.md

# Neo Cafe Dashboard

An integrated dashboard application for Neo Cafe, featuring a coffee-themed interface with order management, menu display, delivery tracking, and an AI-powered chatbot assistant.

## Features

- **Dashboard**: View sales analytics, inventory status, and order tracking
- **Menu Management**: Display and manage menu items with filtering and search
- **Order System**: Process and track customer orders
- **Delivery Tracking**: Track robot deliveries in real-time
- **Chatbot Assistant**: Interact with customers via an AI-powered assistant

## Technologies

- **Dash**: Interactive web application framework
- **Flask**: Backend web server
- **Socket.IO**: Real-time communication
- **Chainlit**: AI chatbot integration
- **Plotly**: Data visualization
- **Bootstrap**: Responsive UI styling

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+ (for Chainlit)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/neo-cafe.git
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
cp .env.example .env
# Edit .env file with your configuration
```

### Running the application

1. Start the Chainlit chatbot:
```bash
cd chainlit_app
chainlit run app.py --port 8001
```

2. In a separate terminal, start the main dashboard:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:8050
```

## Project Structure

- `app.py`: Main application entry point
- `app/`: Core application modules
  - `layouts/`: Dash page layouts
  - `callbacks/`: Callback functions
  - `components/`: Reusable UI components
  - `data/`: Data management
  - `utils/`: Utility functions
- `chainlit_app/`: Chainlit chatbot integration
- `assets/`: Static files (CSS, images, JavaScript)
- `templates/`: HTML templates

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