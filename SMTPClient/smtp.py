import socket
import ssl
import base64
import uuid
import mimetypes
import config

CRLF = "\r\n"

def recv(sock):
    r = sock.recv(4096).decode()
    print("S:", r.strip())
    return r

def send(sock, text):
    print("C:", text.strip())
    sock.sendall(text.encode())

# ------------- 你需要修改的配置 -------------
SMTP_SERVER = "smtp.qq.com"   # 你的邮箱 SMTP 服务器
SMTP_PORT   = 587                # 587 = STARTTLS
USERNAME    = "laurie233@foxmail.com"
PASSWORD    = config.PASSWORD_QQ  # ✅ Gmail 需要 App Password
MAIL_FROM   = USERNAME
RCPT_TO     = "troyenight@163.com"
SUBJECT     = "Multipart Email With Image"
IMAGE_PATH  = "image.jpg"         # 你要发送的本地图片
# -----------------------------------------

# 1. 读取图片并转成 base64
with open(IMAGE_PATH, "rb") as f:
    img_data = f.read()
img_b64 = base64.b64encode(img_data).decode()

# 自动获得 MIME 类型 (image/png, image/jpeg ...)
mime_type = mimetypes.guess_type(IMAGE_PATH)[0] or "application/octet-stream"

# 2. 生成 boundary
boundary = "BOUNDARY_" + uuid.uuid4().hex

# 3. 组装邮件内容
body_text = "Hello!\nThis email contains an image attachment sent using raw sockets."

mime_message = [
    f"From: {MAIL_FROM}",
    f"To: {RCPT_TO}",
    f"Subject: {SUBJECT}",
    "MIME-Version: 1.0",
    f'Content-Type: multipart/mixed; boundary="{boundary}"',
    "",
    f"--{boundary}",
    "Content-Type: text/plain; charset=utf-8",
    "Content-Transfer-Encoding: 7bit",
    "",
    body_text,
    "",
    f"--{boundary}",
    f"Content-Type: {mime_type}; name=\"{IMAGE_PATH}\"",
    "Content-Transfer-Encoding: base64",
    f"Content-Disposition: attachment; filename=\"{IMAGE_PATH}\"",
    "",
    img_b64,
    "",
    f"--{boundary}--",
    ""
]
message = CRLF.join(mime_message)

# 4. 连接 SMTP 服务器
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SMTP_SERVER, SMTP_PORT))
recv(sock)

# 5. EHLO
send(sock, f"EHLO example.com{CRLF}")
recv(sock)

# 6. STARTTLS
send(sock, f"STARTTLS{CRLF}")
recv(sock)
context = ssl.create_default_context()
sock = context.wrap_socket(sock, server_hostname=SMTP_SERVER)

# 7. TLS 之后再 EHLO 一次
send(sock, f"EHLO example.com{CRLF}")
recv(sock)

# 8. AUTH LOGIN 认证
send(sock, f"AUTH LOGIN{CRLF}")
recv(sock)
send(sock, base64.b64encode(USERNAME.encode()).decode() + CRLF)
recv(sock)
send(sock, base64.b64encode(PASSWORD.encode()).decode() + CRLF)
recv(sock)

# 9. 发送邮件指令
send(sock, f"MAIL FROM:<{MAIL_FROM}>{CRLF}")
recv(sock)
send(sock, f"RCPT TO:<{RCPT_TO}>{CRLF}")
recv(sock)
send(sock, f"DATA{CRLF}")
recv(sock)

# 10. 发送 MIME 邮件内容 + 结束符
send(sock, message + CRLF + "." + CRLF)
recv(sock)

# 11. 退出
send(sock, f"QUIT{CRLF}")
recv(sock)

sock.close()
print("\n✅ 发送完成，请检查收件箱（或垃圾箱）！")
