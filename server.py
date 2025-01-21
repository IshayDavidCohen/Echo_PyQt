import sys
import json
import socket
import threading

class Server():
    def __init__(self, port, host):
        self.port = port
        self.host =  host
        self.address = (ip_server, port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.bind(address)
        
        self.chats = {} # need to create, {"chat name": [{"conn": conn, "addr": addr, "username": username}]}
        
        """
        remain: 
            1. error handling to client stop connection -> delete client from chats
            2. start chats from database
            3. found ip addres of current computer
        """
        
    def recev(self, conn, addr):
        try:
            data_string = conn.recv(1024).decode('utf-8')
            data = json.loads(data_string)
            return data
        except e:
            print(f"[connection lost {addr}]")
    
    
    def send(self, conn, addr, status, data):
        # status: success, failed
        try:
            messeage = json.dumps({"status": status, "data": data})
            conn.send(messeage.encode('utf-8'))
        except: 
            print(f"[connection lost {addr}]")


    def checkValidUser(self, username, password):
        with open('database.json', 'r') as file:
            database = json.load(file)
            
            # Reuturn if username and password in users database.
            if username in  database["users"].keys():
                return database["users"][username] == password
    
    
    def authentication(self, conn, addr):
        success = False
        
        while not success:
            data = self.recev(conn, addr)
            username, password = data['username'], data["password"]
            
            if self.checkValiduser(username, password):
                self.send(conn ,addr, "success", {"chats": self.chats_names})
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
                self.send(user["conn"], user["addr"], "success", data={"name": name, "message": message})
    
    
    def handleUser(self, conn, addr, chat):
        while True:
            name, message = self.recev(conn, addr).items()
            self.uploadMessageToDataBase(name, message, chat)
            self.broadcast(name, message, chat)
                


    def main(self):
        socket.listen()
        print(f"[server start to listen...]")

        while True:
            conn, addr = socket.accept()
            print(f"[NEW CONNECTION {addr}]")
            
            username = self.authentication(conn, addr)
            
            chat = self.recev(conn, addr)
            
            self.chats[chat].append({"conn":conn, "addr":addr, "username:": username})
            
            thread = threading.Thread(target=self.handleUser, args=(conn, addr, chat))
            thread.start()



if __name__ == "__main__":
    server = Server(8000, socket.gethostbyname("LAPTOP-H7OBH5BP"))
    server.main()