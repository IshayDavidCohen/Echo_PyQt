import sys
import threading
import argparse
from PyQt5 import QtWidgets

# App dependencies
from src.server.Server import Server
from src.client.Client import Client


class Orchestrator:
    def __init__(self, client_count: int, port: int, host: str):
        self.port = port
        self.host = host
        self.client_count = client_count

        self.server = None
        self.clients = []

        self.run()

    def run(self):
        server_thread = threading.Thread(target=self.start_server)
        server_thread.demon = True
        server_thread.start()

        app = QtWidgets.QApplication(sys.argv)

        for i in range(self.client_count):
            client = Client(port=self.port, host='localhost')
            client.show()
            self.clients.append(client)

        try:
            sys.exit(app.exec_())
        finally:
            if self.server:
                self.server.shutdown()

    def start_server(self):
        self.server = Server(6000, 'localhost')
        self.server.run()


def parse_args():
    parser = argparse.ArgumentParser(description='Orchestrator for Chat Application')
    parser.add_argument('--clients', type=int, default=3, help='Number of clients to run')
    parser.add_argument('--port', type=int, default=6000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='localhost', help='Host/IP to run the server on')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    instance = Orchestrator(client_count=args.clients, port=args.port, host=args.host)
    sys.exit()
