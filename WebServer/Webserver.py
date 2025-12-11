from socket import *
import threading

def serve(connectionSocket):    
    try:         
        message = connectionSocket.recv(1024).decode()
        # GET /HelloWorld.html HTTP/1.1
        filename = message.split()[1]  
        f = open(filename[1:])
        outputdata = f.read()
        #Send one HTTP header line into socket         
        header = 'HTTP/1.1 200 OK\nConnection: close\n' + \
                 f'Content-Length: {len(outputdata)}\n' + \
                 'Content-Type: text/html\n\n'
        connectionSocket.send(header.encode())
        #Send the content of the requested file to the client
        for i in range(0, len(outputdata)):
            connectionSocket.send(outputdata[i].encode())
    except IOError:
        #Send response message for file not found
        err_response = 'HTTP/1.1 404 Not Found\n\n<html><head></head><body><h1>404 Not Found</h1></body></html>\n'
        connectionSocket.send(err_response.encode())
    finally:
        f.close()
        connectionSocket.close()

def main():
    serverPort = 6789
    serverSocket = socket(AF_INET, SOCK_STREAM) 
    serverSocket.bind(('', serverPort))
    serverSocket.listen(5)
    while True:
        #Establish the connection    
        print('Ready to serve...') 
        connectionSocket, addr = serverSocket.accept()
        threading.Thread(target=serve, args=(connectionSocket,)).start()

if __name__ == '__main__':
    main()
