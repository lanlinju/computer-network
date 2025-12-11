# UDPHeartbeatServer.py
# 接收心跳，计算单向时延（需时钟同步），统计丢包、检测客户端离线
import socket
import time

HOST = ''            # 监听所有接口
PORT = 12001
BUFFER = 1024
OFFLINE_THRESHOLD = 5.0  # 秒，如果超过这个时间没收到心跳，认为客户端离线

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
sock.settimeout(1.0)

print(f"Heartbeat server listening on UDP {PORT}")

clients = {}  # key: addr, value: dict {last_seq, last_recv_time, total_received, total_lost, expected_seq}

try:
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER)
        except socket.timeout:
            # 定期检查离线客户端
            now = time.time()
            to_remove = []
            for addr_k, st in clients.items():
                if now - st['last_recv_time'] > OFFLINE_THRESHOLD:
                    print(f"[{addr_k}] OFFLINE (last seen {now - st['last_recv_time']:.1f}s ago)")
                    to_remove.append(addr_k)
            for r in to_remove:
                clients.pop(r, None)
            continue

        recv_time = time.time()
        text = data.decode().strip()
        # 协议: "HB <seq> <timestamp>"
        parts = text.split()
        if len(parts) != 3 or parts[0] != 'HB':
            print(f"Bad packet from {addr}: {text}")
            continue

        try:
            seq = int(parts[1])
            client_ts = float(parts[2])
        except:
            print(f"Malformed heartbeat from {addr}: {text}")
            continue

        st = clients.get(addr)
        if st is None:
            st = {
                'last_seq': seq,
                'expected_seq': seq + 1,
                'last_recv_time': recv_time,
                'total_received': 1,
                'total_lost': 0
            }
            clients[addr] = st
            lost_here = 0
        else:
            # 丢包检测：如果收到的 seq > expected_seq，则中间有丢包
            if seq > st['expected_seq']:
                lost_here = seq - st['expected_seq']
                st['total_lost'] += lost_here
            else:
                lost_here = 0
            st['total_received'] += 1
            st['last_seq'] = seq
            st['expected_seq'] = seq + 1
            st['last_recv_time'] = recv_time

        # 计算单向延迟（需时钟同步）
        one_way = recv_time - client_ts

        print(f"[{addr}] seq={seq} lost_detected={lost_here} one_way={one_way:.4f}s "
              f"received={st['total_received']} lost={st['total_lost']}")

        # 可选：回复ACK（以便客户端测RTT或确认被接收）
        # ack_msg = f"ACK {seq} {recv_time}"
        # sock.sendto(ack_msg.encode(), addr)

except KeyboardInterrupt:
    print("Server shutting down.")
finally:
    sock.close()
