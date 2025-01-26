from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication
import socket
import threading
import json
from window import MainWindow
import sys

class Client(QObject):
    # Signal to emit messages to the GUI
    message_received = pyqtSignal(str, str, str)
    
    def __init__(self, port, server_ip):
        super(Client, self).__init__()
        self.port = port
        self.server_ip = server_ip

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create new socket
        self.socket.connect((server_ip, port))  # Connect to server
        
        self.username = None
        
        # GUI settings
        self.app = QApplication(sys.argv)
        self.screen = self.app.primaryScreen()
        self.window = MainWindow(self)  # Create mainWindow object
     
        # Connect the signal to the window's display_message method
        self.message_received.connect(self.window.display_message)
         
         
    def recev(self):
        # recev data from server and error handling
        try:
            data_string = self.socket.recv(2048).decode('utf-8')
            if not data_string: raise Exception("Disconnected") 
            
            data = json.loads(data_string) # convert data to dict
            return data["status"], data["type"], data["data"] # return status, type and data
        
        except Exception as e:
            print(f"[Connection lost: {e}]")

    
    def send(self, status, type_, data):
        # Send data to server
        try:
            messeage = json.dumps({"status": status, "type":type_, "data": data})
            self.socket.send(messeage.encode('utf-8'))
            
        except Exception as e:
            print(f"[Connection lost: {e}]")


    def authentication(self):
        print("Please sign in:")
        signin = False # success to signin
        
        while not signin:
            # get user name anbd password input from user
            username = input("    Enter user name: ")
            password = input("    Enter your passsword: ")
    
            # send username and password to server
            self.send("success", "auth", {"username": username, "password": password})
            
            status, type_, data = self.recev()  # recev a answer from server
            
            # chack status
            if status == "success":
                print("\nsign in success\n")
                signin = True  # stop loop
            else:
                print("\nsignin failed. Please try again:")
                
        return username, data["chats"]  # return username and list of chat options
    
    
    def pick_chat(self, chats): 
        # Create string with chats options for print it
        options = ""
        for i, chat_name in enumerate(chats): options += f"{i}: {chat_name}\n"
                
        # Get chat num from user
        print("\nPleas pick a chat:")
        print(options)
        num_chat = int(input("Enter chat number: "))
        
        # Send the chat that the user pick to server 
        self.send("success", "pick chat", {"chat": chats[num_chat]})
        
        return chats[num_chat]  # Return the chat user pick


    def get_chat_history(self):
        status, type_, data = self.recev()  # recev data with chat history
        
        for i in range(len(data)):
            message, name = data[i][1], data[i][0]
            # type is who wrote the message
            type_ = "me" if name == self.username else "other"
            
            # Display the message to window using message_recieved signal
            self.message_received.emit(type_, message, name)


    def listen_to_message(self):
        while True:
            status, type_, data = self.recev()  # get new message
            
            # Display the message to window using message_recieved signal
            self.message_received.emit(type_, data['message'], data['name'])
            

    def send_message_to_server(self, text):
        # S ens user new message to server
        self.send("success", "message", {"name": self.username, "message": text})


    def main(self):
        print("Welcome to our live chat!")

        # Run authentication
        self.username, chats = self.authentication()
        
        # Select chat
        chat_name = self.pick_chat(chats)
        print("Conncet to chat: ", chat_name)
              
        # Handle get chat history
        self.get_chat_history()

        # Start a thread for listening to new messages
        self.listen_thread = QThread()
        self.listen_thread.run = self.listen_to_message
        self.listen_thread.start()
        
        # Show GUI   
        self.window.set_window_name(chat_name)
        self.window.show()
        sys.exit(self.app.exec_())
    
    
    
if __name__ == "__main__":
    # If run in other computer please change ip (cmd: "ipconfig" take result from ipv4)
    client = Client(8000, '10.0.0.12') 
    client.main()




