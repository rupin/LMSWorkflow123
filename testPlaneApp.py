import socket
import time
import struct

# Configuration
ESP_IP = "192.168.137.71"  # ESP8266 IP (find actual IP)
ESP_PORT = 6000
LOCAL_PORT = 2390

# Create UDP socket for sending
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Create separate socket for receiving broadcasts
recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
recv_sock.bind(('', LOCAL_PORT))  # Bind to all interfaces
recv_sock.settimeout(2.0)

def send_control(left_speed, right_speed):
    packet = bytes([1, left_speed, right_speed])
    send_sock.sendto(packet, (ESP_IP, ESP_PORT))
    print(f"Sent control: L={left_speed}, R={right_speed}")

def find_esp_ip():
    # Send broadcast to find ESP8266
    broadcast_addr = "192.168.4.255"  # Adjust for your network
    packet = bytes([1, 50, 50])
    send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    send_sock.sendto(packet, (broadcast_addr, ESP_PORT))
    print("Sent broadcast to find ESP8266...")

try:
    # First, find the ESP8266 IP if needed
    find_esp_ip()
    
    # Send initial control packets to trigger telemetry
    for i in range(3):
        send_control(50, 50)
        time.sleep(0.5)
        
        # Check for telemetry response
        try:
            data, addr = recv_sock.recvfrom(1024)
            print(f"Received from {addr}: {[hex(b) for b in data]}")
            
            if len(data) >= 3 and data[0] == 1:
                rssi = data[1]
                voltage = data[2] / 10.0
                print(f"Telemetry - RSSI: {rssi}, Voltage: {voltage}V")
                ESP_IP = addr[0]  # Update ESP IP
                break
        except socket.timeout:
            print("No telemetry received, retrying...")
    
    # Main control loop
    while True:
        send_control(75, 75)
        time.sleep(0.1)
        
        try:
            data, addr = recv_sock.recvfrom(1024)
            if len(data) >= 3 and data[0] == 1:
                rssi = data[1]
                voltage = data[2] / 10.0
                print(f"RSSI: {rssi}dBm, Voltage: {voltage}V")
        except socket.timeout:
            pass
            
        time.sleep(1.5)  # Match telemetry interval

except KeyboardInterrupt:
    print("Stopping...")
finally:
    send_sock.close()
    recv_sock.close()
