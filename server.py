import sys
import json
import socket
import threading


"""
1. save messages in server and update databse ince in while or in the end
2. set on format of message in all code and update client to it also
3. clean code...
4. comments
"""

class Server():
    def __init__(self, port, host):
        self.port = port
        self.host =  host
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        
        self.chats = self.init_chats()  # Format: {"chat name": [{"conn": conn, "addr": addr, "username": username}]}
        
        
    def init_chats(self) -> dict:
        with open('database.json', 'r') as file:
            database = json.load(file)
            
            return {key:[] for key in database["chats"].keys()}
        
        
    def remove_user_from_chat(self, addr, chat):
        if not chat:
            return
        
        for i in range(len(self.chats[chat])):
            user = self.chats[chat][i]
            if user["addr"] == addr:
                username = user["username"]
                self.chats[chat].pop(i)
                break
            
        # send user disconnected from chat
        message = {"type": "user leave", "message": f"{username} DISCONNECT FROM CHAT"}
        self.broadcast(username, message, chat)
    
        
    def recev(self, conn, addr, chat=None):
        try:
            data_string = conn.recv(2048).decode('utf-8')
            if not data_string: raise "Error: data not recev"
            
            data = json.loads(data_string)
            return data
        except:
            print(f"[connection lost {addr}]")
            self.remove_user_from_chat(addr, chat)

    
    def send(self, conn, addr, status, data, chat=None):
        # status: success, failed
        try:
            messeage = json.dumps({"status": status, "data": data})
            conn.send(messeage.encode('utf-8'))
        except: 
            print(f"[connection lost {addr}]")
            self.remove_user_from_chat(addr, chat)


    def checkValidUser(self, username, password):
        with open('./database.json', 'r') as file:
            database = json.load(file)
            
            # Reuturn if username and password in users database.
            if username in database["users"].keys():
                return database["users"][username] == password
            
        return False
    
    
    def authentication(self, conn, addr):
        success = False
        
        while not success:
            data = self.recev(conn, addr)["data"]
            username, password = data['username'], data["password"]
            
            if self.checkValidUser(username, password):
                self.send(conn ,addr, "success", {"chats": list(self.chats.keys())})
                success = True
            else:
                self.send(conn, addr, "failed", {})
                
        return username
    
    
    def uploadMessageToDataBase(self, name, message, chat):
        with open('database.json', 'r') as file:
            database = json.load(file)
        
        database["chats"][chat][name] = message
        
        with open("database.json", "w") as file:
            json.dump(data, jsonFile)
    
    
    def broadcast(self, name, message, chat):
        for user in self.chats[chat]:
            if user["username"] != name:
                self.send(user["conn"], user["addr"], "success", {"type": "message", "name": name, "message": message}, chat)
    
    
    def handleUser(self, conn, addr, chat, username):
        # Send messge to chat that new user join
        message = {"type": "new user", "message": f"{username} CONNECT TO CHAT"}
        self.broadcast(username, message, chat)
        
        
        while True:
            name, message = self.recev(conn, addr).items()
            self.uploadMessageToDataBase(name, message, chat)
            self.broadcast(name, message, chat)         


    def main(self):
        self.socket.listen()
        print(f"[server start to listen...]")

        while True:
            conn, addr = self.socket.accept()
            print(f"[NEW CONNECTION {addr}]")
            
            username = self.authentication(conn, addr)
            
            chat = self.recev(conn, addr)["data"]["chat"]
            
            self.chats[chat].append({"conn":conn, "addr":addr, "username": username})
            
            thread = threading.Thread(target=self.handleUser, args=(conn, addr, chat, username))
            thread.start()



if __name__ == "__main__":
    server = Server(8000, '10.0.0.12') # If run in other computer please change ip (cmd: "ipconfig" take result from ipv4)
    server.main()