# UDPHeartbeatClient.py
# 客户端定期发送心跳： "HB <seq> <timestamp>"
import socket
import time
import threading

SERVER = ('127.0.0.1', 12001)
INTERVAL = 1.0   # 秒
TOTAL = 0        # 0 表示持续发送，或设置为具体次数

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1.0)

stop_event = threading.Event()

def send_heartbeats():
    seq = 1
    while not stop_event.is_set():
        ts = time.time()
        msg = f"HB {seq} {ts}"
        try:
            sock.sendto(msg.encode(), SERVER)
        except Exception as e:
            print("Send error:", e)
        print(f"Sent seq={seq} ts={ts:.3f}")
        seq += 1
        if TOTAL and seq > TOTAL:
            break
        time.sleep(INTERVAL)

try:
    t = threading.Thread(target=send_heartbeats, daemon=True)
    t.start()
    # 主线程可以同时监听ACK（如果服务器回复ACK），或者只是等待退出
    if TOTAL == 0:
        print("Press Ctrl-C to stop client.")
        while True:
            time.sleep(1)
    else:
        t.join()
except KeyboardInterrupt:
    print("Stopping client.")
    stop_event.set()
finally:
    sock.close()
