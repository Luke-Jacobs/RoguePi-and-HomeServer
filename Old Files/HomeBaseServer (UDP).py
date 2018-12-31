import socket


while True:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", 80))
    while True:
        try:
            data, addr = s.recvfrom(1024)
            if data == b"":
                print("Closed connection...")
                break
            print(data)
            s.sendto("YOLO", addr)
        except Exception as e:
            print("Exception: "+str(e))
            break
