#!/usr/bin/env python3
import socket
import sys

def http_client(server_host, server_port, filename):
    # Create socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to server
        client_socket.connect((server_host, server_port))
        print(f"Connected to {server_host}:{server_port}")
        
        # Send HTTP GET request
        request = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}\r\n\r\n"
        client_socket.send(request.encode())
        print(f"Sent request: GET /{filename} HTTP/1.1")
        
        # Receive response
        response = b""
        while True:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            response += chunk
        
        # Print response
        print("\n" + "="*50)
        print("Server Response:")
        print("="*50)
        print(response.decode())
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python client.py server_host server_port filename")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    filename = sys.argv[3]
    
    http_client(server_host, server_port, filename)