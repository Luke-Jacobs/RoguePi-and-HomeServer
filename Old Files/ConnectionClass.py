import socket, threading


class Client:
    def __init__(self):
        self.host = ""
        self.port = 0
        self.timeout = 0.0
        self.noblocking = 0
        self.sock = None

    def setup(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket()

    def connect(self, timeout=None):
        if timeout:
            self.sock.settimeout(timeout)
        self.sock.connect((self.host, self.port))

    def send(self, data):
        self.sock.send(data)

    def recv(self, timeout=None):
        if timeout:
            self.sock.settimeout(timeout)
        self.sock.recv(2048)

    def talk(self, data):
        self.sock.send(data)
        return self.sock.recv(2048)


class Server:

    def __init__(self):
        self.port = 0
        self.maxthreads = 1
        self.host = "0.0.0.0"
        self.sock = None
        self.handler = None

    def setup(self, port, handler, host=None):
        if host:
            self.host = host
        self.port = port
        self.sock = socket.socket()
        self.sock.bind((self.host, self.port))
        self.sock.listen(self.maxthreads)
        self.handler = handler

    def runforever(self):
        while True:
            conn, addr = self.sock.accept()
            thread = threading.Thread(target=self.handler, args=(conn, addr))
            thread.start()

