import socket
import sys
import time
import logging
from threading import Thread, Lock

SERVERPORT = 8554

TXT = "TXT----"
PIC = "PIC----"
EOF = "----EOF"

bufferLock = Lock()


class InputHandler(Thread):
    """A thread to grab user input without having to wait for it (non-blocking)."""

    def __init__(self):
        Thread.__init__(self)
        self.cmd = ""  # A place to store user input where the main thread can access it

    def run(self):
        """Run in the background grabbing user input."""
        global bufferLock
        # User input
        while True:
            newCommand = str(raw_input())  # Get input from user
            logging.debug('CMD: %s' % newCommand)
            bufferLock.acquire()  # Get access to the shared 'cmd' value
            self.cmd = newCommand  # Set cmd to user value
            print('Stored command: %s' % self.cmd)
            bufferLock.release()  # Allow main thread to retrieve the value of 'cmd'

    def clear(self):
        self.cmd = ""


def manageConnection(conn, userInput):
    """Handle PING/PONG, send user commands, and present RPi data."""
    try:
        #
        while True:
            data = conn.recv(2048)

            # Reply with PING (and a command from userInput)
            bufferLock.acquire()
            # print(userInput.cmd)
            if data.count("PING"):  # if server wants us to ping
                # sys.stdout.write('[SEND] Responding to PING with command: %s' % userInput.cmd)
                # Send PONG response first, then the command we got from the InputHandler thread
                conn.send(b"PONG" + userInput.cmd.encode())
            else:
                if userInput.cmd:
                    # print('[SEND] Received no PING, so just sending: %s' % userInput.cmd)
                    conn.send(userInput.cmd.encode())
            userInput.cmd = ""
            bufferLock.release()

            # If we received data that should be presented
            if data.count(TXT):
                data = data[len(TXT):]
                sys.stdout.write("\n%s\n>>" % data)

            if data.count(PIC):
                sys.stdout.write("[+] Receiving picture...")
                data = data[len(PIC):]
                while data.find(EOF) == -1:
                    data += conn.recv(2048)
                    logging.debug(len(data))
                sys.stdout.write("done\n")
                data = data[:-len(EOF)]  # take away the EOF
                # TODO Ask user for filename
                with open("2.jpeg", "wb") as fp:
                    fp.write(data)
                sys.stdout.write("[+] Written data to 2.jpeg\n>>")
                conn.send(b"PONG")  # <-- might not work

            if data == b"":
                print("\n[-][SOCKET] Closed connection...")
                break

    except Exception as e:
        print("\n[-][SOCKET] Exception: %s" % e)


def waitForConnections():
    """Wait for connections from the Raspberry Pi. If we get a connection, call manageConnection."""
    # Constants for this function
    CONNECTION_TIMEOUT = 15
    # Start the thread for non-blocking stdin reading
    userInput = InputHandler()
    userInput.start()
    # Look for connections continuously
    while True:
        s = socket.socket()  # Create TCP socket object
        s.bind(("0.0.0.0", SERVERPORT))  # Accept a connection from any address (domain name or ip)
        s.listen(1)  # Listen for 1 device
        print "Listening for connections..."
        conn, addr = s.accept()
        print "Accepted connection: ", addr
        conn.settimeout(CONNECTION_TIMEOUT)
        userInput.clear()  # Clear user input for new connection
        manageConnection(conn, userInput)  # Returns when an error happens


if __name__ == '__main__':
    waitForConnections()

