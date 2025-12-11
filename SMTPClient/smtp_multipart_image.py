from socket import *
import base64
import mimetypes
import config

subject = "I love computer networks!"
msg = "I love computer networks!!!"
endmsg = "\r\n.\r\n"

# Choose a mail server (e.g. Google mail server) and call it mailserver 
mailserver = "smtp.163.com"

# Sender and receiver email addresses
fromaddr = "troyenight@163.com"
toaddr = "laurie233@foxmail.com"

# Auth information (Encode with base64)
username = base64.b64encode(fromaddr.encode()).decode()
password = base64.b64encode(config.PASSWORD_163.encode()).decode()

# 读取图片文件并编码为base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string

# 图片路径 - 请确保这个图片文件存在
image_path = "image.jpg"  # 修改为您的图片路径
image_data = encode_image(image_path)

# 自动获得 MIME 类型 (image/png, image/jpeg ...)
mime_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream"

# 生成唯一的边界字符串
boundary = "----=_NextPart_" + base64.b64encode(str(id(msg)).encode()).decode()[:20]

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

# 构建MIME格式的邮件内容
message = f'From: <{fromaddr}>\r\n'
message += f'To: <{toaddr}>\r\n'
message += f'Subject: {subject}\r\n'
message += 'MIME-Version: 1.0\r\n'
message += f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n'
message += '\r\n'

# 文本部分
message += f'--{boundary}\r\n'
message += 'Content-Type: text/html; charset="utf-8"\r\n'
message += 'Content-Transfer-Encoding: 7bit\r\n'
message += '\r\n'
message += msg + '\r\n'
message += '这是一个包含图片的邮件：\r\n'
message += '<img src="cid:image1" alt="测试图片" style="max-width: 300px;">\r\n'
message += '\r\n'

# 图片部分
message += f'--{boundary}\r\n'
message += f'Content-Type: {mime_type}; name="{image_path}"\r\n'
message += 'Content-Transfer-Encoding: base64\r\n'
message += f'Content-Disposition: inline; filename="{image_path}"\r\n'
# message += f'Content-Disposition: attachment; filename="{image_path}"\r\n'
message += 'Content-ID: <image1>\r\n'  # 这里的Content-ID必须与HTML中的cid一致
message += '\r\n'

# 发送邮件头部
clientSocket.sendall(message.encode())

# 分块发送base64编码的图片数据（避免单次发送数据过大）
chunk_size = 1024
for i in range(0, len(image_data), chunk_size):
    chunk = image_data[i:i+chunk_size] + '\r\n'
    clientSocket.sendall(chunk.encode())

# 发送结束边界
message_end = f'\r\n--{boundary}--\r\n'
clientSocket.sendall(message_end.encode())

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

print("邮件发送完成！")