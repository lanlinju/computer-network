#!/usr/bin/env python3
"""
smtp_html_cid.py
Send an HTML email with an inline image (CID) using raw sockets + STARTTLS + AUTH LOGIN.
Python 3.
"""

import socket
import ssl
import base64
import uuid
import mimetypes
import textwrap
import sys
import config

CRLF = "\r\n"

def recv_all(sock):
    """Receive a single server response chunk (not a full multiline parser)."""
    data = sock.recv(4096)
    if not data:
        return ''
    return data.decode(errors='ignore')

def send_and_recv(sock, text, expect_start=None):
    """Send text (already with CRLF) and print/return response."""
    print("C:", text.strip().replace("\r\n", "\\r\\n"))
    sock.sendall(text.encode())
    reply = recv_all(sock)
    print("S:", reply.strip().replace("\r\n", "\\r\\n"))
    if expect_start and not reply.startswith(expect_start):
        print(f"Warning: expected reply starting with {expect_start} but got: {reply.splitlines()[0] if reply else 'NO_REPLY'}")
    return reply

def chunk_base64(b64str, width=76):
    return "\r\n".join(textwrap.wrap(b64str, width))

def build_mime_message(from_addr, to_addr, subject, text_body, html_body, inline_image_path, cid="image1"):
    """
    Construct the MIME message string with nested boundaries:
    multipart/mixed
      multipart/alternative
        text/plain
        multipart/related
          text/html
          inline image (Content-ID: <cid>)
    """
    # detect mime type for image
    mime_type = mimetypes.guess_type(inline_image_path)[0] or "application/octet-stream"
    maintype, subtype = mime_type.split("/", 1)

    # read and base64 encode image, wrap to 76 columns
    with open(inline_image_path, "rb") as f:
        img_b = f.read()
    img_b64 = base64.b64encode(img_b).decode()
    img_b64_wrapped = chunk_base64(img_b64, 76)

    # boundaries
    outer_b = "BOUT_" + uuid.uuid4().hex
    alt_b   = "BALT_" + uuid.uuid4().hex
    rel_b   = "BREL_" + uuid.uuid4().hex

    lines = []
    # headers
    lines.append(f"From: {from_addr}")
    lines.append(f"To: {to_addr}")
    lines.append(f"Subject: {subject}")
    lines.append("MIME-Version: 1.0")
    lines.append(f'Content-Type: multipart/mixed; boundary="{outer_b}"')
    lines.append("")  # end headers

    # start outer
    lines.append(f"--{outer_b}")
    lines.append(f'Content-Type: multipart/alternative; boundary="{alt_b}"')
    lines.append("")

    # plain text part
    lines.append(f"--{alt_b}")
    lines.append("Content-Type: text/plain; charset=utf-8")
    lines.append("Content-Transfer-Encoding: 7bit")
    lines.append("")
    lines.append(text_body)
    lines.append("")

    # multipart/related (HTML + inline)
    lines.append(f"--{alt_b}")
    lines.append(f'Content-Type: multipart/related; boundary="{rel_b}"')
    lines.append("")

    # HTML part inside related
    lines.append(f"--{rel_b}")
    lines.append("Content-Type: text/html; charset=utf-8")
    lines.append("Content-Transfer-Encoding: 7bit")
    lines.append("")
    lines.append(html_body)
    lines.append("")

    # inline image part
    lines.append(f"--{rel_b}")
    lines.append(f"Content-Type: {mime_type}; name=\"{inline_image_path}\"")
    lines.append("Content-Transfer-Encoding: base64")
    lines.append(f"Content-Disposition: inline; filename=\"{inline_image_path}\"")
    lines.append(f"Content-ID: <{cid}>")
    lines.append("")
    lines.append(img_b64_wrapped)
    lines.append("")

    # end related
    lines.append(f"--{rel_b}--")
    lines.append("")

    # end alternative
    lines.append(f"--{alt_b}--")
    lines.append("")

    # (optionally you could add other attachments here as further parts of outer)
    # end outer
    lines.append(f"--{outer_b}--")
    lines.append("")

    # join with CRLF
    message = CRLF.join(lines)
    return message

