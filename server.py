import sys
import json
import socket
import threading
from time import sleep

"""
1. save messages in server and update databse ince in while or in the end
3. clean code...
4. comments
"""

"""
Format of data move between server and client: 
    {
        "status": "success"/"fail", 
        "type": "user leave"/"new user"/"message"/"auth"/"pick chat"/"history", 
        "data": {
            "message": "some text...",
            "name': "user name",
            "chats": ["chat name 1", "name chat 2", ....]
            "username": "user name", 
            "password": "password"
            }
    }

"""


class Server():
    def __init__(self, port, host):
        self.port = port
        self.host =  host
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        
        self.chats_users = self.initialize_chats_users()  # Format: {"chat name": [{"conn": conn, "addr": addr, "username": username}]}
        self.chat_messages = self.initialize_chats_messages()  # Format: {"chat name": [(username, message), ...], ....}
        
        
    def initialize_chats_users(self):
        with open('database.json', 'r') as file:
            database = json.load(file)
            
            return {key:[] for key in database["chats"].keys()}
        
        
    def initialize_chats_messages(self):
        with open('database.json', 'r') as file:
            database = json.load(file)
            
            return database["chats"]
    
    
    def uploadMessageHistoryToDataBase(self):  
        def upload():
            while True: 
                sleep(30) 
                with open('database.json', 'r') as file:
                    database = json.load(file)
                
                database["chats"] = self.chat_messages
                
                with open("database.json", "w") as file:
                    json.dump(database, file)
                    
        thread = threading.Thread(target=upload)
        thread.start()
                
        
    def recev(self, conn, addr, chat=None):
        try:
            data_string = conn.recv(2048).decode('utf-8')
            if not data_string: raise "Error: data not recev"
            
            data = json.loads(data_string)
            
            return data["status"], data["type"], data["data"]
        except:
            print(f"[connection lost {addr}]")
            self.remove_user_from_chat(addr, chat)
            
            return "fail", None, None

    
    def send(self, conn, addr, status, type_, data, chat=None):
        try:
            messeage = json.dumps({"status": status, "type": type_, "data": data})
            conn.send(messeage.encode('utf-8'))
        except: 
            print(f"[connection lost {addr}]")
            self.remove_user_from_chat(addr, chat)
    
    
    def broadcast(self, name, type_, message, chat):
        for user in self.chats_users[chat]:
            if user["username"] != name:
                print(f" send --{name}:{message}-- to", user["username"])
                self.send(user["conn"], user["addr"], "success", type_, {"name": name, "message": message}, chat)
    
    
    def remove_user_from_chat(self, addr, chat):
        if not chat:
            return
        
        for i in range(len(self.chats_users[chat])):
            user = self.chats_users[chat][i]
            if user["addr"] == addr:
                username = user["username"]
                self.chats_users[chat].pop(i)
                break
            
        # send user disconnected from chat
        self.broadcast(username, "user leave", f"{username} DISCONNECT FROM CHAT", chat)
    

    def checkValidUser(self, username, password):
        with open('./database.json', 'r') as file:
            database = json.load(file)
            
            # Reuturn if username and password in users database.
            if username in database["users"].keys():
                return database["users"][username] == password
            
        return False
    
    
    def send_history(self, conn, addr, chat):
        self.send(conn, addr, "success", "history", self.chat_messages[chat] , chat)
    
    
    def authentication(self, conn, addr):
        success = False
        
        while not success:
            status, type_, data = self.recev(conn, addr)
            username, password = data['username'], data["password"]
            
            if self.checkValidUser(username, password):
                self.send(conn ,addr, "success", "pick chat" ,{"chats": list(self.chats_users.keys())})
                success = True
            else:
                self.send(conn, addr, "failed", "auth", {})
                
        return username
    
    
    def handleUser(self, conn, addr, chat, username):
        # Send messge to all users in chat that new user join
        self.broadcast(username, "new user", f"{username} CONNECT TO CHAT", chat)
        
        # Send message history to user
        self.send_history(conn, addr, chat)
        
        while True:
            status, type_, data = self.recev(conn, addr)
            if status == 'fail': break # client left
                
            name, message = data["name"], data["message"]
            self.chat_messages[chat].append([name, message])  
            self.broadcast(name, "message", message, chat)         


    def main(self):
        self.socket.listen()
        print(f"[server start to listen...]")
        
        # Upload history to database at regular intervals 
        self.uploadMessageHistoryToDataBase()

        while True:
            conn, addr = self.socket.accept()
            print(f"[NEW CONNECTION {addr}]")
            
            username = self.authentication(conn, addr)
            
            status, type_, data = self.recev(conn, addr)
            chat = data["chat"]
            
            self.chats_users[chat].append({"conn":conn, "addr":addr, "username": username})
            
            thread = threading.Thread(target=self.handleUser, args=(conn, addr, chat, username))
            thread.start()



if __name__ == "__main__":
    # If run in other computer please change ip (cmd: "ipconfig" take result from ipv4)
    server = Server(8000, '10.0.0.12')
    server.main()
