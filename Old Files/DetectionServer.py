import socket, time
from motiondetect import MotionDetector
from threading import Event
from Queue import Queue

EOF = b"EOF----"
TXT = b"TXT----"
IMG = b"IMG----"

def runServer(openPort=1101):
    global EOF, TXT, IMG

    cmdList = Queue()
    outList = Queue()
    stopper = Event()
    process = MotionDetector(cmdList, outList, stopper)

    s = socket.socket()
    s.bind(("0.0.0.0", openPort))
    s.listen(1)
    print("[+] Server setup")

    #server main loop to handle each connection
    while True:
        conn, addr = s.accept()
        conn.send("CONNECTED\n")

        #handle each request
        while True:
            try:
                data = conn.recv(2048)
            except socket.error as e:
                print("[-] Connection reset")
                print(e)
                break
            if data == b"":
                conn.close()
                print("[-] Connection closed")
                break

            print "[+] Input:", data  # debugging

            if data == b"START": #start the motion detector
                if not process.is_alive():
                    if process.ident:
                        print "[i] Starting new process"
                        cmdList = Queue()
                        outList = Queue()
                        stopper = Event()
                        process = MotionDetector(cmdList, outList, stopper)
                    process.start()
                else:
                    print "[i] Process is already alive!"
            elif data == b"STOP": #stop detector
                stopper.set()
            elif data == b"KILL": #stop everything
                stopper.set()
                while not process.isStopped: #wait for process to end
                    time.sleep(1)
                s.close()
                return
            else: #send any other cmds to the MD thread itself
                cmdList.put(data)
                output = outList.get() #wait for output
                print "[+] Output:", output # debugging
                if output == IMG: #for the special case of sending an img
                    conn.send(IMG + process.dataToBeFetched + EOF)

runServer()
