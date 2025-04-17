# Neo Cafe Dashboard System Architecture

## Overview
The Neo Cafe Dashboard is an integrated application featuring a coffee-themed interface with order management, menu display, delivery tracking, and an AI-powered chatbot assistant. The system uses a multi-component architecture with robust communication channels between components.

## Architecture Diagram

```mermaid
flowchart TD
    Client["Client Browser"]
    WebServer["Web Server (Flask/Dash)"]
    DashFE["Dash Frontend"]
    FlaskBE["Flask API Backend"]
    CommBridge["Communication Bridge"]
    SocketIO["Socket.IO Events"]
    IframeMsg["Parent-Child iframe Messaging"]
    HTTPAPI["HTTP API Endpoints"]
    FileMsg["File-based Message Exchange"]
    DB[(Database)]
    Chainlit["Chainlit AI Chatbot"]
    Data["Menu & Order Data"]
    LangChain["LangChain Framework"]
    OpenAI["OpenAI API (GPT)"]
    RobotAPI["Robot API"]
    Robots["Delivery Robots"]

    Client <--> WebServer
    
    subgraph WebServer
        DashFE <--> FlaskBE
    end
    
    WebServer <--> CommBridge
    FlaskBE <--> RobotAPI
    RobotAPI <--> Robots
    
    subgraph CommBridge
        SocketIO
        IframeMsg
        HTTPAPI
        FileMsg
    end
    
    CommBridge <--> Chainlit
    DB <--> WebServer
    DB <--> Chainlit
    DB <--> Data
    Chainlit <--> LangChain
    LangChain <--> OpenAI
```

## Core Components

### 1. Web Application (Dash + Flask)
- **Frontend**: Built with Dash (a Python framework for building analytical web applications)
  - Interactive UI components
  - Real-time data visualization with Plotly
  - Bootstrap for responsive styling
  - Client-side JavaScript for enhanced interactivity

- **Backend**: Flask server
  - RESTful API endpoints
  - Session management
  - Authentication handling
  - Database interactions

### 2. AI Chatbot (Chainlit)
- Chainlit framework for chat interface
- LangChain integration for:
  - Knowledge base retrieval
  - Order processing
  - Menu search
  - Customer assistance

### 3. Database System
- SQLite database for:
  - Order management
  - User information
  - Menu items
  - Chat history preservation

### 4. Communication Bridge
Implements multiple redundant channels for reliable communication:
- **Socket.IO**: Real-time bidirectional event-based communication
- **Parent-Child iframe Messaging**: Direct browser messaging
- **HTTP API endpoints**: Standard REST communication
- **File-based Message Exchange**: Fallback mechanism for reliability

### 5. Order Management System
- Order creation, tracking, and updating
- Inventory management
- Delivery tracking

### 6. Robot Delivery System
- Simple API interface to robot fleet
- Dispatch and tracking capabilities
- Real-time delivery status updates

## Data Flow

1. **User Interface Interactions**:
   - Users interact with the Dash frontend
   - UI events trigger callbacks
   - Callbacks communicate with backend services

2. **Order Processing**:
   - Orders can be placed via dashboard or chatbot
   - Multiple validation and standardization steps
   - Persistent storage in database
   - Real-time status updates

3. **Chat Communication**:
   - Messages flow between dashboard and chatbot
   - Multiple fallback mechanisms ensure delivery
   - Session persistence across components

4. **AI Assistant Flow**:
   - User queries processed by LangChain agent
   - Vector store used for knowledge retrieval
   - Specialized tools for different functions (menu search, order placement, etc.)
   - Responses formatted for appropriate context

5. **Robot Delivery Flow**:
   ```mermaid
   sequenceDiagram
       participant Dashboard
       participant RobotAPI
       participant Robot
       
       Dashboard->>RobotAPI: Dispatch order
       RobotAPI->>Robot: Send delivery instructions
       Robot->>RobotAPI: Send location updates
       RobotAPI->>Dashboard: Update delivery status
       Robot->>RobotAPI: Order delivered
       RobotAPI->>Dashboard: Mark order complete
   ```

