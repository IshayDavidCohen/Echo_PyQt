import socket
import threading
import json
from GUI import MainWindow
from PyQt5.QtWidgets import QApplication
import sys

"""
1. update all message to same format as in serve
2. Find a way to pass text from input to Client
3. use better ui that works
4. clean code and comments
"""

class Client():
    def __init__(self, port, server_ip):
        self.port = port
        self.server_ip = server_ip

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((server_ip, port))
        
        self.username = None
        
        self.app = QApplication(sys.argv)
        self.screen = self.app.primaryScreen()
        self.window = MainWindow(self.send_message)
     
         
    def recev(self) -> dict:
        try:
            data_string = self.socket.recv(2048).decode('utf-8')
            if not data_string: raise 
            
            data = json.loads(data_string)
            return data
        except:
            print(f"[connection lost...")

    
    def send(self, status, data):
        # status: success, failed
        try:
            messeage = json.dumps({"status": status, "data": data})
            self.socket.send(messeage.encode('utf-8'))
        except : 
            print(f"[connection lost...]")


    def authentication(self):
        print("Please sign in:")
        signin = False
        
        while not signin:
            username = input("Enter user name: ")
            password = input("Enter your passsword: ")
    
            self.send("success", {"username": username, "password": password})
            
            data = self.recev()
            
            if data["status"] == "success":
                print("sign in success")
                signin = True
            else:
                print("signin failed. Please try again")
                
        return username, data["data"]["chats"]
    
    
    def pick_chat(self, chats): 
        # Create string with chats options
        options = ""
        for i, chat_name in enumerate(chats): options += f"{i}: {chat_name}\n"
                
        # Get chat num from user
        print("\nPleas pick a chat:")
        print(options)
        num_chat = int(input("Enter chat number: "))
        
        # Send the chat user pick to server and return it
        self.send("success", {"chat": chats[num_chat]})
        
        return chats[num_chat]


    def listen_to_message(self):
        while True:
            data = self.recev()["data"]
            if data["type"] == "message":
                self.window.add_message(f"{data['name']}: {data['message']}", "black")


    def send_message(self, text):
        self.send("success", {"type": "message", "name": self.username, "message": text})


    def main(self):
        print("Welcome to our live chat!")

        self.username, chats = self.authentication()
        
        chat_name = self.pick_chat(chats)
        print("Conncet to chat: ", chat_name)
        
        # Init GUI   
        self.window.show()
        sys.exit(self.app.exec_())
        
        thread = threading.Thread(target=self.listen_to_message, args=())
        thread.start()
    
    
    
    
    
if __name__ == "__main__":
    client = Client(8000, '10.0.0.12') # If run in other computer please change ip (cmd: "ipconfig" take result from ipv4)
    client.main()




