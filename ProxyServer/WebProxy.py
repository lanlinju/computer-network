from socket import *
import threading
import hashlib
import os
import time

CACHE_DIR = "./cache"
os.makedirs(CACHE_DIR, exist_ok=True)

MAX_CACHE_FILE = 10 * 1024 * 1024  # 单文件最大 10MB
MAX_CACHE_TOTAL = 100 * 1024 * 1024  # 总缓存 100MB 触发清理
CACHE_TTL = 600  # 10分钟

cache_index = {}  # key → {path, time}
cache_lock = threading.RLock()

server_sock = socket(AF_INET, SOCK_STREAM)
server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
server_sock.bind(('', 8888))
server_sock.listen(128)
print("🚀 Proxy Server running on port 8888...")

def sha256(text: str):
    return hashlib.sha256(text.encode()).hexdigest()


def cache_valid(key):
    with cache_lock:
        info = cache_index.get(key)
        if not info:
            return False
        if time.time() - info["time"] > CACHE_TTL:
            try: os.remove(info["path"])
            except: pass
            del cache_index[key]
            print("⏳ Cache expired:", key)
            return False
        return True


def cache_total_size():
    return sum(os.path.getsize(os.path.join(CACHE_DIR, f))
               for f in os.listdir(CACHE_DIR)
               if os.path.isfile(os.path.join(CACHE_DIR, f)))


def clear_cache_all():
    print("\n🧹 Cache >100MB, clearing ALL...\n")
    for f in os.listdir(CACHE_DIR):
        try: os.remove(os.path.join(CACHE_DIR, f))
        except: pass
    cache_index.clear()


def auto_clean():
    while True:
        time.sleep(60)
        if cache_total_size() > MAX_CACHE_TOTAL:
            with cache_lock:
                clear_cache_all()


def parse_host_port(url):
    host_port = url.split("/")[0]
    if ":" in host_port:
        h, p = host_port.split(":", 1)
        return h, int(p)
    return host_port, 80


def handle_client(cli, addr):
    print("\nClient:", addr)
    try:
        data = b""
        # 读到请求头
        while b"\r\n\r\n" not in data:
            part = cli.recv(4096)
            if not part:
                return
            data += part

        header, body = data.split(b"\r\n\r\n", 1)
        header_text = header.decode(errors="ignore")

        # 解析请求行
        parts = header_text.split(" ")
        if len(parts) < 2:
            return
        method, url = parts[0], parts[1]

        # 计算缓存 key（仅 GET 可能用到）
        key = sha256(method + url)
        cache_file = os.path.join(CACHE_DIR, key + ".cache")

        # ✅ 判断是否可缓存（只有 GET 才可能缓存）
        cacheable = (
            method.upper() == "GET"
            and "Range:" not in header_text
            and not any(x in url.lower() for x in [".mp4", ".m3u8", ".mp3", ".flv"])
        )

        # ✅ POST 需要读取完整请求体（根据 Content-Length）
        if method.upper() == "POST":
            content_length = 0
            for line in header_text.split("\r\n"):
                if line.lower().startswith("content-length"):
                    content_length = int(line.split(":")[1].strip())

            # 读完 body（可能未完全接收完）
            while len(body) < content_length:
                body += cli.recv(4096)

            cacheable = False

        # ✅ GET 缓存命中
        if cacheable and cache_valid(key):
            print("✅ Cache hit")
            with open(cache_index[key]["path"], "rb") as f:
                while chunk := f.read(8192):
                    cli.sendall(chunk)
            return

        print("❌ Cache miss" if cacheable else "🔁 Proxy (no cache)")

        # 解析 host
        clean_url = url.replace("/http://", "").replace("http://", "").lstrip("/")
        host, port = parse_host_port(clean_url)

        upstream = socket(AF_INET, SOCK_STREAM)
        upstream.connect((host, port))

        # 重新构建请求
        request_line = f"{method} http://{clean_url} HTTP/1.1\r\n"
        headers = ""
        for line in header_text.split("\r\n")[1:]:
            if line.lower().startswith("host:"):
                continue
            if not line.strip():
                break
            headers += line + "\r\n"

        host_header = f"Host: {host}\r\n" if port == 80 else f"Host: {host}:{port}\r\n"

        final_request = (request_line + host_header + headers + "\r\n").encode() + body
        print("→ Proxy Request:", final_request)
        upstream.sendall(final_request)

        response =b''
        while True:
            chunk = upstream.recv(8192)
            if not chunk:
                break
            cli.sendall(chunk)
            if cacheable:
                response += chunk

        upstream.close()

        if cacheable and len(response) < MAX_CACHE_FILE:
            with open(cache_file, "wb") as f_cache:
                f_cache.write(response)
            with cache_lock:
                cache_index[key] = {"path": cache_file, "time": time.time()}
            print("💾 Cached:", len(response), "bytes")
            
    except Exception as e:
        print("Error:", e)
    finally:
        try:
            cli.close()
        except:
            pass

clear_cache_all()
threading.Thread(target=auto_clean, daemon=True).start()

try:
    while True:
        c, a = server_sock.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()
except KeyboardInterrupt:
    server_sock.close()
