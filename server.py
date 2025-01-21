import sys
import socket
import threading

port = 8000
ip_server = socket.gethostbyname("LAPTOP-H7OBH5BP") # איך
print(ip_server)
address = (ip_server, port)