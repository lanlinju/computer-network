# server.py
from socket import *
import threading
import os
import urllib.parse
import mimetypes
import sys

# ---------- 配置 ----------
# 从命令行参数获取根目录，如果没有提供则使用当前目录
if len(sys.argv) > 1:
    ROOT_DIR = os.path.abspath(sys.argv[1])
else:
    ROOT_DIR = os.path.abspath(".")
PORT = 8080
# --------------------------

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

def safe_abs_path(url_path: str) -> str:
    """
    将 URL 路径转换为安全的绝对文件系统路径。
    1. 解码 URL
    2. 去掉前导 '/'
    3. 拼接到 ROOT_DIR 并规范化
    4. 检查是否越权
    """
    url_path = urllib.parse.unquote(url_path)  # 解码中文/空格等
    rel = url_path.lstrip("/")  # 去掉前导斜杠
    abs_path = os.path.normpath(os.path.join(ROOT_DIR, rel))
    root_norm = os.path.normpath(os.path.abspath(ROOT_DIR))
    abs_path = os.path.abspath(abs_path)
    if not abs_path.startswith(root_norm):
        # 尝试越权，拒绝
        raise PermissionError("Forbidden")
    return abs_path

def list_dir_bytes(abs_path: str, url_path: str) -> bytes:
    """
    生成目录索引页（HTML，UTF-8 bytes）
    url_path: 原始请求路径（用于生成 link）
    """
    try:
        items = os.listdir(abs_path)
    except PermissionError:
        items = []
    items.sort(key=lambda x: (not os.path.isdir(os.path.join(abs_path, x)), x.lower()))

    # 面包屑
    parts = [p for p in url_path.strip("/").split("/") if p] if url_path.strip("/") else []
    bread = '<a href="/">🏠 Home</a>'
    cur = ""
    for p in parts:
        cur += "/" + p
        bread += f' / <a href="{cur}/">{p}</a>'

    # 列表项
    rows = ""
    base = url_path if url_path.endswith("/") else (url_path + "/")
    
    # 上级目录（只在非根目录显示）
    if url_path != "/":
        # 计算上级目录路径
        parent_parts = parts[:-1]  # 去掉最后一部分
        if parent_parts:
            parent_path = "/" + "/".join(parent_parts) + "/"
        else:
            parent_path = "/"
        rows += f'<div class="item folder"><a href="{parent_path}">📁 ../</a></div>'

    for name in items:
        full = os.path.join(abs_path, name)
        disp = name + ("/" if os.path.isdir(full) else "")
        # 重要：仅对 name 做编码，不编码斜杠
        link = base + urllib.parse.quote(name)
        icon = "📁" if os.path.isdir(full) else "📄"
        size_info = ""
        if os.path.isfile(full):
            try:
                size_info = f"<span class='size'>{format_size(os.path.getsize(full))}</span>"
            except:
                size_info = ""
        rows += f'''
        <div class="item {'folder' if os.path.isdir(full) else 'file'}">
            <a href="{link}">
                <div class="icon">{icon}</div>
                <div class="meta">
                    <div class="name" title="{html_escape(disp)}">{html_escape(disp)}</div>
                    <div class="sub">{size_info}</div>
                </div>
            </a>
        </div>
        '''

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Index of {html_escape(url_path)}</title>
<style>
:root {{
  --bg: #0f1216;
  --card: #14171b;
  --accent: #4db2ff;
  --muted: #9aa4b2;
  --text: #e6eef6;
}}

[data-theme="light"] {{
  --bg: #f5f7fa;
  --card: #ffffff;
  --accent: #007acc;
  --muted: #6c757d;
  --text: #2c3e50;
}}