## Technology Stack

- **Frontend**: 
  - Dash (Python-based React)
  - Bootstrap CSS
  - Socket.IO client
  - Custom JavaScript

- **Backend**:
  - Flask
  - Socket.IO
  - Eventlet (for optimized Socket.IO)

- **AI Components**:
  - Chainlit
  - LangChain
  - OpenAI API (GPT models)
  - FAISS vector store

- **Robot Delivery**:
  - REST API endpoints (GET/POST/PUT)
  - WebSocket for real-time location tracking
  - Plotly for map visualization

- **Database**:
  - SQLite

- **Infrastructure**:
  - Synchronous and asynchronous processing
  - Multi-process application startup
  - Graceful error handling and recovery

## Deployment Architecture

```mermaid
flowchart LR
    User["User"]
    
    subgraph "Option 1: Combined Runner"
        Run["run.py"]
        Run --> DashApp1["Dash (Port 8050)"]
        Run --> ChainlitApp1["Chainlit (Port 8000)"]
        Run --> RobotSim1["Robot Simulator (Port 8051)"]
    end
    
    subgraph "Option 2: Eventlet Runner"
        RunEventlet["run_with_eventlet.py"]
        RunEventlet --> DashApp2["Dash with Eventlet (Port 8050)"]
        RunEventlet --> ChainlitApp2["Chainlit (Port 8000)"]
        RunEventlet --> RobotSim2["Robot Simulator (Port 8051)"]
    end
    
    subgraph "Option 3: Separate Components"
        DashApp3["app.py (Port 8050)"]
        ChainlitApp3["chainlit run app.py (Port 8000)"]
        RobotSim3["robot_simulator.py (Port 8051)"]
    end
    
    User --> Run
    User --> RunEventlet
    User --> DashApp3
    User --> ChainlitApp3
```

The application can be deployed in three ways:
1. **Combined Runner**: Starts both Dash and Chainlit simultaneously
2. **Eventlet Runner**: Optimized for Socket.IO performance
3. **Separate Components**: Individual startup for development purposes

## Communication Sequence

```mermaid
sequenceDiagram
    participant User
    participant DashUI as Dash UI
    participant Server as Flask Server
    participant Bridge as Message Bridge
    participant Chainlit
    participant GPT as OpenAI GPT
    participant DB as Database
    participant Robot as Robot API
    
    User->>DashUI: Send message
    DashUI->>Bridge: Forward message
    
    alt Socket.IO Channel
        Bridge->>Chainlit: Emit socket event
    else Iframe Channel
        Bridge->>Chainlit: Post message to iframe
    else HTTP API Channel
        Bridge->>Server: REST API call
        Server->>Chainlit: Forward message
    else File-based Channel
        Bridge->>DB: Write message to file
        Chainlit->>DB: Poll for new messages
    end
    
    Chainlit->>GPT: Process with LangChain
    GPT->>Chainlit: Return response
    
    alt Place Order
        Chainlit->>DB: Store order
        Chainlit->>Bridge: Notify order created
        Bridge->>DashUI: Update order status
        
        alt Robot Delivery
            Server->>Robot: Dispatch robot
            Robot->>Server: Send location updates
            Server->>DashUI: Update tracking map
        end
    end
    
    Chainlit->>Bridge: Send response
    Bridge->>DashUI: Display response
    DashUI->>User: Show message
```

## Key Design Patterns

1. **Bridge Pattern**: Used in message_bridge.py to decouple abstraction from implementation
2. **Observer Pattern**: Used in Socket.IO event handling
3. **Fallback Strategy Pattern**: Multiple communication methods with automatic fallback
4. **Factory Pattern**: For creating various UI components
5. **Proxy Pattern**: In the chatbot's knowledge base search

## Security Considerations

- Session-based authentication
- Token verification between components
- Cross-origin resource sharing configuration
- Error handling that doesn't expose sensitive information
- Secure robot command validation
- Emergency stop capability