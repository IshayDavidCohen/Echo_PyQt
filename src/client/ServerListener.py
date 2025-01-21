import socket
import json
from PyQt5.QtCore import QThread, pyqtSignal


class ServerListener(QThread):
    # Define different signals that will be used
    channel_update = pyqtSignal(str)  # For channel-related updates
    message_received = pyqtSignal(str, str)  # (channel,message)
    server_error = pyqtSignal(str)  # For error messages

    def __init__(self, socket):
        super().__init__()
        self.socket = socket
        self.running = True

    def run(self):
        # Main loop that listens for server messages
        while self.running:
            try:
                # Assuming messages are JSON
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    continue

                # Parse the received JSON data
                messages = data.strip().split('\n')
                for message in messages:
                    try:
                        update = json.loads(message)
                        self.handle_server_update(update)
                    except json.JSONDecodeError:
                        continue
            except socket.error as e:
                self.server_error.emit(f"[CLIENT/ServerListener] Connection error: {str(e)}")
                break

    def handle_server_update(self, update):
        update_type = update.get('type')
        if update_type == 'channel_update':
            self.channel_update.emit(update.get('data'))

        elif update_type == 'chat_message':
            self.message_received.emit(
                update.get('channel'),
                update.get('message')
            )
        # Might need to add more

    def stop(self):
        self.running = False
        self.wait()
