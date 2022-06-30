import socket
import sys
import time
HOST = socket.gethostname()
PORT = 32752
if len(sys.argv) > 1 and sys.argv[1].isdigit():
    PORT = int(sys.argv[1])

def recieve_message(s):
    data = b""
    while True:
        data += s.recv(1024)
        if (b" "+data)[-1:] == b";": #space added on the back to insure no indexerror
            break
    return data[:-1] #remove semicolon for convenience

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print(f"Binding {socket.gethostbyname(socket.getfqdn())} on port {PORT}")
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            time.sleep(1/120)
            data = recieve_message(conn)
            conn.sendall(b"1 100 100,0 200 200,1 125 125;")
