import requests, json, time, sys, socket, subprocess, signal, select
import RPi.GPIO as GPIO
import logging
from PiExecute import PiExecute

# Debug
logging.basicConfig(filename='connector.log', level=logging.DEBUG)
console_log = logging.StreamHandler()
console_log.setLevel(logging.DEBUG)
log = logging.getLogger()
log.addHandler(console_log)
log.setLevel(logging.DEBUG)
log.info('-'*10 + 'NEW RUN' + '-'*10)

# Constants
TXT = "TXT----"


class VisualOutput(Thread):
    """A class to interact with GPIO lighting."""

    wifiLight = 7
    internetLight = 10
    connectionLight = 12
    pingLight = 13
    all = (wifiLight, internetLight, connectionLight, pingLight)

    def __init__(self):
        """Setup all the lights."""
        GPIO.setmode(GPIO.BOARD)
        for light in self.all:
            GPIO.setup(light, GPIO.OUT)

    def off(self):
        """Turn all lights off."""
        for light in self.all:
            GPIO.output(light, 0)


class HomeConnector:

    HOMEPORT = 8554

    # Constants
    loginPostUrl = "https://wifilogin.xfinity.com/user_login.php"
    loginPageUrl = "https://wifilogin.xfinity.com/start.php"
    hashIdentifiers = ("'hash': \"", "\"")
    macIdentifiers = ("'client_mac': \"", "\"")
    geturlIdentifiers = ("'get_url': \"", "\"")

    loginPortal = "/portal_captive.php"
    testURL = "google.com"

    @staticmethod
    def exit(signal, frame):
        logging.info("Exiting...")
        pinsOff()
        HomeConnector.killVPN()
        # PiExecute("KILLALL")
        sys.exit(0)

    def __init__(self, xfinityUsername, xfinityPassword):
        """Initialize connector."""
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
    def attendToConnection(conn):
        global pingPin
        LARGE_FILE_TIMEOUT = 5
        PING_SLEEP = 2
        COMMAND_WAIT = 3

        logging.debug('Attending to connection...')
        while True:
            try:
                # send ping and wait for pong
                log.info("[i] Sending PING...")
                conn.send(b"PING")
                GPIO.output(pingPin, 1)  # Light up status light
                resp = conn.recv(4)
                if resp != b"PONG":
                    log.info("[-] Unusual response from home: %s" % resp)
                else:
                    log.info("[+] Received PONG!")
                    GPIO.output(pingPin, 0)

                # receive and execute commands
                ready = select.select([conn], [], [], COMMAND_WAIT)
                if ready[0]:  # if command ready
                    cmd = conn.recv(2048)
                    log.info("[+] Got data: %s" % cmd)
                    response = PiExecute(cmd)
                    if not response:
                        response = TXT + "[-] Run CMD returned None"
                    # log.info("[i] Server response: %s" % response)
                    conn.sendall(response)
                    if len(response) > 2048:  # extra time
                        time.sleep(LARGE_FILE_TIMEOUT)
                    time.sleep(PING_SLEEP)  # sleep a little before pinging

            except Exception, e:
                log.info("[-] Home sending/receiving error: %s" % str(e))
                break
        GPIO.output(pingPin, 0)
        logging.error('Leaving attend connection function -> back to debugging connection')

    def getConnection(self):
        """Return a socket after attempting to connect to the HomeBase server."""

        # Constants
        NO_WIFI_SLEEP = 3
        LOSE_CONNECTION_TIMEOUT = 20
        LOGIN_TIMEOUT = 2
        HOME_SOCKET_TIMEOUT = 15
        HOME_SOCKET_RETRIES = 3

        # Setup
        setupPins()
        pinsOff()

        while True:  # Main loop
            logging.info('Checking wifi...')

            while self.checkWifi():  # If connected to some wifi
                log.info(green("[+] Connected to wifi"))
                GPIO.output(pin1, 1)

                log.info('Checking login...')
                while self.login():  # If can access internet
                    # Update log/lights
                    log.info(green("[++] Can access internet"))
                    GPIO.output(pin2, 1)

                    # Try to connect to home
                    log.info("Trying to connect to home...")
                    self.socket = socket.socket()
                    self.socket.settimeout(HOME_SOCKET_TIMEOUT)  # Initial connection
                    nFails = 0
                    for i in range(HOME_SOCKET_RETRIES):  # retries for connection before checking wifi
                        if self.attemptHomeConnection():
                            break
                        else:
                            log.info('Failed home socket connection')
                            nFails += 1
                    if nFails == HOME_SOCKET_RETRIES:  # if both attempts failed
                        log.info('[--] Exceeded number of home socket retries!')
                        del self.socket
                        continue

                    # If can access home
                    log.info(green("[+++] Connected to home base!"))
                    GPIO.output(pin3, 1)
                    self.socket.settimeout(LOSE_CONNECTION_TIMEOUT)  # timeout for losing connection

                    self.attendToConnection(self.socket)  # Run commands and PING/PONG to maintain connection

                # if internet connection broke
                log.info(red("[--] Internet login unsuccessful"))
                GPIO.output(pin2, 0)
                time.sleep(LOGIN_TIMEOUT)

            # if no wifi connection
            GPIO.output(pin1, 0)
            log.info(red("[-] Wifi connection broken"))
            time.sleep(NO_WIFI_SLEEP)  # wait for wifi connection

    @staticmethod
    def getBetween(identifiers, haystackStr):
        """Get a section of text in between two identifiers."""
        startLoc = haystackStr.find(identifiers[0]) + len(identifiers[0])
        endLoc = haystackStr[startLoc:].find(identifiers[1]) + startLoc
        return haystackStr[startLoc:endLoc]

    @staticmethod
    def checkWifi():
        """Checks to see if the RPi is connected to Wifi."""
        try:
            subprocess.check_output("iwgetid")
            return True
        except subprocess.CalledProcessError:  # if not connected
            return False

    def login(self):
        """
        Get info needed to login to user_login and then login
        :param startPage:
        :return:
        """

        # Get redirect page
        page = self.session.get("http://%s" % self.testURL)
        if self.loginPortal in page.url:  # If we receive a portal login
            logging.info('Received login portal...')
        elif self.testURL in page.url:  # If we receive Google
            log.info('Received test page. You are already logged in.')
            return True
        else:
            raise RuntimeError('Received an unknown page URL')

        # Collect form data
        self.loginForm['hash'] = self.getBetween(self.hashIdentifiers, page.text)
        self.loginForm['client_mac'] = self.getBetween(self.macIdentifiers, page.text)
        self.loginForm['get_url'] = self.getBetween(self.geturlIdentifiers, page.text)
        print "Sending form: %s" % str(self.loginForm)

        # Send form data and wait on response
        resp = self.session.post(self.loginPostUrl, data=self.loginForm)
        if resp.status_code != 200:
            print('Bad response from server after sending form! Code: %d' % resp.status_code)
        resp = json.loads(resp.text)
        if resp['response'] == 'Success':
            print('Successful login response!')
            return True
        else:
            print('Login response failed!')
            return False

    def attemptHomeConnection(self):
        try:
            self.socket.connect(("67.184.6.29", self.HOMEPORT))
            return True
        except Exception, e:
            log.warn("Error: %s" % str(e))
            return False

    # VPN functions

    @staticmethod
    def killVPN():
        """Kill the VPN process running in the background."""
        try:
            vpnProcesses = subprocess.check_output("ps -A | grep vpn", shell=True).split("\n")
        except subprocess.CalledProcessError:
            return True
        log.info("[i] ps returned: %s" % repr(vpnProcesses))
        vpnProcesses.remove("")
        for proc in vpnProcesses:
            id = proc.split(" ")[1]
            log.info("[i] Killing vpn process (%s)" % id)
            subprocess.Popen("sudo kill -9 %s" % id, shell=True)

    @staticmethod
    def startVPN():
        try:
            vpnProcesses = subprocess.check_output("ps -A | grep vpn", shell=True)
        except subprocess.CalledProcessError:
            vpnProcesses = None

        if not vpnProcesses or vpnProcesses.count("defunct"):  # if not running
            log.info("[i] Starting VPN...")
            p = subprocess.Popen("openvpn /etc/openvpn/vpngate_japan.ovpn", shell=True, stdout=subprocess.PIPE)  # start vpn
            if p:
                while True:  # wait till vpn is done starting
                    line = p.stdout.readline()
                    if line.count("Sequence Complete"):
                        break
                    log.info("[+] VPN Connected!")
            return True
        else:
            log.info("[i] VPN is already running")
            return False


#colored text
RED = "\033[0;31m"
GREEN = "\033[0;32m"
NC = "\033[0m"

def red(txt): return RED+txt+NC
def green(txt): return GREEN+txt+NC


if __name__ == '__main__':
    username = 'jeffnkarajacobs@yahoo.com'
    password = 'Luke5wim5fa5t'
    con = HomeConnector(username, password)
    con.getConnection()
