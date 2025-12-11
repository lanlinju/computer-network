from socket import *
import threading
import os
import urllib.parse
import sys

if len(sys.argv) > 1:
    ROOT_DIR = os.path.abspath(sys.argv[1])
else:
    ROOT_DIR = os.path.abspath(".")
PORT = 8080

def list_dir(path, url_path):
    items = os.listdir(path)
    html = "<html><head><meta charset='utf-8'><title>Index of {}</title></head><body>".format(url_path)
    html += f"<h2>Index of {url_path}</h2><hr><ul>"

    # 上级目录
    if url_path != "/":
        parent = os.path.dirname(url_path.rstrip("/"))
        if not parent.endswith("/"):
            parent += "/"
        html += f'<li><a href="{parent}">../</a></li>'

    for name in items:
        full_path = os.path.join(path, name)
        display = name + ("/" if os.path.isdir(full_path) else "")
        link = urllib.parse.quote(name)
        html += f'<li><a href="{url_path}{link}">{display}</a></li>'

    html += "</ul><hr></body></html>"
    return html.encode("utf-8")

def serve(conn):
    try:
        request = conn.recv(4096).decode("utf-8", errors="ignore")
        first_line = request.split("\n")[0]
        
        # 解析路径
        path = first_line.split(" ")[1]
        path = urllib.parse.unquote(path)
        abs_path = os.path.join(ROOT_DIR, path.lstrip("/"))

        print("Request:", path)

        # 目录索引
        if os.path.isdir(abs_path):
            if not path.endswith("/"):
                redirect = f"HTTP/1.1 301 Moved Permanently\r\nLocation: {path}/\r\n\r\n"
                conn.send(redirect.encode())
                return
            body = list_dir(abs_path, path)
            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n\r\n"
            )
            conn.send(header.encode() + body)
            return

        # 处理文件（支持 Range）
        if not os.path.exists(abs_path):
            conn.send(b"HTTP/1.1 404 Not Found\r\n\r\nFile Not Found")
            return

        size = os.path.getsize(abs_path)
        ext = os.path.splitext(abs_path)[1].lower()
        mime = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".ogg": "video/ogg",
            ".html": "text/html",
            ".jpg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".txt": "text/plain",
        }.get(ext, "application/octet-stream")

        # 解析 Range
        start, end = 0, size - 1
        for line in request.split("\r\n"):
            if line.lower().startswith("range:"):
                r = line.split("=")[1]
                s, e = r.split("-")
                if s.isdigit(): start = int(s)
                if e.isdigit(): end = int(e)
                break

        end = min(end, size - 1)
        length = end - start + 1

        if length != size:
            header = (
                "HTTP/1.1 206 Partial Content\r\n"
                f"Content-Type: {mime}\r\n"
                f"Content-Length: {length}\r\n"
                f"Content-Range: bytes {start}-{end}/{size}\r\n"
                "Accept-Ranges: bytes\r\nConnection: close\r\n\r\n"
            )
        else:
            header = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Type: {mime}\r\n"
                f"Content-Length: {size}\r\n"
                "Accept-Ranges: bytes\r\nConnection: close\r\n\r\n"
            )

        conn.send(header.encode())

        # 发送文件内容
        with open(abs_path, "rb") as f:
            f.seek(start)
            remain = length
            buf = 64 * 1024
            while remain > 0:
                chunk = f.read(min(buf, remain))
                if not chunk: break
                try:
                    conn.send(chunk)
                except BrokenPipeError:
                    break
                remain -= len(chunk)


    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 创建一个临时socket来获取本机IP
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(("", PORT))
    s.listen(10)
    print(f"📁 File server running at: ")
    print(f"   http://127.0.0.1:{PORT}/")
    print(f"   http://{get_local_ip()}:{PORT}/")

    while True:
        c, _ = s.accept()
        threading.Thread(target=serve, args=(c,)).start()

if __name__ == "__main__":
    main()
