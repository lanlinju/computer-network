from socket import *
import base64
import mimetypes
import ssl
import config

subject = "I love computer networks!"
msg = "I love computer networks!!!"
endmsg = "\r\n.\r\n"

# Choose a mail server (e.g. Google mail server) and call it mailserver 
mailserver = "smtp.qq.com"
port = 587  # Gmail使用587端口（STARTTLS）或465端口（SSL）

# Sender and receiver email addresses
fromaddr = "laurie233@foxmail.com"  
toaddr = "troyenight@163.com"

# Auth information (Encode with base64)
username = base64.b64encode(fromaddr.encode()).decode()
password = base64.b64encode(config.PASSWORD_QQ.encode()).decode()  # 替换为Gmail应用专用密码

def recvline(sock):
    data = sock.recv(1024)
    if not data:
        return ''
    return data.decode()

def send_and_recv(sock, msg, expect_code=None):
    """Send msg (string, already with CRLF) and return server reply."""
    print("C: " + msg.strip().replace("\r\n", "\\r\\n"))
    sock.sendall(msg.encode())
    reply = recvline(sock)
    print("S: " + reply.strip().replace("\r\n", "\\r\\n"))
    if expect_code and not reply.startswith(expect_code):
        print(f"Warning: expected reply starting with {expect_code} but got: {reply.strip()}")
    return reply

# 读取图片文件并编码为base64
def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return encoded_string
    except FileNotFoundError:
        print(f"警告: 图片文件 {image_path} 未找到，将发送不带图片的邮件")
        return None

# 图片路径
image_path = "image.jpg"  # 修改为您的图片路径
image_data = encode_image(image_path)

# 自动获得 MIME 类型
mime_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream" if image_data else ""

# 生成唯一的边界字符串
boundary = "----=_NextPart_" + base64.b64encode(str(id(msg)).encode()).decode()[:20]

# Create socket called clientSocket and establish a TCP connection with mailserver
print(f"正在连接到 {mailserver}:{port}...")
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((mailserver, port))

recv = recvline(clientSocket)
print("S:", recv)
if recv[:3] != '220':
    print("220 reply not received from server.")

# 发送EHLO命令（不是HELO，因为我们需要ESMTP扩展）
ehloCommand = 'EHLO Alice\r\n'
send_and_recv(clientSocket, ehloCommand, '250')

# 发送STARTTLS命令开始TLS加密
# print("开始TLS加密...")
send_and_recv(clientSocket, 'STARTTLS\r\n', '220')

# 包装socket为SSL连接
context = ssl.create_default_context()
clientSocket = context.wrap_socket(clientSocket, server_hostname=mailserver)
# print("TLS连接已建立")

# TLS连接建立后需要重新发送EHLO
send_and_recv(clientSocket, ehloCommand, '250')

# Send AUTH LOGIN command
send_and_recv(clientSocket, 'AUTH LOGIN\r\n', '334')

send_and_recv(clientSocket, username + '\r\n', '334')
send_and_recv(clientSocket, password + '\r\n', '235')

# Send MAIL FROM command and print server response.
send_and_recv(clientSocket, f'MAIL FROM: <{fromaddr}>\r\n', '250')

# Send RCPT TO command and print server response.
send_and_recv(clientSocket, f'RCPT TO: <{toaddr}>\r\n', '250')

# Send DATA command and print server response.
send_and_recv(clientSocket, 'DATA\r\n', '354')

# 构建MIME格式的邮件内容
message = f'From: <{fromaddr}>\r\n'
message += f'To: <{toaddr}>\r\n'
message += f'Subject: {subject}\r\n'
message += 'MIME-Version: 1.0\r\n'

if image_data:
    message += f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n'
    message += '\r\n'
    
    # 文本部分
    message += f'--{boundary}\r\n'
    message += 'Content-Type: text/plain; charset="utf-8"\r\n'
    message += 'Content-Transfer-Encoding: 7bit\r\n'
    message += '\r\n'
    message += msg + '\r\n'
    message += '\r\n'
    
    # 图片部分
    message += f'--{boundary}\r\n'
    message += f'Content-Type: {mime_type}; name="{image_path}"\r\n'
    message += 'Content-Transfer-Encoding: base64\r\n'
    message += f'Content-Disposition: attachment; filename="{image_path}"\r\n'
    message += '\r\n'
else:
    # 如果没有图片，发送纯文本邮件
    message += 'Content-Type: text/plain; charset="utf-8"\r\n'
    message += '\r\n'
    message += msg + '\r\n'

# 发送邮件头部
clientSocket.sendall(message.encode())

# 如果有图片，分块发送base64编码的图片数据
if image_data:
    chunk_size = 1024
    for i in range(0, len(image_data), chunk_size):
        chunk = image_data[i:i+chunk_size] + '\r\n'
        clientSocket.sendall(chunk.encode())
    
    # 发送结束边界
    message_end = f'\r\n--{boundary}--\r\n'
    clientSocket.sendall(message_end.encode())

# Message ends with a single period.
send_and_recv(clientSocket, endmsg, '250')

# Send QUIT command and get server response.
send_and_recv(clientSocket, 'QUIT\r\n', '221')

# Close the socket
clientSocket.close()

print("邮件发送完成！")