def send_email_starttls_auth(smtp_server, smtp_port, username, password, from_addr, to_addr, subject, text_body, html_body, inline_image_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(15)
    print(f"Connecting to {smtp_server}:{smtp_port} ...")
    sock.connect((smtp_server, smtp_port))

    # greeting
    resp = recv_all(sock)
    print("S:", resp.strip())
    if not resp.startswith("220"):
        print("Warning: server greeting not 220")

    # EHLO
    send_and_recv(sock, f"EHLO example.com{CRLF}", expect_start="250")

    # STARTTLS
    send_and_recv(sock, f"STARTTLS{CRLF}", expect_start="220")

    # wrap with TLS
    context = ssl.create_default_context()
    tls_sock = context.wrap_socket(sock, server_hostname=smtp_server)

    # EHLO again after TLS
    send_and_recv(tls_sock, f"EHLO example.com{CRLF}", expect_start="250")

    # AUTH LOGIN
    send_and_recv(tls_sock, f"AUTH LOGIN{CRLF}", expect_start="334")
    send_and_recv(tls_sock, base64.b64encode(username.encode()).decode() + CRLF, expect_start="334")
    send_and_recv(tls_sock, base64.b64encode(password.encode()).decode() + CRLF, expect_start="235")

    # MAIL FROM / RCPT TO / DATA
    send_and_recv(tls_sock, f"MAIL FROM:<{from_addr}>{CRLF}", expect_start="250")
    send_and_recv(tls_sock, f"RCPT TO:<{to_addr}>{CRLF}", expect_start="250")
    send_and_recv(tls_sock, f"DATA{CRLF}", expect_start="354")

    # build MIME message
    message = build_mime_message(from_addr, to_addr, subject, text_body, html_body, inline_image_path, cid="image1")

    # send message and end with CRLF.CRLF (a single dot on a line)
    # Note: To be strict, ensure message lines end with CRLF; our build does that.
    send_and_recv(tls_sock, message + CRLF + "." + CRLF, expect_start="250")

    # QUIT
    send_and_recv(tls_sock, f"QUIT{CRLF}", expect_start="221")
    tls_sock.close()
    print("Done.")

if __name__ == "__main__":
    # ------------------ 配置项（请修改） ------------------
    SMTP_SERVER = "smtp.qq.com"       # 例如 smtp.gmail.com
    SMTP_PORT   = 587                    # 使用 STARTTLS 的端口
    USERNAME    = "laurie233@foxmail.com" # 用于 AUTH LOGIN（通常和 MAIL FROM 相同）
    PASSWORD    = config.PASSWORD_QQ    # Gmail 推荐使用 App Password（两步验证开启时）
    MAIL_FROM   = USERNAME
    RCPT_TO     = "troyenight@163.com"
    SUBJECT     = "HTML + Inline Image (CID) Demo"
    IMAGE_PATH  = "image.jpg"           # 本地图片文件（相对或绝对路径）
    # 简单文本与 HTML（示例）
    TEXT_BODY = "This is a fallback plain-text body. Your client does not support HTML."
    # HTML body uses cid:image1 to reference the inline image
    HTML_BODY = """\
<html>
  <body>
    <h2>Hello — HTML with inline image (CID)</h2>
    <p>This image is embedded inline using Content-ID (CID):</p>
    <img src="cid:image1" alt="inline image" style="max-width:600px; height:auto;">
    <p>Regards,<br/>Socket SMTP Client</p>
  </body>
</html>
"""
    # ------------------ 结束配置 ------------------

    # basic existence check for image
    try:
        with open(IMAGE_PATH, "rb"):
            pass
    except Exception as e:
        print(f"Cannot open image file '{IMAGE_PATH}': {e}")
        sys.exit(1)

    try:
        send_email_starttls_auth(
            SMTP_SERVER, SMTP_PORT, USERNAME, PASSWORD,
            MAIL_FROM, RCPT_TO, SUBJECT, TEXT_BODY, HTML_BODY, IMAGE_PATH
        )
    except Exception as ex:
        print("Error during sending:", ex)
        sys.exit(1)
