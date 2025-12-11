from socket import *
import time
serverName = 'localhost'
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)
for i in range(1,11):
    send_time = time.time()
    message = f"{i} {send_time}"
    clientSocket.sendto(message.encode(), (serverName, serverPort))

clientSocket.close()    