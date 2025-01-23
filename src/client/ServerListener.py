import socket
import json
from PyQt5.QtCore import QThread, pyqtSignal

SERVER_RESPONSES = ['SIGNIN_SUCCESS', 'SIGNUP_SUCCESS', 'USER_EXISTS',
                    'WRONG_PASSWORD', 'WRONG_PASSWORD', 'NOT_IN_CHANNEL', 'MAX_USERS_REACHED']


class ServerListener(QThread):
    # Define different signals that will be used
    auth_response = pyqtSignal(str)  # Auth responses
    metadata_response = pyqtSignal(dict)
    channel_update = pyqtSignal(str)  # For channel-related updates
    message_received = pyqtSignal(dict)  # (channel,message)
    server_error = pyqtSignal(str)  # For error messages

    def __init__(self, socket):
        super().__init__()
        self.socket = socket
        self.running = True
        self.EMIT_MAPPER = {'get_users': self.metadata_response,
                            'chat_message': self.message_received}

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
                for response in SERVER_RESPONSES:
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
                    print(f"[DEBUG] ServerListener parsed JSON: {update}")
                    if update.get('action') in self.EMIT_MAPPER:
                        self.EMIT_MAPPER[update.get('action')].emit(update.get('data'))

                except json.JSONDecodeError:
                    print(f"[DEBUG] Could not parse as JSON: {data}")

            except socket.timeout:
                continue
            except socket.error as e:
                self.server_error.emit(f"[CLIENT/ServerListener] Connection error: {str(e)}")
                break

    def stop(self):
        self.running = False
