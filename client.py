import socket
import sys
HOST = sys.argv[1]
PORT = 32752
if len(sys.argv) > 2 and sys.argv[2].isdigit():
    PORT = int(sys.argv[2])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print(f"Attempting connection to {HOST} on port {PORT}")
    s.connect((HOST, PORT))
    s.sendall(b"data")