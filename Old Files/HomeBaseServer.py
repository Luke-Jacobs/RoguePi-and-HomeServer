import socket

SERVERPORT = 8554

while True:
    s = socket.socket(socket.AF_INET)
    s.bind(("0.0.0.0", SERVERPORT))
    s.listen(1)
    print("Listening for connections")
    conn, addr = s.accept()
    print("Accepted connection!", addr)
    conn.settimeout(15)
    while True:
        try:
            data = conn.recv(2048)
            if data == b"":
                print("Closed connection...")
                break
            print(data)
            conn.send(b"PONG")
        except Exception as e:
            print("Exception: "+str(e))
            break

