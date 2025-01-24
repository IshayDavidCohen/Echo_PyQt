# Echo

Real-time multi-client chat application built with PyQt5 and socket programming.


## Architecture

```
                                  +-------------+
                                  |             |
                                  | Orchestrator|
                                  |   (main.py) |
                                  |             |
                                  +------+------+
                                         |
                         +---------------+---------------+
                         |                               |
                   +-----v-----+                   +-----v-----+
                   |           |                   |           |
                   |  Server   |                   |  Client   |
                   |           |                   |           |
                   +-----+-----+                   +-----+-----+
                         |                               |
                         |                               |
              +---------+---------+             +--------+--------+
              |                   |             |                 |
        +-----v-----+      +-----v-----+  +----v----+     +-----v-----+
        |  handle_  |      | broadcast |  |  auth   |     |  handle   |
        | connection|      | message   |  | handler |     |  message  |
        +-----------+      +-----------+  +---------+     +-----------+
```

## Features
- Multi-client support
- Real-time messaging
- User authentication (signup/signin)
- Active users list
- Message broadcasting

## Getting Started

### Prerequisites
- Python 3.8+
- PyQt5

### Installation
```bash
git clone https://github.com/IshayDavidCohen/Echo_PyQt.git
cd Echo_PyQt
pip install -r requirements.txt
```

### Running the Application
```bash
python main.py [--clients=N] [--port=PORT] [--host=HOST]
```

Arguments:
- `--clients`: Number of client windows (default: 3)
- `--port`: Server port (default: 6000)
- `--host`: Server host (default: localhost)

## Project Structure

```
echo/
├── src/
│   ├── client/
│   │   ├── Client.py          # Main client UI and logic
│   │   ├── ClientConnection.py # Socket handling for client
│   │   └── ServerListener.py  # Client-side message handling
│   ├── server/
│   │   └── Server.py         # Server implementation
│   └── utility/
│       └── Settings.py       # Global settings
├── main.py                   # Application entry point
└── requirements.txt
```

## How It Works

1. **Orchestrator (main.py)**
   - Initializes server thread
   - Launches multiple client instances
   - Manages application lifecycle

2. **Server**
   - Handles client connections
   - Manages authentication
   - Broadcasts messages
   - Tracks active users

3. **Client**
   - Provides login/signup UI
   - Manages chat interface
   - Handles real-time message updates
   - Maintains server connection

