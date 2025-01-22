import sys
import json
import socket
import threading

from typing import Dict, List, Optional

# App Dependencies
from src.utility.Settings import ENCODING, MAX_USERS_PER_CHANNEL, USERNAMES_FILE


class Channel:
    def __init__(self, name: str):
        self.name = name
        self.users: List[Dict] = []  # List of {conn, addr, username}
        self.messages: List[Dict] = []  # Chat History

    def add_user(self, conn, addr, username) -> bool:
        # Check if channel is full
        if len(self.users) >= MAX_USERS_PER_CHANNEL:
            return False

        # Check if user is already in the channel
        if any(user['username'] == username for user in self.users):
            return False

        # Add user to channel and inform with message.
        self.users.append({
            "conn": conn,
            "addr": addr,
            "username": username
        })

        self.messages.append({
            "sender": "SERVER",
            "content": f"{username} has joined the channel."
        })

        return True

    def remove_user(self, username: str):
        self.users = [user for user in self.users if ["username"] != username]
        self.messages.append({
            "sender": "SERVER",
            "content": f"{username} has left the channel."
        })

    def broadcast(self, message: str, sender: str, server):

        # Add message to history
        self.messages.append({
            "sender": sender,
            "content": message
        })

        # Send to all users except sender
        for user in self.users:
            if user["username"] != sender:
                server.send_message(user["conn"], f"MESSAGE {self.name} {sender} {message}")

    def get_user_list(self) -> List[str]:
        return [user["username"] for user in self.users]

    def user_in_channel(self, username: str) -> bool:
        return any(user["username"] == username for user in self.users)

    def get_history(self, limit: int = 50) -> List[Dict]:
        return self.messages[-limit:]

    def notify_users(self, server, message: str):
        for user in self.users:
            server.send_message(user["conn"], message)


