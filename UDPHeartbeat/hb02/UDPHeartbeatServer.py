# UDPHeartbeatServer.py
import socket
import time
import threading

def heartbeat_server(host='', port=13000):
    # 创建UDP套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.settimeout(1.0)  # 设置套接字超时，以便定期检查
    server_socket.bind((host, port))
    
    print(f"心跳服务器正在监听端口 {port}...")
    
    # 存储客户端状态
    client_status = {}
    # 用于线程安全的锁
    status_lock = threading.Lock()
    
    def check_timeouts():
        """定期检查客户端超时的线程函数"""
        while True:
            time.sleep(2)  # 每2秒检查一次
            current_time = time.time()
            
            with status_lock:
                timeout_clients = []
                for client_key, status in client_status.items():
                    if current_time - status['last_seen'] > 5:  # 5秒超时
                        timeout_clients.append(client_key)
                
                for client_key in timeout_clients:
                    print(f"警告: 客户端 {client_key} 可能已停止运行! (最后活动: {current_time - client_status[client_key]['last_seen']:.1f}秒前)")
                    del client_status[client_key]
    
    # 启动超时检查线程
    timeout_thread = threading.Thread(target=check_timeouts)
    timeout_thread.daemon = True
    timeout_thread.start()
    
    while True:
        try:
            # 接收心跳包
            message, client_address = server_socket.recvfrom(1024)
            current_time = time.time()
            
            # 解析心跳消息
            try:
                parts = message.decode().split()
                if len(parts) >= 3 and parts[0] == "HEARTBEAT":
                    sequence_number = int(parts[1])
                    client_time = float(parts[2])
                    
                    # 计算时间差（单向延迟）
                    time_diff = current_time - client_time
                    
                    # 更新客户端状态
                    client_key = f"{client_address[0]}:{client_address[1]}"
                    with status_lock:
                        client_status[client_key] = {
                            'last_seen': current_time,
                            'sequence': sequence_number,
                            'last_delay': time_diff,
                            'first_seen': client_status.get(client_key, {}).get('first_seen', current_time)
                        }
                    
                    print(f"收到来自 {client_key} 的心跳 #{sequence_number}, 延迟: {time_diff*1000:.3f}ms")
                    
                    # 定期显示活跃客户端状态
                    if sequence_number % 10 == 0:
                        print(f"当前活跃客户端: {len(client_status)}")
                        
            except (ValueError, IndexError) as e:
                print(f"收到格式错误的心跳包来自 {client_address}: {e}")
            
        except socket.timeout:
            # 超时是正常的，用于让出时间给其他操作
            continue
        except KeyboardInterrupt:
            print("\n服务器关闭。")
            break
        except Exception as e:
            print(f"服务器错误: {e}")
            break
    
    server_socket.close()

if __name__ == "__main__":
    heartbeat_server()