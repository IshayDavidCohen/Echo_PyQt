import sys
import json
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QMessageBox

# App dependencies
from src.client.CreateChannel import CreateChannelDialog
from src.client.ChannelManager import ChannelManager, ChannelType
from src.client.ClientConnection import ClientConnection


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
                    "AUTH_ERROR": "Authentication error occurred!"
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
        self.client.channel_response.connect(self._handle_channel_update)
        self.client.message_received.connect(self._handle_message)
        self.client.server_error.connect(self._handle_error)

        # Init Channel Manager
        self.channel_manager = ChannelManager(self)

        # Set username in UI
        self.username_label.setText(f'Welcome,    {username}.')

        # Initialize empty channels list
        self.channels = []

        # Connect UI elements
        self.logout_button.clicked.connect(self.logout)
        self.create_channel_button.clicked.connect(self.create_channel)
        self.channel_list.itemDoubleClicked.connect(self.join_channel)
        self.send_message_button.clicked.connect(self.send_message)

    def create_channel(self):
        dialog = CreateChannelDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:

            channel_name = dialog.channel_name.text()
            if channel_name:
                self.client.create(channel_name)

    def join_channel(self, item):
        channel_name = item.text()
        self.client.join_channel(channel_name)

    def send_message(self):
        if self.client.current_channel is None:
            QMessageBox.warning(self, 'Error', 'Please join a channel first!')
            return

        message = self.message_input.toPlainText()
        if message:
            self.client.send_message(message)
            self.message_input.clear()

    def logout(self):
        # Disconnect ClientConnection
        self.client.send_message('logout')

        # Clear all data
        self.close()

        # Show credentials window again
        self.credentials_window.main_window = None
        self.credentials_window.show()

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

    def _handle_message(self, message: str):
        self.chat_display.append(f"{message}")

    def _handle_error(self, error: str):
        QMessageBox.critical(self, 'Server Error', error)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    # Create and show credentials window
    credentials_window = Client()
    credentials_window.show()

    sys.exit(app.exec_())