class Server:
    def __init__(self, port: int, host: str):
        self.port = port
        self.host = host
        self.channels: Dict[str, Channel] = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))

        self.chats = {}  # need to create, {"chat name": [{"conn": conn, "addr": addr, "username": username}]}

        """
        remain: 
            1. error handling to client stop connection -> delete client from chats
            2. start chats from database
            3. found ip addres of current computer
        """

    def run(self):
        """Main server loop that handles initial connections"""
        self.socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

        while True:
            try:
                conn, addr = self.socket.accept()
                print(f"New connection from {addr}")

                # Start a new authentication handler thread
                auth_thread = threading.Thread(
                    target=self.handle_connection,
                    args=(conn, addr)
                )
                auth_thread.daemon = True
                auth_thread.start()

            except Exception as e:
                print(f"Error accepting connection: {e}")

    def handle_connection(self, conn, addr):
        """Handles the lifetime of a client connection"""
        try:
            while True:  # Connection lifecycle loop
                # Wait for auth command
                auth_result = self.authenticate(conn, addr)

                if auth_result != 'SIGNIN_SUCCESS':
                    # We still want to wait for authentication even if exists or wrong credentials
                    print(f'[DEBUG] - [SERVER/AUTH]: {auth_result}, waiting for new auth request')
                    continue
                elif auth_result is None:
                    conn.close()
                    return

                username = auth_result

                # Start client session
                try:
                    self.handle_client_session(conn, addr, username)
                except ConnectionResetError:
                    print(f"Client {username} disconnected abruptly")
                except Exception as e:
                    print(f"Error in client session for {username}: {e}")

                # Session ended (logout) - loop back to wait for new auth
                print(f"User {username} logged out")

        except Exception as e:
            print(f"Connection handler error for {addr}: {e}")
        finally:
            conn.close()

    def handle_client_session(self, conn, addr, username: str):
        """
        Handle individual client connection
        TODO: Maybe break to ENUM after project works, function too unreadable
        """
        current_channel = None

        while True:
            try:
                data = conn.recv(1024).decode(ENCODING)
                if not data:
                    break

                print(f'[DEBUG] - [SERVER/HANDLE_CLIENT]: Received data: {data}')

                command = data.split()
                if not command:
                    continue

                action = command[0]

                if action == "create":

                    if len(command) < 2:
                        self.send_message(conn, "INVALID_CHANNEL_FORMAT")
                        continue

                    response = self.handle_create_channel(command[1], conn, addr)
                    self.send_message(conn, response)
                elif action == 'logout':
                    # Clean logout - allows re-authentication
                    if current_channel:
                        self.handle_leave_channel(current_channel, username)
                    self.send_message(conn, 'LOGOUT_SUCCESS')
                    break
                elif action == "join":

                    if len(command) < 2:
                        self.send_message(conn, "INVALID_CHANNEL_FORMAT")
                        continue

                    response = self.handle_join_channel(command[1], username, conn, addr)
                    if response == "JOIN_SUCCESS":
                        current_channel = command[1]
                    self.send_message(conn, response)

                elif action == "leave":
                    if current_channel:
                        self.handle_leave_channel(current_channel, username)
                        current_channel = None
                        self.send_message(conn, "LEAVE_SUCCESS")
                    else:
                        self.send_message(conn, "NOT_IN_CHANNEL")

                elif action == "/quit":
                    self.send_message(conn, "QUIT_SUCCESS")
                    break

                else:  # Treat as message if in channel
                    if current_channel:
                        channel = self.channels[current_channel]
                        channel.broadcast(data, username, self)
                    else:
                        self.send_message(conn, "NOT_IN_CHANNEL")

            except Exception as e:
                print(f"Error handling client {username} at {addr}: {e}")
                break

        # Cleanup on disconnect
        if current_channel:
            self.handle_leave_channel(current_channel, username)
        print(f"Client disconnected: {username} at {addr}")

    def get_channels(self) -> Dict:
        return self.channels

    def broadcast_channel_update(self, action: str, channel_name: str):
        update = {
            "type": "channel_update",
            "action": action,
            "channel": channel_name
        }

        # Broadcast to all users in all channels
        for channel in self.channels.values():
            for user in channel.users:
                try:
                    self.send_message(user['conn'], update)
                except Exception as e:
                    print(f"Failed to send update to {user['username']}: {e}")

    def handle_create_channel(self, channel_name: str, conn, addr) -> str:
        if channel_name in self.channels:
            return "CHANNEL_EXISTS"

        self.channels[channel_name] = Channel(channel_name)
        self.broadcast_channel_update("create", channel_name)
        return "CHANNEL_CREATED_SUCCESS"

    def handle_join_channel(self, channel_name: str, username: str, conn, addr) -> str:
        # No channel
        if channel_name not in self.channels:
            return "NO_SUCH_CHANNEL"

        # Full
        channel = self.channels[channel_name]
        if len(channel.users) >= MAX_USERS_PER_CHANNEL:
            return "CHANNEL_FULL"

        if channel.add_user(conn, addr, username):
            # Notify other users in the channel
            channel.broadcast(f"{username} has joined the channel", "SERVER", self)
            return "JOIN_SUCCESS"
        return "JOIN_FAILED"

    def handle_leave_channel(self, channel_name: str, username: str) -> str:
        if channel_name not in self.channels:
            return "NO_SUCH_CHANNEL"

        channel = self.channels[channel_name]
        channel.remove_user(username)
        channel.broadcast(f"{username} has left the channel", "SERVER", self)

        # If channel is empty remove it.
        if not channel.users:
            del self.channels[channel_name]
            self.broadcast_channel_update("delete", channel_name)

        return "LEAVE_SUCCESS"

    def authenticate(self, conn, addr) -> Optional[str]:
        """Handle user authentication"""
        try:
            data = conn.recv(1024).decode(ENCODING).split()
            if not data or len(data) != 3:
                self.send_message(conn, "INVALID_FORMAT")
                return None

            print(f'[DEBUG] - [SERVER/AUTH] Received data: {data}')

            action, username, password = data

            with open(USERNAMES_FILE, 'r') as f:
                users = json.load(f)

            if action == "signin":
                if username in users and users[username] == password:
                    self.send_message(conn, "SIGNIN_SUCCESS")
                    return username

                # Failed to sign in
                self.send_message(conn, "WRONG_PASSWORD")
                return "WRONG_PASSWORD"

            elif action == "signup":
                if username in users:
                    self.send_message(conn, "USER_EXISTS")
                    return "USER_EXISTS"

                # Create new user
                users[username] = password
                with open(USERNAMES_FILE, 'w') as f:
                    json.dump(users, f)
                self.send_message(conn, "SIGNUP_SUCCESS")
                return username

        except Exception as e:
            print(f"Authentication error for {addr}: {e}")
            self.send_message(conn, "AUTH_ERROR")
            return None

    def send_message(self, conn, message: str):
        """Send message to client with consistent encoding"""
        try:
            conn.send(message.encode(ENCODING))
        except Exception as e:
            print(f"Error sending message: {e}")


if __name__ == "__main__":
    # Use localhost for development
    host = 'localhost'
    port = 6000

    server = Server(port, host)
    server.run()
