from threading import Thread
from picamera import PiCamera
from Queue import Queue
import io
import time

TXT = "TXT----"
PIC = "PIC----"
EOF = "----EOF"


class Camera(Thread):

    HELP = """
    PURPOSE:
        To retrieve a live picture from the device.
    FUNCTIONS:
        snap"""

    def __init__(self):
        Thread.__init__(self)
        self.camera = None
        self.stopThread = False
        self.taskList = Queue()
        self.outputList = Queue()

    # Call a function by string
    def __getitem__(self, arguments):
        # Item is a list of arguments
        if arguments == ["snap"]:
            if not self.is_alive():  # If we didn't has this, the process would block forever
                return TXT + "[-] Cannot snap an image if the module is not running!"
            self.taskList.put("snap")
            return self.outputList.get(block=True)
        elif arguments == ["help"]:
            return TXT + self.HELP
        else:
            return TXT + "[-] Unknown camera command"

    def run(self):
        print("[+] Camera thread running")
        # Initialize camera
        self.camera = PiCamera()
        self.camera.resolution = (640, 480)
        self.camera.framerate = 30

        while True:
            cmd = self.taskList.get(block=True)
            if cmd == "snap":  # Snap picture
                buff = io.BytesIO()
                self.camera.capture(buff, 'jpeg')
                buff.seek(0)
                picData = buff.read()
                print("[i] Pic data: %d" % len(picData))
                self.outputList.put(PIC + picData + EOF)
            elif cmd == "stop":
                print('[i] Camera module stopping')
                break

        self.camera.close()

    def stop(self):
        self.taskList.put("stop")
        return

    def status(self):
        if self.is_alive():
            return TXT + "[+] Thread is running"
        else:
            return TXT + "[-] Thread is not running"
