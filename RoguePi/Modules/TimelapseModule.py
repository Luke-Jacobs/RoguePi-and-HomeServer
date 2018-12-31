from threading import Thread
from Queue import Queue, Empty
from picamera import PiCamera
from os import makedirs, path
import time

TXT = "TXT----"


class Timelapse(Thread):

    HELP = """
    PURPOSE:
        Takes a pretty timelapse (if you put it in a pretty spot).
    FUNCTIONS:
        setup [n pictures] [n delay in secs] [folder to save images]
        status
    """

    def __init__(self):
        Thread.__init__(self)
        self.nPictures = 60
        self.nPicturesTaken = 0
        self.nDelay = 10
        self.folder = "/home/pi/timelapse/"
        self.taskList = Queue()

    # Call a function by string
    def __getitem__(self, arguments):
        if len(arguments) > 1 and arguments[0] == "setup":  # If commmand and args
            return self.setup(int(arguments[1]), int(arguments[1]), arguments[2])
        elif arguments == ["help"]:
            return TXT + self.HELP
        else:  # if unknown command
            return TXT + "[-] Unknown timelapse command"

    def setup(self, nPictures=None, nDelay=None, folder=None):
        if nPictures:
            self.nPictures = nPictures
        if nDelay:
            self.nDelay = nDelay
        if folder:
            self.folder = folder
        return TXT + "[i] Setup timelapse"

    def status(self):
        return TXT + "[+] Thread has taken %d pictures out of %s. It is %s" % \
               (self.nPicturesTaken, self.nPictures, "ALIVE" if self.is_alive() else "DEAD")

    def stop(self):
        self.taskList.put("stop")
        return

    def run(self):
        print("[+] Timelapse thread running")
        # Init camera
        self.camera = PiCamera()
        self.camera.resolution = (640, 480)
        self.camera.framerate = 30
        # Setup write directory
        if not path.exists(self.folder):
            makedirs(self.folder)  # Make folder if it doesn't exist
        # Reset variables
        self.nPicturesTaken = 0
        while True:
            # Respond to any commmands
            try:
                cmd = self.taskList.get(block=False)
            except Empty:
                cmd = ""

            # Stop signal
            if cmd == "stop":
                break

            # Take picture
            if self.nPicturesTaken == self.nPictures:
                break  # Stop the timelapse
            picPath = "%s%d.jpg" % (self.folder, self.nPicturesTaken)
            print 'Taking image %d for timelapse' % self.nPicturesTaken
            # Capture and write image to file
            fp = open(picPath, 'wb')
            self.camera.capture(fp)
            fp.close()
            self.nPicturesTaken += 1
            # Wait a certain time
            time.sleep(self.nDelay)
        # Release resource
        self.camera.close()
