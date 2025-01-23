import sys
import json
import socket
import threading

from typing import Dict, List, Optional

# App Dependencies
from src.utility.Settings import ENCODING, MAX_USERS_PER_CHANNEL, USERNAMES_FILE


class Server:
    def __init__(self, port: int, host: str):
        self.port = port
        self.host = host
        self.users: List[str] = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.auth = False

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
                auth = self.authenticate(conn, addr)

                auth_message = auth.get('auth_message')
                auth_result = auth.get('auth_result')

                print(f'[DEBUG] - [SERVER/AUTH]: {auth_result}, {auth_message}')

                if auth_message == 'SIGNIN_SUCCESS':
                    self.auth = True

                username = auth_result

                # Start client session
                if self.auth:
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

                if action == 'logout':
                    # Clean logout - allows re-authentication
                    self.users.remove(username)
                    self.auth = False
                    self.send_message(conn, 'LOGOUT_SUCCESS')
                    # TODO: Need to broadcast new users list to everyone
                    break
                elif action == 'get_users':
                    users = json.dumps({'action': action, 'data': {'users': self.users}})
                    self.send_message(conn, users)

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

    def broadcast_channel_update(self, action: str, channel_name: str):
        # Needs to be reworked
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

    def broadcast_message(self, message: str):
        # Needs to be reworked
        update = {
            "type": "chat_message",
            "message": message
        }


    def authenticate(self, conn, addr) -> Optional[Dict]:
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
                    self.users.append(username)
                    return {'auth_result': username, 'auth_message': 'SIGNIN_SUCCESS'}

                # Failed to sign in
                self.send_message(conn, "WRONG_PASSWORD")
                return {'auth_result': None, 'auth_message': 'WRONG_PASSWORD'}

            elif action == "signup":
                if username in users:
                    self.send_message(conn, "USER_EXISTS")
                    return {'auth_result': None, 'auth_message': 'USER_EXISTS'}

                # Create new user
                users[username] = password
                with open(USERNAMES_FILE, 'w') as f:
                    json.dump(users, f)
                self.send_message(conn, "SIGNUP_SUCCESS")
                return {'auth_result': username, 'auth_message': 'SIGNUP_SUCCESS'}

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
