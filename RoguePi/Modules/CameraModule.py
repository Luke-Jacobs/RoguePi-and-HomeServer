from threading import Thread
from picamera import PiCamera
from Queue import Queue
import io
import time

TXT = "TXT----"
PIC = "PIC----"
EOF = "----EOF"

class Camera(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.camera = None
        self.stopThread = False
        self.taskList = Queue()
        self.outputList = Queue()

    #call a function by string
    def __getitem__(self, item):
        if item == "SNAP":
            return self.snap()
        else:
            return TXT + "[-] Unknown camera command"


    def run(self):
        print("[+] Camera thread running")
        # init camera
        self.camera = PiCamera()
        self.camera.resolution = (640, 480)
        self.camera.framerate = 30

        while True:
            cmd = self.taskList.get(block=True)
            if cmd == "SNAP": #snap picture
                buff = io.BytesIO()
                #self.camera.start_preview() # Camera warm-up time
                #time.sleep(2)
                self.camera.capture(buff, 'jpeg')
                buff.seek(0)
                picData = buff.read()
                print("[i] Pic data: %d" % len(picData))
                self.outputList.put(PIC + picData + EOF)
            elif cmd == "STOP":
                break

        self.camera.close()

    def stop(self):
        self.taskList.put("STOP")
        return

    def snap(self):
        self.taskList.put("SNAP")
        return self.outputList.get(block=True)

    def status(self):
        if self.is_alive():
            return TXT + "[+] Thread is running"
        else:
            return TXT + "[-] Thread is not running"
