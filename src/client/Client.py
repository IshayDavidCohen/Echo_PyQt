import sys
import json
from typing import List, Dict
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QMessageBox
from datetime import datetime

# App dependencies
from src.client.ChannelManager import ChannelType
from src.client.ClientConnection import ClientConnection
from src.utility.Settings import MAX_USERS_PER_CHANNEL


class Client(QtWidgets.QMainWindow):
    def __init__(self, port: int, host: str):
        super().__init__()

        # Load the UI file
        uic.loadUi('./src/ui/CredentialsWindow.ui', self)

        # Initialize client connection
        self.client = ClientConnection(host, port)

        # Attach client signals
        self.client.auth_response.connect(self._handle_auth_response)
        self.client.server_error.connect(self._handle_error)

        # Connect buttons to their functions
        self.login_button.clicked.connect(self.login)
        self.signup_button.clicked.connect(self.signup)

        # Store main window ref
        self.main_window = None

        self._establish_connection()

    def login(self):
        username = self.username_input.toPlainText()
        password = self.password_input.toPlainText()

        if not username or not password:
            QMessageBox.warning(self, 'Error', 'Please fill all fields!')
            return

        # Checking connection before login
        self._check_connection()
        print("[DEBUG] Sending auth request...")  # Debug print
        self.client.send_auth('signin', username, password)

    def signup(self):
        username = self.username_input.toPlainText()
        password = self.password_input.toPlainText()

        if not username or not password:
            QMessageBox.warning(self, 'Error', 'Please fill all fields!')
            return

        # Checking connection before signup
        self._check_connection()
        self.client.send_auth('signup', username, password)

    def open_main_window(self, username):
        # Always create a fresh instance
        self.main_window = MainWindow(username, self)
        self.main_window.show()
        self.hide()

    def closeEvent(self, event):
        """Handle window close"""
        self.client.disconnect()
        event.accept()

    # Private functions and signal handlers
    def _handle_auth_response(self, response: str):
        """Handle authentication responses from server"""

        print(f"[DEBUG] Got auth response: {response}")  # Debug print

        response = response.strip()

        # Block signals to prevent multiple signals - Might need to check functionality, right now its commented out
        # self.client.blockSignals(True)

        try:
            username = self.username_input.toPlainText()

            if response == "SIGNIN_SUCCESS":
                if self.main_window is None:
                    self.open_main_window(username)
                    self._clear_inputs()
            elif response == "SIGNUP_SUCCESS":
                QMessageBox.information(self, 'Success', 'Account created successfully!')
                self._clear_inputs()
            else:
                error_messages = {
                    "USER_EXISTS": "Username already exists!",
                    "WRONG_PASSWORD": "Invalid credentials!",
                    "INVALID_FORMAT": "Invalid username or password format!",
                    "AUTH_ERROR": "Authentication error occurred!",
                    "MAX_USERS_REACHED": "Maximum users reached!",
                    "USER_LOGGED_IN": "User already logged in!"
                }
                QMessageBox.warning(self, 'Error',
                                    error_messages.get(response, "Unknown error occurred!"))
        finally:
            pass
            # self.client.blockSignals(False)

    def _handle_error(self, error: str):
        """Handle server error messages"""
        QMessageBox.critical(self, 'Server Error', error)
        self.is_connected = False  # Mark connection as invalid

    def _clear_inputs(self):
        """Clear input fields"""
        self.username_input.clear()
        self.password_input.clear()

    def _check_connection(self):
        if self.client.is_connected is False:
            QMessageBox.critical(self, 'Connection Error',
                                 'Lost connection to server. Please restart the application.')
            self.close()
            sys.exit(1)

    def _establish_connection(self):
        self.client.connect()
        self._check_connection()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, username, credentials_window):
        super().__init__()

        # Load the UI file
        uic.loadUi('./src/ui/Main.ui', self)

        # Store credentials window ref
        self.credentials_window = credentials_window
        self.username = username

        # Get client connection from credentials window
        self.client = credentials_window.client

        # Connect client signals
        self.client.metadata_response.connect(self.update_users_list)
        self.client.message_received.connect(self._handle_server_broadcast)
        self.client.server_error.connect(self._handle_error)

        # Set username in UI
        self.username_label.setText(f'Welcome,    {username}.')
        self.max_users_allowed.setText(f'{MAX_USERS_PER_CHANNEL}')

        # Get all connected users
        self.client.get_users()

        # Connect UI elements
        self.logout_button.clicked.connect(self.logout)
        self.message_input.returnPressed.connect(self.send_message_button.click)
        self.send_message_button.clicked.connect(self.send_message)

    def send_message(self):
        message_time = datetime.now().strftime("%H:%M:%S")
        message = self.message_input.text()

        if message:
            self._handle_message(message_time, self.username, message)

            # Send to server
            self.client.send_message(
                json.dumps({'time': message_time, 'user': self.username, 'message': message}))

            self.message_input.clear()

    def update_users_list(self, users: Dict) -> None:
        server_res = users.get('users')
        if server_res is None:
            server_res = []

        self.user_count.setText(f"{len(server_res)}")
        self.users_list.clear()
        self.users_list.addItems(server_res)

    def logout(self):
        # Disconnect ClientConnection
        self.client.send_message('logout')

        # Clear all data
        self.close()

        # Show credentials window again
        self.credentials_window.main_window = None
        self.credentials_window.show()

    def _handle_message(self, time: str, sender: str, message: str):
        self.chat_display.append(f"[{time}] {sender}: {message}")

    def _handle_server_broadcast(self, server_payload: Dict):
        time = server_payload.get('time')
        sender = server_payload.get('sender')
        message = server_payload.get('message')

        if time and sender and message:
            self._handle_message(time, sender, message)

    def _handle_channel_update(self, data):
        try:
            update = json.loads(data)
            action = update.get('action')
            channel = update.get('channel')
            self.channel_manager.handle_action(action=ChannelType[action.upper()],
                                               channel_name=channel,
                                               data=update.get('data'))
        except Exception as e:
            print(f"Error handling channel update: {e}")

    def _handle_error(self, error: str):
        QMessageBox.critical(self, 'Server Error', error)

    def closeEvent(self, event):
        self.logout()
        self.credentials_window.main_window = None
        super().closeEvent(event)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    # Create and show credentials window
    credentials_window = Client()
    credentials_window.show()

    sys.exit(app.exec_())
