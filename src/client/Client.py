import socket
import sys
import json
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QMessageBox

# App dependencies
from src.client.ServerListener import ServerListener
from src.client.CreateChannel import CreateChannelDialog
from src.client.ChannelManager import ChannelManager, ChannelType
from src.utility.Settings import ENCODING, USERNAMES


class CredentialsWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Load the UI file
        uic.loadUi('./src/ui/CredentialsWindow.ui', self)

        # Connect buttons to their functions
        self.login_button.clicked.connect(self.login)
        self.signup_button.clicked.connect(self.signup)

        # Store main window ref
        self.main_window = None

    def login(self):
        username = self.username_input.toPlainText()
        password = self.password_input.toPlainText()

        try:
            with open(USERNAMES, 'r') as file:
                users = json.load(file)

            if username in users and users.get(username) == password:
                self.open_main_window(username)
            else:
                QMessageBox.warning(self, 'Error', 'Invalid Credentials')

        except FileNotFoundError:
            QMessageBox.warning(self, 'Error', 'No users registered yet!')

    def signup(self):
        username = self.username_input.toPlainText()
        password = self.password_input.toPlainText()

        if not username or not password:
            QMessageBox.warning(self, 'Error', 'Please fill all fields!')
            return

        try:
            with open(USERNAMES, 'r') as file:
                users = json.load(file)
        except FileNotFoundError:
            users = {}

        if username in users:
            QMessageBox.warning(self, 'Error', 'Username already exists!')
            return

        users[username] = password

        with open(USERNAMES, 'w') as file:
            json.dump(users, file)

        QMessageBox.information(self, 'Success', 'Account created successfully!')

        # TODO:  Probably should clear text boxes

    def open_main_window(self, username):
        # Always create a fresh instance
        self.main_window = MainWindow(username, self)
        self.main_window.show()
        self.hide()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, username, credentials_window):
        super().__init__()

        # Load the UI file
        uic.loadUi('./src/ui/Main.ui', self)

        # Store credentials window ref
        self.credentials_window = credentials_window

        # Init Channel Manager
        self.channel_manager = ChannelManager(self)

        # Store username and initialize socket
        self.username = username
        self.socket = None
        self.server_listener = None
        self.current_channel = None

        # Set username in UI
        self.username_label.setText(f'Welcome,    {username}.')

        # Initialize empty channels list
        self.channels = []

        # Connect UI elements
        self.logout_button.clicked.connect(self.logout)
        self.create_channel_button.clicked.connect(self.create_channel)
        # self.channel_list.itemDoubleClicked.connect(self.join_channel)
        # self.send_message_button.clicked.connect(self.send_message)

        # Connect to server
        # self.connect_to_server()

    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', 6000))  # TODO: Placeholder needs to be changed!

            # Set up the listener
            self.setup_server_listener()

            self.authenticate()
        except socket.error as e:
            QMessageBox.critical(self, 'Connection Error', f'Failed to connect to server: {str(e)}')
            self.close()
            self.credentials_window.show()

    def setup_server_listener(self):
        self.server_listener = ServerListener(self.socket)

        # Connect signals to slots
        self.server_listener.channel_update.connect(self.handle_channel_update)
        self.server_listener.message_received.connect(self.handle_message)
        self.server_listener.server_error.connect(self.handle_server_error)

        # Activate listener
        self.server_listener.start()

    def authenticate(self):
        auth_message = f"signin {self.username} {self.credentials_window.password_input.toPlainText()}"
        self.socket.sendall(auth_message.encode(ENCODING))

        # Wait for response
        response = self.socket.recv(1024).decode(ENCODING)

        if response != "SIGNIN_SUCCESS":
            QMessageBox.critical(self, 'Authentication Error', 'Failed to server authentication')
            self.close()
            self.credentials_window.show()

    def create_channel(self):
        dialog = CreateChannelDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            channel_name = dialog.channel_name.text()

            if channel_name:
                try:
                    self.socket.sendall(f"create {channel_name}".encode(ENCODING))
                except (BrokenPipeError, AttributeError):
                    QMessageBox.critical(self, 'Connection Error',
                                         'Lost connection to server while trying to create channel')
                    self.close()
                    self.credentials_window.show()

    # def join_channel(self):
    #     channel_name = self.channel_list.selectedItems()[0].text()  # TODO: Need to implement only a single select
    #     if not channel_name:
    #         QMessageBox.warning(self, 'Error', 'Please enter a channel name!')
    #         return
    #     try:
    #         self.socket.sendall(f"join {channel_name}".encode(ENCODING))
    #     except (BrokenPipeError, AttributeError):
    #         QMessageBox.critical(self, 'Connection Error', 'Lost connection to server while trying to join channel')
    #         self.close()
    #         self.credentials_window.show()

    def send_message(self):
        if not self.current_channel:
            QMessageBox.warning(self, 'Error', 'Please join a channel first!')
            return

        message = self.message_input.toPlainText()
        if message:
            try:
                self.socket.sendall(message.encode(ENCODING))
            except (BrokenPipeError, AttributeError):
                QMessageBox.critical(self, 'Connection Error', 'Lost connection to server while trying to send message')
                self.close()
                self.credentials_window.show()

            self.message_input.clear()

    def handle_channel_update(self, data):
        try:
            update = json.load(data)
            action = update.get('action')
            channel = update.get('channel')

            try:
                channel_action = ChannelType[action.upper()]
                self.channel_manager.handle_action(action=channel_action, channel_name=channel, data=update.get('data'))
            except KeyError:
                print(f'[CLIENT] Unknown channel action: {action}')
        except json.JSONDecodeError:
            print(f'[CLIENT] Failed to parse channel update')

    def join_channel(self, item):
        channel_name = item.text()
        self.channel_manager.handle_action(ChannelType.JOIN, channel_name)

    def logout(self):
        # Clear all data
        self.close()

        # Show credentials window again
        self.credentials_window.show()

    def retrieve_channel(self):
        pass

    def retrieve_channel_data(self, channel_name: str):
        pass

    # TODO: Need to implement update from server (channel was deleted, created, etc.)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    # Create and show credentials window
    credentials_window = CredentialsWindow()
    credentials_window.show()

    sys.exit(app.exec_())
