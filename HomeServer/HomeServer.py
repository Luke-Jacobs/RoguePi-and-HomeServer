import socket  # For networking
import sys  # For writing to console
import logging  # For debugging
from threading import Thread, Lock  # For non-blocking user input
from Queue import Queue  # For interacting with the user input thread

SERVERPORT = 8554

# Data type tags
TXT = "TXT----"
PIC = "PIC----"
EOF = "----EOF"


class InputHandler(Thread):
    """A thread to grab user input without having to wait for it (non-blocking)."""

    # Python enum for input tasks
    ASK_FOR_FILENAME = 0
    DEFAULT_FILENAME = 'test.bin'

    def __init__(self):
        Thread.__init__(self)
        self.stdin = Queue()  # A place to store user input where the main thread can access it
        self.inputTasks = Queue()  # A place to store special input tasks that the main thread needs done

    def run(self):
        """Run in the background grabbing user input."""
        while True:
            stdin = str(raw_input())  # Get input from user
            logging.debug('STDIN: %s' % stdin)
            if not self.inputTasks.empty():
                newTask = self.inputTasks.get(block=False)
                if newTask[0] == self.ASK_FOR_FILENAME:  # If the main thread wants us to ask for a filename
                    if not stdin:  # If the user chooses default
                        stdin = self.DEFAULT_FILENAME
                    with open(stdin, "wb") as fp:
                        fp.write(newTask[1])  # Write the file data coupled with the taskname
                    sys.stdout.write("[+] Written data to %s\n>>" % stdin)
            else:  # If the user is just entering a command
                self.stdin.put(stdin)  # Put commandline data into a shared variable

    def clear(self):
        self.stdin = Queue()  # Delete contents of old Queue and start again

    def newLine(self):
        """For pretty console interaction."""
        if self.inputTasks.empty():
            sys.stdout.write('>>')


def manageConnection(conn, userInput):
    """Handle PING/PONG, send user commands, and present RPi data."""
    PONG = b"PONG"
    PING = b"PING"
    try:
        # Manage the connection until we encounter an error (at that point return)
        while True:
            # Grab a chunk of data from the stream
            data = conn.recv(2048)

            # Reply with PING (and a command from userInput)
            reply = b""
            if data.count(PING):  # if server wants us to ping
                logging.debug('[RECV] Received PING')
                reply += PONG
            # Handle commands
            if not userInput.stdin.empty():
                command = userInput.stdin.get(block=False)
            else:
                command = None
            if command is not None:  # If our thread has user input waiting for us
                reply += command.encode()
            logging.debug('[SEND] Responding with: %s' % reply)
            conn.send(reply)

            # If we received data that should be presented
            if data.count(TXT):
                data = data[len(TXT):]
                sys.stdout.write("\n%s\n" % data)
                userInput.newLine()

            if data.count(PIC):
                sys.stdout.write("[+] Receiving picture...")
                # Receive bits of the picture and combine them
                data = data[len(PIC):]
                while data.find(EOF) == -1:
                    data += conn.recv(2048)
                    logging.debug(len(data))
                conn.send(b"PONG")  # <-- the RPi might timeout before we send this FIXME
                sys.stdout.write("done\n")
                data = data[:-len(EOF)]  # take away the EOF
                # Ask user where to save this file data
                sys.stdout.write('Filename to store image data [%s]: ' % userInput.DEFAULT_FILENAME)
                userInput.inputTasks.put((InputHandler.ASK_FOR_FILENAME, data))

            if data == b"":
                print("\n[-][SOCKET] Closed connection...")
                break
    except Exception as e:
        print("\n[-][SOCKET] Exception: %s" % str(e))


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
        sys.stdout.write("Listening for connections...\n")
        conn, addr = s.accept()
        sys.stdout.write("Accepted connection: %s on port %d\n>>" % addr)
        conn.settimeout(CONNECTION_TIMEOUT)
        userInput.clear()  # Clear user input for new connection
        manageConnection(conn, userInput)  # Returns when an error happens


if __name__ == '__main__':
    waitForConnections()

