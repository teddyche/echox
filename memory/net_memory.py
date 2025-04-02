import socket
import json

MEMORY = {"echo-x": {"etat": "en vie", "niveau": 99}}

HOST = "127.0.0.1"
UDP_PORT = 5050
TCP_PORT = 5051

data = json.dumps(MEMORY).encode()

# 🔹 Envoi UDP
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.sendto(data, (HOST, UDP_PORT))
udp_sock.close()
print("[📡 UDP] Mémoire envoyée.")

# 🔸 Envoi TCP
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.connect((HOST, TCP_PORT))
tcp_sock.sendall(data)
tcp_sock.close()
print("[📡 TCP] Mémoire envoyée.")

