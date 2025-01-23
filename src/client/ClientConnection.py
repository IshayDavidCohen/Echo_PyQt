import socket
from PyQt5.QtCore import QObject, pyqtSignal

# App Dependencies
from src.client.ServerListener import ServerListener
from src.utility.Settings import ENCODING


class ClientConnection(QObject):
    # Define signals for UI updates
    auth_response = pyqtSignal(str)  # For authentication responses
    metadata_response = pyqtSignal(dict)  # For channel-related responses
    message_received = pyqtSignal(str, str)  # channel, message
    server_error = pyqtSignal(str)  # For error messages

    def __init__(self, host: str, port: int):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self.server_listener = None
        self.current_channel = None
        self.is_connected = False

    def connect(self) -> bool:
        try:
            # Reset
            self.socket = None
            if self.server_listener is not None:
                self.server_listener.stop()
                self.server_listener = None

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))

            # Set up the listener
            self.setup_server_listener()
            self.is_connected = True
            return True
        except socket.error as e:
            self.server_error.emit(f"Connection failed: {str(e)}")
            return False

    def setup_server_listener(self):
        print("[DEBUG] Setting up server listener")  # Debug print
        self.server_listener = ServerListener(self.socket)

        # Direct connection of signals
        print("[DEBUG] Connecting ServerListener signals...")
        self.server_listener.auth_response.connect(self.auth_response)
        self.server_listener.metadata_response.connect(self.metadata_response)
        self.server_listener.message_received.connect(self.message_received)
        self.server_listener.server_error.connect(self._handle_server_error)

        print("[DEBUG] Starting ServerListener thread...")
        self.server_listener.start()

    # All the network functions we might need
    def send_auth(self, action: str, username: str, password: str):
        """Send authentication request"""
        print(f"[DEBUG] ClientConnection sending: {action}")  # Debug print
        auth_message = f"{action} {username} {password}"
        self._send(auth_message)

    def get_users(self):
        self._send("get_users")

    def send_message(self, message: str):
        """Send chat message"""
        self._send(message)

    def disconnect(self):
        """Clean disconnect from server"""
        if self.server_listener:
            self.server_listener.stop()
        if self.socket:
            try:
                self._send("/quit")
                self.socket.close()
            except:
                pass

    def _send(self, message: str):
        """Internal method to send messages to server"""
        try:
            self.socket.sendall(message.encode(ENCODING))
        except Exception as e:
            self.server_error.emit(f"Send failed: {str(e)}")

    # Signal Handlers
    # def _handle_metadata_update(self, data):
    #     self.metadata_response.emit(data)

    def _handle_message(self, channel, message):
        self.message_received.emit(channel, message)

    def _handle_server_error(self, error):
        self.server_error.emit(error)