*{{box-sizing:border-box}}
body{{margin:0;font-family:Inter,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);padding:18px;transition:background 0.3s, color 0.3s}}
.header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}}
.header .title{{font-weight:700;font-size:18px}}
.bread{{color:var(--muted);font-size:13px;margin-top:6px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}}
.item{{
  background:var(--card);
  border-radius:10px;
  padding:12px;
  display:flex;
  align-items:center;
  gap:10px;
  min-height:80px;
  max-height:80px;
  overflow:hidden;
  transition:all 0.3s ease;
  border: 1px solid transparent;
  -webkit-tap-highlight-color: transparent;
  cursor: pointer;
}}
.item a{{
  display:flex;
  align-items:center;
  gap:10px;
  width:100%;
  color:inherit;
  text-decoration:none;
  -webkit-tap-highlight-color: transparent;
}}
.item:hover{{
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}}
.folder:hover {{
  background: rgba(27, 58, 107, 0.1);
  border-color: rgba(27, 58, 107, 0.3);
}}
[data-theme="light"] .folder:hover {{
  background: rgba(187, 222, 251, 0.3);
  border-color: rgba(187, 222, 251, 0.5);
}}
.file:hover {{
  background: rgba(43, 43, 61, 0.1);
  border-color: rgba(43, 43, 61, 0.3);
}}
[data-theme="light"] .file:hover {{
  background: rgba(245, 245, 245, 0.5);
  border-color: rgba(245, 245, 245, 0.7);
}}
.icon{{width:44px;height:44px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:20px;background:linear-gradient(135deg,#0b1220,#131820);transition:background 0.3s}}
[data-theme="light"] .icon{{background:linear-gradient(135deg,#e3f2fd,#f3e5f5)}}
.meta{{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center}}
.name{{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.sub{{color:var(--muted);font-size:13px;margin-top:6px;display:flex;justify-content:space-between;align-items:center}}
.size{{font-size:12px;color:var(--muted)}}
.folder .icon{{background:linear-gradient(135deg,#1b3a6b,#15324f)}}
[data-theme="light"] .folder .icon{{background:linear-gradient(135deg,#bbdefb,#90caf9)}}
.file .icon{{background:linear-gradient(135deg,#2b2b3d,#2e2932)}}
[data-theme="light"] .file .icon{{background:linear-gradient(135deg,#f5f5f5,#eeeeee)}}

.theme-toggle{{
  background:var(--card);
  border:1px solid var(--muted);
  border-radius:20px;
  padding:8px 12px;
  color:var(--text);
  cursor:pointer;
  font-size:12px;
  transition:all 0.3s;
  display:flex;
  align-items:center;
  gap:6px;
  -webkit-tap-highlight-color: transparent;
}}
.theme-toggle:hover{{
  border-color:var(--accent);
  transform:scale(1.05);
}}

/* 响应式调整 - 平板 */
@media (max-width: 768px) {{
  body {{
    padding: 12px;
  }}
  .header {{
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }}
  .header > div:last-child {{
    width: 100%;
    justify-content: space-between;
  }}
  .grid {{
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 10px;
  }}
  .item {{
    min-height: 70px;
    max-height: 70px;
    padding: 10px;
  }}
  .icon {{
    width: 36px;
    height: 36px;
    font-size: 16px;
  }}
  .name {{
    font-size: 14px;
  }}
  .sub, .size {{
    font-size: 11px;
  }}
}}

/* 响应式调整 - 手机 */
@media (max-width: 480px) {{
  .grid {{
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 8px;
  }}
  .item {{
    min-height: 65px;
    max-height: 65px;
    padding: 8px;
  }}
  .icon {{
    width: 32px;
    height: 32px;
    font-size: 14px;
  }}
  .bread {{
    font-size: 12px;
    line-height: 1.4;
  }}
  .header .title {{
    font-size: 16px;
  }}
  .header > div:last-child {{
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }}
}}
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="title">Index</div>
    <div class="bread">{bread}</div>
  </div>
  <div style="display:flex;align-items:center;gap:12px;color:var(--muted);font-size:13px">
    <div>Root: {html_escape(ROOT_DIR)}</div>
    <button class="theme-toggle" onclick="toggleTheme()">
      <span id="theme-icon">🌙</span> <span id="theme-text">深色</span>
    </button>
  </div>
</div>

<div class="grid">
{rows}
</div>

<script>
// 主题切换功能
function getTheme() {{
  return localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
}}

function setTheme(theme) {{
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  
  const icon = document.getElementById('theme-icon');
  const text = document.getElementById('theme-text');
  if (theme === 'light') {{
    icon.textContent = '☀️';
    text.textContent = '浅色';
  }} else {{
    icon.textContent = '🌙';
    text.textContent = '深色';
  }}
}}

function toggleTheme() {{
  const currentTheme = getTheme();
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  setTheme(newTheme);
}}

// 初始化主题
setTheme(getTheme());

// 监听系统主题变化
window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', e => {{
  if (!localStorage.getItem('theme')) {{
    setTheme(e.matches ? 'light' : 'dark');
  }}
}});
</script>

</body>
</html>
"""
    return html.encode("utf-8")

def html_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))

def format_size(n: int) -> str:
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024.0:
            return f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"

def serve(conn):
    try:
        req = conn.recv(8192).decode(errors="ignore")
        if not req:
            return
        first_line = req.split("\r\n")[0]
        parts = first_line.split()
        method, url_path = parts[0], parts[1]
        print("Request:", urllib.parse.unquote(url_path))

        # 只处理 GET
        if method.upper() not in ("GET", "HEAD"):
            conn.send(b"HTTP/1.1 405 Method Not Allowed\r\nAllow: GET, HEAD\r\n\r\n")
            return

        # 规范化路径并获得绝对路径
        try:
            abs_path = safe_abs_path(url_path)
        except PermissionError:
            conn.send(b"HTTP/1.1 403 Forbidden\r\n\r\nForbidden")
            return

        # 如果是目录，返回目录页（保证目录 URL 以 / 结尾）
        if os.path.isdir(abs_path):
            if not url_path.endswith("/"):
                # 跳转到带 / 的 URL（让浏览器请求子文件时能拼接正确路径）
                location = url_path + "/"
                resp = f"HTTP/1.1 301 Moved Permanently\r\nLocation: {location}\r\nConnection: close\r\n\r\n"
                conn.send(resp.encode())
                return
            body = list_dir_bytes(abs_path, url_path)
            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n\r\n"
            )
            conn.send(header.encode() + body)
            return

        # 如果是文件，支持 Range
        if os.path.isfile(abs_path):
            size = os.path.getsize(abs_path)
            mime = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"

            # 解析 Range 头
            range_header = None
            for line in req.split("\r\n"):
                if line.lower().startswith("range:"):
                    try:
                        range_header = line.split(":",1)[1].strip()
                    except:
                        range_header = None
                    break

            start, end = 0, size - 1
            is_partial = False
            if range_header and range_header.lower().startswith("bytes="):
                try:
                    r = range_header.split("=",1)[1]
                    s, e = r.split("-",1)
                    if s.strip() != "":
                        start = int(s)
                    if e.strip() != "":
                        end = int(e)
                    # clamp
                    if start < 0: start = 0
                    if end > size - 1: end = size - 1
                    if start > end:
                        conn.send(b"HTTP/1.1 416 Range Not Satisfiable\r\n\r\n")
                        return
                    is_partial = True
                except Exception:
                    is_partial = False

            length = end - start + 1

            if is_partial:
                status_line = "HTTP/1.1 206 Partial Content\r\n"
                content_range = f"Content-Range: bytes {start}-{end}/{size}\r\n"
            else:
                status_line = "HTTP/1.1 200 OK\r\n"
                content_range = ""

            header = (
                status_line +
                f"Content-Type: {mime}\r\n" +
                "Accept-Ranges: bytes\r\n" +
                content_range +
                f"Content-Length: {length}\r\n" +
                "Connection: close\r\n\r\n"
            )
            conn.send(header.encode())

            # 发送文件片段
            with open(abs_path, "rb") as f:
                f.seek(start)
                remain = length
                buf = 64 * 1024
                while remain > 0:
                    chunk = f.read(min(buf, remain))
                    if not chunk:
                        break
                    try:
                        conn.send(chunk)
                    except BrokenPipeError:
                        # 客户端中断，优雅结束
                        break
                    remain -= len(chunk)
            return

        # 默认：未找到
        conn.send(b"HTTP/1.1 404 Not Found\r\n\r\nNot Found")

    except Exception as e:
        print("Serve error:", e)
        try:
            conn.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\nServer Error")
        except:
            pass
    finally:
        try: conn.close()
        except: pass

def main():
    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(("", PORT))
    s.listen(20)
    
    # 获取本机IP地址
    local_ip = get_local_ip()
    print(f"📁 File server running at:")
    print(f"   http://127.0.0.1:{PORT}/")
    print(f"   http://{local_ip}:{PORT}/")
    print("Use Ctrl+C to stop the server")
    
    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=serve, args=(conn,), daemon=True).start()
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        s.close()

if __name__ == "__main__":
    main()