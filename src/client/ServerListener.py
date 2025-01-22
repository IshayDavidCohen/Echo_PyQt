import socket
import json
from PyQt5.QtCore import QThread, pyqtSignal

SERVER_RESPONSES = ['SIGNIN_SUCCESS', 'SIGNUP_SUCCESS', 'USER_EXISTS', 'WRONG_PASSWORD', 'WRONG_PASSWORD', 'NOT_IN_CHANNEL']


class ServerListener(QThread):
    # Define different signals that will be used
    auth_response = pyqtSignal(str)  # Auth responses
    channel_update = pyqtSignal(str)  # For channel-related updates
    message_received = pyqtSignal(str, str)  # (channel,message)
    server_error = pyqtSignal(str)  # For error messages

    def __init__(self, socket):
        super().__init__()
        self.socket = socket
        self.running = True

    # def run(self):
    #     # Main loop that listens for server messages
    #
    #     self.socket.settimeout(0.5)  # Set half a second of timeout
    #     while self.running:
    #         try:
    #             # Assuming messages are JSON
    #             data = self.socket.recv(1024).decode('utf-8')
    #             if not data:
    #                 continue
    #
    #             print(f"[DEBUG] ServerListener received: {data}")
    #             if any(response in data for response in SERVER_RESPONSES):
    #                 print(f"[DEBUG] ServerListener emitting auth response: {data}")
    #                 self.auth_response.emit(data)
    #                 continue
    #
    #             # Parse the received JSON data
    #             messages = data.strip().split('\n')
    #             for message in messages:
    #                 try:
    #                     update = json.loads(message)
    #                     self.handle_server_update(update)
    #                 except json.JSONDecodeError:
    #                     print(f"[DEBUG] Could not parse as JSON: {data}")
    #
    #         except socket.timeout:
    #             # Continue loop to check running flag
    #             continue
    #         except socket.error as e:
    #             self.server_error.emit(f"[CLIENT/ServerListener] Connection error: {str(e)}")
    #             break

    def run(self):
        self.socket.settimeout(0.5)
        while self.running:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    continue

                data = data.strip()
                print(f"[DEBUG] ServerListener received: {data}")

                # Clean up the response - take only the first instance of a response
                for response in ["SIGNIN_SUCCESS", "SIGNUP_SUCCESS", "USER_EXISTS",
                                 "WRONG_PASSWORD", "NOT_IN_CHANNEL"]:
                    if response in data:
                        # Extract just the response code
                        response_start = data.find(response)
                        print(f"[DEBUG] Original response: {response}")
                        clean_response = data[response_start:response_start + len(response)]
                        print(f"[DEBUG] ServerListener emitting cleaned auth response: {clean_response}")
                        self.auth_response.emit(clean_response)
                        break  # Only emit the first match

                # Try JSON for other messages
                try:
                    update = json.loads(data)
                    self.handle_server_update(update)
                except json.JSONDecodeError:
                    print(f"[DEBUG] Could not parse as JSON: {data}")

            except socket.timeout:
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
