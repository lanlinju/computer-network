# UDPHeartbeatClient.py
import socket
import time
import threading
import random

def heartbeat_client(server_host='localhost', server_port=13000, interval=1, client_id=None):
    # 创建UDP套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sequence_number = 1
    running = True
    
    if client_id is None:
        client_id = f"client_{random.randint(1000, 9999)}"
    
    packets_sent = 0
    start_time = time.time()
    
    def send_heartbeat():
        nonlocal sequence_number, packets_sent
        while running:
            try:
                # 发送心跳包
                current_time = time.time()
                message = f"HEARTBEAT {sequence_number} {current_time} {client_id}"
                client_socket.sendto(message.encode(), (server_host, server_port))
                packets_sent += 1
                sequence_number += 1
                
                # 每10个包显示一次状态
                if packets_sent % 10 == 0:
                    uptime = time.time() - start_time
                    print(f"[{client_id}] 已发送 {packets_sent} 个心跳包, 运行时间: {uptime:.1f}秒")
                    
            except Exception as e:
                print(f"[{client_id}] 发送心跳失败: {e}")
            
            time.sleep(interval)
    
    def simulate_network_issues():
        """模拟网络问题的线程（用于测试）"""
        time.sleep(15)  # 15秒后开始模拟问题
        print(f"\n[{client_id}] 模拟网络问题：心跳间隔增加到3秒")
        global interval
        interval = 3
        
        time.sleep(10)  # 再等10秒
        print(f"\n[{client_id}] 恢复正常心跳间隔")
        interval = 1
    
    # 启动心跳发送线程
    heartbeat_thread = threading.Thread(target=send_heartbeat)
    heartbeat_thread.daemon = True
    heartbeat_thread.start()
    
    # 启动网络问题模拟线程（可选，用于测试）
    # network_thread = threading.Thread(target=simulate_network_issues)
    # network_thread.daemon = True
    # network_thread.start()
    
    print(f"[{client_id}] 心跳客户端已启动，每 {interval} 秒发送一次心跳到 {server_host}:{server_port}")
    print("按 Ctrl+C 停止...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n[{client_id}] 停止心跳客户端...")
        running = False
        uptime = time.time() - start_time
        print(f"[{client_id}] 总共发送 {packets_sent} 个心跳包, 总运行时间: {uptime:.1f}秒")

if __name__ == "__main__":
    # 可以启动多个客户端进行测试
    # heartbeat_client(client_id="client_1", interval=1)
    heartbeat_client(interval=1)