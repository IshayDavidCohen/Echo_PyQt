import socket

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)
print(hostname, ip_address)

database = {
    "users": {
        "nadav": 1234
    },

    "chats": {
        "genral": {
            "nadav": "hello",
            "bot1": "bi"
        }
    }
}


print([i for i in database["chats"].keys() ])
print(list(database.keys()))