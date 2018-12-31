from threading import Thread
from Queue import Queue
from picamera import PiCamera

TXT = "TXT----"

class Timelapse(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.nPictures = 60
        self.nPicturesTaken = 0
        self.nDelay = 10
        self.folder = "/home/pi/timelapse/"

        self.taskList = Queue()

    #call a function by string
    def __getitem__(self, item):
        parts = item.split(" ")
        if len(parts) > 1 and parts[0] == "SETUP": #if commmand and args
            return self.setup(int(parts[1]), int(parts[1]), parts[2])
        else: #if junk command
            return TXT + "[-] Unknown timelapse command"

    def setup(self, nPictures=None, nDelay=None, folder=None):
        if nPictures: self.nPictures = nPictures
        if nDelay: self.nDelay = nDelay
        if folder: self.folder = folder
        return TXT + "[i] Setup timelapse"

    def status(self):
        if self.is_alive():
            return TXT + "[+] Thread has taken %d pictures out of %s" % \
                   (self.nPicturesTaken, self.nPictures)
        else:
            return TXT + "[-] Thread not running"

    def stop(self):
        self.taskList.put("STOP")
        return

    def run(self):
        print("[+] Timelapse thread running")
        # init camera
        self.camera = PiCamera()
        self.camera.resolution = (640, 480)
        self.camera.framerate = 30

        while True:
            #respond to any commmands
            cmd = ""
            try: cmd = self.taskList.get(block=False)
            except: pass #if empty

            if cmd == "STOP":
                break
            #take picture
            picPath = "%s%d.jpeg" % (self.folder, self.nPicturesTaken)
            self.camera.capture(picPath)
            self.nPicturesTaken += 1

        self.camera.close()
