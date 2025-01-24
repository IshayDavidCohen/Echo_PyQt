import socket
import threading
import json
from window import MainWindow
from PyQt5.QtWidgets import QApplication
import sys

"""
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
        self.window = MainWindow(self)
     
         
    def recev(self):
        try:
            data_string = self.socket.recv(2048).decode('utf-8')
            if not data_string: raise 
            
            data = json.loads(data_string)
            print("recev", data)
            return data["status"], data["type"], data["data"]
        except:
            print(f"[connection lost...]")

    
    def send(self, status, type_, data):
        try:
            messeage = json.dumps({"status": status, "type":type_, "data": data})
            self.socket.send(messeage.encode('utf-8'))
        except : 
            print(f"[connection lost...]")


    def authentication(self):
        print("Please sign in:")
        signin = False
        
        while not signin:
            username = input("Enter user name: ")
            password = input("Enter your passsword: ")
    
            self.send("success", "auth", {"username": username, "password": password})
            
            status, type_, data = self.recev()
            
            if status == "success":
                print("sign in success")
                signin = True
            else:
                print("signin failed. Please try again")
                
        return username, data["chats"]
    
    
    def pick_chat(self, chats): 
        # Create string with chats options
        options = ""
        for i, chat_name in enumerate(chats): options += f"{i}: {chat_name}\n"
                
        # Get chat num from user
        print("\nPleas pick a chat:")
        print(options)
        num_chat = int(input("Enter chat number: "))
        
        # Send the chat user pick to server and return it
        self.send("success", "pick chat", {"chat": chats[num_chat]})
        
        return chats[num_chat]


    def get_chat_history(self):
        status, type_, data = self.recev()
        print(data)
        
        for i in range(len(data)):
            message, name = data[i][1], data[i][0]
            self.window.display_message(message, name)


    def listen_to_message(self):
        while True:
            status, type_, data = self.recev()
            if type_ == "message":
                self.window.display_message(data['message'], data['name'])


    def send_message_to_server(self, text):
        self.send("success", "message", {"name": self.username, "message": text})


    def main(self):
        print("Welcome to our live chat!")

        # Auth
        self.username, chats = self.authentication()
        
        # Select chat
        chat_name = self.pick_chat(chats)
        print("Conncet to chat: ", chat_name)
              
        # Handle chat history
        self.get_chat_history()

        # Start thread of listening to messages
        thread = threading.Thread(target=self.listen_to_message, args=())
        thread.start()
        
        # Init GUI   
        self.window.set_chat_name(chat_name)
        self.window.show()
        sys.exit(self.app.exec_())
    
    
    
if __name__ == "__main__":
    # If run in other computer please change ip (cmd: "ipconfig" take result from ipv4)
    client = Client(8000, '10.0.0.12') 
    client.main()




