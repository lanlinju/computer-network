
# 220 hamburger. edu
# HELO crepes . fr
# 250 He llo crep es. fr, pleased to meet you
# MAIL FROM: <alice@crepes.fr>
# 250 alice@crepes.fr ... Sender ok
# RCPT TO: <bob@hamburger.edu>
# 250 bob@hamburger.edu ... Recipient ok
# DATA
# 354 Enter mail, end with"." on a line by i tself
# Do you like ketchup?
# How about pickles?
# .
# 250 Message accepted for delivery
# QUIT
# 221 hamburger.edu closing connection 

# From: alice@crepes.fr
# To: bob@hamburger.edu
# Subject: Searching for t h e me an i n g of life . 
# \r\n

# troyenight@163.com
# LIN1362375397531

from socket import *
import base64
import config

subject = "I love computer networks!"
contenttype = "text/plain"
msg = "I love computer networks!!!"
endmsg = "\r\n.\r\n"
# Choose a mail server (e.g. Google mail server) and call it mailserver 
mailserver = "smtp.163.com"

# Sender and receiver email addresses
fromaddr = "troyenight@163.com"
toaddr = "lanlinju@outlook.com"

# Auth information (Encode with base64)
# 1. 登录163邮箱，进入"设置" → "POP3/SMTP/IMAP"， 开启"SMTP服务"
# 2. 获取授权码（不是邮箱密码）
username = base64.b64encode(fromaddr.encode()).decode()
password = base64.b64encode(config.PASSWORD_163.encode()).decode()

# Create socket called clientSocket and establish a TCP connection with mailserver
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((mailserver, 25))

recv = clientSocket.recv(1024).decode()
print(recv)
if recv[:3] != '220':
    print("220 reply not received from server.")

# Send HELO command and print server response.
heloCommand = 'HELO Alice\r\n'
clientSocket.send(heloCommand.encode())
recv1 = clientSocket.recv(1024).decode()
print(recv1)
if recv1[:3] != '250':
    print('250 reply not received from server.')

# Send AUTH LOGIN command
clientSocket.sendall('AUTH LOGIN\r\n'.encode())
recv = clientSocket.recv(1024).decode()
print(recv)
if recv[:3] != '334':
    print('334 reply not received from server.')

clientSocket.sendall((username + '\r\n').encode())
recv = clientSocket.recv(1024).decode()
print(recv)
if recv[:3] != '334':
    print('334 reply not received from server.')

clientSocket.sendall((password + '\r\n').encode())
recv = clientSocket.recv(1024).decode()
print(recv)
if recv[:3]!= '235':
    print('235 reply not received from server.')

# Send MAIL FROM command and print server response.
clientSocket.send(f'MAIL FROM: <{fromaddr}>\r\n'.encode())
recv = clientSocket.recv(1024).decode()
print(recv)
if recv[:3]!= '250':
    print('250 reply not received from server.')

# Send RCPT TO command and print server response.
clientSocket.send(f'RCPT TO: <{toaddr}>\r\n'.encode())
recv = clientSocket.recv(1024).decode()
print(recv)
if recv[:3]!= '250':
    print('250 reply not received from server.')

# Send DATA command and print server response.
clientSocket.send(b'DATA\r\n')
recv = clientSocket.recv(1024).decode()
print(recv)
if recv[:3]!= '354':
    print('354 reply not received from server.')

# Send message data.
message = f'From: <{fromaddr}>\r\n'
message += f'To: <{toaddr}>\r\n'
message += f'Subject: {subject}\r\n'
message += f'Content-Type: {contenttype}\r\n\r\n'
message += msg
clientSocket.sendall(message.encode())

# Message ends with a single period.
clientSocket.sendall(endmsg.encode())
recv = clientSocket.recv(1024).decode()
print(recv)
if recv[:3]!= '250':
    print('250 reply not received from server.')

# Send QUIT command and get server response.
clientSocket.send(b'QUIT\r\n')
recv = clientSocket.recv(1024).decode()
print(recv)

# Close the socket
clientSocket.close()
