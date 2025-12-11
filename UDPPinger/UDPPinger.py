from socket import *
import time

serverName = '127.0.0.1'
serverPort = 12000

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(1)

rtt_list = []
lost_count = 0

for seq in range(1, 11):
    send_time = time.time()
    msg = f"Ping {seq} {send_time}"

    try:
        clientSocket.sendto(msg.encode(), (serverName, serverPort))
        recv_msg, _ = clientSocket.recvfrom(1024)
        recv_time = time.time()

        rtt = (recv_time - send_time) * 1000
        rtt_list.append(rtt)
        print(f"Seq {seq:2}: Reply from {serverName}:    Bytes={len(recv_msg)}    RTT = {rtt:.3f}ms")
    except Exception as e:
        lost_count += 1
        print(f"Seq {seq:2}: Request timed out")

clientSocket.close()

print(f"\n{serverName} 的 Ping 统计信息:")
print(f"    数据包: 已发送 = 10, 已接收 = {10 - lost_count}, 丢失 = {lost_count} ")
print(f"    丢包率: {lost_count / 10 * 100:.1f}%")

if rtt_list:
    stat = (
        f"最短 RTT: {min(rtt_list):.3f} ms    "
        f"最长 RTT: {max(rtt_list):.3f} ms    "
        f"平均 RTT: {sum(rtt_list) / len(rtt_list):.3f} ms"
    )
    print(stat)