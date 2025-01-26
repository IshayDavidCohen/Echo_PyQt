import sys
import json
import socket
import threading
from time import sleep

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
        self.host =  host  # ip address
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create new socket 
        self.socket.bind((host, port))  # open the socket
        
        self.chats_users = self.initialize_chats_users()  # Format: {"chat name": [{"conn": conn, "addr": addr, "username": username}, ...], ...}
        self.chat_messages = self.initialize_chats_messages()  # Format: {"chat name": [[username, message], ...], ....}
        
        
    def initialize_chats_users(self):
        # open database.json file
        with open('database.json', 'r') as file:
            database = json.load(file)
            
            # return dict of key is "chat name" and value is empty list.
            return {key:[] for key in database["chats"].keys()}
        
        
    def initialize_chats_messages(self):
        # open database.json file
        with open('database.json', 'r') as file:
            database = json.load(file)
            
            return database["chats"]  # return chats dict from database
    
    
    def uploadMessageHistoryToDataBase(self):  
        # function that upload the data from self.chat_messages to database
        def upload():
            while True: 
                sleep(30)  # wait 30 seconds 
                # open database.json file for read
                with open('database.json', 'r') as file:
                    database = json.load(file)
                
                database["chats"] = self.chat_messages  # update chats in database
                
                # open atabase.json for puting the new data inside.
                with open("database.json", "w") as file:
                    json.dump(database, file)
                    
        # Make upload function run in the background while server is runing, using threads.
        thread = threading.Thread(target=upload)
        thread.start()
                
        
    def recev(self, conn, addr, chat=None):
        # recev data from client and error handling
        try:
            # recev data and check data is valid
            data_string = conn.recv(2048).decode('utf-8')
            if not data_string: raise "Error: data not recev"
            
            data = json.loads(data_string)  # convert data to dick
            
            return data["status"], data["type"], data["data"]  # return status, type and data
        except:
            # connection lost - remove user from chat
            print(f"[connection lost {addr}]")
            self.remove_user_from_chat(addr, chat)
            
            return "fail", None, None  # return status as fail

    
    def send(self, conn, addr, status, type_, data, chat=None):
        # Send data to client
        try:
            messeage = json.dumps({"status": status, "type": type_, "data": data})
            conn.send(messeage.encode('utf-8'))
        except: 
            print(f"[connection lost {addr}]")
            self.remove_user_from_chat(addr, chat)
    
    
    def broadcast(self, name, type_, message, chat):
        for user in self.chats_users[chat]:
            if user["username"] != name:
                self.send(user["conn"], user["addr"], "success", type_, {"name": name, "message": message}, chat)

    
    def remove_user_from_chat(self, addr, chat):
        # if user not connect to any chat stop the function.
        if not chat:
            return
        
        # Find user in the chat he connected to and remove him.
        for i in range(len(self.chats_users[chat])):
            user = self.chats_users[chat][i]
            if user["addr"] == addr:
                username = user["username"]  # save his username for after the loop.
                self.chats_users[chat].pop(i)
                break
            
        print(f"[{username} Left chat: {chat}]")    
           
        # send broadcast to all other users that username disconnected from chat. type - user leave
        self.broadcast(username, "user leave", f"{username} DISCONNECT FROM CHAT", chat)
    

    def checkValidUser(self, username, password):
        # chack username is not already connect
        for users in self.chats_users.values():
            for user in users:
                if user["username"] == username:
                    return False
        
        # Reuturn if username and password in users database and are correct.
        with open('./database.json', 'r') as file:
            database = json.load(file)
            
            if username in database["users"].keys():
                return database["users"][username] == password
            
        return False
    
    
    def send_history(self, conn, addr, chat):
        # send to user all chat history. data type - history, data a list.
        self.send(conn, addr, "success", "history", self.chat_messages[chat] , chat)
    
    
    def authentication(self, conn, addr):
        success = False # is success to login
        
        while not success:
            status, type_, data = self.recev(conn, addr) # recev data
            username, password = data['username'], data["password"]  
            
            # If username and password is valid send to user chats options ad recev chat name else let him try again.
            if self.checkValidUser(username, password):
                self.send(conn ,addr, "success", "pick chat" ,{"chats": list(self.chats_users.keys())}) # send success and chats options
                status, type_, data = self.recev(conn, addr)  # receve chat name that user choices to connect.
                chat = data["chat"]
                success = True  # Stop the loop
            else:
                self.send(conn, addr, "failed", "auth", {}) # send fails so he try again
                
        return username, chat # return username and chat that user pick to main
    
    
    def handleUser(self, conn, addr, chat, username):
        # Send messge to all users in chat that new user join
        self.broadcast(username, "new user", f"{username} CONNECT TO CHAT", chat)
        print(f"[{username} Joined chat: {chat}]")    
        
        # Send message history to user
        self.send_history(conn, addr, chat)
        
        while True:
            status, type_, data = self.recev(conn, addr, chat)  # wait for get message from user
            if status == 'fail': break # client left
                
            name, message = data["name"], data["message"]
            self.chat_messages[chat].append([name, message])  # Add new message to chat_messages
            self.broadcast(name, "message", message, chat)    # Broadcast the message to other users     


    def main(self):
        self.socket.listen() # start listen for connections 
        print(f"[server start to listen...]")
        
        # start therad to upload data of chats to database every repeated seconds 
        self.uploadMessageHistoryToDataBase()

        while True:
            conn, addr = self.socket.accept()  # wait for connection 
            print(f"[NEW CONNECTION {addr}]")
            
            # Run authentication to the user that connected
            username, chat = self.authentication(conn, addr)  
            
            # Add user to the chat he connected to
            self.chats_users[chat].append({"conn":conn, "addr":addr, "username": username})
            
            # Start a therad for handling user
            thread = threading.Thread(target=self.handleUser, args=(conn, addr, chat, username))
            thread.start()



if __name__ == "__main__":
    # If run in other computer please change ip (cmd: "ipconfig" take result from ipv4)
    server = Server(8000, '10.0.0.12')
    server.main()
